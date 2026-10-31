"""Acquire exact public eShop square artwork, without retail/demonstration banners."""
from pathlib import Path
from urllib.request import Request,urlopen
import json,re,unicodedata,hashlib,io
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/research/cover-post2015'
targets={
 'workbook-03-16-kirby-star-allies':('Kirby Star Allies','workbook-03-16-kirby-star-allies.txt'),
 'workbook-03-29-yoshi-s-crafted-world':("Yoshi's Crafted World",'workbook-03-29-yoshi-s-crafted-world.txt'),
 'wikipedia-2369138':('Metroid Dread','wikipedia-2369138.txt'),
 'wikipedia-74839375':('Another Code: Recollection','wikipedia-74839375.txt'),
 'wikipedia-79613753':('Donkey Kong Bananza','wikipedia-79613753-second.html'),
}
def norm(s):return ''.join(c.lower()for c in unicodedata.normalize('NFKD',s.replace('\u2122','').replace('\u00ae',''))if c.isalnum())
records=[]
for eid,(name,filename)in targets.items():
 row={'entry_id':eid,'title':name,'status':'hold'}
 try:
  html=(OUT/'pages'/filename).read_text(encoding='utf8')
  match=re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',html)
  state=json.loads(match.group(1))['props']['pageProps']['initialApolloState']
  products=[(key,value)for key,value in state.items()if key.startswith('Product:')and norm(value.get('name',''))==norm(name)and 'productImage({"shape":"square"})'in value]
  if len(products)!=1:raise ValueError('Exact digital product identity ambiguous: '+str(len(products)))
  key,product=products[0];delivery=product['productImage({"shape":"square"})']['url']
  url=delivery[delivery.index('https://atum-img-'):]
  with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=20)as response:data=response.read(8<<20)
  image=Image.open(io.BytesIO(data));image.load();path=OUT/(eid+'-native-square.bin');path.write_bytes(data)
  row.update(status='pending_visual_review',url=url,publisher_delivery_url=delivery,source_snapshot='build/research/cover-post2015/pages/'+filename,source_product_key=key,source_product_name=product['name'],recovery_local_source=path.relative_to(ROOT).as_posix(),width=image.width,height=image.height,sha256=hashlib.sha256(data).hexdigest())
 except Exception as error:row['error']=str(error)
 records.append(row);print(eid,row['status'],row.get('width'),row.get('error',''),flush=True)
(OUT/'nintendo-square-acquisitions.json').write_text(json.dumps(records,indent=2,ensure_ascii=True)+'\n',encoding='utf8')
