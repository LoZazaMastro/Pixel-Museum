"""Deduplicated native codec metadata audit for every assembled catalog film.

No source metadata is rewritten and no stream bytes are downloaded. AVC selection
uses the same native selector; AAC availability is counted independently.
"""
import importlib.util,json
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
p=Path(__file__).with_name('discover-museum-videos.py');sp=importlib.util.spec_from_file_location('discovery',p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
catalog=json.loads((m.ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries'];records={};invalid=[]
for entry in catalog:
 for video in entry.get('videos',[]):
  vid=video.get('youtube_id') or parse_qs(urlparse(video.get('url','')).query).get('v',[''])[0]
  if not vid:invalid.append({'entry_id':entry['id'],'title':video.get('title',''),'reason':'No YouTube video identity'});continue
  records.setdefault(vid,[]).append({'entry_id':entry['id'],'entry_title':entry['title'],'video_title':video.get('title','')})
folder=m.CACHE/'native-compatibility';folder.mkdir(exist_ok=True)
def probe(vid):
 path=folder/(vid+'.json');metadata=m.CACHE/('video-'+vid+'.json')
 if metadata.exists():
  cached=json.loads(metadata.read_text(encoding='utf8'))
  if cached.get('native_compatible_avc_aac') is True:return vid,cached
 if path.exists():return vid,json.loads(path.read_text(encoding='utf8'))
 try:r=m.app_metadata('--player',vid)
 except Exception as error:r={'id':vid,'ok':False,'error':str(error)}
 r['checked_utc']=datetime.now(timezone.utc).isoformat();m.save(path,r);return vid,r
results={}
with ThreadPoolExecutor(max_workers=2) as pool:
 for count,future in enumerate(as_completed([pool.submit(probe,vid) for vid in records]),1):
  vid,r=future.result();results[vid]={'native_compatible_avc_aac':bool(r.get('native_compatible_avc_aac')),'avc_format_count':r.get('avc_format_count',0),'aac_format_count':r.get('aac_format_count',0),'native_selection':r.get('native_selection','none'),'error':r.get('error',''),'checked_utc':r.get('checked_utc'),'references':records[vid]}
  if count%50==0:print('CHECKED',count,flush=True)
output={'checked_utc':datetime.now(timezone.utc).isoformat(),'unique_catalog_films':len(records),'catalog_video_references':sum(map(len,records.values())),'compatible':sum(v['native_compatible_avc_aac'] for v in results.values()),'pending':sum(not v['native_compatible_avc_aac'] for v in results.values()),'invalid_records':invalid,'films':results,'scope':'Native AVC software selector and available AAC audio metadata. No stream bytes downloaded; not a PS5 playback claim.'}
m.save(m.CACHE/'all-catalog-codec-audit.json',output)
print('DONE',output['unique_catalog_films'],'unique films',output['compatible'],'compatible',output['pending'],'pending',flush=True)
