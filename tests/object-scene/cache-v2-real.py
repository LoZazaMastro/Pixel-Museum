"""Isolated actual authored model/cache copies; never changes production assets."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/model-sidecar-v2-probe'
index = json.loads((ROOT / 'models/index.json').read_text())
recovery = ROOT / 'build/research/native-source71-recoverable'
baseline_index = json.loads((recovery / 'models/index.json').read_text()) if (recovery / 'models/index.json').exists() else index
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
models = [r for r in baseline_index['models'] if r['exhibit_id'] in ('playstation-5', 'wii-u-gamepad')]
records = []
for model in models:
    asset = ROOT / model['asset_file']
    live = next(r for r in index['models'] if r['exhibit_id'] == model['exhibit_id'])
    production_sidecar = ROOT / live['artwork_cache']['asset_file']
    production_sha = sha(production_sidecar)
    sidecar = ROOT / model['artwork_cache']['asset_file']
    if sha(sidecar) != model['artwork_cache']['sha256']:
        sidecar = recovery / model['artwork_cache']['asset_file']
    assert sha(asset) == model['sha256'] == live['sha256'] and sha(sidecar) == model['artwork_cache']['sha256']
    targets = {}
    for variant in ('before', 'after'):
        folder = OUT / 'assets' / variant
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / asset.name
        shutil.copy2(asset, target)
        shutil.copy2(sidecar, target.with_suffix('.artwork.pmc'))
        targets[variant] = target
    command = ['bash', 'tests/object-scene/bake-artwork-cache.sh']
    command += ['--v2', '--source-id='+model['exhibit_id'], targets['after'].relative_to(ROOT).as_posix()]
    subprocess.run(command, cwd=ROOT, check=True)
    for variant, path in targets.items():
        args = ['bash', 'tests/object-scene/run.sh', path.relative_to(ROOT).as_posix(), '--size=3840x2160', '--adaptive-upload', '--yaw=-0.35']
        args += model.get('include_groups', [])
        log = OUT / (model['exhibit_id']+'-'+variant+'.log')
        with log.open('w') as stream:
            subprocess.run(args, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
        text = log.read_text()
        assert text.count('no GL error, state restored.') == 2
        assert 'Cache/revisit PASS:' in text and '32 requests remain cancelled' in text
    pairs = []
    for angle in (0, 1):
        before = Path(str(targets['before'])+'-'+str(angle)+'.png')
        after = Path(str(targets['after'])+'-'+str(angle)+'.png')
        assert sha(before) == sha(after), model['exhibit_id']+' actual4K pixels changed'
        pairs.append({'angle': angle, 'identical_sha256': sha(after)})
    assert sha(asset) == model['sha256'] and sha(sidecar) == model['artwork_cache']['sha256'] and sha(production_sidecar) == production_sha
    records.append({'model': model['exhibit_id'], 'original_asset_sha256': sha(asset), 'original_v1_cache_sha256': sha(sidecar), 'before_cache_bytes': sidecar.stat().st_size, 'v2_cache_bytes': targets['after'].with_suffix('.artwork.pmc').stat().st_size, 'v2_cache_sha256': sha(targets['after'].with_suffix('.artwork.pmc')), 'actual4K_byte_identical': pairs, 'production_assets_unchanged': True})
path = OUT / 'actual4K-reconciliation.json'
path.write_text(json.dumps({'status': 'PASS_exact4K_GL_cache_revisit_cancel', 'models': records}, indent=2)+'\n')
print(path.relative_to(ROOT), sha(path))
