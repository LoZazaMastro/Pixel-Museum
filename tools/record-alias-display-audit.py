"""Record bounded saved-ID resolution and the real startup/accepted-mode distinction."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/research/catalog-aliases'
SDK = Path('F:/Playhub/PS5/CD Player/.deps/ps5-opengl/ps5-opengl-sdk-1.0.2/sdk')


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while data := stream.read(1 << 20):
            digest.update(data)
    return digest.hexdigest()


snapshot_root = ROOT / 'build/research/native-source57-recoverable'
snapshot = json.loads((snapshot_root / 'manifest.json').read_text(encoding='utf8'))
for name, record in snapshot['files'].items():
    assert sha(snapshot_root / name) == record['sha256']
assert sha(ROOT / 'build/eboot.elf') == snapshot['files']['build/eboot.elf']['sha256']
unit = (OUT / 'unit.log').read_text(encoding='utf8')
screen = (OUT / 'actual-screen.log').read_text(encoding='utf8')
display = (ROOT / 'build/research/display-refresh/lifecycle.log').read_text(encoding='utf8')
assert 'Catalog aliases PASS:' in unit and 'PASS actualScreen saved aliases:' in screen
assert 'PASS dynamic Display:' in display and 'PASS legacy Display:' in display
references = (ROOT / 'build/research/display-refresh/native-object-api-references.txt').read_text()
for symbol in ('eglGetDisplayModePS5', 'eglSetDisplayModePS5', 'eglSetDisplayRefreshPS5', 'eglSwapInterval'):
    assert symbol in references
historic_path = ROOT / 'build/console-slice/checkpoint20-live/session-after-model-failures.log'
historic = historic_path.read_text(encoding='utf8').splitlines()
accepted = [(n + 1, line) for n, line in enumerate(historic) if 'display accepted 3840x2160@120 Hz' in line]
assert accepted
param = json.loads((ROOT / 'sce_sys/param.json').read_text(encoding='utf8'))
assert param['attribute3'] & 0x80040 == 0x80040
files = ('src/museum/catalog.cpp', 'src/museum/catalog.hpp', 'src/museum/screen.cpp',
    'tests/catalog-aliases.cpp', 'host/catalog_alias_checks.hpp', 'tools/prepare-opengl.sh',
    'tests/display-refresh/stub.cpp', 'tests/display-refresh/run.sh', 'tests/runtime_catalog_test.cpp',
    'src/main.cpp', 'src/platform/ps5/display_egl.cpp', 'src/platform/ps5/display_egl.hpp')
receipt = {'status': 'host_parser_actualScreen_and_display_lifecycle_PASS_native_next_group_pending',
    'entry_alias_schema': 'Top-level object string old-id -> string existing canonical-id',
    'alias_record_limit': 4096, 'alias_id_bytes_limit': 192, 'alias_hop_limit': 32,
    'resolution': 'Real entry wins; chains resolve only to real entries. Cycles, dangling chains, malformed/overlong records and oversized optional tables do not add timeline stops. Failed catalogue parse preserves the previous working aliases.',
    'actual_preference_cases': ['NES', 'PSP calendar wrapper', 'direct canonical', 'multi-hop retired ID', 'cycle', 'dangling', 'unknown'],
    'logs': {name: {'sha256': sha(ROOT / name)} for name in (
        'build/research/catalog-aliases/unit.log', 'build/research/catalog-aliases/actual-screen.log',
        'build/research/display-refresh/lifecycle.log', 'build/research/display-refresh/native-object-api-references.txt')},
    'display': {'sdk_startup_defaults': [1920, 1080, 60], 'application_runtime_request': [3840, 2160, 120],
        'existing_display_dependent_fallback_hz': 60, 'swap_interval': 1,
        'native_object_has_dynamic_API_calls': True, 'SDK_display_headers': {
            name: sha(SDK / 'include' / name) for name in ('ps5_opengl_display.h', 'ps5_opengl_display_modes.h')},
        'changes': 'Build-log wording only. Existing dynamic request/fallback, SDK defaults, renderer mode and pacing are unchanged.',
        'historical_physical_console_evidence': {'path': historic_path.relative_to(ROOT).as_posix(),
            'sha256': sha(historic_path), 'line': accepted[0][0], 'text': accepted[0][1],
            'meaning': 'Historical scanout acceptance at120Hz; not a measurement of120 rendered frames per second or a new physical test.'},
        'local_package_attribute3': param['attribute3'], 'console_writes': False},
    'source_sha256': {name: sha(ROOT / name) for name in files},
    'recoverable_source57': {'manifest': 'build/research/native-source57-recoverable/manifest.json',
        'manifest_sha256': sha(snapshot_root / 'manifest.json'), 'files_all_verified': len(snapshot['files']),
        'current_elf_unchanged': True, 'native_sha256': sha(ROOT / 'build/eboot.elf')},
    'limits': ['New aliases are verified through native C++ host parser and actual Screen method; current ELF is intentionally unchanged until the next grouped assembly/build.',
        'Display tests are lifecycle stubs using the actual Display implementation; physical timing/FPS and newly negotiated HDMI status are not inferred from these tests.']}
path = OUT / 'verification.json'
path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(path.relative_to(ROOT), sha(path))
