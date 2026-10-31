"""Promote one measured existing-format cache; leave grouped catalogues untouched."""
from pathlib import Path
import copy,hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'build/research/atari-vcs-lossless-cache-benchmark'
sys.path.insert(0,str(ROOT/'tools'))
from model_artwork_cache import checked_artwork_cache
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
indexpath=ROOT/'models/index.json';original=indexpath.read_bytes();index=json.loads(original)
before=copy.deepcopy(index);row=next(r for r in index['models'] if r['exhibit_id']=='atari-vcs')
assert not row.get('artwork_cache')
assert sha(ROOT/row['asset_file'])==row['sha256']=='f0dfcdb148233965012023f952adfb9547d31cde47c547401ed55031f44cf0e2'
proof=json.loads((P/'verification.json').read_text(encoding='utf8'))
assert proof['status']=='PASS_LOSSLESS_CACHE_STAGE_AND_TOTAL_LATENCY_BENEFIT_HOST_ONLY'
cache=ROOT/proof['cache']['path'];assert sha(cache)==proof['cache']['sha256']
dest=ROOT/'models/atari-vcs.artwork.pmc';assert not dest.exists()
licensepath=ROOT/'models/licenses/atari-vcs.json'
(P/'pre-promotion-index.json').write_bytes(original)
shutil.copyfile(licensepath,P/'pre-promotion-atari-vcs-license.json')
catalogs={p:sha(ROOT/p) for p in ['content/catalog.json','build/runtime-preview/content/catalog.json']}
shutil.copyfile(cache,dest)
row['artwork_cache']={'asset_file':'models/atari-vcs.artwork.pmc','format_version':1,
 'source_sha256':row['sha256'],'bytes':dest.stat().st_size,'sha256':sha(dest),
 'content':'Offline-derived exact original RGBA8 base pixels and existing colour/data mip chains. Lossless Zstandard frames with verified content checksums; source GLB remains unchanged. Original PNG fallback on cache miss, mismatch or corruption.'}
assert checked_artwork_cache(ROOT,row)==Path('models/atari-vcs.artwork.pmc')
for old,new in zip(before['models'],index['models']):
 if old['exhibit_id']!='atari-vcs':assert old==new
 else:assert old=={k:v for k,v in new.items() if k!='artwork_cache'}
def write(path,obj):
 pending=path.with_suffix(path.suffix+'.cache-next')
 pending.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8');pending.replace(path)
write(licensepath,row);write(indexpath,index)
assert all(sha(ROOT/p)==v for p,v in catalogs.items())
receipt={'status':'SOURCE_ONLY_PROVIDER_PROMOTED_NEXT_CATALOG_REFRESH_REQUIRED',
 'provider':row['artwork_cache'],'source_GLBS_unchanged':True,'source_sha256':row['sha256'],
 'model_index_sha256':sha(indexpath),'license_record_sha256':sha(licensepath),
 'benchmark_receipt':{'path':(P/'verification.json').relative_to(ROOT).as_posix(),'sha256':sha(P/'verification.json')},
 'unchanged_current_catalogues':catalogs,'master_or_runtime_edited':False,'native_CPP_edited':False,'console_transfer':False,
 'limits':'Measured host loading improvement only. Existing source-boundV1format, pixels/mips/geometry unchanged; no GPUmemorysaving, instantloading or120FPS claim.'}
out=P/'source-provider-promotion.json';write(out,receipt)
print(out.relative_to(ROOT),sha(out))
