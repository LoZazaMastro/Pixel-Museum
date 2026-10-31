import hashlib, importlib.util, json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=module('p',R/'content/expansion/soundtrack-broad-pipeline.py');v=module('v',R/'tools/discover-museum-videos.py')
D=p.RESEARCH/'modern-original-four-more';D.mkdir(exist_ok=True)
cat=json.loads((R/'content/catalog.json').read_text(encoding='utf8'));cat=cat if isinstance(cat,list) else cat['entries'];ids={(p.norm(e['title']),e['year']):e['id'] for e in cat}
groups=[
 ('The Witcher 3: Wild Hunt',2015,'Marcin Przybyłowicz',[
  ('xhxP_WNjnCk','Geralt of Rivia',{'original_Witcher_theme_composers':'Adam Skorupa; Paweł Błaszczak','orchestration':'David Christiansen','conductor':'Bernd Ruf','orchestra':'Brandenburgisches Staatsorchester Frankfurt'},'https://www.youtube.com/watch?v=H1XRvZGJAMk','Official original 2015 CD Projekt Red soundtrack, eMuzyka digital release. Original Witcher theme and orchestration roles preserved.'),
  ('1m-8wbz1qhg','The Trail',{'performance':'Percival','mixing':'Jakub Pietrzak','production':'Marcin Przybyłowicz'},'https://www.youtube.com/watch?v=s3L0_ez0Dg4','Official original 2015 CD Projekt Red soundtrack, eMuzyka digital release; original game trailer cue also included on the game album.')]),
 ('Nuclear Throne',2015,'Jukio Kallio',[
  ('Ly8r4167BnU','Kings and Queens of Wasteland',{},'https://jukiokallio.bandcamp.com/album/nuclear-throne-ost','Original 2015 game soundtrack, composer-issued DistroKid release.'),
  ('FXB3f5RKV1A','Legend of the Throne',{},'https://jukiokallio.bandcamp.com/album/nuclear-throne-ost','Original 2015 game soundtrack, composer-issued DistroKid release.'),
  ('1HOTdsA7eaQ','Nuclear Throne',{},'https://jukiokallio.bandcamp.com/album/nuclear-throne-ost','Original 2015 game soundtrack, composer-issued DistroKid release.')]),
 ('Life Is Strange',2015,'Jonathan Morali',[
  ('7Ep_5rMWMKY','Golden Hour',{'performance':'Jonathan Morali'},'https://www.youtube.com/watch?v=7Ep_5rMWMKY','Original 2015 game score, composer-issued recording.'),
  ('-o7F7_nipP0','Max & Chloé',{'performance':'Jonathan Morali'},'https://www.youtube.com/watch?v=-o7F7_nipP0','Original 2015 game score, composer-issued recording.')]),
 ('Return of the Obra Dinn',2018,'Lucas Pope',[
  ('z895klg3LyE','Main Title',{},'https://store.steampowered.com/app/1568780/Return_of_the_Obra_Dinn_Soundtrack/','Original game main-menu music captured by archival uploader using Audacity. Capture hardware and precise album edit not identified; not represented as the later commercial album master.')])
]
entries=[];audit=[]
for game,year,composer,rows in groups:
 eid=ids.get((p.norm(game),year))
 if not eid:print('ARTICLE_HOLD',game,flush=True);continue
 ts=[]
 for vid,title,roles,source,version in rows:
  a=p.watch(vid)
  try:c=v.metadata(vid,{'title':a['title'],'channel':a['author']});assert c.get('native_compatible_avc_aac')
  except Exception as ex:audit.append({'youtube_id':vid,'status':'CODEC_HOLD','reason':str(ex)});continue
  official=game!='Return of the Obra Dinn'
  t={'youtube_id':vid,'url':'https://www.youtube.com/watch?v='+vid,'title':title,'creator':composer,'composer_source':source,'recording_context_source':source,'recording_version':version,'additional_recording_roles':roles,'uploader':a['author'],'channel_url':'https://www.youtube.com/channel/'+a['channelId'],'source_page':'https://www.youtube.com/watch?v='+vid,'official_uploader_verified':official,'publishing_kind':'official_game_recording' if official else 'archival_game_recording','duration_seconds':int(a['lengthSeconds']),'verification_receipt':'build/research/soundtrack-broad/watch/'+vid+'.json','native_codec_metadata_receipt':'build/research/video-discovery/video-'+vid+'.json','native_codec_metadata_verified':True,'playback_verified_on_ps5':False,'rights':'Composition and recording rights remain with original composers, publishers, performers and labels; archive upload credit does not imply official endorsement.'}
  if game=='Nuclear Throne':t['additional_recording_roles']={'recording_and_mixing':'Jukio Kallio','mastering':'Petri Majuri'};t['primary_role_source']='https://www.youtube.com/watch?v=Jk5jogaEsz8'
  if game=='Life Is Strange':t['publisher_composer_context_source']='https://blog.playstation.com/2018/08/20/life-is-strange-2-begins-september-27-on-ps4/'
  ts.append(t);audit.append({'game':game,'youtube_id':vid,'status':'CANDIDATE_PENDING_PEER','actual_title':a['title'],'actual_description_read':True});print(game,title,'AVC_AAC',flush=True)
 if ts:entries.append({'entry_id':eid,'match_title':game,'match_year':year,'title':'Listen to '+game,'composer':composer,'curator_note':'Listen to music by '+composer+' from '+game+'.','tracks':ts})
f=D/'four-modern-games8-candidate.json';f.write_text(json.dumps({'publication_status':'awaiting_independent_review','entries':entries},ensure_ascii=False,indent=2)+'\n',encoding='utf8');(D/'four-modern-editorial-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('FINAL',len(entries),sum(len(e['tracks']) for e in entries),hashlib.sha256(f.read_bytes()).hexdigest(),flush=True)
