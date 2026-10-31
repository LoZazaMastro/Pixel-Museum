"""Check the fifth active checkpoint against its immutable approval inputs."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];GROUP='fifth-switch5-media5-source76'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def owners(doc):
    out={}
    for e in doc['entries']:
        out[e['id']]=e
        out.update({f['id']:f for f in e.get('editorial_features',[])})
    return out
master=load('content/catalog.json');runtime=load('build/runtime-preview/content/catalog.json')
old=load('build/research/native-fourth-source73-recoverable/files/content/catalog.json')
mo,ro,oo=owners(master),owners(runtime),owners(old)
assert len(master['entries'])==len(runtime['entries'])==1400
assert master['entry_aliases']==runtime['entry_aliases']==old['entry_aliases'] and len(master['entry_aliases'])==23
for eid,e in oo.items():
    for field in ('body','story_headings','title','year','date'):
        assert e.get(field)==mo[eid].get(field)==ro[eid].get(field),(eid,field)
prior=load('build/research/gba-steamdeck-vr-eve-skyrim-final5-source73-final-proof.json')
for row in prior['body_records']:
    eid,n=row['entry_id'],row['index']
    assert hashlib.sha256(mo[eid]['body'][n].encode()).hexdigest()==row['body_sha256']
assert len(prior['body_records'])==186
switch=load('content/expansion/museum-switch-game-additions-reviewed.json');new=[]
for batch in switch['batches']:
    for e in load(batch['candidate_path'])['entries']:
        assert e['id'] not in oo
        for field in ('body','story_headings','title','year'):
            assert mo[e['id']][field]==ro[e['id']][field]==e[field]
        for field in ('month','day','precision'):assert mo[e['id']]['date'][field]==ro[e['id']]['date'][field]==e['date'][field]
        assert mo[e['id']]['date']['region']==ro[e['id']]['date']['region']==''
        assert len(mo[e['id']]['images'])==len(ro[e['id']]['images'])==7
        for im in e['images']:
            for table in (mo,ro):
                actual=next(i for i in table[e['id']]['images'] if i['url']==im['url'])
                assert actual.get('story_paragraph',-1)==im.get('story_paragraph',-1)
        new.append(dict(entry_id=e['id'],body_paragraphs=5,images=7,official_videos=1))
assert len(new)==5
added=[]
for eid,e in oo.items():
    oldurls={i['url'] for i in e.get('images',[])}
    current={i['url'] for i in mo[eid].get('images',[])}
    assert oldurls<=current,eid
    for i in mo[eid].get('images',[]):
        if i['url'] not in oldurls:
            assert i['story_paragraph']>=0
            assert any(j['url']==i['url'] and j.get('story_paragraph')==i['story_paragraph'] for j in ro[eid]['images'])
            added.append(dict(entry_id=eid,url=i['url'],paragraph=i['story_paragraph']))
assert len(added)==5
music=load('content/expansion/soundtrack-multitrack-priority-overrides.json')
assert len(music['entries'])==76 and sha('content/expansion/soundtrack-multitrack-priority-overrides.json')=='26db196e074924347ab6639959b0440cfec108b15887ea7f6bf111ac220697d1'
rooms=[]
for e in music['entries'][-3:]:
    actual=mo[e['entry_id']]['soundtrack'];native=ro[e['entry_id']]['soundtrack']
    assert actual['tracks']==e['tracks']
    assert len(native['tracks'])==len(e['tracks'])
    for a,b in zip(native['tracks'],e['tracks']):
        for f in ('youtube_id','title','creator','url','source_page','start_seconds','end_seconds'):assert a.get(f)==b.get(f)
    for f in ('full_album_collection','coverage_status','album_completeness'):assert actual[f]==e[f]
    rooms.append(dict(entry_id=e['entry_id'],recordings=len(e['tracks']),full_published_album=e['full_album_collection'],all_native_bounds_preserved=True))
assert sum(r['recordings'] for r in rooms)==158
models=[m for e in master['entries'] for m in e.get('models',[])]
assert len(models)==30
atari=next(m for m in models if m.get('exhibit_id')=='atari-vcs' or m.get('asset_file')=='models/atari-vcs.glb')
assert atari['artwork_cache']['sha256']=='cb97fde4107551cdf0a752ede1de3b15d83051a99acbea60d2baf5c08760d9f2'
integrity=load('build/research/'+GROUP+'-integrity.json');assert integrity['missing_full_or_preview']==0
freeze=load('build/research/'+GROUP+'-input-freeze.json')
for p,r in freeze['files'].items():assert sha(p)==r['sha256'],p
proof=dict(status='PASS_COHERENT_FIFTH_SOURCE_RUNTIME_LOCAL_MEDIA_NOT_COMPLETION',master_sha256=sha('content/catalog.json'),runtime_sha256=sha('build/runtime-preview/content/catalog.json'),runtime_bytes=(ROOT/'build/runtime-preview/content/catalog.json').stat().st_size,entries=1400,culture=342,aliases=23,models=30,prior186_revised_bodies_still_exact=True,all_prior_entry_bodies_dates_headings_preserved=True,new_articles=new,new_article_paragraphs=25,new_article_assets=35,new_existing_story_images=added,new_music_rooms=rooms,source_override_entries=76,required_local_images=integrity['required_unique_image_urls'],missing_full_or_preview=0,recovery='build/research/native-fourth-source73-recoverable/manifest.json',recovery_sha256=sha('build/research/native-fourth-source73-recoverable/manifest.json'),actual_composition_gap_last_verified=389,composition_scope='Previous fourth only; fresh fifth actual composition must be profiled. No inferred subtraction.',ready_to_claim_complete=False)
out='build/research/'+GROUP+'-final-proof.json';(ROOT/out).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8')
print(out,sha(out));print(json.dumps({k:v for k,v in proof.items() if k not in ['new_articles','new_existing_story_images']},indent=2))
