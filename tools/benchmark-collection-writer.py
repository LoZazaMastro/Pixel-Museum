#!/usr/bin/env python3
"""Exercise only the writer's isolated probe namespace; no application data changes."""
from pathlib import Path
from ftplib import FTP, error_perm
import argparse, hashlib, io, json, secrets, socket, struct, time

ROOT = Path(__file__).resolve().parents[1]
MARKER = b'PIXEL-MUSEUM-COLLECTION-WRITER-V1'
MAGIC = b'PMCW001\0'


def exact(sock, count):
    data = bytearray()
    while len(data) < count:
        part = sock.recv(count - len(data))
        if not part:
            raise RuntimeError('Writer closed the channel: ' + repr(bytes(data)))
        data.extend(part)
    return bytes(data)


def ack(sock):
    value = exact(sock, 24)
    if value[:4] != b'PMA1':
        raise RuntimeError('Unexpected writer response: ' + repr(value))
    code, offset, pid = struct.unpack('>IQQ', value[4:])
    if code:
        raise OSError(code, 'Writer rejected request')
    return offset, pid


def request(sock, command, value=0, body=b''):
    sock.sendall(b'PMC1' + struct.pack('>IQ', command, value))
    if body:
        sock.sendall(body)
    return ack(sock)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--host', default='192.168.1.56')
    parser.add_argument('--mib', type=int, default=64, choices=(64, 128, 256, 512))
    args = parser.parse_args()
    elf = bytearray((ROOT / 'build/collection-writer/collection_writer.elf').read_bytes())
    shoff = struct.unpack_from('<Q', elf, 40)[0]
    shsize, shcount = struct.unpack_from('<HH', elf, 58)
    assert elf[:4] == b'\x7fELF' and shoff + shsize * shcount == len(elf)
    assert elf.count(MARKER) == 1
    at = elf.index(MARKER)
    assert at + 16384 <= len(elf)
    source = ROOT / 'build/collection-delivery-20261031/packs/images-001.tar'
    with source.open('rb') as file:
        body = file.read(args.mib << 20)
    assert len(body) == args.mib << 20
    sha = hashlib.sha256(body).hexdigest()
    nonce = secrets.token_bytes(32)
    config = MAGIC + struct.pack('>II', 0, 1) + nonce + struct.pack('>I', 1)
    config += sha.encode('ascii') + struct.pack('>Q', len(body))
    elf[at:at + 16384] = config.ljust(16384, b'\0')
    probe = '/data/pixel-museum-writer-probe-' + nonce.hex()
    assert probe.startswith('/data/pixel-museum-writer-probe-')
    report = dict(status='PLAN_ONLY', bytes=len(body), namespace=probe,
                  app_data_untouched=True, transport='loader-owned private stdin/stdout')
    if not args.execute:
        print(json.dumps(report, indent=2)); return
    with socket.create_connection((args.host, 9021), timeout=10) as sock:
        sock.settimeout(30)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.sendall(elf)  # ELF framing ends at section table; DO NOT half-close.
        sock.sendall(MAGIC + nonce)
        _, pid = ack(sock)
        offset, _ = request(sock, 1, 0)
        assert offset == 0
        begin = time.monotonic()
        for offset in range(0, len(body), 2 << 20):
            block = body[offset:offset + (2 << 20)]
            written, _ = request(sock, 2, len(block), block)
            assert written == offset + len(block)
        durable, _ = request(sock, 3)
        elapsed = time.monotonic() - begin
        assert durable == len(body)
        with FTP() as ftp:
            ftp.connect(args.host, 2121, timeout=12); ftp.login('anonymous', 'codex')
            received = io.BytesIO()
            ftp.retrbinary('RETR ' + probe + '/downloads/' + sha + '.tar.part', received.write)
            assert hashlib.sha256(received.getbuffer()).hexdigest() == sha
        report.update(status='PASS_NATIVE_HELPER_DURABLE_BYTES_SHA_READBACK', pid=pid,
                      seconds=elapsed, mib_per_second=args.mib / elapsed, sha256=sha)
        output = ROOT / 'build/collection-delivery-20261031/native-payload-writer-probe.json'
        output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
        print(json.dumps(report, indent=2), flush=True)
        request(sock, 4)
    with FTP() as ftp:
        ftp.connect(args.host, 2121, timeout=12); ftp.login('anonymous', 'codex')
        for attempt in range(20):
            try:
                ftp.sendcmd('MLST ' + probe)
            except error_perm as error:
                if not str(error).startswith('550 No such'):
                    raise
                break
            time.sleep(.1)
        else:
            raise RuntimeError('Probe cleanup not complete')
    report['probe_cleanup'] = 'PASS_ABSENT'
    output = ROOT / 'build/collection-delivery-20261031/native-payload-writer-probe.json'
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
