"""Freeze, prove, and recover the two associations plus one sentence cleanup."""
from pathlib import Path
import copy,hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];GROUP='twelfth-two-bindings-one-release-sentence';BASE='build/research/'+GROUP
PREVIOUS='build/research/native-eleventh-source86-recoverable';RECOVERY='build/research/native-twelfth-source86-recoverable'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def record(p):return dict(bytes=(ROOT/p).stat().st_size,sha256=sha(p))
def write(p,v):
    target=ROOT/p;assert not target.exists(),p;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8');print(p,sha(p))
mode=sys.argv[1]
if mode=='freeze':
    assert sha('content/catalog.json')=='50e3d1f91119a6aa7dd62032ef8f7c7f7a42a053d67a7b05ea3e9b51bdca70ba'
    assert sha('build/runtime-preview/content/catalog.json')=='a7c071c8d89d02863fdf7798da991674995ab1f419642a3a1c28e55eeb045e9a'
    assert sha(PREVIOUS+'/manifest.json')=='ed9c0eda9e475e6d11c4d4989374e3139d09a87aff426765e7267c28bcb9a5fe'
    for p,r in load(PREVIOUS+'/manifest.json')['files'].items():assert sha(PREVIOUS+'/files/'+p)==r['sha256'],p
    names=set(load('build/research/eleventh-clarity5-fact1-media-source86-input-freeze.json')['files'])
    names.update(['tools/twelfth-existing-bindings-checkpoint.py','content/expansion/reviewed_episode2_bindings.py','content/expansion/museum-episode2-existing-bindings-reviewed.json','content/expansion/reviewed_dishonored_release_prose.py','content/expansion/museum-dishonored-release-prose-reviewed.json','build/research/twelfth-episode2-existing-bindings/two-existing-publisher-still-bindings-candidate.json','build/research/twelfth-episode2-existing-bindings/root-independent-two-bindings-review.json','build/research/twelfth-episode2-existing-bindings/isolated-two-bindings-one-sentence-check.json','build/research/dishonored-single-release-prose-cleanup/candidate.json','build/research/dishonored-single-release-prose-cleanup/independent-single-release-prose-cleanup-review.json',PREVIOUS+'/manifest.json','build/research/eleventh-source86-scoped/verification.json','build/research/eleventh-source86-scoped/recovery-independent-verification.json'])
    for s in load('build/research/twelfth-episode2-existing-bindings/two-existing-publisher-still-bindings-candidate.json')['source_receipts']:names.add(s['path'])
    fonts={p.relative_to(ROOT).as_posix():record(p.relative_to(ROOT).as_posix()) for p in (ROOT/'assets/fonts').glob('*.huifont')}
    write(BASE+'-input-freeze.json',dict(status='APPROVED_BOUNDED_TWELFTH_INPUTS',files={p:record(p) for p in sorted(names)},fonts=fonts,native=record('build/eboot.elf'),image_manifest=record('assets/images/manifest.json'),recovery=PREVIOUS+'/manifest.json',recovery_sha256=sha(PREVIOUS+'/manifest.json'),scope='Exactly two existing image paragraph indices and one regional rollout sentence. No build, new asset, unrelated prose or completeness claim.'))
