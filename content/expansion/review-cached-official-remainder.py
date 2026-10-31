import json,hashlib,importlib.util,re,copy
from pathlib import Path
R=Path('.').resolve();rs=R/'build/research/soundtrack-broad';s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p);src=rs/'checkpoints/cached-official-remainder-2026-10-21.json';doc=json.loads(src.read_text());cat=json.loads((R/'content/catalog.json').read_text());games={e['id']:e for e in (cat if isinstance(cat,list) else cat['entries'])};rows=[]
for e in games.values():p.TITLE_YEARS.setdefault(p.norm(e['title']),set()).add(e['year'])
holds={
'hLDFH_r077w':'Shanachieversion includes NamiUehara outside independently allocated musicroles; arrangement/performerallocation unresolved.',
'bKQUUx9vJ5c':'NamiUehara musicrole not independently allocated; do not silentlyeraseextra namedperson.',
'hvo7c0m8ME4':'ExistingDataDiscs2021versusnewPC88recordingcontext remains independentlyheld.',
'KtC6XmH_19o':'Deliveredcue includes JoelEriksson originaltheme contribution omitted by infoboxduo; underlyingcomposition/arrangementcredits need exactallocation.',
'UkAz5YFw_x8':'Deliveredcue names83key as well asShoji; extra creatorrole unresolved.',
'ScUZhX9mVEk':'ElizabethLarkin/KeeleyBumford individual lyric/vocalroles not independentlyverified; no silentartistintersection.',
'CiDZ40LxTD4':'Trials incorporates originalHalo theme; underlyingO_Donnell/Salvatoricompositioncredit notallocated byKazuma-only delivery.',
'fAdpMMNeiuM':'Deliveryopening repeats two albumcomposers without cueallocation; mainTheme cannot be narrowed toMacQuayle automatically.',
'35UTD2Sm4NU':'DeliverytitleSantaolalla and genericMusicBySantaolalla/Quayle disagree in scope; need exact cuecomposer allocation.',
'oYi3re2eQQc':'Distinct2020remake iscorrectexhibit, but BillHemstapat role in cue notindependently distinguished from ShunsukeKida composition.',
'2u7Tkcry_bo':'YoukiYamamoto/AyakoTsuchiya roles unresolved; cannot omit namedmusic contributor from artistline.',
'ofjSpw3fgOk':'ActualUematsu+Hamauzu credit requires precise underlyingcomposition/arrangementallocation; existinggeneratedHamauzu-only credit insufficient.',
'rWm3icbxBIo':'Publisherlabels Tekken3 OpeningMovie PlayStation2Version; actualgame originallyPS1, alleged PS2version not resolved. Do not invent a port.',
'obX7W9cLEKk':'Deliverydescription supplies whole four-composer albumroster, not actualAloyTheme cueallocation.',
'oGiEST4kERk':'PenkaKouneva role in actualcue not allocated independently; likelyorchestration cannot be silentlyassumed.',
'8LOR9JXK1Og':'PenkaKouneva role in actualcue not allocated independently.',
'cQUJQb39yP8':'KnownNieR2021 individual arrangementrole hold; incorrectShazam proof excluded.',
'f_F8UgNA_cc':'DS2007version is a distinctremake rather than an ordinary hardwareport for1991exhibit; JunyaNakano role also unresolved.',
'd09COB_glTw':'Generatedcreator ispublisher/projectbrand, but actualcue names JunichiNakatsuru; exact primarycomposer source required.',
'TKlkuJl66Cs':'JoseDelgado/SachikoMiyano roles unresolved, no silentintersection.',
'N1ethcfDbcg':'JoseDelgado/SachikoMiyano roles unresolved, no silentintersection.',
'W08LL46V4hw':'JoseDelgado/DaisukeShinoda roles unresolved, no silentintersection.',
'WyTRg-DJ99M':'RyoYamazaki additionalcue role requires independentlyverified arrangement credit.',
'SBfoWTB-T_U':'DimengYuan additionalcue role requires independentarrangement/compositionallocation.',
'KvekqlSuEfI':'JustinAucoin additionalcue role not independently allocated; do not silentlydiscard.',
'jPyodXTpUgc':'JustinAucoin additionalcue role not independently allocated; do not silentlydiscard.'}
for e in doc['entries']:
 entry=games[e['entry_id']];names,url,ev=p.composer(entry);names=p.clean_composer_names(names,entry['title']);rr=[]
 for prior in e['tracks']:
  vid=prior['youtube_id'];v=p.watch(vid);flat={'id':vid,'title':v['title'],'channel':v['author'],'channel_id':v['channelId'],'description':v['shortDescription']};track,reason=p.consider(entry,flat,names,url);reason=holds.get(vid) or reason;fix={};roles={}
  if not p.composer_source_identity_verified(entry,url):reason=reason or 'Independent exactgamecomposer/source not verified.'
  if not reason:
   # Current narrow Composer-role parser generates every exactmusic composer
   # rather than swallowing performers/engineers or dropping comma-role authors.
   fix={k:track[k] for k in ['creator','independently_matched_composers','composer_source']}
   for line in v['shortDescription'].splitlines():
    prefix,sep,value=line.partition(':')
    if sep and len(prefix)<190 and any(re.fullmatch(r'lyricist|orchestrator|vocalist|associated performer|recording arranger|arranger|conductor',x.strip(),re.I) for x in prefix.split(',')):
     roles.setdefault('delivered_role_fields',[]).append({'roles':prefix.strip(),'credit':value.strip()})
   if vid=='7C7x4A9e7MA':fix.update(title='Silent Fjord (Terra Nil: Volume 2, 2025 soundtrack release)',recording_version='Terra Nil: Volume 2 official soundtrack release (2025); no base-launch cueappearance claim.',recording_release_year=2025)
   if vid=='IdFWL2f3cIs':fix.update(recording_version='Civilization V: Brave New World expansion theme; official2025soundtrackrelease, not base2010launchmusic.',recording_release_year=2025)
   if entry['id']=='wikipedia-72677863':fix.update(recording_version='Official Atari50 soundtrack release (2026), cue for named includedgame/module; no claim of original2022cueappearance.',recording_release_year=2026)
   if vid=='EEYMlUVKmyE':fix.update(creator='Yu-Peng Chen',independently_matched_composers=['Yu-Peng Chen']);roles['recording_artist_collective']='HOYO-MiX'
   if vid=='V5Ar0dKnl6Y':roles['featured_vocalist']='Eivor Palsdottir';roles['source']='https://bearmccreary.com/god-of-war-ragnarok/'
  rr.append({'youtube_id':vid,'status':'HOLD' if reason else 'PASS','actual_title':v['title'],'actual_uploader':v['author'],'watch_receipt':prior['verification_receipt'],'evidence':reason or 'Actualexactgame/album publication read, explicitcueComposer/MusicBy field or singlehuman exactpublishercredit matches independentlyverifiedsamegameauthor. No unauditedadditionalhuman contributor discarded; brands/performers keptseparately.','corrected_track_fields':fix,'additional_recording_roles':roles})
 rows.append({'entry_id':entry['id'],'title':entry['title'],'status':'PASS' if all(t['status']=='PASS' for t in rr) else 'PARTIAL_PASS' if any(t['status']=='PASS' for t in rr) else 'HOLD','tracks':rr,'composer_source':url,'composer_evidence':ev})
p.write(rs/'cached-official-remainder-editorial-audit.json',{'snapshot':src.relative_to(R).as_posix(),'snapshot_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'scope':'All68game/136actualpublicationreceipts read. Explicit albumsegment handlesSonysequelidentities; multi-roleComposer fields read whereverinrolelist. Ambiguousroles/versionheld. Codec+independentreviewrequired; notproduction.','entries':rows});print('ROWS',len(rows),'PASSGAMES',sum(any(t['status']=='PASS' for t in e['tracks']) for e in rows),'PASSCUE',sum(t['status']=='PASS' for e in rows for t in e['tracks']),'HOLDCUE',sum(t['status']=='HOLD' for e in rows for t in e['tracks']))
