#!/usr/bin/env python3
"""Stage the small image-collection edition without modifying the full dist."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(8 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'dist/PPSA70421')
    parser.add_argument('--delivery', type=Path, default=ROOT / 'build/collection-delivery-20261031')
    parser.add_argument('--eboot', type=Path, help='Fresh CollectionInstaller-enabled executable, supplied by final build')
    parser.add_argument('--zip', action='store_true', help='Create verified base ZIP; requires explicit --eboot and finished packs')
    args = parser.parse_args()
    if args.zip and not args.eboot:
        parser.error('--zip requires explicit --eboot from the new build')
    base = args.delivery / 'base/PPSA70421'
    base.mkdir(parents=True, exist_ok=True)
    expected = set()
    copied = 0

    def copy_changed(source, destination):
        nonlocal copied
        if destination.exists():
            before, after = source.stat(), destination.stat()
            if (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns):
                return
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied += 1
    for directory, children, filenames in os.walk(args.source):
        relative = Path(directory).relative_to(args.source)
        if relative.as_posix() == 'assets':
            children[:] = [child for child in children if child != 'images']
        for filename in filenames:
            source = Path(directory) / filename
            rel = source.relative_to(args.source)
            # Only these resources follow the new installer UI. All remaining
            # content stays byte-identical to the already previously distributed stable build.
            if rel.parts[:2] in (('content', 'ui-locales'), ('assets', 'fonts')):
                continue
            destination = base / rel
            if not (args.eboot and rel.as_posix() == 'eboot.bin'):
                copy_changed(source, destination)
            expected.add(rel.as_posix())
    for folder in ('content/ui-locales', 'assets/fonts'):
        for source in (ROOT / folder).rglob('*'):
            if source.is_file():
                rel = source.relative_to(ROOT)
                copy_changed(source, base / rel)
                expected.add(rel.as_posix())
    manifest = Path('assets/images/manifest.json')
    (base / manifest).parent.mkdir(parents=True, exist_ok=True)
    copy_changed(args.source / manifest, base / manifest)
    expected.add(manifest.as_posix())
    pending = []
    for name in ('collection-files.json', 'collection-packs.json'):
        source = args.delivery / 'packs' / name
        if source.exists():
            copy_changed(source, base / 'content' / name)
            expected.add('content/' + name)
        else:
            pending.append(name)
    if args.eboot:
        assert args.eboot.is_file()
        copy_changed(args.eboot, base / 'eboot.bin')
    parameter_path = base / 'sce_sys/param.json'
    parameters = json.loads(parameter_path.read_text(encoding='utf-8'))
    parameters['contentVersion'] = '00.001.001'
    # /download0 holds the full persistent image collection plus one verified
    # temporary pack and bounded caches. The stable source dist stays untouched.
    parameters['downloadDataSize'] = 16384
    parameter_text = json.dumps(parameters, ensure_ascii=False, indent=2) + '\n'
    if parameter_path.read_text(encoding='utf-8') != parameter_text:
        parameter_path.write_text(parameter_text, encoding='utf-8')
    actual = {p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}
    assert actual == expected, 'Unexpected staging files; no files were deleted'
    files = [{'path': name, 'bytes': (base / name).stat().st_size} for name in sorted(expected)]
    report = {'status': 'READY_NEW_EXECUTABLE' if args.eboot and not pending else 'STAGED_REQUIRES_FINAL_EXECUTABLE_OR_PACK_MANIFEST',
              'source_dist_unchanged': True, 'base_root': str(base), 'pending': pending,
              'new_eboot_supplied': bool(args.eboot), 'eboot_sha256': digest(base / 'eboot.bin'),
              'copied_files_this_run': copied,
              'updated_resources': ['content/ui-locales from current source', 'assets/fonts from current source'],
              'contentVersion': '00.001.001',
              'downloadDataSize': 16384,
              'parameter_override': 'Only staged sce_sys/param.json; published stable dist untouched',
              'files': files, 'bytes': sum(row['bytes'] for row in files),
              'installation_note': 'An internet connection is required for the initial image collection download. Original-quality images are stored persistently for later use. The full preloaded-image package is also available.'}
    if args.zip:
        assert not pending, 'Image packs must finish before creating ZIP'
        output = args.delivery / 'PPSA70421-Store.zip'
        assert not output.exists(), 'Refusing to overwrite a delivered ZIP'
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
            for row in files:
                archive.write(base / row['path'], 'PPSA70421/' + row['path'])
        assert output.stat().st_size < 2 * 1024 ** 3, 'ZIP exceeds release asset limit'
        with zipfile.ZipFile(output) as archive:
            assert archive.testzip() is None
            assert {i.filename.removeprefix('PPSA70421/'): i.file_size for i in archive.infolist()} == {row['path']: row['bytes'] for row in files}
        report.update(zip=str(output), zip_bytes=output.stat().st_size, zip_sha256=digest(output), status='PASS_BASE_ZIP_CRC_INVENTORY_NEW_EXECUTABLE')
    (args.delivery / 'base-package-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('status', 'bytes', 'new_eboot_supplied', 'pending')}), flush=True)


if __name__ == '__main__':
    main()
