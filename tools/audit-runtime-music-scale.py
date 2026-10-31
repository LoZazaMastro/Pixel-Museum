"""Read-only byte analysis. No catalogue writes or parser-limit changes."""
from pathlib import Path
from collections import Counter
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'build/research/current-work-notes'
P.mkdir(exist_ok=True)
path=ROOT/'build/runtime-preview/content/catalog.json'
raw=path.read_bytes();original=json.loads(raw)
sha=lambda b:hashlib.sha256(b).hexdigest()
encoded=lambda d:(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf8')
def rooms(doc):
 for e in doc['entries']:
  if e.get('soundtrack'):yield e['soundtrack']
  yield from e.get('soundtrack_rooms',[])
count=sum(1 for r in rooms(original));tracks=sum(len(r.get('tracks',[])) for r in rooms(original))
with_music=[e for e in original['entries'] if any(r.get('tracks') for r in ([e['soundtrack']] if e.get('soundtrack') else [])+e.get('soundtrack_rooms',[]))]
unique_game_entries=[e for e in with_music if e.get('kind')=='game']
assert count and tracks
used_room={'title','composer','curator_note','tracks'}
used_track={'youtube_id','url','title','caption','creator','source_page','start_seconds','end_seconds'}
def native_music(doc):
 return [{k:copy.deepcopy(v) for k,v in r.items() if k in used_room and k!='tracks'}|{'tracks':[{k:copy.deepcopy(v) for k,v in t.items() if k in used_track} for t in r.get('tracks',[])]} for r in rooms(doc)]
stage1=copy.deepcopy(original)
removed_room=Counter();removed_track=Counter()
for r in rooms(stage1):
 for key in list(r):
  if key not in used_room:removed_room[key]+=len(encoded({key:r.pop(key)}))
 for t in r.get('tracks',[]):
  for key in list(t):
   if key not in used_track:removed_track[key]+=len(encoded({key:t.pop(key)}))
assert native_music(stage1)==native_music(original)
stage2=copy.deepcopy(stage1)
# These authoring metadata fields are not read anywhere in Catalog::parse.
# Keep all source citations/credits and factual_note despite its hidden drawline.
unused_entry={'editorial_mode','language','source_identity_correction','calendar_link_provenance','date_provenance','canonical_reference_restoration','disclosed_english_correction','identity_media_admission','source_edition_restoration','editorial_revision'}
removed_entry=Counter();implicit_conversion=0
for e in stage2['entries']:
 for key in list(e):
  if key in unused_entry:removed_entry[key]+=len(encoded({key:e.pop(key)}))
 if isinstance(e.get('canonical_narrative_enrichment'),dict):
  # Existing parser only tests presence/type of this object as a boolean.
  # Preserve that exact true result through the already supported explicit flag.
  removed_entry['canonical_narrative_enrichment_object_payload']+=len(encoded({'canonical_narrative_enrichment':e.pop('canonical_narrative_enrichment')}))
  e['explicit_story_media_only']=True;implicit_conversion+=1
assert native_music(stage2)==native_music(original)
stage3=copy.deepcopy(stage2);duplicate_urls=0
for r in rooms(stage3):
 for t in r.get('tracks',[]):
  if t.get('source_page') and t.get('url')==t['source_page']:
   t.pop('url');duplicate_urls+=1
base=len(encoded(original));sizes={'current':base,'music_fields_not_read_by_parser':len(encoded(stage1)),'plus_entry_provenance_not_read_and_existing_boolean_equivalent':len(encoded(stage2)),'plus_optional_redundant_track_URL_schema_change':len(encoded(stage3))}
assert path.read_bytes()==raw
report={
 'status':'READ_ONLY_BYTE_ESTIMATES_NOT_PRODUCTION_PROJECTION',
 'runtime':{'path':path.relative_to(ROOT).as_posix(),'sha256':sha(raw),'bytes':len(raw),'entries':len(original['entries'])},
 'rooms':count,'tracks':tracks,'unique_entries_with_music':len(with_music),'unique_game_entries_with_music':len(unique_game_entries),
 'counting_note':'Room and track counts include separate rooms and legacy alternatives. Only distinct game entry IDs with a nonempty playable room count as games with music.',
 'parser_limit_bytes':16<<20,'current_headroom_bytes':(16<<20)-len(raw),
 'serialized_variant_bytes':sizes,'serialized_savings_bytes':{k:base-v for k,v in sizes.items() if k!='current'},
 'unused_room_field_bytes':dict(removed_room.most_common()),'unused_track_field_bytes':dict(removed_track.most_common()),'unused_entry_field_bytes':dict(removed_entry.most_common()),
 'already_supported_boolean_conversions':implicit_conversion,
 'strict_music_native_fields_preserved_in_first_two_compactions':True,
 'optional_URL_deduplication':{'equal_source_page_URL_records':duplicate_urls,'requires_explicit_native_equivalence_review':True,'why':'Current soundtrack validation requires a source_page and player uses youtube_id; Credits already displays source_page. Parsed VideoRecord.url would differ, so treat as a schema-semantic change, not a no-code strict equivalent.'},
 'growth_estimates':{'current_music_bytes':sum(len(encoded(r)) for r in rooms(original)),
  'current_track_average_bytes':round(sum(len(encoded(t)) for r in rooms(original) for t in r.get('tracks',[]))/tracks,2),
  'strict_compacted_track_average_bytes':round(sum(len(encoded(t)) for r in rooms(stage1) for t in r.get('tracks',[]))/tracks,2),
  'estimated20k_tracks_strict_compacted_bytes':round(sum(len(encoded(t)) for r in rooms(stage1) for t in r.get('tracks',[]))/tracks*20000)},
 'recommendation':'First remove parser-ignored duplicated metadata in runtime projection, preserving full authoring/credits inventories. Then plan bounded per-room lazy local sidecars: timeline index holds title/composer/count plus validated local album reference; only the selected room is parsed. Do not raise the global16MiBcap or claim projected compaction alone solves100kcue scale.',
 'validation_required_before_change':['Existing native runtime-equivalence comparison against same authoring records, source/media/credit equality, explicit-story-media boolean legacy regression.','Measure parsed resident-memory and parse-time effect using current real dataset, not JSONbytes alone.','Any lazy-room schema requires path/hash/bounds validation, cancellation-safe asynchronous loading,2048trackcap perroom, focus/room state preservation and complete Credits traversal.'],
 'production_or_master_changed':False,'host_or_console_invoked':False}
out=P/'runtime-music-scale-read-only.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(out.relative_to(ROOT),sha(out.read_bytes()))
print('runtime',sha(raw),'rooms',count,'tracks',tracks)
print(json.dumps(sizes))
