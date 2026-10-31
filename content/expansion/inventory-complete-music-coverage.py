"""Track full-album coverage without conflating a missing room with a silent game."""
import collections,hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[2]
path=ROOT/'content/catalog.json';catalog=json.loads(path.read_text(encoding='utf-8'))
rows=[]
overrides_path=ROOT/'content/expansion/soundtrack-multitrack-priority-overrides.json'
overrides=json.loads(overrides_path.read_text(encoding='utf-8'))
approved_overrides={e['entry_id']:e for e in overrides.get('entries',[]) if overrides.get('publication_status')=='validated'}
multiple=json.loads((ROOT/'content/expansion/soundtrack-multiple-room-overrides.json').read_text(encoding='utf-8'))
def key(title):return re.sub(r'[^a-z0-9]','',title.lower())
approved_multiple={(key(e['match_title']),e['match_year']):e for e in multiple.get('entries',[]) if multiple.get('publication_status')=='validated'}
known_inventories={
 'wikipedia-32307637':(211,'https://columbia.jp/prod-info/COCX-40313-7/','Published2018album includes licensed original DLC/bonus tracks; not a claim all compositions occur in the launch build.'),
 'wikipedia-67760003':(344,'https://columbia.jp/prod-info/COCX-42298-306/','Published2024original soundtrack includes labelled trailer bonus compositions.'),
 'workbook-10-27-super-mario-odyssey':(136,'https://bzone.co.jp/site/mario_ost/','Published4CDoriginal soundtrack, including vocal/instrumental/Japanese versions and jingles.'),
 'wikipedia-79613463':(348,'https://www.mariowiki.com/Mario_Kart_World_(Nintendo_Music)','Research target from community NintendoMusictranscription, including June–August2026FreeRoamupdates and2bonus tracks. Primary authenticated tracklist reconciliation remains open.'),
 'wikipedia-79613753':(229,'https://www.mariowiki.com/Donkey_Kong_Bananza_(Nintendo_Music)','Research target from community NintendoMusic229track transcription, superseding earlier9track specialrelease. Not a verified publishedmaster collection.'),
 'wikipedia-38323830':(149,'https://www.mariowiki.com/Mario_Kart_8_Deluxe_(Nintendo_Music)','Research target is the later official2017Deluxeport collection including BoosterCoursePass, not a false claim these149versions were all present in the original2014WiiUrelease. Community NintendoMusictranscription awaits primary/mapping review.'),
}
for e in catalog['entries']:
 if e.get('kind')!='game':continue
 soundtrack=e.get('soundtrack') or {};runtime_rooms=e.get('soundtrack_rooms') or [soundtrack]
 tracks=[t for room in runtime_rooms for t in room.get('tracks',[])]
 # Base Battlefield1 is the independently reconciled complete25-recording album.
 complete=e['id']=='wikipedia-47439252' and len(tracks)==25
 if 'battlefield 1'==e['title'].lower() and len(tracks)==25:complete=True
 approved=approved_overrides.get(e['id'])
 expected=25 if complete else None;source='';scope='Complete original tracklist still to acquire.';verified=len(tracks);verified_album_tracks=len(tracks)if complete else None
 if e['id']in known_inventories:expected,source,scope=known_inventories[e['id']]
 if expected is not None and not verified:verified_album_tracks=0
 if approved:
  verified=len(approved['tracks']);album=approved.get('album_completeness',{});partial=approved.get('completeness',{})
  expected=album.get('expected_tracks',partial.get('expected_published_album_tracks',partial.get('official_base_published_album_tracks',expected)))
  source=album.get('inventory_receipt',album.get('inventory_source',source))
  verified_album_tracks=album.get('verified_album_tracks',partial.get('individual_album_tracks_verified'))
  if verified_album_tracks is None and approved.get('full_album_collection') and verified==expected:verified_album_tracks=verified
  complete=bool(expected and verified_album_tracks==expected and verified>=expected and approved.get('full_album_collection'))
  scope=album.get('source',approved.get('recording_collection_scope','Individual published-album reconciliation unresolved.'))
 multi=approved_multiple.get((key(e['title']),e['year']))
 room_inventory=[]
 if multi:
  rooms=multi['soundtrack_rooms'];verified=sum(len(room['tracks'])for room in rooms)
  expected=sum(room['expected_album_tracks']for room in rooms)
  complete=all(room.get('full_album_collection') and len(room['tracks'])==room['expected_album_tracks']for room in rooms)
  verified_album_tracks=verified if complete else None
  source='build/research/death-stranding2-complete-score/root-independent-complete72-review.json'
  scope='Two independently reconciled published albums, kept as separate Woodkid and Ludvig Forssell listening rooms.'
  room_inventory=[{'id':room.get('id'),'expected_tracks':room['expected_album_tracks'],'verified_tracks':len(room['tracks']),'full_album_collection':bool(room.get('full_album_collection'))}for room in rooms]
 rows.append({'entry_id':e['id'],'title':e['title'],'year':e['year'],'status':'full'if complete else 'partial'if verified else 'unresolved','runtime_recordings':len(tracks),'verified_tracks_in_source_modules':verified,'verified_published_album_tracks':verified_album_tracks,'expected_tracks':expected,'missing_tracks':max(0,expected-verified_album_tracks)if expected is not None and verified_album_tracks is not None else None,'tracklist_source':source,'inventory_scope':scope,'source_override_pending_assembly':bool(approved or multi),'soundtrack_rooms':room_inventory,'complete_inventory_source':'build/research/soundtrack-broad/battlefield1-complete/independent-base25-final-reconciliation.json'if complete and not approved and not multi else source,'reason':'Album tracklist/order independently reconciled.'if complete else 'Some verified recordings are present; full album completeness still unresolved. Suites, raw variants and edited album tracks are different units.'if verified else 'No approved listening room yet. This is not evidence of absent music.'})
out={'schema_version':1,'scope':'All game exhibits; complete base-game original soundtrack or documented licensed playlist. No DLC required; Battlefield1 explicitly base25 only. A missing record never means no score.','catalog_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'counts':dict(collections.Counter(r['status']for r in rows)),'games':rows,'no_score_confirmed':[],'no_score_policy':'Only populate after an exact original-game primary/technical source confirms no composed score. Old title-based silent lists are research leads, not proof.'}
dest=ROOT/'content/expansion/soundtrack-full-coverage-inventory.json';dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(len(rows),out['counts'])
