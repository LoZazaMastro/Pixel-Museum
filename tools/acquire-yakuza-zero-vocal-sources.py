"""Acquire bounded public source HTML, never audio/video."""
from pathlib import Path
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor
import hashlib,json
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'build/research/soundtrack-broad/yakuza-zero-public-collection'
sources=[
 ('shonan-original-bubble-single','https://www.134r.com/discography/s15.html',['バブル','作曲']),
 ('shonan-original-come-again-album','https://www.134r.com/discography/a09.html',['紅','松田岳二']),
 ('toys-factory-original-bubble-single','https://www.toysfactory.co.jp/sp/artist/shonan/disco/1287',['バブル','2015']),
 ('toys-factory-original-come-again-album','https://www.toysfactory.co.jp/sp/artist/shonan/disco/1335',['紅','エンディング']),
 ('sega-yakuza5-original-composition-press-reprint','https://www.4gamer.net/games/139/G013951/20121219002/',['ばかみたい','福山光晴','堀井亮佑']),
 ('sega-kiwami-variant-author-corroboration','https://www.sega.jp/topics/detail/160125_soft_1/',['ばかみたい','福山光晴','堀井亮佑'])]
def fetch(spec):
 name,url,required=spec;path=P/(name+'.html')
 try:
  if path.exists(): raw=path.read_bytes();status=200
  else:
   with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as r: raw=r.read();status=r.status
  text=raw.decode('utf8',errors='replace')
  okay=status==200 and all(t in text for t in required) and len(raw)>3000
  if okay:path.write_bytes(raw)
  return {'url':url,'path':path.relative_to(ROOT).as_posix() if okay else None,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'http_status':status,'actual_subject_and_credit_body_verified':okay,'required_subject_credit_tokens':required}
 except Exception as e: return {'url':url,'status':'HELD_fetch_failed_no_retry','error':str(e)}
with ThreadPoolExecutor(max_workers=2) as pool: rows=list(pool.map(fetch,sources))
(P/'vocal-primary-source-acquisition.json').write_text(json.dumps({'checked_utc':datetime.now(timezone.utc).isoformat(),'sources':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for r in rows:print(r['url'],r.get('actual_subject_and_credit_body_verified'),r.get('bytes'),r.get('error',''))
