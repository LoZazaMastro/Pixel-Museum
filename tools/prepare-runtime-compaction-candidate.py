"""Isolated candidate removing only fields ignored by the native reader."""
from pathlib import Path
from collections import Counter
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'build/research/runtime-compaction-source73'
P.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def encode(d):return (json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf8')
runtime=ROOT/'build/runtime-preview/content/catalog.json';raw=runtime.read_bytes()
assert sha(raw)=='95cc1374444743e49fd9726a3f16e7b44f8447c4702ac07a3b5afc16568a2ca0'
master=ROOT/'content/catalog.json';master_hash=sha(master.read_bytes())
assert master_hash=='609124314973d6aa78f89125f5d4e99c4acdcc30fa700c9c0126573e882cfc91'
d=json.loads(raw);removed=Counter();converted=[]
unused_entry={'editorial_mode','language','source_identity_correction','calendar_link_provenance','date_provenance','canonical_reference_restoration','disclosed_english_correction','identity_media_admission','source_edition_restoration','editorial_revision'}
unused_room={'album_completeness','recording_collection_scope','independent_review_receipt','completeness','coverage_status','full_album_collection','music_kind','expected_album_tracks','id'}
unused_track={'channel_url','official_uploader_verified'}
def drop(row,keys,scope):
 for key in list(row):
  if key in keys:removed[scope+'.'+key]+=len(encode({key:row.pop(key)}))
for e in d['entries']:
 drop(e,unused_entry,'entry')
 if isinstance(e.get('canonical_narrative_enrichment'),dict):
  converted.append(e['id']);removed['entry.canonical_narrative_enrichment']+=len(encode({'canonical_narrative_enrichment':e.pop('canonical_narrative_enrichment')}))
  e['explicit_story_media_only']=True
 for room in ([e['soundtrack']] if e.get('soundtrack') else [])+e.get('soundtrack_rooms',[]):
  drop(room,unused_room,'room')
  for t in room.get('tracks',[]):drop(t,unused_track,'track')
compact=encode(d)
assert len(compact)<len(raw)<16<<20
assert runtime.read_bytes()==raw and sha(master.read_bytes())==master_hash
(P/'original-runtime.json').write_bytes(raw)
(P/'candidate-runtime.json').write_bytes(compact)
report={'status':'ISOLATED_CANDIDATE_AWAITING_NATIVE_EQUIVALENCE_AND_ROOT_PEER_NOT_ADMITTED',
 'source_master_sha256':master_hash,'original_runtime_sha256':sha(raw),'original_runtime_bytes':len(raw),
 'candidate_runtime_sha256':sha(compact),'candidate_runtime_bytes':len(compact),'saved_bytes':len(raw)-len(compact),
 'removed_serialized_field_bytes':dict(removed.most_common()),'existing_boolean_flag_conversions':converted,
 'url_source_page_tuples_untouched':True,'all_rights_sources_credits_text_unchanged':True,
 'full_authoring_and_credits_inventory_untouched':True,
 'boolean_reason':'Catalog::parse uses canonical_narrative_enrichment object presence only to set explicit_story_media_only; explicitly set the same existingtrue field before omitting the research payload.',
 'no_new_native_schema_or_limit':'No reader code change or parser-cap increase; allremovedfields are alreadyignored by the currentreader.',
 'unchanged_current_master_runtime':True,'runtime_projection_tool_not_changed':True,
 'validation_required':'Actual C++ Catalog loader snapshot of every parsed field, then complete actual native StoryCard composition snapshots and targetedimage mappings.'}
(P/'candidate-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(P/'candidate-runtime.json',sha(compact),len(compact),'saving',len(raw)-len(compact))
