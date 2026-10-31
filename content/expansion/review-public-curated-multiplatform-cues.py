import json,hashlib,importlib.util,re,copy
from pathlib import Path
R=Path('.').resolve();rs=R/'build/research/soundtrack-broad';s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
doc=json.loads((rs/'public-curated-original-cue-candidates.json').read_text());done={e['entry_id'] for e in json.loads((R/'content/expansion/soundtrack-independent-approved.json').read_text())['entries']};prior={e['entry_id'] for e in json.loads((rs/'public-curated-single-platform-editorial-audit.json').read_text())['entries']};cat=json.loads((R/'content/catalog.json').read_text());games={e['id']:e for e in (cat if isinstance(cat,list) else cat['entries'])}
# These decisions follow actual metadata reads, not a generic title-prefix gate.
holds={
 'VoUesRPV2aM':'Actual Gamefield saysSilentHill2024 rather than SilentHill2; sourceidentity typo unresolved, not silently corrected.',
 'zfBZoUOPZhg':'PS4distinct2018remake mixed with PS2/PS3original in source platformlist; recording edition not resolved.',
 'wGKxXKF9PWM':'PS4distinct2018remake mixed with PS2/PS3original in source platformlist; recording edition not resolved.',
 'NxrGyln_lgU':'Saturn andarcade recordings have distinct arrangements; specific capturedversion unresolved.',
 'gQo4Edj7W70':'OriginalPC88 andlaterSegaCD/PS editions have materially different scores; source lists all, exact cue version unresolved.',
 'CZ5xNzWTkeI':'OriginalPC88 andlaterSegaCD/PS editions have materially different scores; source lists all, exact cue version unresolved.',
 'B2JGpIyYzH0':'Source declares Genesis hardware but namesSegaCDcomposers SpencerNilsen/BrianCoburn; originalGenesismusiccredits differ. Contradictoryversion/author held.',
 'qZMbKpHeYDE':'Two whole-game authors declared for individualMvC2cue without roleallocation; needs cuecredits.',
 'wmj4Tkvp0lE':'MagmoorCaverns inherits LowerNorfair composition; wholePrimecomposerroster does not establish originalcueauthors/arrangers.',
 'yoLRsWRG_Oc':'WholePrimecomposerroster copied to individual cue; exactallocation unresolved.',
 'olTFALdsjwM':'WholePrimecomposerroster copied to individual cue; exactallocation unresolved.',
 '8uFWDVsFwAk':'ActualTrackfieldStarboard conflicts with titlePowerRoom; contradictorycueidentity held.',
 'UqaDfxAtgyU':'Two whole-game authors copied to Starboard; exactcompositionallocation unresolved.',
 'QwOKWh9u0bw':'Cherrygrove individual author not independently distinguished from GoldSilver joint composers; hold rather than assume archivalMasuda field alone.',
 'aHFkHDSCnkw':'BeatsInMyHead contains vocal/lyricist roles not yet independently established; do not erase extra creator.',
 'ML2dT0sTj9o':'MidnaLament composition sources conflict betweenMinegishi/Kondo; individualauthor not resolved from game-widecomposerlist.',
 'oacRvlgVXoE':'Archive saysTreasureCoveTrove rather than TreasureTroveCove; exacttitle/source mismatch held until authoritativecueinventorycorrection.',
 'dRH9RwW-zto':'ActualTrackfieldNewAtlantis contradicts titleNeon; contradictorycueidentity held.',
 'x2K7l191aPA':'Arcade/Saturn have distinct arrangements, bothgamecomposers copied; exactrecordingversion/roles unresolved.',
 'BcInbMc1bUE':'Arcade/SNES different recording arrangements; exactrecordingversion unresolved.',
 'wLdbBuUvUoo':'WholeDoubleDash two-composer roster on specificcue; exactcueallocation unresolved.',
 'HZhjxtuwKJg':'WholeDoubleDash two-composer roster on specificcue; exactcueallocation unresolved.',
 'WWdDrhthcf4':'WholeDoubleDash two-composer roster on specificcue; exactcueallocation unresolved.',
 'P0QERrbzSBY':'ArchivalKojiKondo credit conflicts with actualGalaxyOST tracklisting MahitoYokota; do not promote wrongcuecredit.',
 'Bi0Hvmxgjuo':'ArchivalKojiKondo credit conflicts with actualGalaxyOST tracklisting MahitoYokota; do not promote wrongcuecredit.',
 'ktFy3cqTaLg':'Bothwholegamecomposers copied; originalOverturecuecredit needs preciseauthor.',
 'aoi2Dbkna2U':'Shrinecueauthor exactallocation not established from threegamecomposers; do not inferindividualrole.'
}
# Explicitly reviewed same-game/score publications. Hardware listed by curator
# is preserved as a list, never falsely represented as a proven capture device.
allowed={
'wikipedia-19539395','workbook-03-11-chrono-trigger','workbook-07-05-nights-into-dreams','wikipedia-8036013','wikipedia-847507','wikipedia-12915762','wikipedia-22493479','workbook-11-01-uncharted-3-drake-s-deception','workbook-02-23-nier-automata','wikipedia-613343','wikipedia-575509','wikipedia-4393438','workbook-11-11-the-elder-scrolls-v-skyrim','workbook-05-18-red-dead-redemption','wikipedia-490832','workbook-11-10-fallout-4','wikipedia-563196','wikipedia-314495','wikipedia-61004225','workbook-12-21-phantasy-star-online','workbook-08-02-streets-of-rage','workbook-11-06-halo-4','wikipedia-1042993','wikipedia-59284486','workbook-09-06-starfield','wikipedia-23047813','wikipedia-307333','workbook-11-08-death-stranding','wikipedia-57652736','wikipedia-5459591','wikipedia-24040808','wikipedia-36874131','daily-04-18','wikipedia-43010284','wikipedia-362641','wikipedia-350473','workbook-09-25-halo-3','wikipedia-1645094','wikipedia-73963'}
rows=[];snapshotrows=[]
for e in doc['entries']:
 if e['entry_id'] in done or e['entry_id'] in prior or not e['tracks']:continue
 entry=games[e['entry_id']];names,url,ev=p.composer(entry);srcok=bool(names) and p.composer_source_identity_verified(entry,url);rr=[];snapshotrows.append(copy.deepcopy(e))
 for t in e['tracks']:
  vid=t['youtube_id'];v=p.watch(vid);reason=holds.get(vid)
  if entry['id'] not in allowed:reason=reason or 'Individualcomposition/recordingcontext still undereditorialreview.'
  reason=reason or p.archive_declared_game_error(entry,v) or p.recording_identity_policy(vid,entry['id'],v) or ('' if srcok else 'Independentexactgamecomposer/source unresolved')
  match=re.search(r'(?im)^Platform(?:\(s\)|s)?:\s*(.+)',v['shortDescription']);platform=match.group(1).strip() if match else ''
  if not platform:reason=reason or 'Actualsource platformcontext missing.'
  fix={}
  if not reason:
   fix={'recording_platform':'Capture hardware not identified','recording_version':'Archival same-game soundtrack. Uploader lists '+platform+'; this platform list is not independently verified and does not identify capture hardware. No original-hardware exclusivity or audio-fingerprint claim.'}
  rr.append({'youtube_id':vid,'status':'HOLD' if reason else 'PASS','actual_title':v['title'],'actual_uploader':v['author'],'source_page':url,'watch_receipt':t['verification_receipt'],'evidence':reason or 'Actual exactgame/individualcue/year fields anddeclaredauthor read; author independentlycorroborated for samegame. Samegame score; no separate remake/sequel/cover claim in actualdescription. Uploaderplatformlist retained as unverifiedclaim, not officialportverification or capturedhardware.','corrected_track_fields':fix})
 rows.append({'entry_id':entry['id'],'title':entry['title'],'status':'PASS' if all(t['status']=='PASS' for t in rr) else 'PARTIAL_PASS' if any(t['status']=='PASS' for t in rr) else 'HOLD','tracks':rr,'composer_source':url,'composer_evidence':ev})
snapshot=rs/'checkpoints/public-curated-remaining-source-review-2026-10-21.json';payload={'publication_status':'research_only_not_admitted','entries':snapshotrows};encoded=json.dumps(payload,ensure_ascii=False,indent=2)+'\n'
if snapshot.exists():assert snapshot.read_text()==encoded
else:snapshot.write_text(encoded,encoding='utf-8')
p.write(rs/'public-curated-remaining-editorial-audit.json',{'snapshot':snapshot.relative_to(R).as_posix(),'snapshot_sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'scope':'Actual remaining52 source metadata/credit/versionread. Per-cueholds preservecontradictions; multi-platformlist is notcapturehardwareproof. Nativecodec andseparateindependentreview still required.','entries':rows});print('ROWS',len(rows),'PASSGAMES',sum(any(t['status']=='PASS' for t in e['tracks']) for e in rows),'PASSCUE',sum(t['status']=='PASS' for e in rows for t in e['tracks']),'HOLDCUE',sum(t['status']=='HOLD' for e in rows for t in e['tracks']))
