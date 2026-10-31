"""Verify public developer films for the bounded recent article batch."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import importlib.util,json,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/research/recent-game-six'
spec=importlib.util.spec_from_file_location('video_research',ROOT/'tools/discover-museum-videos.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
targets=[
 ('wikipedia-80139082','-hiC3qpghP0','Resident Evil',True,'Resident Evil Requiem: its creators discuss the horror design, from Capcom Spotlight in June2025.',4),
 ('wikipedia-80139823','Q36TlmrVKyo','IGN',False,'Nioh3: the original TGS2025 gameplay presentation with developer commentary; this is a development demonstration.',5),
 ('wikipedia-64250594','tliliBfCnUU','FGS',False,'Pragmata: its developers discuss the game in the Future Games Show gamescom2025 interview.',4),
 ('wikipedia-81838290','gpBteyC_OrA','Bandai Namco Entertainment America',True,'Code VeinII: a producer diary explaining the motorcycle and its role in traversing the game world.',1),
 ('wikipedia-78591702','iyHL4QZrMaI','Insider Gaming',False,'Dispatch: a conversation with the creators at AdHoc Studio about making the game.',3),
 ('wikipedia-78591702','5tCfik9R8ss','AdHoc Studio',True,'Dispatch: members of the original cast discuss their work on the game.',0),
 ('wikipedia-73307133','qGIMQ7TvhI4','IO Interactive',True,'007 First Light: gameplay director Andreas Krogh and senior level designer Thomas Pulluelo explain their design choices in Beyond the Light Episode1.',5)]
def acquire(target):
 eid,vid,expected,official,caption,index=target
 try:
  meta=m.metadata(vid,{'title':'','channel':expected});creator=meta.get('channel')or''
  if creator.casefold().strip()!=expected.casefold().strip():raise ValueError('Original uploader identity differs: '+creator)
  if not meta.get('native_compatible_avc_aac'):raise ValueError('Native compatible stream metadata not resolved')
  video={'youtube_id':vid,'url':'https://www.youtube.com/watch?v='+vid,'title':meta['title'],'creator':creator,'source_page':'https://www.youtube.com/watch?v='+vid,'credit':creator+' / original developer conversation publication','license':'Original recording, creator, publisher and game rights retained. Streamed from original publication.','caption':caption,'official_uploader_verified':official,'channel_id':meta.get('channel_id'),'duration_s':meta.get('duration'),'story_paragraph':index,'verification':{'native_codec_metadata_verified':True,'metadata_resolved':True,'availability':meta.get('availability'),'avc_format_count':meta.get('avc_format_count'),'aac_format_count':meta.get('aac_format_count'),'native_selection':meta.get('native_selection'),'checked_utc':meta.get('checked_utc'),'check_scope':'Actual public native AVC/AAC selection plus original uploader/title identity; no physical PS5 playback claim.'}}
  image=m.poster(video)
  if image and image['width']<800:image=None
  if image:video['poster_url']=image['url']
  return {'entry_id':eid,'video':video,'poster':image,'metadata':meta,'status':'native_metadata_and_identity_checked_pending_editorial_peer'}
 except Exception as ex:return {'entry_id':eid,'youtube_id':vid,'status':'held','reason':str(ex)}
with ThreadPoolExecutor(max_workers=2)as pool:rows=list(pool.map(acquire,targets))
(OUT/'developer-films-review-checkpoint.json').write_text(json.dumps({'publication_status':'awaiting_independent_review','entries':rows},indent=2,ensure_ascii=True)+'\n',encoding='utf8')
print(json.dumps([{'entry_id':r['entry_id'],'status':r['status'],'title':r.get('video',{}).get('title'),'reason':r.get('reason')}for r in rows]))
