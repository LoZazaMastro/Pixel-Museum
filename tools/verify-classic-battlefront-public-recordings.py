import concurrent.futures,subprocess,json,re
from pathlib import Path
out=Path('build/research/explicit-zero-music-rooms/bf2005-public-metadata');out.mkdir(parents=True,exist_ok=True);p=json.loads(Path('build/research/explicit-zero-music-rooms/bf2005-122-playlist.json').read_text(encoding='utf-8'));entries=p['entries']
def run(e):
 id=e['id'];path=out/(id+'.json')
 if path.exists():return json.loads(path.read_text(encoding='utf-8'))
 try:
  r=subprocess.run(['C:/Users/Andrea/homebrew/plugins/themedeck/yt-dlp.exe','--dump-single-json','--skip-download','--socket-timeout','8','--retries','0','--no-warnings','https://www.youtube.com/watch?v='+id],capture_output=True,encoding='utf-8',errors='replace',timeout=30);d=json.loads(r.stdout or '{}');fm=d.get('formats',[]);res={k:d.get(k)for k in ['id','title','channel','channel_id','channel_url','duration','availability','description','upload_date']};res['aac_public']=any(str(f.get('acodec','')).startswith('mp4a')for f in fm);res['avc_public']=any(str(f.get('vcodec','')).startswith('avc1')for f in fm);res['status']='verified_public_native_metadata' if res['aac_public'] and res['avc_public'] and r.returncode==0 else 'held';res['requested_id']=id
 except Exception as ex:res={'requested_id':id,'status':'held','error':str(ex)[:200]}
 path.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8');return res
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for r in pool.map(run,entries):
  rows.append(r)
  if len(rows)%20==0:print('Verified metadata',len(rows),flush=True)
(out/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');print('Public native',sum(r['status']=='verified_public_native_metadata'for r in rows),'of',len(rows),flush=True)
