"""Promote only the reviewed PS1 sidecar/provider; no assembly, build or FTP."""
from pathlib import Path
import json,hashlib,shutil,datetime
R=Path(__file__).resolve().parents[1];O=R/'build/research/ps1-v2-provider-thirteenth'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha(p))
def load(p):return json.loads(p.read_text(encoding='utf8'))
def atomic(p,value):
 q=p.with_suffix(p.suffix+'.provider13.part');q.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8');q.replace(p)
qa=R/'build/research/twelfth-source86-scoped/verification.json';assert load(qa)['status'].startswith('PASS')
peer=R/'build/research/ps1-v2-isolated-comparison/root-independent-cache-v2-review.json'
assert sha(peer)=='5feebbd9dae579660fd22db728af620f76b1739ff50d90691777ac92fe086075'
candidate=R/'build/research/ps1-v2-isolated-comparison/after/playstation.artwork.pmc'
assert sha(candidate)=='cc4e2596af2b4e60e31afee35c32d24e9d8f449bb0ce988dac06809365663ff6'
assert candidate.read_bytes()[:8]==b'PMAC0002'
indexpath=R/'models/index.json';old=load(indexpath)
assert old==load(R/'build/research/ps1-v2-isolated-comparison/source-index-snapshot.json')
model=next(m for m in old['models'] if m['exhibit_id']=='playstation');source=R/model['asset_file'];cache=R/model['artwork_cache']['asset_file'];licensepath=R/'models/licenses/playstation.json'
assert sha(source)==model['sha256']=='45d3e26db2af6b9264888d22df0bbef46601248eda43424f01a71f76ca1d6b9d'
assert sha(cache)==model['artwork_cache']['sha256']=='1b20b40a9452af514e45b8e4c0c19fdfaf6779a4770f7f6fae30d48358b34e15'
assert sha(R/'build/eboot.elf')=='71fba8ccff3f25efc1ad610c28b44d459513abc20cc0482ae4c026952a6059f7'
O.mkdir(exist_ok=True);assert not (O/'promotion.json').exists()
backup=O/'previous-provider';backup.mkdir(exist_ok=True);before=[]
for path in [cache,indexpath,licensepath]:
 target=backup/path.relative_to(R);assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target);assert sha(path)==sha(target);before.append(dict(original=rec(path),backup=rec(target)))
new=json.loads(json.dumps(old));selected=next(m for m in new['models'] if m['exhibit_id']=='playstation')
selected['artwork_cache']=dict(asset_file=model['artwork_cache']['asset_file'],format_version=2,source_sha256=model['sha256'],bytes=candidate.stat().st_size,sha256=sha(candidate),content='Offline-derived exact existing RGBA8/sRGB8, RG8/R8 sampled-channel and verified constant upload payloads/mips. No new quantization, resizing or source change. Source-SHA256 binding and checksummed lossless Zstandard frames; worker-only original RGBA fallback on cache miss, mismatch, corruption or unavailable compact format.')
assert all(a==b for a,b in zip(old['models'],new['models']) if a['exhibit_id']!='playstation')
check=dict(selected);check['artwork_cache']=model['artwork_cache'];assert check==model
lic=load(licensepath);lic['artwork_cache']=selected['artwork_cache']
try:
 pending=cache.with_suffix('.pmc.provider13.part');shutil.copy2(candidate,pending);assert sha(pending)==sha(candidate);pending.replace(cache)
 atomic(indexpath,new);atomic(licensepath,lic)
 assert sha(cache)==selected['artwork_cache']['sha256'] and load(indexpath)==new
except BaseException:
 for path in [cache,indexpath,licensepath]:shutil.copy2(backup/path.relative_to(R),path)
 raise
report=dict(status='PASS_PS1_V2_PROVIDER_SOURCE_ONLY_FUTURE13_NO_ASSEMBLY',timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),qa12=rec(qa),root_peer=rec(peer),original_provider_backup=before,promoted_cache=rec(cache),model_index=rec(indexpath),model_license=rec(licensepath),provider=selected['artwork_cache'],original_GLBS_unchanged=rec(source),only_one_model_provider_object_changed=True,all_other_model_rows_exact=True,native_unchanged=rec(R/'build/eboot.elf'),benchmark=rec(R/'build/research/ps1-v2-isolated-comparison/verification.json'),limits=['Only lossless CPU staging/RAM benefit accepted; finalGPUstorage unchanged.','No current catalogue/runtime/dist mutation or package/FTP/nativebuild.','Restore12 provider using previous-provider/models/playstation.artwork.pmc,index.json andlicenses/playstation.json together.','No instantaneous/120FPS/physicalPS5OOMfix claim.'])
(O/'promotion.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(rec(O/'promotion.json')))
