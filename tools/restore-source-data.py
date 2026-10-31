#!/usr/bin/env python3
"""Restore compressed authoring data and optional media from a released app."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, help='Extracted PPSA70421 folder')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    restored = 0
    for row in json.loads((root / 'source-data.json').read_bytes())['compressed_files']:
        target = (root / row['path']).resolve()
        source = (root / row['archive']).resolve()
        if not target.is_relative_to(root) or not source.is_relative_to(root):
            raise SystemExit('Invalid source-data path')
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + '.restore-tmp')
        checksum = hashlib.sha256()
        size = 0
        with gzip.open(source, 'rb') as incoming, temporary.open('wb') as output:
            while block := incoming.read(1024 * 1024):
                output.write(block)
                checksum.update(block)
                size += len(block)
        if checksum.hexdigest() != row['sha256'] or size != row['bytes']:
            temporary.unlink()
            raise SystemExit('Invalid source data: ' + row['path'])
        temporary.replace(target)
        restored += 1
    if args.package:
        package = args.package.resolve(strict=True)
        param = json.loads((package / 'sce_sys/param.json').read_bytes())
        if param.get('titleId') != 'PPSA70421':
            raise SystemExit('--package must point to the extracted PPSA70421 app')
        for folder in ('assets', 'models'):
            if (package / folder).is_dir():
                shutil.copytree(package / folder, root / folder, dirs_exist_ok=True)
        runtime = package / 'sce_module/libc.prx'
        if runtime.is_file():
            shutil.copy2(runtime, root / 'runtime/libc.prx')
        print('Packaged media restored from', package)
    print('Authoring datasets restored:', restored)


if __name__ == '__main__':
    main()
