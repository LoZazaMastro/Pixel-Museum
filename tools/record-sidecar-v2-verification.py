"""Record the admitted mixed-version provider and measured, bounded limits."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/model-sidecar-v2-probe'

def record(path):
    path = ROOT / path
    return {'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

index = json.loads((ROOT / 'models/index.json').read_text(encoding='utf8'))
gamepad, ps5 = [next(r for r in index['models'] if r['exhibit_id'] == name) for name in ('wii-u-gamepad', 'playstation-5')]
assert gamepad['artwork_cache']['format_version'] == 2 and ps5['artwork_cache']['format_version'] == 1
for model in (gamepad, ps5):
    assert record(model['asset_file'])['sha256'] == model['sha256']
    assert record(model['artwork_cache']['asset_file'])['sha256'] == model['artwork_cache']['sha256']
fourk = json.loads((BASE / 'actual4K-reconciliation.json').read_text())
assert len(fourk['models']) == 2 and all(len(r['actual4K_byte_identical']) == 2 for r in fourk['models'])
suite = (BASE / 'fixture-suite-final.log').read_text()
assert suite.count('PASS: 92 neutral pixel/material checks;') == 3
assert suite.count('46 cache-backed full-image shader comparisons') == 2
assert '17 malformed/source/format/mip/endian/frame cases fallback' in suite
assert 'cancelled job commits nothing; SHA256 standard vectors PASS' in suite
assert 'original RGBA preparation queued on worker' in suite
v1 = (BASE / 'v1-compatibility.log').read_text()
assert 'PASS 24 original full-resolution canonical atlases byte-for-byte' in v1
assert 'truncated payload fall back to original PNG' in v1
screen = (BASE / 'actual-screen-memory-gate.log').read_text()
for marker in ('PASS actualScreen large-memory gate daily-11-18', 'PASS actualScreen large-memory gate playstation-5', 'Actual Screen model transitions PASS:'):
    assert marker in screen
native = (BASE / 'native-build.log').read_text()
assert 'Native compile/link/conversion complete' in native and 'error:' not in native
native_sha = record('build/eboot.elf')['sha256']
assert native_sha == '2e4cf0bd0c284595ca0e61b1f8659f250bbb54d0a4a60af774c5e0e3ea1d9ca1'

def timing(model, variant):
    text = (BASE / (model+'-'+variant+'.log')).read_text()
    first = next(line for line in text.splitlines() if '3D ready breakdown:' in line)
    value = lambda pattern: float(re.search(pattern, first).group(1))
    hash_ms = re.search(r'source SHA256 binding ([0-9.]+)ms', text)
    peak = int(re.search(r'peak staged image (\d+) MiB', text).group(1))
    return {'source_read_ms': value(r'file ([0-9.]+)ms'), 'source_sha256_worker_ms': float(hash_ms.group(1)) if hash_ms else 0,
            'parse_and_identity_ms': value(r'parse\+identity ([0-9.]+)ms'), 'mip_and_packing_ms': value(r'mip\+packing ([0-9.]+)ms'),
            'cache_read_decode_ms': value(r'cache \d+ hits ([0-9.]+)ms'), 'gl_storage_ms': value(r'GL allocation ([0-9.]+)ms'),
            'gl_transfer_ms': value(r'row transfer ([0-9.]+)ms'), 'request_ready_ms': value(r'request-to-ready ([0-9.]+)ms'),
            'estimated_gpu_without_new_FBO_MiB': value(r'estimated residency ([0-9.]+) MiB'), 'rounded_prepared_payload_vector_peak_MiB': peak}

recovery = ROOT / 'build/research/native-source71-recoverable'
manifest = json.loads((recovery / 'manifest.json').read_text())
for name, value in manifest['files'].items():
    assert hashlib.sha256((recovery / name).read_bytes()).hexdigest() == value['sha256']
addition = json.loads((recovery / 'model-v1-cache-recovery.json').read_text())
for name, value in addition['files'].items():
    assert hashlib.sha256((recovery / name).read_bytes()).hexdigest() == value['sha256']
sources = ('src/museum/object_scene.cpp', 'src/museum/object_scene.hpp', 'src/museum/object_artwork_cache.hpp',
    'src/museum/object_artwork_cache_v2.hpp', 'src/museum/object_cache_sha256.hpp', 'tests/object-scene/bake-artwork-cache.cpp',
    'tools/model_artwork_cache.py', 'tools/prepare-model-artwork-cache.py', 'tests/object-scene/cache-v2-parity.cpp',
    'tests/object-scene/cache-v2.sh', 'tests/object-scene/cache-v2-real.py', 'tests/object-scene/material-test.cpp',
    'host/model_transition_checks.hpp', 'tests/model-artwork-packaging.py')
logs = ('fixture-suite-final.log', 'v1-compatibility.log', 'actual4K-suite.log', 'actual4K-reconciliation.json',
    'actual-screen-memory-gate.log', 'packaging.log', 'native-build.log', 'gamepad-only-provider-promotion.json')
receipt = {
    'status': 'PASS_native_v1_v2_reader_GamePad_only_v2_provider_NEXT_master_refresh_required',
    'native': {'path': 'build/eboot.elf', **record('build/eboot.elf')},
    'provider': {'GamePad': gamepad['artwork_cache'], 'PS5': ps5['artwork_cache']},
    'unchanged_GLBS': {m['exhibit_id']: record(m['asset_file']) for m in (gamepad, ps5)},
    'model_index': record('models/index.json'), 'gamepad_license_record': record('models/licenses/wii-u-gamepad.json'),
    'format': 'PMAC0002/version2 exact existing RGBA8/sRGB8, RG8/R8 bytes and precomputed mips; all-byte-verified constant texels. No565/4444/quantization/downscale.',
    'integrity': 'Actual loadedGLB SHA256 on the existing worker; byte counts/roles/channel union/format/mipalgorithm/dimensions/offsets checked; Zstd content checksum; unchanged open descriptor; rejected cache commits nothing and originalPNG remains authoritative.',
    'fallback': 'Failed compact allocation/swizzle retires its private handle and packed job, then requeues one originalRGBA job on the same worker. No main-thread decode, second worker or additional full image job.',
    'tests': {'exact_native4K_two_angles_both_models': fourk, 'material_checks': '92cases x3paths', 'full_image_shader_comparisons': '46x2 asyncpaths',
              'v1_GB_PS1_atlas_byte_parity': 24, 'bad_v2_cache_fallback_cases': 17, 'cancelled_commit': 'PASS', 'SHA256_standard_vectors': 'empty/abc/milliona PASS',
              'real_model_revisit_and_32_cancels': 'PASS both4Kmodels', 'actual_Screen_large_admission_retirement': 'GamePad/PS5 PASS, prepared+retired allocation bytes0 before large upload, PS3/PS4 interruptions and FBO reuse PASS', 'packaging_both_versions': 'PASS'},
    'host_GamePad_before': timing('wii-u-gamepad', 'before'), 'host_GamePad_v2': timing('wii-u-gamepad', 'after'),
    'host_PS5_v1': timing('playstation-5', 'before'), 'host_PS5_v2_research_only_not_admitted': timing('playstation-5', 'after'),
    'memory': {'per_nonuniform_ORM_payload_bytes_before': 134217726, 'per_nonuniform_ORM_payload_bytes_after': 44739242,
               'current_model_maximum_payload_vector_bytes_before': 134217726, 'current_model_maximum_payload_vector_bytes_after': 89478484,
               'maximum_payload_vector_reduction_bytes': 44739242, 'compressed_input_temporary_not_in_payload_vector_counter': True,
               'host_process_RSS_not_claimed_reduced': True, 'GPU_storage_estimate_unchanged': True, 'caps_raised': False, 'additional_workers': 0},
    'global_budget_review': 'Timings include live+deferred-retired model objects andFBOs; Screen sums active+2prepared scenes and drains neighbours to0 for large models.512MiB is model-cache policy, not total physicalpool accounting. UI canvases/fonts, visible photo cache/private upload, audio/video/CPU allocations are separate; no impossibleOOM guarantee.',
    'source71_recovery': {'core_manifest': record('build/research/native-source71-recoverable/manifest.json'), 'original_v1_GamePad_cache_manifest': record('build/research/native-source71-recoverable/model-v1-cache-recovery.json'), 'all51core_files_and_v1_cache_verified': True},
    'current_master_and_runtime': {p: record(p) for p in ('content/catalog.json', 'build/runtime-preview/content/catalog.json')},
    'font_files': {p.relative_to(ROOT).as_posix(): record(p.relative_to(ROOT)) for p in (ROOT / 'assets/fonts').glob('*.huifont')},
    'source_files': {p: record(p) for p in sources}, 'logs': {p: record(BASE.relative_to(ROOT)/p) for p in logs},
    'limits': ['Host CPU/softwareGL measurements include fixture sleeps and are not physicalPS5 FPS/loading measurements.',
               'GamePad~151ms faster in the recorded whole-load comparison includingSHA; PS5v2 was slower soPS5 remainsv1.',
               'Maximum indivisibleGL storage calls remain; no instantaneous loading or120FPS claim.',
               'GamePad sourceindex/provider is NEXT; currentSOURCE71 master/runtime reference must be refreshed in the next coherent assembly before packaging/deployment.',
               'No FTP or console mutation performed.']}
path = BASE / 'verification.json'
path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(path.relative_to(ROOT), hashlib.sha256(path.read_bytes()).hexdigest())
