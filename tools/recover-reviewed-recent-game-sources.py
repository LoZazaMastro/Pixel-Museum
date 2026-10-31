"""Acquire a bounded recent-game research batch; never admit it automatically."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor
from PIL import Image,ImageDraw,ImageOps
import hashlib,json,re,io
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/research/recent-game-six';OUT.mkdir(parents=True,exist_ok=True)
TARGETS=[('Resident Evil Requiem',80139082,3764200,2026),('Nioh 3',80139823,3681010,2026),('Pragmata',64250594,3357650,2026),('Code Vein II',77632808,2362060,2026),('Dispatch',77538710,2592160,2025),('007 First Light',73307133,3768760,2026)]
# Actual Wikipedia page IDs are resolved from the parent-researched source file.
parents={re.sub(r' \(video game\)$','',r['title']).lower():r for r in json.loads((ROOT/'content/expansion/recent-catalog-recovery-candidates.json').read_text(encoding='utf8'))['entries']}
TARGETS=[(title,int(parents[title.lower()]['id'].split('-')[-1]),appid,year)for title,_,appid,year in TARGETS]
def fetch(url):
 with urlopen(Request(url,headers={'User-Agent':'PixelMuseum/0.1 historical editorial research; public publisher assets'}),timeout=22)as r:return r.read()
api=OUT/'wikipedia-full-six.json'
if not api.exists():
 url='https://en.wikipedia.org/w/api.php?'+urlencode({'action':'query','format':'json','formatversion':2,'pageids':'|'.join(str(p)for _,p,_,_ in TARGETS),'prop':'extracts|revisions','explaintext':1,'exsectionformat':'plain','exlimit':'max','rvprop':'ids|timestamp|content','rvslots':'main'})
 result=json.loads(fetch(url));api.write_text(json.dumps(result,indent=2,ensure_ascii=True)+'\n',encoding='utf8')
pages={p['pageid']:p for p in json.loads(api.read_text(encoding='utf8')).get('query',{}).get('pages',[])}
assetsfile=OUT/'public-steam-six-assets.json'
if not assetsfile.exists():
 request={'ids':[{'appid':appid}for _,_,appid,_ in TARGETS],'context':{'language':'english','country_code':'US'},'data_request':{'include_assets':True}}
 assetsfile.write_bytes(fetch('https://api.steampowered.com/IStoreBrowseService/GetItems/v1/?'+urlencode({'input_json':json.dumps(request,separators=(',',':'))})))
store_assets={item['appid']:item for item in json.loads(assetsfile.read_bytes())['response']['store_items']}
results=[]
for title,pageid,appid,year in TARGETS:
 row={'title':title,'id':'wikipedia-'+str(pageid),'appid':appid,'year':year,'status':'research_only_pending_text_and_visual_review'}
 try:
  page=pages[pageid]
  if not page.get('extract'):
   individual=OUT/(str(pageid)+'-wikipedia-full.json')
   if not individual.exists():
    request={'action':'query','format':'json','formatversion':2,'pageids':pageid,'prop':'extracts|revisions','explaintext':1,'exsectionformat':'plain','rvprop':'ids|timestamp|content','rvslots':'main'}
    individual.write_bytes(fetch('https://en.wikipedia.org/w/api.php?'+urlencode(request)))
   page=json.loads(individual.read_bytes())['query']['pages'][0]
  if not page.get('extract'):raise ValueError('Full English extract is still unavailable')
  row['wikipedia_page']=page
  storepath=OUT/(str(appid)+'-store.json')
  if not storepath.exists():storepath.write_bytes(fetch('https://store.steampowered.com/api/appdetails?'+urlencode({'appids':appid,'l':'english'})))
  data=json.loads(storepath.read_bytes())[str(appid)]
  if not data['success']:raise ValueError('Steam product unavailable')
  data=data['data'];row['steam_name']=data['name'];row['steam_release_date']=data['release_date']
  normalize=lambda s:re.sub('[^a-z0-9]','',s.lower())
  if normalize(data['name'])!=normalize(title):raise ValueError('Exact Steam game identity mismatch: '+data['name'])
  item=store_assets[appid]
  if normalize(item['name'])!=normalize(title):raise ValueError('Public Steam Browse title mismatch')
  assets=item['assets'];filename=assets.get('library_capsule_2x')or assets.get('library_capsule')
  if not filename:raise ValueError('Publisher library cover not supplied')
  coverurl='https://shared.akamai.steamstatic.com/store_item_assets/'+assets['asset_url_format'].replace('${FILENAME}',filename)
  jobs=[('cover',coverurl)]+[('screenshot-'+str(n),s['path_full'])for n,s in enumerate(data.get('screenshots',[])[:6])]
  def get(job):
   role,url=job;p=OUT/(str(appid)+'-'+role+('-'+hashlib.sha256(url.encode()).hexdigest()[:10]if role=='cover'else'')+'.bin')
   try:
    if not p.exists():
     raw=fetch(url)
     with Image.open(io.BytesIO(raw))as im:im.load()
     p.write_bytes(raw)
    with Image.open(p)as im:im.load();w,h=im.size
    return {'role':role,'url':url,'recovery_local_source':p.relative_to(ROOT).as_posix(),'width':w,'height':h,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'status':'pending_visual_review'if max(w,h)>=800 else'held_small_native_master'}
   except Exception as ex:return {'role':role,'url':url,'status':'failed','error':str(ex)}
  with ThreadPoolExecutor(max_workers=3)as pool:row['images']=list(pool.map(get,jobs))
  row['developer']=data.get('developers',[]);row['publisher']=data.get('publishers',[])
  review=[i for i in row['images']if i['status']=='pending_visual_review'];sheet=Image.new('RGB',(1600,600),'#ece9e1');draw=ImageDraw.Draw(sheet)
  for n,i in enumerate(review):
   with Image.open(ROOT/i['recovery_local_source'])as im:thumb=ImageOps.contain(im.convert('RGB'),(390,265));x=n%4*400;y=n//4*300;sheet.paste(thumb,(x+(390-thumb.width)//2,y))
   draw.text((x+3,y+268),f"{i['role']} / {i['width']}x{i['height']}",fill='black')
  sheet.save(OUT/(str(appid)+'-review.jpg'),quality=94)
 except Exception as ex:row.update(status='held_acquisition_or_identity',error=str(ex))
 results.append(row)
 (OUT/'research-checkpoint.json').write_text(json.dumps({'publication_status':'research_only_not_approved','entries':results},indent=2,ensure_ascii=True)+'\n',encoding='utf8')
 print(title,row['status'],flush=True)
