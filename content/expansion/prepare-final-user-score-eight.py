"""Eight requested original-game scores: research checkpoint requiring peer review."""
import json,hashlib,re,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];B=R/'build/research/soundtrack-broad';D=B/'final-user-score-priorities'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=module('p',R/'content/expansion/soundtrack-broad-pipeline.py');v=module('v',R/'tools/discover-museum-videos.py')
cat=json.loads((R/'content/catalog.json').read_text(encoding='utf-8'));cat=cat if isinstance(cat,list) else cat['entries'];add=json.loads((R/'content/expansion/user-requested-game-additions.json').read_text(encoding='utf-8'))['entries'];ids={(p.norm(e['title']),e['year']):e['id'] for e in cat+add}
sources={
 'auto':'https://musicbrainz.org/release/696fce06-f009-4199-b96c-5105cfb7adb8',
 'matrix':'https://www.matrixfans.net/enter-the-matrix-interview-with-composers-don-davis-and-erik-lundborg/',
 'path':'https://en.wikipedia.org/wiki/The_Matrix:_Path_of_Neo',
 'nfs3':'https://en.wikipedia.org/wiki/Need_for_Speed_III:_Hot_Pursuit',
 'oni2':'https://store.steampowered.com/app/3128200/?l=english',
 'onidawn':'https://en.wikipedia.org/wiki/Onimusha:_Dawn_of_Dreams',
 'oni3':'https://www.squareenixmusic.com/albums/o/onimusha3.shtml',
 'oni1':'https://reikondoh.blog.jp/archives/cat_10009843.html'}
