#!/usr/bin/env python3
"""Probe the native remover only in its isolated writer-probe namespace."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import secrets
import socket
import struct
from ftplib import FTP

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--host', default='192.168.1.56')
    parser.add_argument('--bootstrap-cycles', action='store_true', help='Test two fresh app-owned0700 roots, with REMOVE between sessions')
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('pmcw_probe', ROOT / 'tools/benchmark-collection-writer.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    elf = bytearray((ROOT / 'build/collection-writer/collection_writer.elf').read_bytes())
    assert elf.count(helper.MARKER) == 1
    nonce = secrets.token_bytes(32)
    body = b'Pixel Museum isolated native removal probe\n' * 1024
    sha = hashlib.sha256(body).hexdigest()
    config = helper.MAGIC + struct.pack('>II', 0, 1) + nonce + struct.pack('>I', 1)
    config += sha.encode('ascii') + struct.pack('>Q', len(body))
    at = elf.index(helper.MARKER)
    elf[at:at + 16384] = config.ljust(16384, b'\0')
    fixture_elf = None
    if args.bootstrap_cycles:
        fixture_elf = bytearray((ROOT / 'build/research/collection-removal-crashfix/native-bootstrap-fixture.elf').read_bytes())
        assert fixture_elf.count(helper.MARKER) == 1
        fixture_at = fixture_elf.index(helper.MARKER)
        fixture_elf[fixture_at:fixture_at + 16384] = config.ljust(16384, b'\0')
    prefix = '/data/pixel-museum-writer-probe-'
    probe = prefix + nonce.hex()
    assert len(probe) == len(prefix) + 64
    report = dict(namespace=probe, production_collection_untouched=True,
                  helper_sha256=hashlib.sha256((ROOT / 'build/collection-writer/collection_writer.elf').read_bytes()).hexdigest(),
                  transport='native elfldr merged stdout/stderr', status='PLAN_ONLY',
                  bootstrap_cycles=args.bootstrap_cycles, cycles=[])
    if not args.execute:
        print(json.dumps(report)); return
    report['status'] = 'STARTED'
    output = ROOT / 'build/research/collection-removal-crashfix'
    output.mkdir(parents=True, exist_ok=True)
    try:
        for cycle in range(2 if args.bootstrap_cycles else 1):
            row = dict(cycle=cycle + 1)
            report['active_cycle'] = cycle + 1
            if fixture_elf is not None:
                with socket.create_connection((args.host, 9021), timeout=8) as channel:
                    channel.settimeout(15)
                    channel.sendall(fixture_elf)
                    channel.sendall(helper.MAGIC + nonce)
                    raw_fixture = helper.exact(channel, 24)
                    assert raw_fixture[:4] == b'PMA1', repr(raw_fixture)
                    fixture_code, identity, fixture_pid = struct.unpack('>IQQ', raw_fixture[4:])
                    if fixture_code:
                        report['fixture_error'] = dict(errno=fixture_code, stage=identity >> 32,
                                                       detail=identity & 0xffffffff, pid=fixture_pid)
                        raise OSError(fixture_code, 'Native bootstrap fixture failed')
                    row.update(fixture_pid=fixture_pid, fixture_uid=identity >> 32,
                               fixture_gid=identity & 0xffffffff, fixture_mode='0700')
                    assert (row['fixture_uid'], row['fixture_gid']) == (1, 1)
                    assert channel.recv(256) == b''
            with socket.create_connection((args.host, 9021), timeout=8) as channel:
                channel.settimeout(15)
                channel.sendall(elf)
                channel.sendall(helper.MAGIC + nonce)
                _, pid = helper.ack(channel)
                row['hello'] = 'PASS'
                assert helper.request(channel, 1, 0)[0] == 0
                assert helper.request(channel, 2, len(body), body)[0] == len(body)
                assert helper.request(channel, 3)[0] == len(body)
                row['open_data_finish'] = 'PASS'
                channel.sendall(b'PMC1' + struct.pack('>IQ', 5, 0))
                raw = helper.exact(channel, 24)
                assert raw[:4] == b'PMA1', repr(raw)
                code, value, response_pid = struct.unpack('>IQQ', raw[4:])
                assert response_pid == pid
                row.update(status='PASS' if not code else 'FAIL_NATIVE_REMOVE', errno=code,
                           stage=value >> 32, detail=value & 0xffffffff, pid=pid,
                           clean_eof=channel.recv(256) == b'')
            with FTP() as ftp:
                ftp.connect(args.host, 2121, timeout=8)
                ftp.login('anonymous', 'codex')
                row['probe_absent'] = probe.rsplit('/', 1)[1] not in ftp.nlst('/data')
            report['cycles'].append(row)
            report.update({key: row[key] for key in ('status', 'errno', 'stage', 'detail', 'pid', 'clean_eof', 'probe_absent')})
            assert row['status'] == 'PASS' and row['probe_absent'] and row['clean_eof']
    except Exception as error:
        report.update(status='FAIL_NATIVE_PROBE', error=repr(error))
    finally:
        text = json.dumps(report, indent=2) + '\n'
        (output / ('native-probe-' + nonce.hex() + '.json')).write_text(text, encoding='utf-8')
        (output / 'native-merged-channel-last.json').write_text(text, encoding='utf-8')
        print(json.dumps(report), flush=True)
    if report['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
