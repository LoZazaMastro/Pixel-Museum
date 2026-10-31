"""Acquire exact original game packaging for three Sakurai narrative chapters."""
import hashlib,io,json,pathlib,urllib.request,xml.etree.ElementTree as ET,zipfile
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'build/research/sakurai-complete-illustrations';OUT.mkdir(exist_ok=True)
targets={"Kirby's Dream Land":1992,'Kid Icarus: Uprising':2012}
games={};images=[]
with zipfile.ZipFile(ROOT/'build/research/launchbox/Metadata-range.zip') as z,z.open('Metadata.xml') as stream:
 for _,node in ET.iterparse(stream,events=('end',)):
  if node.tag=='Game':
   g={c.tag:c.text or '' for c in node};node.clear()
   if g.get('Name') in targets and g.get('ReleaseDate','').startswith(str(targets[g['Name']])):games[g['DatabaseID']]=g
  elif node.tag=='GameImage':
   row={c.tag:c.text or '' for c in node};node.clear()
   if row.get('DatabaseID') in games and row.get('Type')=='Box - Front':images.append(row)
results=[]
(OUT/'exact-packaging-source-inventory.json').write_text(json.dumps({'games':games,'images':images},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for title in targets:
 for row in sorted([i for i in images if games[i['DatabaseID']]['Name']==title],key=lambda i:0 if i.get('Region')=='North America' else 1)[:4]:
  name=row.get('FileName') or row.get('Filename');url='https://images.launchbox-app.com/'+name
  try:
   raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 PixelMuseum historical collection'}),timeout=8).read()
   with Image.open(io.BytesIO(raw)) as photo:photo.load();w,h=photo.size
   if max(w,h)<1000 or min(w,h)<600:continue
   dest=OUT/name;dest.write_bytes(raw);g=games[row['DatabaseID']]
   results.append({'url':url,'title':title+' — original game packaging','caption':title+' ('+str(targets[title])+'): original game packaging.','width':w,'height':h,'source_page':'https://gamesdb.launchbox-app.com/games/details/'+row['DatabaseID'],'credit':g.get('Publisher','Nintendo')+'; original packaging scan catalogued by LaunchBox Games Database','creator':g.get('Publisher','Nintendo'),'license':'Original game packaging; publisher and artwork rights retained. Not an open-licensed image.','recovery_local_source':dest.relative_to(ROOT).as_posix(),'quality_verified':'Native archival scan decoded; no enlargement.','verification':{'sha256':hashlib.sha256(raw).hexdigest()},'story_paragraph':1 if targets[title]==1992 else 3})
   print(title,w,h,url,flush=True);break
  except Exception as e:print(type(e).__name__,str(e)[:100],flush=True)
(OUT/'native-packaging-candidates.json').write_text(json.dumps({'entries':results,'source_game_records':games},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