elif mode=='prove':
    master=load('content/catalog.json');runtime=load('build/runtime-preview/content/catalog.json');old=load(PREVIOUS+'/files/content/catalog.json');oldruntime=load(PREVIOUS+'/files/build/runtime-preview/content/catalog.json')
    mo={e['id']:e for e in master['entries']};ro={e['id']:e for e in runtime['entries']};oo={e['id']:e for e in old['entries']};oruntime={e['id']:e for e in oldruntime['entries']}
    assert len(mo)==len(ro)==len(oo)==1400
    targets={'9-nine-episode-2','workbook-10-09-dishonored'}
    assert {i for i in mo if mo[i]!=oo[i]}==targets
    assert {i for i in ro if ro[i]!=oruntime[i]}==targets
    ep=load('build/research/twelfth-episode2-existing-bindings/two-existing-publisher-still-bindings-candidate.json');dish=load('build/research/dishonored-single-release-prose-cleanup/candidate.json')
    assert mo['9-nine-episode-2']['images']==ep['new_images'] and oo['9-nine-episode-2']['images']==ep['old_images']
    for field in set(mo['9-nine-episode-2'])|set(oo['9-nine-episode-2']):
        if field not in ('images','provenance'):assert mo['9-nine-episode-2'].get(field)==oo['9-nine-episode-2'].get(field)
    numeric=[]
    for i,(a,b) in enumerate(zip(ep['old_images'],ep['new_images'])):
        for f in set(a)|set(b):
            if a.get(f)!=b.get(f):numeric.append((i,f,a.get(f),b.get(f)))
    assert numeric==[(1,'story_paragraph',-1,0),(2,'story_paragraph',-1,2)]
    d=mo[dish['entry_id']];prior=oo[dish['entry_id']]
    assert d['body'][0]==dish['body'] and prior['body'][0]==dish['old_body'] and d['body'][1:]==prior['body'][1:]
    assert set(d['body'][0])<=set(prior['body'][0]),'No new displayed characters permitted'
    for f in set(d)|set(prior):
        if f not in ('body','provenance'):assert d.get(f)==prior.get(f)
    for i,e in oo.items():
        for f in ('year','date','models','soundtrack','soundtrack_rooms'):assert e.get(f)==mo[i].get(f),(i,f)
    assert ro['9-nine-episode-2']['images'][1]['story_paragraph']==0 and ro['9-nine-episode-2']['images'][2]['story_paragraph']==2
    assert ro[dish['entry_id']]['body'][0]==dish['body']
    records=load('build/research/eleventh-clarity5-fact1-media-source86-final-proof.json')['body_records'];assert len(records)==206
    for x in records:
        for doc in (mo,ro):assert hashlib.sha256(doc[x['entry_id']]['body'][x['index']].encode()).hexdigest()==x['body_sha256']
    freeze=load(BASE+'-input-freeze.json')
    for p,x in freeze['files'].items():assert sha(p)==x['sha256'],p
    for p,x in freeze['fonts'].items():assert sha(p)==x['sha256'],p
    assert record('build/eboot.elf')==freeze['native'] and record('assets/images/manifest.json')==freeze['image_manifest']
    integrity=load(BASE+'-integrity.json');assert integrity['missing_full_or_preview']==0
    write(BASE+'-final-proof.json',dict(status='PASS_TWELFTH_EXACT_DATA_SCOPE_NO_NEW_NATIVE_OR_FONT_BUILD',catalogues=[dict(path=p,**record(p)) for p in ('content/catalog.json','build/runtime-preview/content/catalog.json')],entries=1400,all_other1398_full_authoring_and_runtime_entry_records_exact=True,numeric_image_changes=numeric,release_sentence_cleanup=dish['entry_id'],prior206_clarity_records_exact=True,body_records=records,all_dates_models_music_unchanged=True,all_image_urls_titles_captions_unchanged=True,new_assets=0,new_display_characters=0,fonts=freeze['fonts'],native=dict(path='build/eboot.elf',**freeze['native']),font_scope='Unchanged946-glyph external fonts inherited from verified11; the shortened Latin sentence adds no characters and all nine complex phrases remain unchanged.',actual_composition_scope='No new actual-screen or global compositor run claimed. Last full verified profile11 remains318; no inferred subtraction and no paragraph1/full-article completion claim.',image_manifest_unchanged=True,required_local_images=integrity['required_unique_image_urls'],missing_full_or_preview=0,recovery=freeze['recovery'],recovery_sha256=freeze['recovery_sha256'],no_native_build=True,no_font_build=True,no_ftp=True,shutdown_authorization=False))
elif mode=='recover':
    proof=load(BASE+'-final-proof.json');assert proof['status'].startswith('PASS')
    for x in proof['catalogues']:assert record(x['path'])==dict(bytes=x['bytes'],sha256=x['sha256'])
    freeze=load(BASE+'-input-freeze.json');names=set(load(PREVIOUS+'/manifest.json')['files'])|set(freeze['files'])
    names.update([BASE+'-input-freeze.json',BASE+'-final-proof.json',BASE+'-integrity.json','build/research/twelfth-existing-parser-equivalence.log','tools/twelfth-existing-bindings-checkpoint.py'])
    records={};out=ROOT/RECOVERY;assert not (out/'manifest.json').exists()
    for p in sorted(names):
        source=ROOT/p;target=out/'files'/p;target.parent.mkdir(parents=True,exist_ok=True);assert out.resolve() in target.resolve().parents
        if p in freeze['files']:assert sha(p)==freeze['files'][p]['sha256'],p
        shutil.copy2(source,target);records[p]=record(RECOVERY+'/files/'+p);assert records[p]==record(p)
    write(RECOVERY+'/manifest.json',dict(status='PASS_RECOVERABLE_TWELFTH_EXACT_DATA_PAYLOAD',catalogues=proof['catalogues'],native=proof['native'],fonts=proof['fonts'],authoring_proof_sha256=sha(BASE+'-final-proof.json'),scope='Restore complete authoring/runtime/credits/selector/font/native pair together. Existing original assets remain at their unchanged recorded paths. No new native/font build or actual-screen completion claim.',files=records))
else:raise ValueError(mode)
