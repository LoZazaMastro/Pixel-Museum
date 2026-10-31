#!/usr/bin/env python3
"""Recover missing historical game imagery from the public LaunchBox metadata dump.

Matches are bounded by the original Wikipedia identity or exact title and release
year. Only actual decoded scans are admitted; no placeholder art is generated.
The original publishers retain rights to packaging and game images.
"""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlparse,unquote
import concurrent.futures,copy,hashlib,io,json,re,unicodedata,sys,xml.etree.ElementTree as ET,zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'build/research/launchbox'

def norm(text):
 text=re.sub(r'\([^)]*(?:video game|\d{4})[^)]*\)','',text,flags=re.I).replace('\u2122','').replace('\u00ae','')
 return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().lower())
def main():
 catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'));semantic='--semantic' in sys.argv;identity='--identity' in sys.argv
 def has_cover(e):
  if not e.get('images'):return False
  image=e['images'][min(e.get('preferred_image',0),len(e['images'])-1)]
  return image.get('cover_art') or image.get('cover_role') or image.get('kind')=='cover' or 'library_600x900' in image.get('url','') or any(w in image.get('title','').lower() for w in ['cover','box art','key art'])
 wanted=[e for e in catalog['entries'] if e['kind']=='game' and ((e.get('images') and e['images'][e.get('preferred_image',0)].get('identity_evidence') and not e['images'][e.get('preferred_image',0)]['identity_evidence'].get('year')) if identity else (not has_cover(e) if semantic else not e.get('images')))]
 names={};wiki={}
 for e in wanted:
  names.setdefault(norm(e['title']),[]).append(e)
  for source in e.get('sources',[]):
   if 'en.wikipedia.org/wiki/' in source.get('url',''):wiki[unquote(urlparse(source['url']).path.split('/wiki/',1)[1]).replace('_',' ').lower()]=e
 candidates={};pictures={};sample=None
 with zipfile.ZipFile(FOLDER/'Metadata-range.zip') as z,z.open('Metadata.xml') as stream:
  for _,item in ET.iterparse(stream,events=('end',)):
   if item.tag=='Game':
    game={child.tag:child.text or '' for child in item};item.clear()
    name=game.get('Name','');release=game.get('ReleaseDate') or game.get('ReleaseYear') or '';year=int(release[:4]) if re.match(r'\d{4}',release) else 0
    wiki_name=unquote(urlparse(game.get('WikipediaURL','')).path.split('/wiki/')[-1]).replace('_',' ').lower()
    matches=[wiki[wiki_name]] if wiki_name in wiki else names.get(norm(name),[])
    for e in matches:
     if norm(name)!=norm(e['title']) and wiki_name not in wiki:continue
     if urlparse(game.get('WikipediaURL','')).fragment and norm(name)!=norm(e['title']):continue
     # A shared Wikipedia URL may span old remakes: retain the original year bound.
     if year and abs(e['year']-year)>3:continue
     if identity and not year:continue
     game['entry_id']=e['id'];game['entry_title']=e['title'];game['entry_year']=e['year'];candidates.setdefault(game['DatabaseID'],[]).append(copy.deepcopy(game))
   elif item.tag=='GameImage':
    image={child.tag:child.text or '' for child in item};item.clear()
    if sample is None:sample=image
    database=image.get('DatabaseID')
    if database not in candidates:continue
    if image.get('Type') not in (['Box - Front','Advertisement Flyer - Front'] if semantic else ['Box - Front','Advertisement Flyer - Front','Screenshot - Gameplay','Screenshot - Game Title']):continue
    for game in candidates[database]:pictures.setdefault(game['entry_id'],[]).append((game,image))
 (FOLDER/('identity-game-image-matches.json' if identity else ('semantic-game-image-matches.json' if semantic else 'missing-game-image-matches.json'))).write_text(json.dumps({'sample_image':sample,'entries':pictures},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('Matched missing subjects',len(pictures),'of',len(wanted),'image example',sample,flush=True)
 output=ROOT/'content/expansion'/('museum-cover-recoveries-identity.json' if identity else ('museum-cover-recoveries-semantic.json' if semantic else 'museum-cover-recoveries-games.json'))
 result=json.loads(output.read_text(encoding='utf8')) if output.exists() else {'schema_version':1,'entries':{},'unavailable':{}}
 local=FOLDER/'scans';local.mkdir(exist_ok=True)
 def save():
  temp=output.with_suffix('.json.tmp');temp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');temp.replace(output)
 def download(item):
  identifier,rows=item
  if identifier in result['entries']:return identifier,result['entries'][identifier],None
  def score(pair):
   game,image=pair;kind=image['Type'];year=(game.get('ReleaseDate') or game.get('ReleaseYear') or str(game['entry_year']))[:4]
   return (abs(int(year)-game['entry_year']) if (game.get('ReleaseDate') or game.get('ReleaseYear')) else 999,0 if game.get('Platform')=='Arcade' else 1,['Box - Front','Advertisement Flyer - Front','Screenshot - Gameplay','Screenshot - Game Title'].index(kind),0 if image.get('Region') in ['North America','United States','World',''] else 1)
  errors=[]
  for game,image in sorted(rows,key=score)[:4]:
   name=image.get('FileName') or image.get('Filename');
   if not name:continue
   url='https://images.launchbox-app.com/'+name;path=local/name
   try:
    if path.exists():body=path.read_bytes()
    else:
     with urlopen(Request(url,headers={'User-Agent':'PixelMuseum/0.1 historical collection'}),timeout=10) as response:body=response.read(24<<20)
    with Image.open(io.BytesIO(body)) as photo:
     photo.load();w,h=photo.size
     if max(w,h)<600 or min(w,h)<200:continue
    path.write_bytes(body)
    publisher=game.get('Publisher') or game.get('Developer') or 'Original game rights holder'
    page='https://gamesdb.launchbox-app.com/games/details/'+game['DatabaseID']
    record={'url':url,'title':game['entry_title']+' - '+('cover art' if image['Type']=='Box - Front' else 'archive illustration'),'width':w,'height':h,'source_page':page,'creator':publisher,'credit':publisher+'; image catalogued by LaunchBox Games Database','license':'Original game packaging and imagery; original publisher rights retained','license_url':'','recovery_local_source':path.relative_to(ROOT).as_posix(),'identity_evidence':{'database_id':game['DatabaseID'],'name':game['Name'],'year':game.get('ReleaseDate') or game.get('ReleaseYear'),'platform':game.get('Platform'),'wikipedia_url':game.get('WikipediaURL'),'image_type':image['Type']},'cover_art':image['Type']=='Box - Front'}
    return identifier,record,None
   except Exception as exc:errors.append(str(exc))
  return identifier,None,'No useful-size matching source image; '+ '; '.join(errors[:2])
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
  futures=[executor.submit(download,item) for item in pictures.items()]
  for count,future in enumerate(concurrent.futures.as_completed(futures),1):
   identifier,record,error=future.result()
   if record:result['entries'][identifier]=record;result['unavailable'].pop(identifier,None)
   else:result['unavailable'][identifier]=error
   if count%25==0:save();print(count,'checked;',len(result['entries']),'covers',flush=True)
 save()
 print(json.dumps({'wanted':len(wanted),'matching_subjects':len(pictures),'recovered':len(result['entries']),'failed':len(result['unavailable'])},indent=2),flush=True)
if __name__=='__main__':main()
