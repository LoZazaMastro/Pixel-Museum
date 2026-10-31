#!/usr/bin/env python3
"""Plan/build verified, deterministic USTAR image packs without altering dist."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'dist/PPSA70421')
    parser.add_argument('--receipt', type=Path, default=ROOT / 'build/research/culture-volumes-artists-delivery-20261031/transfer.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/release-publication-20261031/image-packs')
    parser.add_argument('--collection-id', default='pixel-museum-images-20261031')
    parser.add_argument('--version', default='0.1.1')
    parser.add_argument('--max-mib', type=int, default=900)
    parser.add_argument('--base-url', help='Actual HTTPS release/download directory, required for --build')
    parser.add_argument('--build', action='store_true', help='Without this flag, write only a plan')
    args = parser.parse_args()
    if args.build and (not args.base_url or not args.base_url.startswith('https://')):
        parser.error('--build requires an actual HTTPS --base-url')
    if not 1 <= args.max_mib <= 1900:
        parser.error('--max-mib must be 1..1900')
    args.output.mkdir(parents=True, exist_ok=True)
    receipt = json.loads(args.receipt.read_text(encoding='utf-8'))
    assert receipt['status'].startswith('PASS'), 'Unverified source receipt'
    rows = []
    for row in receipt['files']:
        path = row['relative'].replace('\\', '/')
        if not path.startswith('assets/images/'):
            continue
        pure = PurePosixPath(path)
        assert not pure.is_absolute() and '..' not in pure.parts and '\\' not in path and ':' not in path
        assert len(path.encode('ascii')) <= 100, 'USTAR short filename required'
        source = args.source / path
        assert source.is_file() and not source.is_symlink()
        assert source.stat().st_size == row['bytes'], f'Source size drift: {path}'
        rows.append({'path': path, 'bytes': row['bytes'], 'sha256': row['sha256']})
    rows.sort(key=lambda row: row['path'])
    actual = {p.relative_to(args.source).as_posix() for p in (args.source / 'assets/images').rglob('*') if p.is_file()}
    assert actual == {row['path'] for row in rows}, 'Image receipt and source differ'
    assert any(row['path'] == 'assets/images/manifest.json' for row in rows)
    limit = args.max_mib << 20
    groups, group, size = [], [], 0
    for row in rows:
        stored = 512 + ((row['bytes'] + 511) // 512) * 512
        assert stored + 10240 <= limit, 'Individual file exceeds pack limit'
        if group and size + stored + 10240 > limit:
            groups.append(group)
            group, size = [], 0
        group.append(row)
        size += stored
    if group:
        groups.append(group)
    planned = [{'id': f'images-{n:03}', 'filename': f'images-{n:03}.tar', 'files': group,
                'payload_bytes': sum(row['bytes'] for row in group)} for n, group in enumerate(groups, 1)]
    plan = {'schema_version': 1, 'collection_id': args.collection_id, 'version': args.version,
            'status': 'PLAN_ONLY' if not args.build else 'BUILDING', 'format': 'USTAR uncompressed',
            'source': str(args.source), 'verified_receipt': str(args.receipt), 'receipt_sha256': sha(args.receipt),
            'max_pack_bytes': limit, 'files': len(rows), 'payload_bytes': sum(row['bytes'] for row in rows),
            'image_manifest_sha256': sha(args.source / 'assets/images/manifest.json'), 'packs': planned}
    file_index = {'schema_version': 1, 'image_manifest_sha256': plan['image_manifest_sha256'],
                  'file_count': len(rows), 'expanded_bytes': plan['payload_bytes'],
                  'files': [{'path': row['path'], 'bytes': row['bytes']} for row in rows]}
    (args.output / 'collection-files.json').write_text(json.dumps(file_index, separators=(',', ':')) + '\n', encoding='utf-8')
    (args.output / 'collection-plan.json').write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: plan[key] for key in ('status', 'files', 'payload_bytes', 'max_pack_bytes')}) + f' packs={len(planned)}', flush=True)
    if not args.build:
        return
    started = time.time()
    packs = []
    for pack in planned:
        destination = args.output / pack['filename']
        assert not destination.exists(), f'Refusing to overwrite {destination}'
        temporary = destination.with_suffix('.tar.partial')
        assert not temporary.exists(), f'Previous partial exists: {temporary}'
        with tarfile.open(temporary, 'w', format=tarfile.USTAR_FORMAT) as archive:
            for row in pack['files']:
                source = args.source / row['path']
                fingerprint = source.stat()
                info = tarfile.TarInfo(row['path'])
                info.size = row['bytes']
                info.mode = 0o644
                info.uid = info.gid = info.mtime = 0
                info.uname = info.gname = ''
                digest = hashlib.sha256()

                class Reader:
                    def __init__(self, stream):
                        self.stream = stream

                    def read(self, length=-1):
                        data = self.stream.read(length)
                        digest.update(data)
                        return data

                with source.open('rb') as stream:
                    archive.addfile(info, Reader(stream))
                assert digest.hexdigest() == row['sha256'], f'Source SHA drift: {source}'
                final = source.stat()
                assert (final.st_size, final.st_mtime_ns) == (fingerprint.st_size, fingerprint.st_mtime_ns)
        assert temporary.stat().st_size <= limit
        temporary.rename(destination)
        packs.append({'id': pack['id'], 'url': args.base_url.rstrip('/') + '/' + destination.name,
                      'bytes': destination.stat().st_size, 'sha256': sha(destination), 'format': 'tar',
                      'file_count': len(pack['files']), 'expanded_bytes': pack['payload_bytes']})
        print(f"Verified {destination.name}: {len(pack['files'])} files / {destination.stat().st_size} bytes", flush=True)
    manifest = {'schema_version': 1, 'collection_id': args.collection_id, 'version': args.version,
                'image_manifest_sha256': plan['image_manifest_sha256'], 'files': len(rows),
                'file_count': len(rows), 'expanded_bytes': plan['payload_bytes'],
                'payload_bytes': plan['payload_bytes'], 'packs': packs}
    (args.output / 'collection-packs.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    plan.update(status='PASS_SOURCE_SHA_AND_USTAR_PACKS', elapsed_seconds=round(time.time() - started, 2))
    (args.output / 'collection-plan.json').write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
    print('DONE: collection-packs.json is ready for bundled content; no dist/source files changed', flush=True)


if __name__ == '__main__':
    main()
