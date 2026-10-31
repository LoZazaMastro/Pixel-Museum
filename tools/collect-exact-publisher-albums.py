"""Cache bounded, specifically requested publisher album metadata; no media."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from email.utils import parsedate_to_datetime
import argparse,hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'build/tools/ytmusicapi'))
from ytmusicapi import YTMusic
p=argparse.ArgumentParser();p.add_argument('plan');p.add_argument('--base',required=True);p.add_argument('--output',default='results.json');args=p.parse_args()
BASE=ROOT/args.base;BASE.mkdir(parents=True,exist_ok=True)
state_path=ROOT/'build/research/youtube-metadata-rate-limit-state.json'
client=YTMusic();plan=json.loads((ROOT/args.plan).read_text(encoding='utf8'))
def save(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');tmp.replace(path)
def fetch(path,callback):
 if path.exists():return json.loads(path.read_text(encoding='utf8'))
 state=json.loads(state_path.read_text(encoding='utf8'));now=datetime.now(timezone.utc)
 if state.get('status')=='RATE_LIMITED'and datetime.fromisoformat(state['retry_after_utc'])>now:raise RuntimeError('COOLDOWN')
 try:data=callback()
 except Exception as error:
  save(path.with_suffix('.attempt.json'),{'error':str(error),'metadata_only':True,'observed_at_utc':now.isoformat()})
  if '429'in str(error)or'too many requests'in str(error).lower():
   value=getattr(getattr(error,'response',None),'headers',{}).get('Retry-After','300')
   try:seconds=max(300,int(value))
   except ValueError:
    try:seconds=max(300,(parsedate_to_datetime(value)-now).total_seconds())
    except (ValueError,TypeError):seconds=300
   state.update(status='RATE_LIMITED',retry_after_utc=(now+timedelta(seconds=seconds)).isoformat());save(state_path,state);raise RuntimeError('COOLDOWN')from error
  raise
 save(path,data);time.sleep(1);return data
def key(s):return ''.join(c for c in s.casefold()if c.isalnum())
out=[]
for item in plan:
 folder=BASE/item['entry_id']/hashlib.sha256(item['query'].encode()).hexdigest()[:12];folder.mkdir(parents=True,exist_ok=True)
 try:
  candidates=fetch(folder/'search.json',lambda:client.search(item['query'],filter='albums',limit=3))
  match=next((c for c in candidates if key(c.get('title','')).startswith(key(item['title_prefix']))and (not item.get('required_title_text')or item['required_title_text'].casefold()in c.get('title','').casefold())and any(item['artist'].casefold()in a.get('name','').casefold()for a in c.get('artists',[]))),None)
  result={**item,'status':'no_matching_publisher_album','metadata_only':True,'media_downloaded':False}
  if match and match.get('browseId'):
   ap=folder/(match['browseId']+'.json');album=fetch(ap,lambda:client.get_album(match['browseId']))
   result.update(status='cached_for_review',album={'receipt':ap.relative_to(ROOT).as_posix(),'title':album['title'],'artists':[a['name']for a in album['artists']],'year':album.get('year'),'tracks':len(album['tracks']),'matched_existing_verified_ids':[]})
  out.append(result);save(folder/'result.json',result);print(json.dumps({'query':item['query'],'status':result['status'],'tracks':result.get('album',{}).get('tracks')},ensure_ascii=True),flush=True)
 except Exception as error:
  out.append({**item,'error':str(error)[:150]})
  if 'COOLDOWN'in str(error):break
save(BASE/args.output,out)
