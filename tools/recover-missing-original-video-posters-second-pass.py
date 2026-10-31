import concurrent.futures,hashlib,io,json,re,time
from pathlib import Path
from urllib.request import Request,urlopen
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/video-poster-local-audit-second-pass';OUT.mkdir(parents=True,exist_ok=True)
def recover(row):
 identity=row.get('youtube_id','')
 if not re.fullmatch(r'[A-Za-z0-9_-]{11}',identity or ''):return dict(row,status='invalid_identity')
 for variant in ('hq720.jpg','maxresdefault.webp'):
  u=f'https://i.ytimg.com/{"vi_webp" if variant.endswith("webp") else "vi"}/{identity}/{variant}';p=OUT/'originals'/f'{identity}-{variant}'
  try:
   if p.exists():raw=p.read_bytes()
   else:
    with urlopen(Request(u,headers={'User-Agent':'PixelMuseum image preview collection'}),timeout=10) as response:raw=response.read(12<<20)
   with Image.open(io.BytesIO(raw)) as im:im.load();w,h=im.size
   if w<600 or h<300:continue
   p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
   return dict(row,status='original_recovered_for_review',candidate_url=u,local_source=p.relative_to(ROOT).as_posix(),width=w,height=h,sha256=hashlib.sha256(raw).hexdigest())
  except Exception:continue
 return dict(row,status='no_suitable_original')
def main():
 gaps=json.loads((ROOT/'build/research/chronological-global-native-no-empty-photo-cards/actual-remaining-film-preview-gaps.json').read_text(encoding='utf-8'));rows=[dict(id=r['entry_id'],owner=r['entry_id'],title=r['title'],youtube_id=r['youtube_id'],poster_url=r.get('poster_url'),attached_image=False) for r in gaps]
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for result in pool.map(recover,rows):
   results.append(result)
   if len(results)%30==0:print(f'Checked {len(results)} original film previews',flush=True)
 (OUT/'recovered-original-poster-candidates.json').write_text(json.dumps({'status':'RESEARCH_CANDIDATES_NOT_ADMITTED','rows':results},ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'checked':len(results),'recovered':sum(r['status']=='original_recovered_for_review' for r in results)}),flush=True)
if __name__=='__main__':main()
