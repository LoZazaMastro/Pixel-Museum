"""Preserve a local, immutable source57 binary/font/catalogue recovery point."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/research/native-source57-recoverable'
required = {
    'build/eboot.elf': 'f8a884b849deaa85845a9b37cdb6a31e6224047aa54b393f70a4ac565281867d',
    'content/catalog.json': 'eccc4d9df1f1a41ee02392f91422f984985c0dd0bd272fced73e8971b73c5773',
    'build/runtime-preview/content/catalog.json': '0808fffad3e0b7f652826f9d8ab803c7fa22bd06f57dc92fb308d060041a0805',
    'assets/fonts/cjk-subset.huifont': 'd1817b6260cc7b7fbea6ec2037a55d68774e76c184a075ff4301bf1cca13bccf',
}


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while data := stream.read(1 << 20):
            digest.update(data)
    return digest.hexdigest()


for name, expected in required.items():
    assert sha(ROOT / name) == expected, 'Coherent source57 checkpoint changed: ' + name
paths = set(required)
for folder in ('assets/fonts', 'content/ui-locales', 'content/museum-locales'):
    paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT / folder).glob('*') if p.is_file())
paths.update(('content/human-history.json', 'assets/images/manifest.json', 'models/index.json',
    'build/research/offline-script-shaping/verification.json',
    'build/research/offline-script-shaping/native-build.log',
    'src/museum/catalog.cpp', 'src/museum/catalog.hpp', 'src/museum/screen.cpp', 'src/museum/object_scene.cpp',
    'src/platform/ps5/display_egl.cpp', 'src/platform/ps5/display_egl.hpp', 'src/main.cpp',
    'src/gfx/font.cpp', 'src/gfx/font.hpp', 'src/gfx/font_format.hpp'))
records = {}
for name in sorted(paths):
    source, target = ROOT / name, OUT / name
    target.parent.mkdir(parents=True, exist_ok=True)
    expected = sha(source)
    if not target.exists():
        shutil.copy2(source, target)
    assert sha(target) == expected, 'Refusing to overwrite an immutable snapshot: ' + name
    records[name] = {'bytes': source.stat().st_size, 'sha256': expected}
manifest = {'status': 'immutable_local_source57_recovery_checkpoint_not_deployed',
    'scope': 'Native ELF, complete fonts and licences, source/runtime catalogues, locale/history data, image/model indexes and relevant pre-alias source files.',
    'restore': 'Restore listed paths together after verifying their hashes. Image/model source binaries remain in the workspace under their original immutable names; those large payloads are not duplicated here.',
    'files': records, 'console_transfer': False}
path = OUT / 'manifest.json'
text = json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'
if path.exists():
    assert path.read_text(encoding='utf8') == text
else:
    path.write_text(text, encoding='utf8')
print(path.relative_to(ROOT), sha(path), len(records), 'files')
