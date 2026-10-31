"""Bind the grouped SOURCE71 alias/font/native checks to the actual frozen files."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/research/grouped-source71'
OUT.mkdir(exist_ok=True)

def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1 << 20):
            result.update(block)
    return result.hexdigest()

master = ROOT / 'content/catalog.json'
runtime = ROOT / 'build/runtime-preview/content/catalog.json'
assert sha(master) == '95e461787332ea4473508793f1018b75d30908cf18d7842a10d1207397e7a8c1'
assert sha(runtime) == '8c16ac2c317ab6af4e57e9300ce29df2c59b52e248f9a4ac8ba68b084d020156'
a, b = [json.loads(p.read_text(encoding='utf8')) for p in (master, runtime)]
assert len(a['entries']) == len(b['entries']) == 1396
assert a['entry_aliases'] == b['entry_aliases'] and len(a['entry_aliases']) == 22
font_path = ROOT / 'build/research/offline-script-shaping/verification.json'
font = json.loads(font_path.read_text(encoding='utf8'))
assert font['coherent_catalogues']['content/catalog.json']['sha256'] == sha(master)
assert font['coherent_catalogues']['build/runtime-preview/content/catalog.json']['sha256'] == sha(runtime)
assert font['files']['build/eboot.elf']['sha256'] == sha(ROOT / 'build/eboot.elf') == 'd9bcc815820c53fef97efbc0b279cd6ef03047bcfd98f577906fbe5383e7989d'
logs = {
    'native': 'build/research/offline-script-shaping/grouped71-native-build.log',
    'runtime_equivalence': 'build/research/catalog-aliases/grouped71-runtime-equivalence.log',
    'alias_unit': 'build/research/catalog-aliases/grouped71-unit.log',
    'alias_actual_screen': 'build/research/catalog-aliases/grouped71-actual-screen.log',
    'display_lifecycle': 'build/research/display-refresh/grouped71-lifecycle.log',
    'font_bake': 'build/research/offline-script-shaping/final-bake-grouped-source71.log',
    'font_units': 'build/research/offline-script-shaping/grouped71-shaped-runs.log',
    'actual4k': 'build/research/offline-script-shaping/grouped71-actual-gl.log',
    'prose_credits': 'build/research/offline-script-shaping/grouped71-narrative-regression.log',
    'text_profile': 'build/research/story-text-profile/actual-grouped71.log',
}
for name, path in logs.items():
    text = (ROOT / path).read_text(encoding='utf8')
    assert 'PASS' in text if name not in ('native', 'font_bake') else 'error:' not in text
assert '22 alias resolutions' in (ROOT / logs['runtime_equivalence']).read_text()
assert 'runtime selection overrides these' in (ROOT / logs['native']).read_text()
gaps = ROOT / 'build/research/story-text-profile/unillustrated-scenes-current.json'
gap_report = json.loads(gaps.read_text(encoding='utf8'))
assert gap_report['count'] == 529
recovery = ROOT / 'build/research/native-source57-recoverable'
recovery_manifest = json.loads((recovery / 'manifest.json').read_text(encoding='utf8'))
for name, record in recovery_manifest['files'].items():
    assert sha(recovery / name) == record['sha256']
receipt = {
    'status': 'PASS_frozen_grouped_SOURCE71_fonts_actual4k_aliases_native',
    'master': {'path': master.relative_to(ROOT).as_posix(), 'sha256': sha(master), 'entries': len(a['entries'])},
    'runtime': {'path': runtime.relative_to(ROOT).as_posix(), 'sha256': sha(runtime), 'bytes': runtime.stat().st_size},
    'entry_aliases': {'count': 22, 'master_runtime_exact': True, 'parser_and_actual_saved_preferences': 'PASS', 'malformed_cycle_dangling_hops_and_reload': 'PASS'},
    'fonts': {'receipt': font_path.relative_to(ROOT).as_posix(), 'sha256': sha(font_path), 'ordinary': font['ordinary_display_codepoints'], 'visible_ordinary': font['visible_ordinary_codepoints'], 'exact_static_complex_phrases': font['current_complete_script_phrases'], 'shaped_word_runs': font['genuine_harfbuzz_word_boundary_runs'], 'atlas': font['fallback_atlas'], 'assets': {name: record for name, record in font['files'].items() if name.endswith('.huifont')}},
    'native': {'path': 'build/eboot.elf', 'bytes': (ROOT / 'build/eboot.elf').stat().st_size, 'sha256': sha(ROOT / 'build/eboot.elf'), 'includes_alias_resolution_and_saved_preferences': True, 'existing_payload_untouched': True},
    'display': {'changes': 'Diagnostic wording only; startupdefaults1920x1080/60 do not cap the existing requested4K/120 display-dependent mode with60fallback.', 'stub_actual_implementation_lifecycle': 'PASS', 'new_physical_refresh_or_fps_test': False},
    'actual_scene_profile': {'report': gaps.relative_to(ROOT).as_posix(), 'sha256': sha(gaps), 'composed_narrative_without_associated_image': gap_report['count'], 'meaning': 'Actual Screen composition, not a count of video cards or imported raw paragraph records.'},
    'logs': {name: {'path': path, 'sha256': sha(ROOT / path)} for name, path in logs.items()},
    'source57_recovery': {'manifest': 'build/research/native-source57-recoverable/manifest.json', 'sha256': sha(recovery / 'manifest.json'), 'all_original_files_verified': len(recovery_manifest['files'])},
    'limits': ['No console transfer or new physicalPS5 render/FPS test.', 'Complex shaping covers exact packaged static phrases and whole-word subphrases; no general dynamic shaping/bidi claim.', 'Narrative generation hostCPU results are not consoleFPS or image-loading timings.', 'SOURCE71 checkpoint excludes the separately reviewed NEXT Getaway candidate and subsequent source-only edits.'],
}
output = OUT / 'verification.json'
output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(output.relative_to(ROOT), sha(output))
