"""Match missing originals and named Japanese aliases to archival cover scans.

Uses LaunchBox's publicly offered metadata export. Packaging artwork retains its
original publisher copyright; the database and individual record remain cited.
Only image metadata and verified native masters are written, not catalogue text.
"""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import unquote,urlparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import hashlib,io,json,re,unicodedata,xml.etree.ElementTree as ET,zipfile
from PIL import Image

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
FOLDER=ROOT/'build/research/launchbox';CACHE=ROOT/'build/research/image-quality'

def norm(text):
    text=text.replace('\u2122','').replace('\u00ae','')
    text=re.sub(r'\([^)]*\)','',text)
    text=unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().lower()
    return re.sub('[^a-z0-9]','',text).removeprefix('sidmeiers')

ALIASES={
 'Karuizawa Y\u016bkai Annai':['Karuizawa Yuukai Annai'],
 'Day of the Tentacle':['Maniac Mansion: Day of the Tentacle'],
 'Dune II':['Dune II: The Building of a Dynasty','Dune II: Battle for Arrakis'],
 'Fallout 2':['Fallout 2: A Post Nuclear Role Playing Game','Fallout 2: A Post-Nuclear Role-Playing Game'],
 'Super Mario Bros. 2 (Famicom Disk System)':['Super Mario Bros.: The Lost Levels','Super Mario Bros. 2','Super Mario Bros. 2: For Super Players'],
 'Ys I':['Ys: Ancient Ys Vanished Omen','Ys: The Vanished Omens','Ys','Ys: Ancient Ys Vanished'],
 'Yume K\u014dj\u014d: Doki Doki Panic':['Yume Koujou: Doki Doki Panic','Doki Doki Panic'],
 'EarthBound Beginnings':['Mother','Earth Bound','EarthBound Zero'],
 'Tengai Maky\u014d: Ziria':['Tengai Makyou: Ziria','Far East of Eden: Ziria','Far East of Eden: Tengai Makyou: Ziria'],
 'Castlevania: Rondo of Blood':['Akumajou Dracula X: Chi no Rondo','Akumajo Dracula X: Chi no Rondo','Dracula X: Rondo of Blood'],
 'Donkey Kong Country 2':["Donkey Kong Country 2: Diddy's Kong Quest"],
 'Gakk\u014d de Atta Kowai Hanashi':['Gakkou de Atta Kowai Hanashi'],
 'Dragon Quest VI':['Dragon Quest VI: Maboroshi no Daichi','Dragon Quest VI: Realms of Revelation'],
 'Donkey Kong Country 3':["Donkey Kong Country 3: Dixie Kong's Double Trouble!"],
 'Pok\u00e9mon Red and Green':['Pocket Monsters Red','Pocket Monsters Green','Pokemon Red','Pokemon Green','Pokemon Red Version','Pocket Monsters: Red'],
 'Super Mario RPG':['Super Mario RPG: Legend of the Seven Stars'],
 'Fire Emblem: Genealogy of the Holy War':['Fire Emblem: Seisen no Keifu'],
 'Pok\u00e9mon Giallo':['Pokemon Yellow Version: Special Pikachu Edition','Pokemon Yellow','Pocket Monsters Pikachu'],
 "America's Army: Operations":["America's Army"],
 'Fire Emblem: The Blazing Blade':['Fire Emblem','Fire Emblem: Rekka no Ken','Fire Emblem: Blazing Sword'],
 'Pok\u00e9mon Smeraldo':['Pokemon Emerald Version','Pokemon Emerald','Pocket Monsters Emerald'],
 'Dragon Quest VIII':['Dragon Quest VIII: Journey of the Cursed King','Dragon Quest VIII: Sora to Umi to Daichi to Norowareshi Himegimi'],
 'Persona 3':['Shin Megami Tensei: Persona 3'],
 'Monster Hunter Freedom 2G':['Monster Hunter Portable 2nd G','Monster Hunter Freedom Unite'],
 'Pok\u00e9mon X e Pok\u00e9mon Y':['Pokemon X','Pokemon Y','Pokemon X and Y'],
 'Angelique Luminarise':['Angelique Luminarize'],
 'Call of Duty: Black Ops 6 Zombies':['Call of Duty: Black Ops 6'],
}
HELD_GROUPS={'Compati Hero','9-Nine','Vampire: The Masquerade (Choice of Games)','Command & Conquer Gold: freeware release'}

