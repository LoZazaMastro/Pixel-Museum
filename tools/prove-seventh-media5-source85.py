"""Check the seventh payload against the complete recovered sixth catalogue."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];GROUP='seventh-media5-source85'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def owners(d):
    result={}
    for e in d['entries']:
        result[e['id']]=e;result.update({f['id']:f for f in e.get('editorial_features',[])})
    return result
master=load('content/catalog.json');runtime=load('build/runtime-preview/content/catalog.json');old=load('build/research/native-sixth-source81-recoverable/files/content/catalog.json')
mo,ro,oo=owners(master),owners(runtime),owners(old)
assert len(master['entries'])==len(runtime['entries'])==len(old['entries'])==1400
assert master['entry_aliases']==runtime['entry_aliases']==old['entry_aliases'] and len(master['entry_aliases'])==23
for eid,prior in oo.items():
    for field in ('body','story_headings','title','year','date','models'):
        assert prior.get(field)==mo[eid].get(field)==ro[eid].get(field),(eid,field)
records=load('build/research/sixth-media11-sp4-source81-final-proof.json')['body_records'];assert len(records)==190
for r in records:
    for doc in (mo,ro):assert hashlib.sha256(doc[r['entry_id']]['body'][r['index']].encode()).hexdigest()==r['body_sha256']
added=[]
for eid,e in oo.items():
    prior={i['url'] for i in e.get('images',[])};current={i['url'] for i in mo[eid].get('images',[])};assert prior<=current
    for i in mo[eid].get('images',[]):
        if i['url'] not in prior:
            assert i['story_paragraph']>=0 and any(j['url']==i['url'] and j.get('story_paragraph')==i['story_paragraph'] for j in ro[eid]['images'])
            added.append(dict(owner=eid,url=i['url'],paragraph=i['story_paragraph']))
assert len(added)==5
music=load('content/expansion/soundtrack-multitrack-priority-overrides.json');assert len(music['entries'])==85
assert sha('content/expansion/soundtrack-multitrack-priority-overrides.json')=='9e38d901ecd55361c944d8ff2b7d4734a1997a04a404e8579226ec7ddb515ff3'
musicproof=[]
for e in music['entries'][-4:]:
    actual=mo[e['entry_id']]['soundtrack'];native=ro[e['entry_id']]['soundtrack']
    assert actual['tracks']==e['tracks'] and len(native['tracks'])==len(e['tracks'])
    for a,b in zip(native['tracks'],e['tracks']):
        for f in ('youtube_id','title','creator','url','source_page','start_seconds','end_seconds'):assert a.get(f)==b.get(f)
    for f in ('full_album_collection','coverage_status','album_completeness'):assert actual.get(f)==e.get(f)
    musicproof.append(dict(entry_id=e['entry_id'],recordings=len(e['tracks']),published_album_complete=e['full_album_collection'],all_tracks_and_bounds_preserved=True))
assert sum(x['recordings'] for x in musicproof)==295
integrity=load('build/research/'+GROUP+'-integrity.json');assert integrity['missing_full_or_preview']==0
proof=dict(status='PASS_COHERENT_SEVENTH_SOURCE_RUNTIME_LOCAL_MEDIA_NOT_COMPLETION',master_sha256=sha('content/catalog.json'),runtime_sha256=sha('build/runtime-preview/content/catalog.json'),runtime_bytes=(ROOT/'build/runtime-preview/content/catalog.json').stat().st_size,entries=1400,culture=342,aliases=23,models=30,total_revised_body_records=190,body_records=records,all_prior_bodies_dates_headings_models_preserved=True,new_narrative_image_records=added,approved_music_source_entries=85,new_music_rooms=musicproof,required_local_images=integrity['required_unique_image_urls'],missing_full_or_preview=0,recovery='build/research/native-sixth-source81-recoverable/manifest.json',recovery_sha256=sha('build/research/native-sixth-source81-recoverable/manifest.json'),actual_composition_gap_last_verified=363,composition_scope='Previous sixth only; current seventh actual compositor profile required. No inferred subtraction.',ready_to_claim_complete=False)
out='build/research/'+GROUP+'-final-proof.json';(ROOT/out).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(out,sha(out));print(json.dumps({k:v for k,v in proof.items() if k not in ['body_records','new_narrative_image_records']},indent=2))
