"""Record measured preparation allocation savings and unchanged real renders."""
from pathlib import Path
import hashlib
import json
import re
import statistics
import os
import tempfile
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/research/uniform-packing-probe'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while data := stream.read(1 << 20):
            digest.update(data)
    return digest.hexdigest()


source = ROOT / 'src/museum/object_scene.cpp'
tested = (OUT / 'compact.cpp').read_text(encoding='utf8').split('\nextern "C" void uniform_packing_probe_cpu')[0]
assert source.read_text(encoding='utf8').strip() == tested.strip()
# The comparison generator must also work after production admission, rather
# than silently depending on the old source order. Keep its proof outputs intact.
script = (ROOT / 'tests/object-scene/uniform-packing-probe.sh').read_text(encoding='utf8')
generator = script.split("python3 - <<'PY'\n", 1)[1].split('\nPY\n', 1)[0]
os.chdir(ROOT)
with tempfile.TemporaryDirectory(prefix='museum-uniform-probe-') as folder:
    generator = generator.replace("Path('build/research/uniform-packing-probe')", 'Path(' + repr(folder) + ')')
    exec(compile(generator, '<isolated-repeatability-check>', 'exec'), {})
    regenerated = (Path(folder) / 'compact.cpp').read_text(encoding='utf8').split('\nextern "C" void uniform_packing_probe_cpu')[0]
    assert regenerated.strip() == source.read_text(encoding='utf8').strip()
measurements = {}
for variant in ('reference', 'compact'):
    log = (OUT / ('cpu-' + variant + '.log')).read_text()
    rows = []
    for match in re.finditer(r'iteration=(\d+) original_rgba_mip_bytes=(\d+) packed_cpu_bytes=(\d+) prepare_ms=([\d.]+) exact_rgba_mips=PASS', log):
        i, original, packed, ms = match.groups()
        rows.append({'iteration': int(i), 'original_rgba_mip_bytes': int(original),
                     'packed_cpu_bytes': int(packed), 'prepare_ms': float(ms)})
    assert len(rows) == 5
    measurements[variant] = {'samples': rows, 'mean_host_worker_ms': statistics.mean(r['prepare_ms'] for r in rows)}
before = measurements['reference']['samples'][0]
after = measurements['compact']['samples'][0]
assert before['original_rgba_mip_bytes'] == after['original_rgba_mip_bytes'] == 89478484
assert before['packed_cpu_bytes'] == 44739242 and after['packed_cpu_bytes'] == 2
parity = []
for model in ('ps5', 'gamepad'):
    for angle in (0, 1):
        a, b = (OUT / f'{model}-{variant}-{angle}.png' for variant in ('reference', 'compact'))
        assert sha(a) == sha(b)
        with Image.open(a) as image:
            assert image.size == (3840, 2160)
        parity.append({'model': model, 'angle': angle, 'size': [3840, 2160], 'identical_sha256': sha(a)})
    for variant in ('reference', 'compact'):
        log = (OUT / f'{model}-{variant}.log').read_text()
        assert 'Cache/revisit PASS:' in log and '32 requests remain cancelled' in log
        assert log.count('no GL error, state restored.') == 2
material_log = (OUT / 'materials-production.log').read_text()
assert material_log.count('PASS: 92 neutral pixel/material checks;') == 3
assert 'compact material format unavailable; retrying original RGBA8' in material_log
assets = []
index = json.loads((ROOT / 'models/index.json').read_text(encoding='utf8'))
for row in index['models']:
    if row['exhibit_id'] not in ('playstation-5', 'wii-u-gamepad'):
        continue
    for record in (row, row['artwork_cache']):
        path = ROOT / record['asset_file']
        assert sha(path) == record['sha256']
        assets.append({'asset': record['asset_file'], 'sha256': record['sha256'], 'unchanged': True})
receipt = {'status': 'PASS_exact_pixels_mips_render_lifetime_and_unsupported_format_fallback',
    'production_source_equals_tested_isolated_variant': True, 'production_source_sha256': sha(source),
    'comparison_generator_repeatable_after_production_admission': True,
    'constant_4096_rg8_preparation': measurements,
    'packed_cpu_bytes_avoided': before['packed_cpu_bytes'] - after['packed_cpu_bytes'],
    'prepared_job_vectors_bytes_before': before['original_rgba_mip_bytes'] + before['packed_cpu_bytes'],
    'prepared_job_vectors_bytes_after': after['original_rgba_mip_bytes'] + after['packed_cpu_bytes'],
    'exact_4k_parity': parity, 'source_and_sidecar_assets': assets,
    'material_cases': 92, 'modes': ['synchronous original RGBA', 'asynchronous compact', 'asynchronous forced compact-format failure'],
    'limits': ['Savings are in one exactly uniform atlas preparation job, not a lower GPU residency.',
        'Original RGBA and mip chains remain for lossless RGBA fallback. Other non-uniform atlas preparation is unchanged.',
        'Host CPU timings are not physical PS5 measurements or a claim of instantaneous whole-model loading.',
        'GL immutable-storage allocations and deletion calls remain non-preemptible; memory caps are unchanged.',
        'Current 1398 native binary remains unchanged; production optimization awaits the next coherent native build.'],
    'console_transfer': False}
if '--native-compiled' in sys.argv:
    native_log = ROOT / 'build/research/offline-script-shaping/native-build.log'
    log = native_log.read_text(encoding='utf8')
    assert 'Native compile/link/conversion complete' in log and 'error:' not in log and 'FAILED:' not in log
    native = ROOT / 'build/eboot.elf'
    receipt['native'] = {'bytes': native.stat().st_size, 'sha256': sha(native),
                         'compile_log': native_log.relative_to(ROOT).as_posix()}
    receipt['limits'][-1] = 'Native compile/link/conversion passed with this optimization; no console transfer or physical PS5 timing verification.'
path = OUT / 'verification.json'
path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(path.relative_to(ROOT), sha(path))
print('Packed CPU bytes avoided:', receipt['packed_cpu_bytes_avoided'])
