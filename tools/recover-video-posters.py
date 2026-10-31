"""Use genuine native max-resolution film posters where the publisher provides one."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
import re,json,hashlib,io
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/video-poster-quality';OUT.mkdir(exist_ok=True)
source=json.loads((ROOT/'build/research/local-image-resolution-audit.json').read_text(encoding='utf8'))
targets=[i for i in source['weak_images'] if 'i.ytimg.com/' in i['url']]
def acquire(image):
 old=image['url'];match=re.search(r'/vi(?:_webp)?/([^/]+)/',old)
 if not match:return old,{'status':'fallback_editorial_art','reason':'No identified public video poster URL'}
 url='https://i.ytimg.com/vi/'+match[1]+'/maxresdefault.jpg';receipt=OUT/(match[1]+'.json');local=OUT/(match[1]+'.jpg')
 if receipt.exists():return old,json.loads(receipt.read_text(encoding='utf8'))
 try:
  data=urlopen(Request(url,headers={'User-Agent':'PixelMuseum/0.1 image archive'}),timeout=18).read(12<<20)
  with Image.open(io.BytesIO(data)) as im:im.load();w,h=im.size
  if max(w,h)<800:raise ValueError('Publisher maxres endpoint has no native high-resolution image')
  local.write_bytes(data)
  result={'status':'native_maxres','url':url,'width':w,'height':h,'recovery_local_source':local.relative_to(ROOT).as_posix(),'verification':{'sha256':hashlib.sha256(data).hexdigest(),'native_dimensions':[w,h]}}
 except Exception as error:result={'status':'fallback_editorial_art','reason':str(error)}
 receipt.write_text(json.dumps(result,ensure_ascii=True,indent=2)+'\n',encoding='utf8');return old,result
results={}
with ThreadPoolExecutor(max_workers=6) as pool:
 for n,f in enumerate(as_completed([pool.submit(acquire,t) for t in targets]),1):
  key,row=f.result();results[key]=row
  if n%25==0:print(n,'/',len(targets),'posters checked',flush=True)
output={'schema_version':1,'entries':results}
(ROOT/'content/expansion/video-poster-quality-overrides.json').write_text(json.dumps(output,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
print('Native maxres',sum(r['status']=='native_maxres' for r in results.values()),'fallback',sum(r['status']!='native_maxres' for r in results.values()),flush=True)
