#!/usr/bin/env python3
"""Validate pinned, uncompressed USTAR packs and index their original file bytes."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import re
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
BLOCK = 512


def require(condition, message):
    if not condition:
        raise ValueError(message)


def octal(raw):
    require(not raw or raw[0] < 128, 'Binary TAR numbers are not USTAR octal')
    value = raw.rstrip(b'\0 ').lstrip(b' ')
    require(not value or all(c in b'01234567' for c in value), 'Invalid TAR octal field')
    return int(value or b'0', 8)


def path_field(raw):
    head, _, tail = raw.partition(b'\0')
    require(not any(tail), 'Nonzero bytes after TAR path terminator')
    return head.decode('utf-8', errors='strict')


def safe_path(name):
    p = PurePosixPath(name)
    require(name.startswith('assets/images/') and '\\' not in name and ':' not in name,
            'Unexpected collection path: ' + name)
    require(not p.is_absolute() and all(x not in ('', '.', '..') for x in name.split('/')),
            'Noncanonical collection path: ' + name)
    return name


def build(packs_directory, output, report_path=None):
    begin = time.monotonic()
    manifest_raw = (packs_directory / 'collection-packs.json').read_bytes()
    manifest = json.loads(manifest_raw)
    inventory_raw = (packs_directory / 'collection-files.json').read_bytes()
    inventory = json.loads(inventory_raw)
    require(manifest.get('schema_version') == inventory.get('schema_version') == 1, 'Unsupported schema')
    require(manifest['image_manifest_sha256'] == inventory['image_manifest_sha256'], 'Image manifest pin mismatch')
    require(re.fullmatch(r'[0-9a-f]{64}', manifest['image_manifest_sha256']), 'Invalid image manifest digest')
    expected = {}
    for item in inventory['files']:
        name = safe_path(item['path'])
        require(name not in expected and type(item['bytes']) is int and item['bytes'] >= 0, 'Invalid or duplicate inventory file')
        expected[name] = item['bytes']
    require(len(expected) == manifest['file_count'] == inventory['file_count'], 'Pinned file count mismatch')
    require(sum(expected.values()) == manifest['expanded_bytes'] == inventory['expanded_bytes'], 'Pinned expanded bytes mismatch')
    seen = set()
    result = {'schema_version': 1, 'collection_id': manifest['collection_id'],
              'image_manifest_sha256': manifest['image_manifest_sha256'], 'packs': []}
    receipts = []
    ids = set()
    for pack in manifest['packs']:
        pack_id = pack['id']
        require(re.fullmatch(r'images-[0-9]{3}', pack_id) and pack_id not in ids, 'Invalid or duplicate pack ID')
        ids.add(pack_id)
        require(pack.get('format') == 'tar', 'Only uncompressed TAR packs are supported')
        path = packs_directory / (pack_id + '.tar')
        require(path.is_file() and not path.is_symlink(), 'Missing local regular TAR: ' + str(path))
        before = path.stat()
        require(before.st_size == pack['bytes'] and before.st_size % BLOCK == 0, 'Pinned TAR size mismatch: ' + pack_id)
        digest = hashlib.sha256()
        files = []
        payload = 0
        with path.open('rb') as source:
            def read(count):
                data = source.read(count)
                require(len(data) == count, 'Truncated TAR: ' + pack_id)
                digest.update(data)
                return data

            while source.tell() < before.st_size:
                header = read(BLOCK)
                if not any(header):
                    require(source.tell() + BLOCK <= before.st_size and not any(read(BLOCK)), 'TAR requires two zero terminator blocks')
                    while source.tell() < before.st_size:
                        require(not any(read(min(8 << 20, before.st_size - source.tell()))), 'Nonzero data after TAR terminator')
                    break
                require(header[257:265] == b'ustar\x0000', 'TAR is not POSIX USTAR: ' + pack_id)
                require(octal(header[148:156]) == sum(header[:148]) + 8 * 32 + sum(header[156:]), 'TAR header checksum mismatch')
                require(header[156:157] in (b'0', b'\0'), 'Non-regular TAR member rejected')
                require(not any(header[157:257]), 'Regular TAR member has link target')
                prefix, name = path_field(header[345:500]), path_field(header[:100])
                name = safe_path(prefix + '/' + name if prefix else name)
                size = octal(header[124:136])
                require(name not in seen and name in expected and expected[name] == size, 'Unexpected, duplicate or wrong-size TAR file: ' + name)
                offset = source.tell()
                require(offset + size <= before.st_size, 'Member outside TAR bounds')
                image_manifest_digest = hashlib.sha256() if name == 'assets/images/manifest.json' else None
                remaining = size
                while remaining:
                    data = read(min(8 << 20, remaining))
                    if image_manifest_digest is not None:
                        image_manifest_digest.update(data)
                    remaining -= len(data)
                padding = (-size) % BLOCK
                if padding:
                    require(not any(read(padding)), 'Nonzero TAR file padding')
                if image_manifest_digest is not None:
                    require(image_manifest_digest.hexdigest() == manifest['image_manifest_sha256'], 'Packed image manifest digest mismatch')
                seen.add(name)
                files.append({'path': name, 'offset': offset, 'bytes': size})
                payload += size
            else:
                raise ValueError('TAR has no terminator: ' + pack_id)
        after = path.stat()
        require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'TAR changed while indexing')
        require(digest.hexdigest() == pack['sha256'], 'Pinned TAR SHA256 mismatch: ' + pack_id)
        require(len(files) == pack['file_count'] and payload == pack['expanded_bytes'], 'Pinned per-pack inventory mismatch')
        result['packs'].append({'id': pack_id, 'sha256': pack['sha256'], 'bytes': pack['bytes'], 'files': files})
        receipts.append({'id': pack_id, 'bytes': before.st_size, 'sha256': digest.hexdigest(),
                         'files': len(files), 'payload_bytes': payload, 'mtime_ns': before.st_mtime_ns})
        print(f'{pack_id}: SHA256 PASS, {len(files)} files, {payload} payload bytes', flush=True)
    require(seen == set(expected), 'Not all pinned collection files are indexed')
    require('assets/images/manifest.json' in seen, 'Missing image manifest TAR member')
    output.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')
    with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as temp:
        temp.write(raw)
        temp_path = Path(temp.name)
    os.replace(temp_path, output)
    report = {'status': 'PASS_ALL_USTAR_PACKS_SHA256_AND_INVENTORY', 'collection_id': result['collection_id'],
              'collection_packs_sha256': hashlib.sha256(manifest_raw).hexdigest(),
              'collection_files_sha256': hashlib.sha256(inventory_raw).hexdigest(),
              'index_sha256': hashlib.sha256(raw).hexdigest(), 'index_bytes': len(raw),
              'files': len(seen), 'payload_bytes': sum(expected.values()), 'packs': receipts,
              'elapsed_seconds': round(time.monotonic() - begin, 3)}
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('status', 'files', 'index_bytes', 'elapsed_seconds')}), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packs', type=Path, default=ROOT / 'build/collection-delivery-20261031/packs')
    parser.add_argument('--output', type=Path, default=ROOT / 'content/collection-archive-index.json')
    parser.add_argument('--report', type=Path, default=ROOT / 'build/collection-delivery-20261031/archive-index-report.json')
    args = parser.parse_args()
    build(args.packs, args.output, args.report)
