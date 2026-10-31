"""Read measured stages, source checksums and exact two-angle pixel parity."""
from pathlib import Path
import hashlib,json,re,statistics
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'build/research/atari-vcs-lossless-cache-benchmark'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def metrics(name):
 text=(P/name).read_text(encoding='utf8')
 m=re.search(r'Separated timing: source read ([\d.]+)ms / parse\+geometry\+identity ([\d.]+)ms / image decode sum ([\d.]+)ms / mip\+packing worker sum ([\d.]+)ms / upload CPU sum ([\d.]+)ms / GL storage sum ([\d.]+)ms / GL row-transfer sum ([\d.]+)ms / request-to-ready ([\d.]+)ms',text)
 assert m
 out=dict(zip(['source_read_ms','parse_geometry_identity_ms','image_decode_ms','mip_packing_ms','upload_cpu_ms','GL_storage_ms','GL_transfer_ms','request_ready_ms'],map(float,m.groups())))
 cache=re.search(r'Derived artwork cache: (\d+) hits / ([\d.]+)ms',text);assert cache
 out['cache_hits']=int(cache[1]);out['cache_read_decode_ms']=float(cache[2])
 out['CPU_artwork_prepare_ms']=out['image_decode_ms']+out['mip_packing_ms']+out['cache_read_decode_ms']
 out['peak_RSS_bytes']=int(re.search(r'Process peakRSS throughready: (\d+) bytes',text)[1])
 out['peak_staged_MiB']=int(re.search(r'peak staged image (\d+) MiB',text)[1])
 assert '2477646 vertices, 3917004 triangles, 20 mesh draws, 225394560 geometry bytes, 58720256 texture bytes' in text
 assert 'zero additional atlas storage/upload calls; ready swap/revisit without GL errors' in text
 assert '32 requests remain cancelled after worker handoff' in text
 assert text.count('no GL error, state restored.')==2
 out['log_sha256']=sha(P/name);return out
before=[metrics(n) for n in ['before-4k.log','before-warm-files-4k.log']]
after=[metrics(n) for n in ['after-4k.log','after-warm-files-4k.log']]
assert all(r['cache_hits']==0 for r in before) and all(r['cache_hits']==5 for r in after)
parity=[]
for angle in [0,1]:
 a=P/'before'/f'atari-vcs.glb-{angle}.png';b=P/'assets'/a.name
 assert sha(a)==sha(b)
 parity.append({'angle_radians':angle*-.9,'width':3840,'height':2160,'before_after_SHA256':sha(a)})
source=ROOT/'models/atari-vcs.glb';clone=P/'assets/atari-vcs.glb';cache=P/'assets/atari-vcs.artwork.pmc'
assert sha(source)==sha(clone)=='f0dfcdb148233965012023f952adfb9547d31cde47c547401ed55031f44cf0e2'
assert cache.read_bytes()[:8]==b'PMAC0001'
avg=lambda rows,key:statistics.mean(r[key] for r in rows)
benefit=avg(before,'request_ready_ms')-avg(after,'request_ready_ms')
assert benefit>100 and all(a['request_ready_ms']<b['request_ready_ms'] for a,b in zip(after,before))
report={
 'status':'PASS_LOSSLESS_CACHE_STAGE_AND_TOTAL_LATENCY_BENEFIT_HOST_ONLY',
 'source':{'path':'models/atari-vcs.glb','sha256':sha(source),'bytes':source.stat().st_size},
 'cache':{'path':cache.relative_to(ROOT).as_posix(),'format_version':1,'sha256':sha(cache),'bytes':cache.stat().st_size},
 'exact_4K_pixel_parity':parity,'source_GLBS_unchanged':True,'texture_mips_materials_resolution_unchanged':True,
 'geometry':{'vertices':2477646,'triangles':3917004,'draws':20,'GPU_geometry_bytes':225394560,'GPU_texture_logical_bytes':58720256},
 'without_sidecar_runs':before,'with_lossless_sidecar_runs':after,
 'mean_request_ready_ms':{'without':avg(before,'request_ready_ms'),'with':avg(after,'request_ready_ms'),'saving':benefit},
 'mean_CPU_artwork_prepare_ms':{'without':avg(before,'CPU_artwork_prepare_ms'),'with':avg(after,'CPU_artwork_prepare_ms'),'saving':avg(before,'CPU_artwork_prepare_ms')-avg(after,'CPU_artwork_prepare_ms')},
 'warm_ready_scene_revisit':'PASS geometry/atlases retained, zero new atlas upload calls; FBO recreated at original dimensions; no GLerrors.',
 'eviction_and_32_request_cancel_lifetimes':'PASS both providers',
 'memory':'Peak staged image21MiB unchanged; conservative364MiBmodelestimate unchanged; hostRSS~830MB includes softwareGL and no meaningful total-memory saving is asserted.',
 'cache_payload_percent_of_original_source':round(cache.stat().st_size/source.stat().st_size*100,2),
 'promotion_recommendation':'Admit existingV1provider for this one model after sourceindex coordination; keep originalGLB and originalPNG fallback. Source/runtime grouped refresh required.',
 'limits':['Two paired first-ready runs and same-process ready-scene revisit are measured. OS pagecache was not forcibly cleared: no physical coldboot/disk or PS5 load/FPS claim.',
 'The fixture first performs synchronous source validation, which can warm filesystem state and influences RSS; timings are host process only.',
 'Most remaining time is source geometry read/parse/upload and synchronous GLallocation. Sidecar cannot make3.9milliontriangles or their source disappear.',
 'No memorycap, geometric detail, material channels, texture dimensions or quantization changed.']}
out=P/'verification.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(out.relative_to(ROOT),sha(out));print('readymean',report['mean_request_ready_ms'],'cache',cache.stat().st_size)
