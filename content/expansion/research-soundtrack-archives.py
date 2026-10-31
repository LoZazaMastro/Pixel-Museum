import json,collections,subprocess,concurrent.futures
from pathlib import Path
root=Path('.');rows={};cache=root/'build/research/soundtrack-broad/channels';cache.mkdir(exist_ok=True)
for f in (root/'build/research/soundtrack-broad/search').glob('*.json'):
 for r in json.loads(f.read_text()):
  if r.get('channel_id'):rows[r['id']]=r
counts=collections.Counter();names={}
for f in (root/'build/research/soundtrack-broad/games').glob('*.json'):
 d=json.loads(f.read_text())
 if d['state']!='recording_research_required':continue
 for c in d.get('candidates',[]):
  if c.get('reason','').startswith('Search publisher') and c.get('youtube_id') in rows:
   r=rows[c['youtube_id']];counts[r['channel_id']]+=1;names[r['channel_id']]=r.get('channel')
ids=[cid for cid,n in counts.most_common(220) if not (cache/(cid+'.json')).exists()]
def fetch(cid):
 try:
  cmd=[r'C:/Users/Andrea/homebrew/plugins/themedeck/yt-dlp.exe','--flat-playlist','--playlist-end','3','--dump-single-json','--no-warnings','--skip-download','--socket-timeout','10','--retries','0','https://www.youtube.com/channel/'+cid+'/videos']
  p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=35);d=json.loads(p.stdout);out={'channel_id':cid,'title':d.get('title'),'description':d.get('description'),'channel_is_verified':d.get('channel_is_verified'),'follower_count':d.get('channel_follower_count'),'sample_titles':[e.get('title') for e in d.get('entries',[]) if e],'source_page':'https://www.youtube.com/channel/'+cid,'checked':'2026-10-21'}
  (cache/(cid+'.json')).write_text(json.dumps(out,ensure_ascii=True,indent=2)+'\n');return out
 except Exception as e:return {'channel_id':cid,'error':str(e)}
for r in concurrent.futures.ThreadPoolExecutor(max_workers=2).map(fetch,ids):print(json.dumps(r,ensure_ascii=True),flush=True)
