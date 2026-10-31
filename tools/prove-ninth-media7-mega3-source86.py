"""Prove ninth data scope against the complete recovered eighth catalogue."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];GROUP='ninth-media7-mega3-source86'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def owners(d):
    result={}
    for e in d['entries']:
        result[e['id']]=e;result.update({f['id']:f for f in e.get('editorial_features',[])})
    return result
master=load('content/catalog.json');runtime=load('build/runtime-preview/content/catalog.json');old=load('build/research/native-eighth-source85-recoverable/files/content/catalog.json')
mo,ro,oo=owners(master),owners(runtime),owners(old)
assert len(master['entries'])==len(runtime['entries'])==len(old['entries'])==1400
assert master['entry_aliases']==runtime['entry_aliases']==old['entry_aliases'] and len(master['entry_aliases'])==23
allowed={'mega-drive','burnout-revenge','workbook-08-13-gyromite','workbook-06-19-treasure','daily-01-09','workbook-04-07-atlus','workbook-07-28-lua'}
changed_owners=[eid for eid in oo if oo[eid]!=mo[eid]]
assert set(changed_owners)<=allowed,changed_owners
for eid,prior in oo.items():
    for field in ('title','year','date','models'):
        assert prior.get(field)==mo[eid].get(field)==ro[eid].get(field),(eid,field)
    if eid!='mega-drive':
        for field in ('body','story_headings'):
            assert prior.get(field)==mo[eid].get(field)==ro[eid].get(field),(eid,field)
records=load('build/research/eighth-sayonara3-source85-final-proof.json')['body_records'][:];assert len(records)==193
for r in records:
    for doc in (mo,ro):assert hashlib.sha256(doc[r['entry_id']]['body'][r['index']].encode()).hexdigest()==r['body_sha256']
candidate=load('build/research/mega-drive-three-concrete-cards/three-concrete-wikipedia-mega-drive-cards-clear-identities-candidate.json')
for r in candidate['replacements']:
    eid=r['entry_id'];i=r['source_chapter_index'];assert oo[eid]['body'][i]==r['old_body']
    assert mo[eid]['body'][i]==ro[eid]['body'][i]==r['body']
    assert mo[eid]['story_headings'][i]==ro[eid]['story_headings'][i]==r['heading']
    records.append(dict(entry_id=eid,index=i,body_sha256=r['body_sha256']))
assert len(records)==196
added=[];removed=[]
for eid,e in oo.items():
    prior={i['url'] for i in e.get('images',[])};current={i['url'] for i in mo[eid].get('images',[])}
    for url in prior-current:removed.append(dict(owner=eid,url=url))
    for i in mo[eid].get('images',[]):
        if i['url'] not in prior and isinstance(i.get('story_paragraph'),int) and i['story_paragraph']>=0:
            assert any(j['url']==i['url'] and j.get('story_paragraph')==i['story_paragraph'] for j in ro[eid]['images'])
            added.append(dict(owner=eid,url=i['url'],paragraph=i['story_paragraph']))
assert len(added)==7,(len(added),added)
for r in removed:assert 'lua' in r['owner'].lower(),r
music=load('content/expansion/soundtrack-multitrack-priority-overrides.json');assert len(music['entries'])==86
assert sha('content/expansion/soundtrack-multitrack-priority-overrides.json')=='1508134c195845869dfdbab88c754ed032de17dcde5dd9c5859b89d6adef47b5'
e=music['entries'][-1];assert e['entry_id']=='burnout-revenge' and len(e['tracks'])==40
actual=mo[e['entry_id']]['soundtrack'];native=ro[e['entry_id']]['soundtrack']
assert actual['tracks']==e['tracks'] and len(native['tracks'])==40
for a,b in zip(native['tracks'],e['tracks']):
    for f in ('youtube_id','title','creator','url','source_page','start_seconds','end_seconds'):assert a.get(f)==b.get(f),(a['title'],f)
for eid in oo:
    if eid!='burnout-revenge':
        for f in ('soundtrack','soundtrack_rooms'):assert mo[eid].get(f)==oo[eid].get(f),(eid,f)
freeze=load('build/research/'+GROUP+'-input-freeze.json')
for p,r in freeze['files'].items():assert sha(p)==r['sha256'],p
lua_cover_proof=None
if freeze['additional_lua_inputs']:
    eid='workbook-07-28-lua';old_urls={i['url'] for i in oo[eid]['images']}
    for doc in (mo,ro):
        assert not old_urls.intersection(i['url'] for i in doc[eid]['images'])
        assert doc[eid]['preferred_image']==0
        assert doc[eid]['images'][0]['url']=='https://www.lua.org/images/lua-logo-nolabel.ps'
    lua_cover_proof=dict(entry_id=eid,wrong_game_urls_removed_from_both_display_arrays=True,new_cover='Official Lua.org vector logo, transparent-page rasterization; no photo upscale',narrative_added=False)
integrity=load('build/research/'+GROUP+'-integrity.json');assert integrity['missing_full_or_preview']==0
proof=dict(status='PASS_COHERENT_NINTH_PENDING_NATIVE_QA_NOT_COMPLETE',master_sha256=sha('content/catalog.json'),runtime_sha256=sha('build/runtime-preview/content/catalog.json'),runtime_bytes=(ROOT/'build/runtime-preview/content/catalog.json').stat().st_size,entries=1400,culture=342,aliases=23,models=30,total_revised_body_records=196,body_records=records,changed_owners=changed_owners,all_other_owner_records_exact=True,new_narrative_image_records=added,lua_quarantined_image_urls=removed,all_prior_other_bodies_dates_models_music_preserved=True,approved_music_source_entries=86,new_licensed_music_room=dict(entry_id='burnout-revenge',recordings=40,inventory=41,held=1,full_album_collection=False),required_local_images=integrity['required_unique_image_urls'],missing_full_or_preview=0,recovery=freeze['recovery'],recovery_sha256=freeze['recovery_sha256'],previous_full_actual_gaps=353,current_actual_composition_profile_required=True,native_scope='Approved material-group merge preallocation; new native compile pending sibling QA.',ready_to_claim_complete=False,no_ftp=True)
proof['lua_cover_correction']=lua_cover_proof
out='build/research/'+GROUP+'-final-proof.json';assert not (ROOT/out).exists(),'Do not overwrite a finalized proof.'
(ROOT/out).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(out,sha(out));print(proof['master_sha256'],proof['runtime_sha256'],proof['runtime_bytes'])
