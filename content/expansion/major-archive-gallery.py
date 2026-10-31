"""Add useful native packaging/advertisement scans to longer original stories."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.request import Request,urlopen
from datetime import datetime,timezone
import hashlib,io,json,re,unicodedata,xml.etree.ElementTree as ET,zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;FOLDER=ROOT/'build/research/launchbox';CACHE=ROOT/'build/research/image-quality'
path=HERE/'major-release-additions.json';module=json.loads(path.read_text(encoding='utf-8'))
targets=[e for e in module['entries'] if len(e['body'])>1]
target_by_id={e['id']:e for e in targets}
def norm(text):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().lower())
by_id={};names={norm(e['title']):e for e in targets}
names.update({'sidmeierscivilizationii':e for e in targets if e['title']=='Civilization II'})
games={};pictures={}
for e in targets:
    identity=e['images'][0].get('identity_evidence',{})
    if identity.get('database_id'):by_id[identity['database_id']]=e
with zipfile.ZipFile(FOLDER/'Metadata-range.zip') as archive,archive.open('Metadata.xml') as stream:
    for _,item in ET.iterparse(stream,events=('end',)):
        if item.tag=='Game':
            game={c.tag:c.text or '' for c in item};item.clear();eid=game.get('DatabaseID');entry=by_id.get(eid) or names.get(norm(game.get('Name','')))
            date=game.get('ReleaseDate') or game.get('ReleaseYear') or ''
            if entry and (not re.match(r'\d{4}',date) or abs(int(date[:4])-entry['year'])<=3):games[eid]=(game,entry)
        elif item.tag=='GameImage':
            image={c.tag:c.text or '' for c in item};item.clear();gid=image.get('DatabaseID')
            if gid in games and image.get('Type') in ('Box - Back','Advertisement Flyer - Front','Advertisement Flyer - Back','Screenshot - Gameplay'):
                game,entry=games[gid];pictures.setdefault(entry['id'],[]).append((game,image))
def acquire(item):
    eid,rows=item;result=[];seen={i.get('verification',{}).get('sha256') for i in target_by_id[eid]['images']};existing_urls={i['url'] for i in target_by_id[eid]['images']}
    priority={'Box - Back':0,'Advertisement Flyer - Front':1,'Advertisement Flyer - Back':2,'Screenshot - Gameplay':3}
    rows.sort(key=lambda pair:(priority[pair[1]['Type']],0 if pair[1].get('Region') in ('North America','United States','World','') else 1))
    for game,image in rows[:8]:
        url='https://images.launchbox-app.com/'+image['FileName'];cache=CACHE/(hashlib.sha256(url.encode()).hexdigest()[:16]+Path(image['FileName']).suffix.lower())
        if url in existing_urls:continue
        try:
            if cache.exists():raw=cache.read_bytes()
            else:
                with urlopen(Request(url,headers={'User-Agent':'PixelMuseum historical collection'}),timeout=8) as response:raw=response.read(24<<20)
            with Image.open(io.BytesIO(raw)) as photo:photo.load();w,h=photo.size
            if max(w,h)<600 or min(w,h)<350:continue
            digest=hashlib.sha256(raw).hexdigest()
            if digest in seen:continue
            cache.write_bytes(raw);seen.add(digest);owner=game.get('Publisher') or game.get('Developer') or 'Original publisher'
            result.append({'url':url,'source_page':'https://gamesdb.launchbox-app.com/games/details/'+game['DatabaseID'],
                'title':game['Name']+': original '+image['Type'].lower(),'creator':owner,'credit':owner+' / scan catalogued by LaunchBox Games Database',
                'license':'Original packaging and advertisement artwork; original rights retained.','width':w,'height':h,'native_long_edge':max(w,h),
                'kind':'screenshot' if image['Type']=='Screenshot - Gameplay' else 'archive-artwork','story_paragraph':-1,'quality_verified':'Original archival image decoded at native dimensions; not enlarged.',
                'verification':{'sha256':digest,'checked_utc':datetime.now(timezone.utc).isoformat()}})
            if len(result)==min(3,len(target_by_id[eid]['body'])-1):break
        except Exception:continue
    return eid,result
recovered={}
with ThreadPoolExecutor(max_workers=8) as pool:
    for future in as_completed([pool.submit(acquire,item) for item in pictures.items()]):
        eid,images=future.result();recovered[eid]=images;print(eid,len(images),flush=True)
for entry in module['entries']:
    entry['images'].extend(recovered.get(entry['id'],[]))
    assigned={}
    for image in entry['images']:
        paragraph=image.get('story_paragraph',-1)
        if paragraph>=0:assigned[paragraph]=assigned.get(paragraph,0)+1
    # Every illustration belongs to the exact game, with subject-specific
    # publisher/database provenance. Balance ordinary illustrative cards;
    # surplus scans remain in the gallery rather than inventing paragraphs.
    missing=[n for n in range(len(entry['body'])) if n not in assigned]
    for image in entry['images']:
        if image.get('story_paragraph',-1)<0 and missing:image['story_paragraph']=missing.pop(0)
temp=path.with_suffix('.json.tmp');temp.write_text(json.dumps(module,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(path)
(ROOT/'build/research/major-releases/archive-gallery-enrichment.json').write_text(json.dumps({'entries':{eid:len(images) for eid,images in recovered.items()},'images_added':sum(map(len,recovered.values()))},indent=2)+'\n',encoding='utf-8')
