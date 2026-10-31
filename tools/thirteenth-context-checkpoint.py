"""Freeze and recover a bounded, independently reviewed context-image checkpoint."""
from pathlib import Path
import copy,hashlib,json,runpy,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
BASE='build/research/thirteenth-context-images-source86'
PREVIOUS='build/research/native-twelfth-source86-recoverable'
RECOVERY='build/research/native-thirteenth-source86-recoverable'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def record(p):return dict(bytes=(ROOT/p).stat().st_size,sha256=sha(p))
def write(p,x):
 t=ROOT/p;assert not t.exists(),p;t.parent.mkdir(parents=True,exist_ok=True);t.write_text(json.dumps(x,indent=2)+'\n','utf8');print(p,sha(p))
plan=load(BASE+'-plan.json');mode=sys.argv[1]
if mode=='freeze':
 assert sha('content/catalog.json')=='e09f54a564839edbf695d2562a5cbeb076b51c85e36901a64a8bb121c5dc3faf'
 assert sha('build/runtime-preview/content/catalog.json')=='9c80c6c31a4472c605f85a739ec5bd73c0d134dc71618239c1f2f476ba18c949'
 names=set(load('build/research/twelfth-two-bindings-one-release-sentence-input-freeze.json')['files'])|set(plan['files'])
 names.update(['tools/thirteenth-context-checkpoint.py',BASE+'-plan.json',PREVIOUS+'/manifest.json',PREVIOUS+'/qa-supplement-manifest.json','build/research/twelfth-source86-scoped/verification.json','build/research/twelfth-source86-scoped/recovery-independent-verification.json'])
 write(BASE+'-input-freeze.json',dict(status='APPROVED_THIRTEENTH_INPUTS',files={p:record(p) for p in sorted(names)},native=record('build/eboot.elf'),fonts={p.relative_to(ROOT).as_posix():record(p.relative_to(ROOT).as_posix())for p in (ROOT/'assets/fonts').glob('*.huifont')},previous_manifest=record(PREVIOUS+'/manifest.json'),previous_qa_overlay=record(PREVIOUS+'/qa-supplement-manifest.json'),scope=plan['scope']))
elif mode=='prove':
 master=load('content/catalog.json');runtime=load('build/runtime-preview/content/catalog.json');old=load(PREVIOUS+'/files/content/catalog.json');oldruntime=load(PREVIOUS+'/files/build/runtime-preview/content/catalog.json')
 mo={e['id']:e for e in master['entries']};oo={e['id']:e for e in old['entries']};ro={e['id']:e for e in runtime['entries']};orr={e['id']:e for e in oldruntime['entries']}
 assert len(mo)==len(oo)==len(ro)==1400
 expected=copy.deepcopy(old['entries']);results=[]
 for helper in plan['helpers']:
  results.append(runpy.run_path(str(ROOT/helper))['apply'](expected,ROOT))
 eo={e['id']:e for e in expected};provider=load('build/research/ps1-v2-provider-thirteenth/promotion.json')['provider']
 for model in eo['playstation']['models']:model['artwork_cache']=copy.deepcopy(provider)
 changed={i for i in mo if mo[i]!=oo[i]};assert changed==set(plan['expected_changed_entries']),changed
 assert {i for i in ro if ro[i]!=orr[i]}<=changed
 for i in mo:
  for field in set(mo[i])|set(eo[i]):
   if field!='publication_readiness':assert mo[i].get(field)==eo[i].get(field),(i,field)
  for field in ('body','story_headings','date','year','soundtrack','soundtrack_rooms','videos'):
   assert mo[i].get(field)==oo[i].get(field),(i,field)
  if i!='playstation':assert mo[i].get('models')==oo[i].get('models'),i
 records=load('build/research/twelfth-two-bindings-one-release-sentence-final-proof.json')['body_records']
 for x in records:
  for d in (mo,ro):assert hashlib.sha256(d[x['entry_id']]['body'][x['index']].encode()).hexdigest()==x['body_sha256']
 freeze=load(BASE+'-input-freeze.json')
 for p,x in freeze['files'].items():assert record(p)==x,p
 for p,x in freeze['fonts'].items():assert record(p)==x,p
 assert record('build/eboot.elf')==freeze['native']
 integrity=load(BASE+'-integrity.json');assert integrity['missing_full_or_preview']==0
 write(BASE+'-final-proof.json',dict(status='PASS_THIRTEENTH_EXACT_ADMISSION_SCOPE',catalogues=[dict(path=p,**record(p))for p in ('content/catalog.json','build/runtime-preview/content/catalog.json')],entries=1400,changed_entries=sorted(changed),all_other_full_authoring_runtime_records_unchanged=True,all_prose_headings_dates_videos_music_unchanged=True,body_records=records,previous206_clarity_records_exact=True,helper_results=results,native=dict(path='build/eboot.elf',**freeze['native']),fonts=freeze['fonts'],image_manifest=record('assets/images/manifest.json'),new_original_assets=plan['new_original_assets'],required_local_images=integrity['required_unique_image_urls'],missing_full_or_preview=0,cache_limit='Lossless CPU staging benefit only; no GPU storage or physical PS5 performance claim.',no_native_build=True,no_font_build=True,no_ftp=True,no_shutdown=True))
elif mode=='recover':
 proof=load(BASE+'-final-proof.json');freeze=load(BASE+'-input-freeze.json')
 for r in proof['catalogues']:assert record(r['path'])==dict(bytes=r['bytes'],sha256=r['sha256'])
 names=set(load(PREVIOUS+'/manifest.json')['files'])|set(load(PREVIOUS+'/qa-supplement-manifest.json')['files'])|set(freeze['files'])
 names.update([BASE+'-input-freeze.json',BASE+'-final-proof.json',BASE+'-integrity.json','build/research/thirteenth-existing-parser-equivalence.log','tools/thirteenth-context-checkpoint.py'])
 for rel in plan['new_original_assets']:names.add(rel)
 records={}
 for p in sorted(names):
  target=ROOT/RECOVERY/'files'/p;target.parent.mkdir(parents=True,exist_ok=True);assert (ROOT/RECOVERY).resolve() in target.resolve().parents
  if p in freeze['files']:assert record(p)==freeze['files'][p],p
  shutil.copy2(ROOT/p,target);records[p]=record(RECOVERY+'/files/'+p);assert records[p]==record(p)
 write(RECOVERY+'/manifest.json',dict(status='PASS_RECOVERABLE_THIRTEENTH_DATA',catalogues=proof['catalogues'],native=proof['native'],fonts=proof['fonts'],authoring_proof_sha256=sha(BASE+'-final-proof.json'),scope='Restore coherent authoring/runtime/selector/credits/fonts/native/provider pair. No new native or font build.',files=records))
else:raise ValueError(mode)
