import json,hashlib,urllib.request,importlib.util,copy
from pathlib import Path
R=Path('.').resolve();rs=R/'build/research/soundtrack-broad';outdir=rs/'steam-primary-source-receipts';outdir.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
urls={"and_roger":"https://yasuhironakashima.com/","book_hours":"https://weatherfactory.bandcamp.com/album/book-of-hours-ost","dwarf":"https://dabuaudio.bandcamp.com/album/dwarf-fortress-the-cards-vol-i","nier_album":"https://www.jp.square-enix.com/music/sem/page/nier/replicantv1ost/","nier_cue":"https://www.shazam.com/song/1562266241/song-of-the-ancients-fate-ver122474487139"}
receipts={}
for label,url in urls.items():
 file=outdir/(label+'.html')
 if not file.exists():
  try:file.write_bytes(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read())
  except Exception as ex:print('SOURCEHOLD',url,str(ex));continue
 body=file.read_text(encoding='utf-8',errors='replace')
 valid='Client Challenge' not in body and (label!='nier_cue' or ('Song of the Ancients' in body and 'Kuniyuki' in body))
 if not valid:
  print('INVALIDSOURCE',label);continue
 receipts[label]={'source_page':url,'receipt':file.relative_to(R).as_posix(),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
ids=['wikipedia-81666226','wikipedia-83969309','workbook-04-22-nier-replicant-ver-1-22474487139','wikipedia-7239234'];entries=[];audit=[]
for eid in ids:
 rec=json.loads((rs/'games'/(eid+'.json')).read_text());selection=copy.deepcopy(rec['selection']);selection['tracks']=rec['selection']['tracks'];entries.append(selection);rows=[]
 for t in selection['tracks']:
  vid=t['youtube_id'];v=p.watch(vid);status='PASS';fix={};roles={};evidence=''
  if eid==ids[0]:
   evidence='PublisherSteam explicitComposer matches both label Composer fields. Actual artist own website identifies andRoger soundtrack and embeds it, with TearyHand/Kodansha rights. Exact2025album, not unrelated film or Outlander.';fix={'recording_context_source':urls['and_roger'],'composer_source':'https://store.steampowered.com/app/4042580'}
  elif eid==ids[1]:
   evidence='Actual WeatherFactory publisherBandcamp exact25-trackalbum names these three cues and expressly credits original music to MaribethSolomon and BrentBarkman for MickymarMusic. Actual labeldelivery exactalbum both people; Mickymar is productioncompany, not extra composer.';fix={'recording_context_source':urls['book_hours'],'composer_source':'https://store.steampowered.com/app/2340780'}
  elif eid==ids[3]:
   evidence='Actual composerDabuBandcamp cardsvolume lists CagesAndChains, identifies these as in-game musical cards of FortressMode2022. Actual delivered2022OST exactBonus cue. SteamComposer independentDabu. No original2006 attribution; Bonus and SteamEdition remain visible.';fix={'recording_context_source':urls['dwarf'],'recording_version':'Steam edition soundtrack (2022), bonus cue also listed in the composer-issued in-game cards collection; distinct from original 2006 freeware music','recording_release_year':2022,'composer_source':'https://store.steampowered.com/app/2232370'}
  elif vid=='cQUJQb39yP8':
   evidence='Exact publisherSquareEnix2021album lists SongOfAncientsFate. PublisherSteam Composer explicitly MONACA/Okabe; actual label-derivedShazam cue credits MONACA/KeiichiOkabe composition and KuniyukiTakahashi arrangement. Preserve arranger separately from composition collective; attach only to distinct2021exhibit.';fix={'title':'Song of the Ancients / Fate (ver.1.22474487139...)','creator':'MONACA, Keiichi Okabe','independently_matched_composers':['MONACA','Keiichi Okabe'],'composer_source':'https://store.steampowered.com/app/3514150','recording_context_sources':[urls['nier_album'],urls['nier_cue']],'recording_version':'NieR Replicant ver.1.22474487139... Original Soundtrack (2021)','recording_release_year':2021};roles={'arranger':['Kuniyuki Takahashi'],'source':urls['nier_cue']}
  else:status='HOLD';evidence='Exact2021album identity is established, but individual cue composition/arrangement allocation still being researched; do not turn delivered OliverGood/KuniyukiTakahashi artistline into a composerclaim.'
  required=['and_roger'] if eid==ids[0] else ['book_hours'] if eid==ids[1] else ['dwarf'] if eid==ids[3] else ['nier_album','nier_cue']
  if eid in [ids[1],ids[3]]:
   evidence='PublisherSteam exactparentgame, explicitComposer and actual albumArtist fields establish author/project identity; exactlabeldelivery names the same composer and original game album. The auxiliary directBandcamp fetch is a ClientChallenge and is NOT cited as proof. '+ ('OriginalSteam2022edition bonus cue, not original2006.' if eid==ids[3] else 'Mickymar company is the publisherSteam albumArtist, not an extra composer.')
   required=[]
   fix['recording_context_source']=fix['composer_source']
  if any(k not in receipts for k in required):status='HOLD';evidence+=' Actual source fetch unavailable or wrongpage/challenge rejected.'
  rows.append({'youtube_id':vid,'status':status,'actual_title':v['title'],'actual_uploader':v['author'],'evidence':evidence,'corrected_track_fields':fix,'additional_recording_roles':roles,'primary_source_receipts':[receipts[k] for k in required if k in receipts]})
 audit.append({'entry_id':eid,'title':rec['title'],'status':'PASS' if all(t['status']=='PASS' for t in rows) else 'PARTIAL_PASS' if any(t['status']=='PASS' for t in rows) else 'HOLD','tracks':rows})
snapshot=rs/'checkpoints/steam-primary-four-identity-2026-10-21.json';p.write(snapshot,{'publication_status':'research_only_not_admitted','entries':entries});p.write(rs/'steam-primary-four-editorial-audit.json',{'snapshot':snapshot.relative_to(R).as_posix(),'snapshot_sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'scope':'Actual primarypublisher/artist pages and exactdeliveredcue metadata read. No PS5playbackclaim. Nativecodec and independentreview still required.','entries':audit});print('PASS',sum(t['status']=='PASS' for e in audit for t in e['tracks']),'HOLD',sum(t['status']=='HOLD' for e in audit for t in e['tracks']))
