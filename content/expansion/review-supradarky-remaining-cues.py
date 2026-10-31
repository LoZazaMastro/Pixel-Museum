import json,copy,re,hashlib,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];B=R/'build/research/soundtrack-broad';spec=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
master=json.loads((R/'content/catalog.json').read_text());games={e['id']:e for e in (master if isinstance(master,list) else master['entries'])};done={e['entry_id'] for e in json.loads((B/'checkpoints/incremental-336-578-official-curated-rolefixed-2026-10-21.json').read_text())['entries']};rows=[e for name in ['supradarky-original-cue-candidates.json','supradarky-additional-cue-candidates.json'] for e in json.loads((B/name).read_text())['entries'] if e.get('tracks') and e['entry_id'] not in done]
holds={
'YcFt05iPI1o':'PC/3DO/SNES releases have different arrangements; actual capture version unidentified.',
'B75qVu6z8Ec':'PC/3DO/SNES releases have different arrangements; actual capture version unidentified.',
'Egmm38lXifc':'Vocal Sloprano cue needs lyric/vocal contributor roles in addition to Robin Beanland.',
'3qP9xLMVtcY':'PC/Wii releases contain different arrangement options; exact Moonsong recording unresolved.',
'QlgIuBG9SHE':'Specific StormEagle cue copies whole-game five-composer roster; exact role allocation unresolved.',
'GV8zdmBsbVo':'ChopChop rap cue requires lyric/vocal roles in addition to whole-game two-composer roster.',
'BZNozDLACaU':'Individual WorldBowser cue copies whole-game four-composer roster; exact role allocation unresolved.',
'4vgnMr1uW0A':'Individual PiranhaCreeper cue copies whole-game four-composer roster; exact role allocation unresolved.',
'0Q2tiNfywTU':'EditMode cue uses inherited NSMBU material; exact current/original composition roles unresolved.',
'EUb71hXBOK4':'Individual Metamorphosis cue names both whole-game composers; exact roles need primary cue allocation.',
'Dl6c55pclgg':'Individual Octoman cue copies whole-game Shoji/Kasho roster; exact role allocation unresolved.',
'TiC2vl9m9qo':'Individual Spade cue copies whole-game Shoji/Kasho roster; exact role allocation unresolved.',
'Et5JyYt82Ng':'TaxiRide cue joint composition roles not distinguished from whole-game Totaka/Ota roster.',
'aeM-wHBQ6A0':'Specific Submarine cue joint composition roles not independently allocated between Andersen/Ryberg.',
'ZsF5aG4ki2c':'CreativeExercise cue copies whole-game three-composer roster; exact allocation unresolved.',
'TF3ES0-vjiQ':'RemnantTwilight inherits Zelda themes; original composition versus arrangement roles unresolved.',
'IX7WoBJ_piE':'Underwater cue copies whole-game Kondo/Tanaka roster; exact allocation unresolved.',
'7kcLH8_n9-M':'BiancoHills cue copies whole-game Kondo/Tanaka roster; exact allocation unresolved.',
'fVCrhSWo0fk':'Shenmue MainTheme credit RyujiIuchi conflicts with TaroIwashiro; held until cue-specific primary resolution.',
'2FaymLM-NKw':'ChristmasDobuita cue precise author not independently corroborated.',
'LDcJRhJ4_2w':'Arcade/3DO have different arrangements; exact capture and cue roles unresolved.',
'x-OcnH8MP8I':'Licensed JamiSieber track needs original developer license/album context, not generic game composer roster.',
'JU2TIk0aPoY':'Published ACE+ credit must be independently distinguished from ACE; do not silently drop Hiramatsu.',
'vG5J-Kv-jjU':'Published ACE+ credit must be independently distinguished from ACE; do not silently drop Hiramatsu.',
'2bKeHpItLaU':'Published ACE+ credit must be independently distinguished from ACE; do not silently drop Hiramatsu.'}
audit=[];candidates=[]
for e in rows:
 game=games[e['entry_id']];names,url,ev=p.composer(game);srcok=p.composer_source_identity_verified(game,url);rr=[];selected=[]
 for tr in e['tracks']:
  t=copy.deepcopy(tr);vid=t['youtube_id'];v=json.loads((B/'watch'/(vid+'.json')).read_text());reason=holds.get(vid) or ('' if srcok else 'Exact original game composer source identity unresolved') or p.archive_declared_game_error(game,v);match=re.search(r'(?im)^Platform(?:\(s\)|s)?:\s*(.+)',v['shortDescription']);platform=match[1] if match else t.get('archive_index_record',{}).get('Platform','');fix={}
  if not platform:reason=reason or 'Platform/version context missing from both actual publication and attributed curator index.'
  if not reason:
   fix={'recording_platform':'Capture hardware not identified','recording_version':'Archival same-game score. Uploader lists '+platform+'; this platform list is not independently verified and does not identify capture hardware. No original-hardware exclusivity or audio-fingerprint claim.'}
   if vid=='dvQEPoa97oM':fix.update(creator='Yasuaki Iwata',independently_matched_composers=['Yasuaki Iwata'],cue_credit_scope='Actual watch publication names Yasuaki Iwata for ShopClosing; generic multi-composer public-index roster is not imported as this cue credit.')
   t.update(fix);t['composer_source']=url;t['independent_review_receipt']='';selected.append(t)
  rr.append({'youtube_id':vid,'status':'HOLD' if reason else 'PASS','actual_title':v['title'],'actual_uploader':v['author'],'actual_metadata_receipt':'build/research/soundtrack-broad/watch/'+vid+'.json','composer_source':url,'composer_evidence':ev,'evidence':reason or 'Actual exact-game cue/title/year fields and declared named author read, corroborated against independent original-game credits. Source linked archival collection number/index matches. No remake, fan remix or false capture-hardware claim.','corrected_track_fields':fix})
 audit.append({'entry_id':e['entry_id'],'title':e['title'],'status':'PASS' if len(selected)==len(rr) else 'PARTIAL_PASS' if selected else 'HOLD','tracks':rr})
 if selected:
  composers=[]
  for t in selected:
   for n in t['independently_matched_composers']:
    if n not in composers:composers.append(n)
  candidates.append({'entry_id':e['entry_id'],'match_title':e['title'],'match_year':game['year'],'title':'Listen to '+e['title'],'tracks':selected,'composer':', '.join(composers),'curator_note':'Listen to music by '+', '.join(composers)+' from '+e['title']+'.','independent_composer_credit':{'composers':names,'source_page':url,'evidence':ev}})
snapshot=B/'checkpoints/supradarky-remaining73-source-review-2026-10-21.json';snapshot.write_text(json.dumps({'publication_status':'research_only_not_admitted','entries':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8');p.write(B/'supradarky-remaining73-editorial-audit.json',{'snapshot':snapshot.relative_to(R).as_posix(),'snapshot_sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'scope':'Individual actual source reads and conservative role/version decisions. Independent second review and native codec required before production. Whole-game multicomposer rosters not silently copied to individual cues.','entries':audit});p.write(B/'supradarky-remaining73-reviewed-candidates.json',{'publication_status':'awaiting_independent_review_and_codec','entries':candidates});print('ROOMS',len(rows),'PASSGAMES',len(candidates),'PASSCUE',sum(len(e['tracks']) for e in candidates),'HOLDS',sum(t['status']=='HOLD' for e in audit for t in e['tracks']))
