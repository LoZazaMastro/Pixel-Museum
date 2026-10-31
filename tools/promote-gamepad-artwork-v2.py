"""Promote only the independently tested GamePad derivative; no master/FTP."""
from pathlib import Path
import hashlib
import json
import shutil
import os

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/model-sidecar-v2-probe'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
receipt = json.loads((BASE / 'actual4K-reconciliation.json').read_text())
review = next(r for r in receipt['models'] if r['model'] == 'wii-u-gamepad')
index_path = ROOT / 'models/index.json'
index = json.loads(index_path.read_text(encoding='utf8'))
row = next(r for r in index['models'] if r['exhibit_id'] == 'wii-u-gamepad')
master = ROOT / row['asset_file']
destination = ROOT / row['artwork_cache']['asset_file']
candidate = BASE / 'assets/after/wii-u-gamepad.artwork.pmc'
assert sha(master) == row['sha256'] == review['original_asset_sha256']
assert sha(candidate) == review['v2_cache_sha256'] == '50c347daa7bc90e9d155712b2c337266ed4c419dc564acb27699a636b09c63c2'
assert candidate.read_bytes()[:8] == b'PMAC0002'
recovery = ROOT / 'build/research/native-source71-recoverable'
backup = recovery / 'models/wii-u-gamepad.artwork.pmc'
backup.parent.mkdir(exist_ok=True)
if not backup.exists():
    assert sha(destination) == review['original_v1_cache_sha256']
    shutil.copy2(destination, backup)
assert sha(backup) == review['original_v1_cache_sha256']
addition = recovery / 'model-v1-cache-recovery.json'
recovery_note = {'scope': 'Additional original v1 derivative needed to restore the complete SOURCE71 model provider after GamePad-only v2 promotion.', 'files': {'models/wii-u-gamepad.artwork.pmc': {'sha256': sha(backup), 'bytes': backup.stat().st_size}}, 'original_core_manifest_unchanged': 'manifest.json', 'source_glb_unchanged': row['sha256']}
text = json.dumps(recovery_note, indent=2)+'\n'
if addition.exists():
    assert addition.read_text() == text
else:
    addition.write_text(text)
temporary = destination.with_suffix(destination.suffix+'.new')
shutil.copy2(candidate, temporary)
assert sha(temporary) == review['v2_cache_sha256']
os.replace(temporary, destination)
row['artwork_cache'].update(format_version=2, bytes=destination.stat().st_size, sha256=sha(destination), content='Offline-derived exact existing RGBA8/sRGB8, RG8/R8 sampled-channel and verified constant upload payloads/mips. No new quantization, resizing or source change. Source-SHA256 binding and checksummed lossless Zstandard frames; worker-only original RGBA fallback on cache miss, mismatch, corruption or unavailable compact format.')
for path, value in ((index_path, index), (ROOT / 'models/licenses/wii-u-gamepad.json', row)):
    temporary = path.with_suffix(path.suffix+'.new')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    os.replace(temporary, path)
assert sha(master) == row['sha256']
ps5 = next(r for r in index['models'] if r['exhibit_id'] == 'playstation-5')
assert ps5['artwork_cache']['format_version'] == 1
assert sha(ROOT / ps5['artwork_cache']['asset_file']) == ps5['artwork_cache']['sha256']
out = {'status': 'GamePad_only_v2_source_provider_PROMOTED_NEXT_master_refresh_required', 'gamepad': row['artwork_cache'], 'source_glb_sha256_unchanged': row['sha256'], 'model_index_sha256': sha(index_path), 'license_record_sha256': sha(ROOT / 'models/licenses/wii-u-gamepad.json'), 'source71_original_v1_recovery': {'path': backup.relative_to(ROOT).as_posix(), 'sha256': sha(backup), 'addition_manifest': addition.relative_to(ROOT).as_posix(), 'addition_manifest_sha256': sha(addition)}, 'ps5_kept_v1': True, 'master_or_runtime_edited': False, 'console_transfer': False}
path = BASE / 'gamepad-only-provider-promotion.json'
path.write_text(json.dumps(out, indent=2)+'\n')
print(path.relative_to(ROOT), sha(path))
