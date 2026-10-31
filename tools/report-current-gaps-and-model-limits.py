"""Read-only work notes bound to the actual407-scene frozen composition."""
from pathlib import Path
from collections import Counter
import hashlib,json
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'build/research/current-work-notes'
P.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=ROOT/'build/research/sano3-media15-font-scoped/actual-profile-frozen.json'
d=json.loads(source.read_text(encoding='utf8'))
assert d['count']==len(d['entries'])==407
main=[r for r in d['entries'] if r['feature']<0]
features=[r for r in d['entries'] if r['feature']>=0]
counts=Counter((r['entry_id'],r['feature'],r['feature_title']) for r in features)
report={'status':'READ_ONLY_ACTUAL_COMPOSED_SCENE_BACKLOG','source':{'path':source.relative_to(ROOT).as_posix(),'sha256':sha(source)},
 'runtime_sha256':'60db30463f7bac87be323f2c1e2b1d92bf393b283d342cfded0bf37828d66362',
 'total_scenes':407,'main_body':{'scenes':len(main),'entry_count':len({r['entry_id'] for r in main}),'percent':round(len(main)/407*100,2)},
 'editorial_features':{'scenes':len(features),'entry_count':len({r['entry_id'] for r in features}),'distinct_features':len(counts),'percent':round(len(features)/407*100,2),
  'gaps_per_feature_histogram':dict(Counter(counts.values()))},
 'main_body_scenes':main,'feature_scenes':features,'counted_from_native_composer_not_raw_source_paragraphs':True,
 'limits':['These407are the frozen third-group baseline, not the upcoming SOURCE72 fourth group.','All407currently have one sourceparagraph per unillustrated composed card. New media must be measured by native composition, not subtracted arithmetically.'],
 'checked_utc':datetime.now(timezone.utc).isoformat()}
target=P/'actual407-main-vs-features.json'
target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
models=json.loads((ROOT/'models/index.json').read_text(encoding='utf8'))['models']
uncached=sorted([{'model':m['exhibit_id'],'file':m['asset_file'],'source_bytes':(ROOT/m['asset_file']).stat().st_size} for m in models if not m.get('artwork_cache')],key=lambda r:r['source_bytes'],reverse=True)
note={
 'scope':'Read-only current3Dlimits; no production changes, renderer invocation or PS5 access.',
 'facts':[
  '30model assets are attached. Odyssey, original NintendoDS and launch Xbox360 remain genuine source/identity holds; no downloaded wrong hardware is promoted.',
  'Historical PS5 console trace showed graphics allocation failure0x505/resource80020023 in the2304MiBphysical driverpool. Current fixes have host pixel/lifetime tests, not a new successful physical-console stress measurement.',
  'Current active/prepared/retired resources are accounted before large admission. GPU neighbour cache stays512MiB with160MiBreserve; models above352MiB are not retained or background-warmed. Large-console revisits therefore require work again.',
  'Image-pressure handling drops nonvisible photoGPUtextures and defers neighbour uploads; visible/transition pictures remain. Mip/source files stay intact.',
  'Decode/cache work is on the worker, with one bounded atlas job. GLstorage allocation still runs synchronously and cannot be preempted by the adaptive2to16MiB transfer budget.512KiBchunks bound transfers, not the driver allocation call.',
  'PS3 has20distinct nonuniform RGBA mipchains totaling917154448logical bytes. Conservative1750.15MiBGPUestimate is not a measured CPUpeak. No exact duplicate/uniform atlas win was found; weakening accounting would hide risk.',
  'GamePad exactnativepayload sidecarv2 reduced measured host requestready1750.32to1599.66ms and prepared-payload vector peak127to85MiB, with identical4Kpixels. PS5keptv1becausev2wasnotawinner; no universalinstantloading claim.',
  'GPU timer and display120Hzacceptance are distinct from delivered120FPS. Physical PS5 frame-time/load/OOM retest remains necessary.'
 ],
 'bounded_next_option':{
  'proposal':'Benchmark the existing lossless artwork sidecar on one currently uncached, texture-heavy model (AtariVCS or NES), with unchangedGLB/materials/mips and exact4Kpixelparity. Adopt only if measured total latency/CPUpeak improves without unjustified payload growth.',
  'basis':'23of30currentmodelrecords have no artwork sidecar; the largest uncachedGLBs are AtariVCS131662820B andNES104798288B. These are file sizes, not decodedGPUestimates.',
  'implementation_risk':'Uses existing validated source-hash-bound cache provider/reader; no new quantization, renderer API or memorycap. Offline sidecar size and cachehit timings still need measurement.',
  'alternative':'An owningSTBdecodebuffer API can eliminate one64MiBcopy on a4KcoldPNGfallback. It does not improve cache-hotPS3 and changes shared image consumers, so it is lower priority than a bounded existing-provider trial.',
  'not_selected':'Release/reallocateactiveFBO would save84.375MiBat4K1920-high but historical~65msreallocationcanhurtrevisit; do not implement speculatively.'},
 'uncached_model_sources':uncached,
 'evidence_paths':['build/research/ps3-memory-lifetime-audit/buffer-lifetime-review.json','build/research/model-sidecar-v2-probe/verification.json','build/research/model-uniform-probe/verification.json','src/museum/screen.cpp','src/museum/object_scene.cpp','src/yt/image.cpp'],
 'current_source_hashes':{p:sha(ROOT/p) for p in ['models/index.json','src/museum/screen.cpp','src/museum/object_scene.cpp','src/yt/image.cpp']},
 'checked_utc':datetime.now(timezone.utc).isoformat()}
(P/'current-3d-limits-and-next-bounded-option.json').write_text(json.dumps(note,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
text='''Current 3D work note (read-only)

407-gap baseline: 219 main-body scenes (64 entries), 188 editorial-feature scenes (47 features across 47 entries, four gaps each). The upcoming group must be profiled independently.

30 models are attached; Odyssey, original Nintendo DS and launch Xbox 360 remain real source holds. Models above 352 MiB are excluded from the 512 MiB neighbour GPU cache, so instant large-model revisits are not promised. Worker decode and incremental uploads preserve quality, but synchronous GL storage allocation can still stall. Historical console OOMs remain pending a fresh physical PS5 stress run. Host PASS does not prove 120 FPS.

PS3 has 20 distinct, nonuniform chains and 874.67 MiB of logical mip bytes. The 1750 MiB figure is conservative GPU accounting, not CPU peak. No duplicate or uniform-texture saving remains. GamePad v2 measured about 151 ms faster on the host and 42 MiB less prepared-vector peak, with exact 4K parity. PS5 stays on v1.

Next safe candidate: benchmark the existing lossless sidecar on one uncached large asset (Atari VCS or NES), preserving original GLB, mips and materials. 23 of 30 models lack sidecars. Adopt only after size, load, peak and pixel tests; do not raise caps, downscale or quantize. Removing the cold STB output copy is possible but does not help cache-hot PS3.
'''
(P/'current-3d-worknote.txt').write_text(text,encoding='utf8')
print(target.relative_to(ROOT),sha(target))
print('main',len(main),'features',len(features),'features_count',len(counts),'uncachedmodels',len(uncached))