def main():
    held=json.loads((HERE/'major-release-coverage-audit.json').read_text(encoding='utf-8'))['held']
    targets=[{'id':'major:'+norm(e['title'])+':'+str(e['year']),'title':e['title'],'year':e['year'],'major':True} for e in held if e.get('year')]
    targets += [{**e,'major':False} for e in json.loads((FOLDER/'unmatched-game-cover-subjects.json').read_text(encoding='utf-8'))['entries'] if e['year']>=1980 and e['title'] not in HELD_GROUPS]
    aliases={};target_by_id={e['id']:e for e in targets}
    for e in targets:
        for name in [e['title'],*ALIASES.get(e['title'],[])]:aliases.setdefault(norm(name),[]).append(e)
    candidates={};pictures={};nearby={}
    with zipfile.ZipFile(FOLDER/'Metadata-range.zip') as archive,archive.open('Metadata.xml') as stream:
        for _,item in ET.iterparse(stream,events=('end',)):
            if item.tag=='Game':
                game={child.tag:child.text or '' for child in item};item.clear()
                name=game.get('Name','');release=game.get('ReleaseDate') or game.get('ReleaseYear') or '';year=int(release[:4]) if re.match(r'\d{4}',release) else 0
                for e in aliases.get(norm(name),[]):
                    if year and abs(e['year']-year)>3:continue
                    record={**game,'entry_id':e['id'],'entry_title':e['title'],'entry_year':e['year']}
                    candidates.setdefault(game['DatabaseID'],[]).append(record)
                if any(t in norm(name) for t in ['honorofkings','fantasywestward','magiccat','karuizawa','angelique','gakkou','tengai','ysancient']):nearby[game['DatabaseID']]=game
            elif item.tag=='GameImage':
                image={child.tag:child.text or '' for child in item};item.clear()
                if image.get('Type') not in ('Box - Front','Advertisement Flyer - Front'):continue
                for game in candidates.get(image.get('DatabaseID'),[]):pictures.setdefault(game['entry_id'],[]).append((game,image))
    (FOLDER/'major-alias-matches.json').write_text(json.dumps({'entries':pictures,'nearby_names':nearby},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('TARGETS',len(targets),'MATCHED',len(pictures),flush=True)
    local=FOLDER/'scans';local.mkdir(exist_ok=True)
    def download(item):
        eid,rows=item
        def score(pair):
            game,image=pair;year=int((game.get('ReleaseDate') or game.get('ReleaseYear') or str(game['entry_year']))[:4])
            return (0 if image['Type']=='Box - Front' else 1,abs(year-game['entry_year']),0 if image.get('Region') in ('North America','United States','World','') else 1)
        for game,image in sorted(rows,key=score)[:16]:
            name=image.get('FileName') or image.get('Filename')
            if not name:continue
            remote='https://images.launchbox-app.com/'+name;source=local/name
            try:
                if source.exists():raw=source.read_bytes()
                else:
                    with urlopen(Request(remote,headers={'User-Agent':'PixelMuseum/0.1 historical collection'}),timeout=20) as response:raw=response.read(24<<20)
                with Image.open(io.BytesIO(raw)) as photo:photo.load();w,h=photo.size
                if max(w,h)<600 or min(w,h)<350 or w/h>2.2:continue
                source.write_bytes(raw)
                cached=CACHE/(hashlib.sha256(remote.encode()).hexdigest()[:16]+Path(name).suffix.lower());cached.write_bytes(raw)
                owner=game.get('Publisher') or game.get('Developer') or 'Original game rights holder'
                row={'url':remote,'title':game['entry_title']+': original game cover','width':w,'height':h,
                    'source_page':'https://gamesdb.launchbox-app.com/games/details/'+game['DatabaseID'],
                    'creator':owner,'credit':owner+'; scan catalogued by LaunchBox Games Database',
                    'license':'Original game packaging; original publisher and artwork rights retained. Not an open-licensed image.',
                    'kind':'cover','cover_role':True,'story_paragraph':0,'native_long_edge':max(w,h),
                    'quality_verified':'Original archival scan decoded at native dimensions; no enlargement.',
                    'verification':{'sha256':hashlib.sha256(raw).hexdigest(),'checked_utc':datetime.now(timezone.utc).isoformat()},
                    'recovery_local_source':source.relative_to(ROOT).as_posix(),
                    'identity_evidence':{'database_id':game['DatabaseID'],'name':game['Name'],'year':game.get('ReleaseDate') or game.get('ReleaseYear'),
                        'platform':game.get('Platform'),'wikipedia_url':game.get('WikipediaURL'),'image_type':image['Type']}}
                return eid,row,None
            except Exception:continue
        return eid,None,'No matching native scan meeting quality bounds'
    major_output=HERE/'major-launchbox-cover-sources.json';alias_output=HERE/'museum-cover-recoveries-aliases.json'
    by_name=json.loads(major_output.read_text(encoding='utf-8')).get('entries',{}) if major_output.exists() else {}
    overrides=json.loads(alias_output.read_text(encoding='utf-8')).get('entries',{}) if alias_output.exists() else {}
    failures={}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures=[pool.submit(download,item) for item in pictures.items()]
        for count,future in enumerate(as_completed(futures),1):
            eid,row,error=future.result()
            e=target_by_id[eid]
            if row:
                if e['major']:by_name[norm(e['title'])+'|'+str(e['year'])]=row
                else:overrides[eid]=row
            else:failures[eid]=error
            if count%15==0:print('VERIFIED',count,'major',len(by_name),'aliases',len(overrides),flush=True)
    for e in targets:
        if e['id'] not in pictures:failures[e['id']]='No unambiguous archive title/year match'
    (HERE/'major-launchbox-cover-sources.json').write_text(json.dumps({'entries':by_name,'failures':failures},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (HERE/'museum-cover-recoveries-aliases.json').write_text(json.dumps({'entries':overrides,'failures':failures},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('DONE',len(by_name),'major',len(overrides),'existing aliases','unresolved',len(failures),flush=True)

if __name__=='__main__':main()
