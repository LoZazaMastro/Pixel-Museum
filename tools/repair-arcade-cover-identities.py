"""Prefer actual first-release arcade advertisements over later console packaging."""
from pathlib import Path
from urllib.request import Request,urlopen
import concurrent.futures,io,json,re,unicodedata,xml.etree.ElementTree as ET,zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def norm(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',re.sub(r'\([^)]*\)','',s)).encode('ascii','ignore').decode().lower())
def main():
 entries=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries'];wanted={}
 for e in entries:
  if e['kind']!='game' or e['year']>2000:continue
  p=e['images'][e.get('preferred_image',0)];evidence=p.get('identity_evidence',{})
  if evidence and evidence.get('platform')!='Arcade':wanted[(norm(e['title']),e['year'])]=e
 games={};images={}
 with zipfile.ZipFile(ROOT/'build/research/launchbox/Metadata-range.zip') as z,z.open('Metadata.xml') as stream:
  for _,node in ET.iterparse(stream,events=('end',)):
   if node.tag=='Game':
    g={c.tag:c.text or '' for c in node};node.clear();date=g.get('ReleaseDate') or g.get('ReleaseYear') or ''
    if not re.match(r'\d{4}',date) or g.get('Platform')!='Arcade':continue
    e=wanted.get((norm(g.get('Name','')),int(date[:4])))
    if e:games[g['DatabaseID']]=(e,g)
   elif node.tag=='GameImage':
    i={c.tag:c.text or '' for c in node};node.clear()
    if i.get('DatabaseID') in games and i.get('Type')=='Advertisement Flyer - Front':images.setdefault(i['DatabaseID'],[]).append(i)
 out=ROOT/'content/expansion/museum-cover-recoveries-arcade.json';result={'schema_version':1,'entries':{},'unavailable':{}}
 def acquire(dbid):
  e,g=games[dbid]
  for i in sorted(images[dbid],key=lambda i:0 if i.get('Region') in ['North America','Japan'] else 1)[:3]:
   url='https://images.launchbox-app.com/'+i['FileName'];file=ROOT/'build/research/launchbox/scans'/i['FileName']
   try:
    if not file.exists():file.write_bytes(urlopen(Request(url,headers={'User-Agent':'PixelMuseum/0.1 Historical Collection'}),timeout=8).read(20<<20))
    with Image.open(file) as photo:photo.load();w,h=photo.size
    if max(w,h)<600 or min(w,h)<300:continue
    return e['id'],dict(url=url,title=e['title']+' - original arcade promotional flyer',width=w,height=h,source_page='https://gamesdb.launchbox-app.com/games/details/'+dbid,creator=g.get('Publisher','Original publisher'),credit=g.get('Publisher','Original publisher')+' / LaunchBox scan archive',license='Original publisher and illustration rights retained; historical arcade advertisement',license_url='',recovery_local_source=file.relative_to(ROOT).as_posix(),cover_art=True,identity_evidence={'database_id':dbid,'name':g['Name'],'year':g.get('ReleaseDate') or g.get('ReleaseYear'),'platform':'Arcade','wikipedia_url':g.get('WikipediaURL'),'image_type':i['Type']}),None
   except Exception:continue
  return e['id'],None,'No useful-size original arcade advertisement acquired'
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for entry_id,image,error in pool.map(acquire,images):
   if image:result['entries'][entry_id]=image
   else:result['unavailable'][entry_id]=error
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'wanted':len(wanted),'matched':len(images),'recovered':len(result['entries']),'unavailable':result['unavailable']},indent=2),flush=True)
if __name__=='__main__':main()
