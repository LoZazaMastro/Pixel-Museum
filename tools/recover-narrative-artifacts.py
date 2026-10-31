"""Illustrate existing stories with exact-edition archival packaging and flyers.

The matching database identity was established during the cover recovery pass.
Only distinct, useful-size original scans are admitted, with publisher credits.
"""
from pathlib import Path
from urllib.request import Request,urlopen
import concurrent.futures,copy,io,json,xml.etree.ElementTree as ET,zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'content/expansion/museum-narrative-artifacts.json'
def main():
 catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
 covers=json.loads((ROOT/'content/expansion/museum-cover-recoveries-games.json').read_text(encoding='utf8'))['entries']
 major={e['id'] for e in json.loads((ROOT/'content/expansion/major-release-additions.json').read_text(encoding='utf8'))['entries']}
 by_id={e['id']:e for e in catalog['entries']};wanted={};mapping={}
 for entry_id,cover in covers.items():
  e=by_id.get(entry_id)
  if not e or entry_id in major:continue
  used={i.get('story_paragraph',n) for n,i in enumerate(e['images'])}
  gaps=[n for n in range(len(e['body'])) if n not in used]
  if not gaps:continue
  database_id=cover.get('identity_evidence',{}).get('database_id')
  if database_id:wanted[entry_id]={'entry':e,'cover':cover,'gaps':gaps};mapping.setdefault(database_id,[]).append(entry_id)
 images={entry_id:[] for entry_id in wanted}
 with zipfile.ZipFile(ROOT/'build/research/launchbox/Metadata-range.zip') as z,z.open('Metadata.xml') as stream:
  for _,item in ET.iterparse(stream,events=('end',)):
   if item.tag=='GameImage':
    record={c.tag:c.text or '' for c in item};item.clear()
    if record.get('Type') not in ['Box - Back','Advertisement Flyer - Front','Advertisement Flyer - Back']:continue
    for entry_id in mapping.get(record.get('DatabaseID'),[]):images[entry_id].append(record)
   elif item.tag=='Game':item.clear()
 previous=json.loads(OUT.read_text(encoding='utf8')) if OUT.exists() else {'schema_version':1,'entries':{},'unavailable':{}}
 def acquire(entry_id):
  if entry_id in previous['entries']:return entry_id,previous['entries'][entry_id],None
  spec=wanted[entry_id];chosen=[];cover=spec['cover'];e=spec['entry']
  candidates=sorted(images[entry_id],key=lambda i:(0 if i['Type']=='Box - Back' else 1,0 if i.get('Region')==cover.get('identity_evidence',{}).get('region') else 1))
  for record in candidates[:2]:
   if len(chosen)>=1:break
   url='https://images.launchbox-app.com/'+record['FileName'];path=ROOT/'build/research/launchbox/scans'/record['FileName']
   if url in {im['url'] for im in e['images']}:continue
   try:
    if not path.exists():path.write_bytes(urlopen(Request(url,headers={'User-Agent':'PixelMuseum/0.1 Historical Collection'}),timeout=8).read(20<<20))
    with Image.open(path) as photo:photo.load();w,h=photo.size
    if max(w,h)<600 or min(w,h)<300:continue
    item={'url':url,'title':e['title']+' - '+record['Type'].lower()+' ('+cover['identity_evidence'].get('platform','original edition')+')','source_page':cover['source_page'],'width':w,'height':h,'creator':cover.get('creator','Original publisher'),'credit':cover.get('credit','Original publisher / LaunchBox Games Database'),'license':cover.get('license','Original rights retained'),'license_url':cover.get('license_url',''),'recovery_local_source':path.relative_to(ROOT).as_posix(),'story_paragraph':spec['gaps'][len(chosen)],'identity_evidence':{**cover.get('identity_evidence',{}),'image_type':record['Type']}}
    chosen.append(item)
   except Exception:continue
  return entry_id,chosen,None if chosen else 'No further useful-size original packaging or flyer acquired'
 def save():
  temp=OUT.with_suffix('.json.tmp');temp.write_text(json.dumps(previous,ensure_ascii=False,indent=2)+'\n',encoding='utf8');temp.replace(OUT)
 with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
  futures=[pool.submit(acquire,entry_id) for entry_id in wanted]
  for count,future in enumerate(concurrent.futures.as_completed(futures),1):
   entry_id,items,error=future.result()
   if items:previous['entries'][entry_id]=items
   if error:previous['unavailable'][entry_id]=error
   if count%25==0:save();print(f'{count}/{len(wanted)} subjects checked; {sum(map(len,previous["entries"].values()))} original narrative illustrations',flush=True)
 save();print(json.dumps({'subjects':len(wanted),'illustrated':len(previous['entries']),'new_images':sum(map(len,previous['entries'].values())),'unavailable':len(previous['unavailable'])},indent=2),flush=True)
if __name__=='__main__':main()
