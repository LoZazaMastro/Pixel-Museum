from pathlib import Path
from urllib.request import Request,urlopen
import json,hashlib,io,concurrent.futures
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'content/expansion/museum-cover-recoveries-origins.json'
rows=[('wikipedia-3989467','https://images.launchbox-app.com/fbe40479-fa6a-436e-bc15-e7b635cef019.png','Lemonade Stand - Apple II publication, following the original mainframe game','https://gamesdb.launchbox-app.com/games/images/132700-lemonade-stand','MECC / Apple'),('wikipedia-1631185','https://images.launchbox-app.com/beb27a7d-9662-4c2b-aa9e-c6d9787149a0.jpg','Tanktics - Commodore PET publication','https://gamesdb.launchbox-app.com/games/images/164826-tanktics','Chris Crawford'),('wikipedia-22815518','https://upload.wikimedia.org/wikipedia/commons/3/39/Fonz_1976_sega_arcade_flyer.JPG','Fonz - original 1976 Sega arcade flyer','https://commons.wikimedia.org/wiki/File:Fonz_1976_sega_arcade_flyer.JPG','Sega'),('wikipedia-13136650','https://upload.wikimedia.org/wikipedia/commons/4/48/Trek73_video_game_screenshot.png','Trek73 - preserved terminal display','https://commons.wikimedia.org/wiki/File:Trek73_video_game_screenshot.png','TREK73 contributors')]
def get(row):
 entry_id,url,title,page,credit=row
 try:
  b=urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 Pixel Museum research'}),timeout=25).read();im=Image.open(io.BytesIO(b));im.load();w,h=im.size
  if max(w,h)<600:raise ValueError(f'too small {w}x{h}')
  ext=im.format.lower().replace('jpeg','jpg');p=ROOT/'build/research/image-quality'/(hashlib.sha256(url.encode()).hexdigest()[:16]+'.'+ext);p.write_bytes(b)
  return entry_id,dict(url=url,title=title,source_page=page,width=w,height=h,creator=credit,credit=credit+' / historical archive',license='Original rights retained; historical illustration',license_url='',recovery_local_source=p.relative_to(ROOT).as_posix()),None
 except Exception as e:return entry_id,None,str(e)
def main():
 d=json.loads(OUT.read_text(encoding='utf8'))
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as x:
  for entry_id,img,err in x.map(get,rows):
   print(entry_id,err or(str(img['width'])+'x'+str(img['height'])),flush=True)
   if img:d['entries'][entry_id]=img
 OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if __name__=='__main__':main()
