"""Prove the bounded tenth payload against recovered ninth authoring data."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];GROUP='tenth-clarity5-media4-source86'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def owners(d):
    result={}
    for e in d['entries']:result[e['id']]=e;result.update({f['id']:f for f in e.get('editorial_features',[])})
    return result
master=load('content/catalog.json');runtime=load('build/runtime-preview/content/catalog.json');old=load('build/research/native-ninth-source86-recoverable/files/content/catalog.json')
mo,ro,oo=owners(master),owners(runtime),owners(old)
assert len(master['entries'])==len(runtime['entries'])==len(old['entries'])==1400
assert master['entry_aliases']==runtime['entry_aliases']==old['entry_aliases']
plans=__import__('runpy').run_path(str(ROOT/'content/expansion/reviewed_clarity_next.py'))['PLANS'][-2:]
records=load('build/research/ninth-media7-mega3-source86-final-proof.json')['body_records'][:];assert len(records)==196
textowners=set()
for c,_ in plans:
    candidate=load(c if c.startswith('build/') else 'build/research/playhub-semantic-coverage/wiki-clarity/'+c)
    for r in candidate['replacements']:
        eid=r['entry_id'];i=r['source_chapter_index'];textowners.add(eid)
        assert oo[eid]['body'][i]==r['old_body']
        assert mo[eid]['body'][i]==ro[eid]['body'][i]==r['body']
        assert mo[eid]['story_headings'][i]==ro[eid]['story_headings'][i]==r['heading']
        records.append(dict(entry_id=eid,index=i,body_sha256=r['body_sha256']))
assert len(records)==201 and len({(r['entry_id'],r['index']) for r in records})==201
for r in records:
    for doc in (mo,ro):assert hashlib.sha256(doc[r['entry_id']]['body'][r['index']].encode()).hexdigest()==r['body_sha256']
added=[]
for eid,e in oo.items():
    for f in ('year','date','title','models','soundtrack','soundtrack_rooms'):assert e.get(f)==mo[eid].get(f),(eid,f)
    if eid not in textowners:
        for f in ('body','story_headings'):assert e.get(f)==mo[eid].get(f)==ro[eid].get(f),(eid,f)
    prior={i['url'] for i in e.get('images',[])};current={i['url'] for i in mo[eid].get('images',[])};assert prior<=current
    for i in mo[eid].get('images',[]):
        if i['url'] not in prior:
            assert i['story_paragraph']>=0
            assert any(x['url']==i['url'] and x.get('story_paragraph')==i['story_paragraph'] for x in ro[eid]['images'])
            added.append(dict(owner=eid,url=i['url'],paragraph=i['story_paragraph']))
assert len(added)==4,added
allowed=textowners|{r['owner'] for r in added}|{'daily-12-12','roberta-williams','minecraft'}
changed=[eid for eid in oo if oo[eid]!=mo[eid]];assert set(changed)<=allowed,changed
freeze=load('build/research/'+GROUP+'-input-freeze.json')
for p,r in freeze['files'].items():assert sha(p)==r['sha256'],p
assert sha('build/eboot.elf')==freeze['native_sha256']
integrity=load('build/research/'+GROUP+'-integrity.json');assert integrity['missing_full_or_preview']==0
proof=dict(status='PASS_COHERENT_TENTH_PENDING_SCOPED_QA_NOT_COMPLETE',master_sha256=sha('content/catalog.json'),runtime_sha256=sha('build/runtime-preview/content/catalog.json'),runtime_bytes=(ROOT/'build/runtime-preview/content/catalog.json').stat().st_size,entries=1400,culture=342,aliases=23,models=30,total_revised_body_records=201,body_records=records,changed_owners=changed,all_other_owner_records_exact=True,new_narrative_image_records=added,all_dates_models_music_preserved=True,source86_sha256=sha('content/expansion/soundtrack-multitrack-priority-overrides.json'),media81_sha256=sha('content/expansion/museum-story-gap-illustrations-reviewed.json'),required_local_images=integrity['required_unique_image_urls'],missing_full_or_preview=0,recovery=freeze['recovery'],recovery_sha256=freeze['recovery_sha256'],previous_full_actual_gaps=334,current_actual_composition_profile_required=True,no_new_native_code_or_compile=True,native_sha256=sha('build/eboot.elf'),ready_to_claim_complete=False,no_ftp=True)
out='build/research/'+GROUP+'-final-proof.json';assert not (ROOT/out).exists();(ROOT/out).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(out,sha(out));print(proof['master_sha256'],proof['runtime_sha256'],proof['runtime_bytes'])
