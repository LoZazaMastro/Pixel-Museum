"""Probe codec metadata with the native selector; never open stream bytes."""
import importlib.util,json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
p=Path(__file__).with_name('discover-museum-videos.py');sp=importlib.util.spec_from_file_location('discovery',p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
source=m.HERE/'museum-video-selections.json';data=json.loads(source.read_text(encoding='utf8'));folder=m.CACHE/'native-compatibility';folder.mkdir(exist_ok=True)
def probe(entry):
 v=entry['videos'][0];vid=v['youtube_id'];path=folder/(vid+'.json')
 if path.exists():return vid,json.loads(path.read_text(encoding='utf8'))
 try:r=m.app_metadata('--player',vid)
 except Exception as error:r={'id':vid,'ok':False,'error':str(error)}
 r['checked_utc']=datetime.now(timezone.utc).isoformat();m.save(path,r);return vid,r
results={}
with ThreadPoolExecutor(max_workers=2) as pool:
 for count,future in enumerate(as_completed([pool.submit(probe,e) for e in data['entries']]),1):
  vid,r=future.result();results[vid]=r
  if count%25==0:print('CHECKED',count,'COMPATIBLE',sum(bool(x.get('native_compatible_avc_aac')) for x in results.values()),flush=True)
ready=[];pending=[]
for entry in data['entries']:
 v=entry['videos'][0];r=results[v['youtube_id']];verification=v['verification']
 verification.update(native_codec_metadata_verified=bool(r.get('native_compatible_avc_aac')),avc_format_count=r.get('avc_format_count',0),aac_format_count=r.get('aac_format_count',0),native_selection=r.get('native_selection','none'),native_codec_checked_utc=r['checked_utc'])
 if r.get('native_compatible_avc_aac'):
  ready.append(entry)
  selection=m.CACHE/('selection-'+entry['entry_id']+'.json');d=json.loads(selection.read_text(encoding='utf8'));d['video']=v;m.save(selection,d)
 else:
  verification['playback_resolution_pending']=True;pending.append({'entry':entry,'reason':r.get('error') or 'Native AVC/AAC pair not resolved'})
m.save(m.CACHE/'native-compatibility-audit.json',{'checked':len(results),'compatible':len(ready),'pending':pending,'scope':'Native software AVC selector plus AAC availability; no stream bytes or PS5 playback tested.'})
m.save(source,dict(data,entries=ready))
m.save(m.HERE/'museum-video-codec-pending.json',{'entries':[x['entry'] for x in pending]})
print('DONE',len(ready),'compatible',len(pending),'pending',flush=True)