extra={
 'onimusha3-original-album':(sources['oni3'],['Masamichi Amano','Opening']),
 'nfs3-original-game':(sources['nfs3'],['1998','Rom Di Prisco','Matt Ragan']),
 'onimusha2018-publisher-tracklist':('https://www.4gamer.net/games/431/G043161/20180912089/',['23','鬼武者']),
 'jamie-composer-projects':('https://www.jamiechristopherson.com/projects',['Onimusha']),
}
receipts={}
for key,(url,markers) in extra.items():
 f=D/'primary'/(key+'.html')
 try:
  raw=f.read_text(encoding='utf-8') if f.exists() else p.fetch(url);body=p.text(raw);assert all(m in body or m in raw for m in markers)
  f.write_text(raw,encoding='utf-8');receipts[key]={'source_page':url,'local_source':str(f.relative_to(R)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'actual_body_retrieved':True,'semantic_markers':markers}
 except Exception as ex:receipts[key]={'source_page':url,'actual_body_retrieved':False,'error':str(ex)}
groups=[
 ('Auto Modellista',2002,'auto',[
  ('idvXg6q--tM','Upper — Opening','Tetsuya Shibata',{},'Original2002 soundtrack album, disc1track1; credited archival recording.'),
  ('MXGaqOS38v4','Full Scaled','Tetsuya Shibata',{},'Original2002 soundtrack album, disc1track4; credited archival recording.'),
  ('T8ejI1Yebqg','Main Menu — Garage Life','Tetsuya Shibata',{},'Original2002 soundtrack album, disc2track7; credited archival recording.')]),
 ('Enter the Matrix',2003,'matrix',[
  ('kvxrkK50GZo','Action and Fighting — Original Game Score Suite','Erik Lundborg',{'original_Matrix_themes':'Don Davis','game_score_orchestration_and_conducting':'Erik Lundborg'},'Original2003 videogame score recordings, tracks1–7 of the promotional album. Game-specific re-recorded adaptations; not the original film recordings.'),
  ('yavc31xmLlI','Suspense — Original Game Score Suite','Erik Lundborg',{'original_Matrix_themes':'Don Davis','game_score_orchestration_and_conducting':'Erik Lundborg'},'Original2003 videogame score recordings, tracks8–12 of the promotional album. Game-specific re-recorded adaptations; not the original film recordings.'),
  ('ER2bjG-2Tgs','Cineractives — Original Game Score Suite','Erik Lundborg',{'original_Matrix_themes':'Don Davis','game_score_orchestration_and_conducting':'Erik Lundborg'},'Original2003 videogame score recordings, tracks17–25 of the promotional album. Game-specific re-recorded adaptations; not the original film recordings.')]),
 ('The Matrix: Path of Neo',2005,'path',[
  ('UwBiiPQ7qw8','Hiya Fellas','Tobias Enhus',{},'Original2005game score; credited archival cue, capture hardware not identified.'),
  ('7hfPX4dAtGs','Path of Neo — Main Theme','Tobias Enhus',{},'Original2005game main-menu edit; credited archival recording, not the longer commercial soundtrack-album edit.')]),
 ('Need for Speed III: Hot Pursuit',1998,'nfs3',[
  ('c2NpizI1GxA','Aquila 303','Rom Di Prisco',{},'Original1998game score; credited archival cue, capture hardware and precise game edit not independently identified.'),
  ('XD0IoKoCFPQ','Romulus 3','Rom Di Prisco',{},'Original1998game score; credited archival recording, capture hardware not identified.'),
  ('uhTe7NPx0p8','Snow Bags','Matt Ragan',{},'Original1998game score; credited archival recording, capture hardware not identified.')]),
 ('Onimusha 2: Samurai\'s Destiny',2002,'oni2',[
  ('3A9QmBelYn4','Truth of Brave — Main Theme','Taro Iwashiro',{},'Original2002 Onimusha2 Orchestra Album, Taro Iwashiro Selection; official same-game orchestral album arrangement, archival upload.'),
  ('JcxsNpGbsI0','Truth of Loyalty — Ekei Ankokuji\'s Theme','Taro Iwashiro',{},'Original2002 Onimusha2 Orchestra Album, Taro Iwashiro Selection; official same-game orchestral album arrangement, archival upload.'),
  ('EwR0MUzc8DM','Truth of Resolution — Oyu of Odani\'s Theme','Taro Iwashiro',{},'Original2002 Onimusha2 Orchestra Album, Taro Iwashiro Selection; official same-game orchestral album arrangement, archival upload.')]),
 ('Onimusha: Dawn of Dreams',2006,'onidawn',[
  ('sviIrk7iJsY','Cutscene 1','Jamie Christopherson',{},'Original2006game cutscene score, composer-named publication. No claim about gameplay music by Hideyuki Fukasawa.'),
  ('2tI8fp6tyLI','Cutscene 7','Jamie Christopherson',{},'Original2006game cutscene score, composer-named publication. No claim about gameplay music by Hideyuki Fukasawa.'),
  ('0aQ9tybx3sU','Cutscene 3','Jamie Christopherson',{},'Original2006game cutscene score, composer-named publication. No claim about gameplay music by Hideyuki Fukasawa.')]),
 ('Onimusha 3: Demon Siege',2004,'oni3',[
  ('R5SZAan1_U8','Onimusha 3 — Opening','Masamichi Amano',{'orchestra':'Warsaw Philharmonic National Orchestra','orchestration_and_conducting':'Masamichi Amano'},'Original2004 soundtrack album, disc1track1; original opening-movie score, credited archival recording.')]),
 ('Onimusha: Warlords',2001,'oni1',[
  ('HpSkRSKRtAA','Hama no Hibiki — Complete 2018 Remaster Soundtrack Album','Rei Kondoh, Sho Kobayashi, Keisuke Mochizuki',{'lead_game_score_composer':'Rei Kondoh','additional_game_score_composers':'Sho Kobayashi, Keisuke Mochizuki'},'Official2018 Hama no Hibiki soundtrack album for the same-game remaster released worldwide2019. Full23-track album, archival upload; new remaster score, not the original2001 PS2 music.')])]
entries=[];audit=[]
for game,year,sourcekey,rows in groups:
 eid=ids.get((p.norm(game),year))
 if not eid:print('ARTICLE_HOLD',game,flush=True);continue
 tracks=[]
 for vid,title,composer,roles,version in rows:
  actual=p.watch(vid);q={'game':game,'youtube_id':vid,'title':title,'creator':composer,'actual_title':actual['title'],'actual_uploader':actual['author']}
  try:codec=v.metadata(vid,{'title':actual['title'],'channel':actual['author']});assert codec.get('native_compatible_avc_aac')
  except Exception as ex:q.update(status='CODEC_HOLD',reason=str(ex));audit.append(q);continue
  t={'youtube_id':vid,'url':'https://www.youtube.com/watch?v='+vid,'title':title,'creator':composer,'composer_source':sources[sourcekey],
    'recording_context_source':sources[sourcekey],'additional_recording_roles':roles,'recording_version':version,
    'uploader':actual['author'],'channel_url':'https://www.youtube.com/channel/'+actual['channelId'],'source_page':'https://www.youtube.com/watch?v='+vid,
    'official_uploader_verified':False,'publishing_kind':'credited_archival_game_recording','duration_seconds':int(actual['lengthSeconds']),
    'rights':'Original composition and recording rights remain with the game publishers, credited composers, original labels and relevant recording owners. Archive uploader credit does not imply official endorsement.',
    'verification_receipt':'build/research/soundtrack-broad/watch/'+vid+'.json','native_codec_metadata_receipt':'build/research/video-discovery/video-'+vid+'.json',
    'native_codec_metadata_verified':True,'playback_verified_on_ps5':False}
  if sourcekey=='auto':t['game_score_composer_source']='https://en.wikipedia.org/wiki/Auto_Modellista';t['credit_source_kind']='Exact original album per-track credit transcription; original game independently names Shibata/Abe, not all composers assigned to every cue.'
  if sourcekey=='oni1':
   t['credit_scope']='Whole23-track album collection credit to all three documented score composers; no per-cue joint-authorship assertion.';t['recording_release_year']=2018;t['publisher_album_context_source']=extra['onimusha2018-publisher-tracklist'][0]
  if sourcekey=='oni2':t['recording_release_year']=2002
  tracks.append(t);q['status']='CANDIDATE_PENDING_PEER';audit.append(q);print(game,title,'AVC_AAC',flush=True)
 if tracks:entries.append({'entry_id':eid,'match_title':game,'match_year':year,'title':'Listen to '+game,'composer':', '.join(dict.fromkeys(t['creator'] for t in tracks)),'curator_note':'Listen to music from '+game+'.','tracks':tracks})
 (D/'eight-score-editorial-review.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
f=D/'eight-requested-games19-candidate.json';f.write_text(json.dumps({'publication_status':'awaiting_independent_role_version_review','entries':entries},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(D/'primary/additional-eight-source-receipts.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('FINAL',len(entries),sum(len(e['tracks']) for e in entries),hashlib.sha256(f.read_bytes()).hexdigest(),flush=True)
