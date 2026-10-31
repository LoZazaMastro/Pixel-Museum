"""Check final bounded authoring scope and actual runtime against tenth recovery."""
from pathlib import Path
import hashlib,json,runpy
ROOT=Path(__file__).resolve().parents[1];GROUP='eleventh-clarity5-fact1-media-source86'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def owners(d):
    result={}
    for e in d['entries']:result[e['id']]=e;result.update({f['id']:f for f in e.get('editorial_features',[])})
    return result
master=load('content/catalog.json');runtime=load('build/runtime-preview/content/catalog.json');old=load('build/research/native-tenth-source86-recoverable/files/content/catalog.json');mo,ro,oo=owners(master),owners(runtime),owners(old)
assert len(master['entries'])==len(runtime['entries'])==len(old['entries'])==1400 and master['entry_aliases']==runtime['entry_aliases']==old['entry_aliases']
records=load('build/research/tenth-clarity5-media4-source86-final-proof.json')['body_records'][:];assert len(records)==201
join=runpy.run_path(str(ROOT/'content/expansion/reviewed_clarity_next.py'));textowners=set();factual=[]
for c,_ in list(join['PLANS'][-3:])+list(join['POST_MEDIA_PLANS']):
    for r in load(c)['replacements']:
        eid=r['entry_id'];i=r['source_chapter_index'];textowners.add(eid)
        assert oo[eid]['body'][i]==r['old_body'] and mo[eid]['body'][i]==ro[eid]['body'][i]==r['body']
        assert mo[eid]['story_headings'][i]==ro[eid]['story_headings'][i]==r['heading']
        rec=dict(entry_id=eid,index=i,body_sha256=r['body_sha256'])
        (factual if 'bg3-early-access' in c else records).append(rec)
assert len(records)==206 and len(factual)==1 and len({(r['entry_id'],r['index']) for r in records})==206
for r in records+factual:
    for doc in (mo,ro):assert hashlib.sha256(doc[r['entry_id']]['body'][r['index']].encode()).hexdigest()==r['body_sha256']
imagechanged=[]
for eid,e in oo.items():
    for f in ('title','year','date','models','soundtrack','soundtrack_rooms'):assert e.get(f)==mo[eid].get(f),(eid,f)
    if eid not in textowners:
        for f in ('body','story_headings'):assert e.get(f)==mo[eid].get(f)==ro[eid].get(f),(eid,f)
    if e.get('images')!=mo[eid].get('images'):
        imagechanged.append(eid)
        assert 'alive' in eid.lower(),eid
        for i in mo[eid]['images']:
            assert any(x['url']==i['url'] and x.get('story_paragraph')==i.get('story_paragraph') for x in ro[eid]['images'])
assert len(imagechanged)<=1
allowed=textowners|set(imagechanged);changed=[eid for eid in oo if oo[eid]!=mo[eid]];assert set(changed)<=allowed,changed
freeze=load('build/research/'+GROUP+'-input-freeze.json')
for p,r in freeze['files'].items():assert sha(p)==r['sha256'],p
assert sha('build/eboot.elf')==freeze['native_sha256']
integrity=load('build/research/'+GROUP+'-integrity.json');assert integrity['missing_full_or_preview']==0
proof=dict(status='PASS_ELEVENTH_BOUNDED_CONTENT_PENDING_SCOPED_QA_NOT_COMPLETE',master_sha256=sha('content/catalog.json'),runtime_sha256=sha('build/runtime-preview/content/catalog.json'),runtime_bytes=(ROOT/'build/runtime-preview/content/catalog.json').stat().st_size,entries=1400,culture=342,aliases=23,models=30,total_revised_body_records=206,body_records=records,separate_factual_fix_records=factual,changed_owners=changed,all_other_owner_records_exact=True,illustration_array_changed_owners=imagechanged,all_dates_models_music_preserved=True,source86_sha256=sha('content/expansion/soundtrack-multitrack-priority-overrides.json'),media81_sha256=sha('content/expansion/museum-story-gap-illustrations-reviewed.json'),required_local_images=integrity['required_unique_image_urls'],missing_full_or_preview=0,recovery=freeze['recovery'],recovery_sha256=freeze['recovery_sha256'],previous_full_actual_gaps=318,no_new_native_code_or_compile=True,native_sha256=sha('build/eboot.elf'),no_further_source_admissions=True,ready_to_claim_complete=False,no_ftp=True,shutdown_authorization=False)
out='build/research/'+GROUP+'-final-proof.json';assert not (ROOT/out).exists();(ROOT/out).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(out,sha(out));print(proof['master_sha256'],proof['runtime_sha256'],proof['runtime_bytes'])
