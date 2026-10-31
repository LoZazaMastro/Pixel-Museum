"""Append only the independently approved licensed Burnout collection to NEXT."""
from pathlib import Path
import hashlib,json,copy,sys
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert len(sys.argv)==2,'Pass the root-approved independent receipt path.'
rp=sys.argv[1];r=load(rp);assert r['status']=='PASS'
candidate='build/research/soundtrack-broad/burnout-revenge-licensed-original/forty-original-licensed-songs-candidate.json'
assert sha(candidate)==r['candidate_sha256']=='6ddc01dfaea7ed62ceb6dc84729f9e25142ab98dfb07c6e41b545caf6d0afcff'
source='content/expansion/soundtrack-multitrack-priority-overrides.json';oldsha='9e38d901ecd55361c944d8ff2b7d4734a1997a04a404e8579226ec7ddb515ff3';assert sha(source)==oldsha
s=load(source);before=copy.deepcopy(s['entries']);assert len(before)==85
doc=load(candidate)
for record in doc['source_receipts']:assert sha(record['path'])==record['sha256']
e=copy.deepcopy(doc['entries'][0]);assert e['entry_id']=='burnout-revenge' and e['music_kind']=='licensed_playlist' and e['composer']=='Various artists'
assert len(e['tracks'])==40 and e['tracks'][0]['creator']=='Yellowcard' and not e['full_album_collection']
assert not any(x['entry_id']==e['entry_id'] for x in before)
e['independent_review_receipt']=rp;s['entries'].append(e);assert s['entries'][:85]==before
s['scope']='Independently reviewed music collections, including explicitly identified licensed-song playlists. Completeness is stated per game and published inventory; partial collections remain qualified.'
p=ROOT/(source+'.tmp');p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8');p.replace(ROOT/source)
report=dict(status='PASS_NEXT86_SOURCE_ONLY',source_sha256=sha(source),previous_source_sha256=oldsha,source_entries=86,prior85_exactly_preserved=True,new_licensed_recordings=40,published_inventory=41,held=doc['held_recordings'],independent_review_receipt=rp,independent_review_sha256=sha(rp),master_sha256=sha('content/catalog.json'),runtime_sha256=sha('build/runtime-preview/content/catalog.json'),master_runtime_modified=False)
out='build/research/soundtrack-broad/burnout-revenge-licensed-original/source86-next-promotion.json';(ROOT/out).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report,indent=2))
