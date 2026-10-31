"""Name the Switch coverage gaps without mistaking mobile games or absent music."""
import hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[2];catalog=json.loads((ROOT/'content/catalog.json').read_text())
priority=['The Legend of Zelda: Breath of the Wild','The Legend of Zelda: Tears of the Kingdom','Super Mario Odyssey','Super Mario Bros. Wonder','Mario Kart 8 Deluxe','Mario Kart World','Donkey Kong Bananza']
explicit=['Kirby Star Allies','Super Smash Bros. Ultimate','Super Mario Maker 2','Fire Emblem: Three Houses','Astral Chain',"Luigi's Mansion 3",'Animal Crossing: New Horizons','Super Mario 3D All-Stars','Super Mario Bros. 35',"Super Mario 3D World + Bowser's Fury",'Metroid Dread','Pokémon Legends: Arceus','Xenoblade Chronicles 3','Splatoon 3','Bayonetta 3','Pokémon Scarlet and Violet','The Legend of Zelda: Echoes of Wisdom','Metroid Prime 4: Beyond']
def norm(t):return re.sub('[^a-z0-9]','',t.lower())
aliases={'pokemonscarletandviolet':['pokemonscarletviolet'],'supermario3dworldbowsersfury':['supermario3dworldbowsersfury']}
entries=catalog['entries'];found=[];missing=[]
for e in entries:
 if e.get('kind')!='game' or e['year']<2017:continue
 corpus=' '.join([e.get('summary',''),*e.get('body',[])])
 name=norm(e['title']);is_explicit=next((t for t in priority+explicit if norm(t)==name or name in aliases.get(norm(t),[])),None)
 if not is_explicit and not re.search(r'Nintendo Switch(?:\s*2)?',corpus):continue
 if 'Mario Kart Tour'==e['title']:continue
 platform='Nintendo Switch 2' if re.search(r'Nintendo Switch 2',corpus[:3000])or e['title']in['Mario Kart World','Donkey Kong Bananza']else'Nintendo Switch'
 tracks=e.get('soundtrack',{}).get('tracks',[])
 source=[];expected=None
 if 'Breath of the Wild'==e['title'].split(':')[-1].strip():expected=211;source=['https://columbia.jp/prod-info/COCX-40313-7/']
 if 'Tears of the Kingdom'==e['title'].split(':')[-1].strip():expected=344;source=['https://columbia.jp/prod-info/COCX-42298-306/']
 if e['title']=='Super Mario Odyssey':expected=136;source=['https://bzone.co.jp/site/mario_ost/'];note='Primary label site currently denies direct fetch;136 is also documented by original CD archival inventory.'
 else:note=''
 found.append({'entry_id':e['id'],'title':e['title'],'platform':platform,'platform_scope':'Explicit priority Nintendo release'if is_explicit else'Article text mentions Switch; this is not proof it originated on Switch.','priority':e['title']in priority,'runtime_verified_recordings':len(tracks),'status':'partial'if tracks else'unresolved','expected_published_album_tracks':expected,'expected_count_scope':'Published album may include bonus cues or DLC; distinguish before claiming base-game completeness.'if expected else'Complete original tracklist still to acquire.','tracklist_sources':source,'note':note})
for title in priority+explicit:
 if not any(norm(e['title'])==norm(title)or norm(e['title'])in aliases.get(norm(title),[])for e in entries):missing.append({'title':title,'state':'no separate exact-title exhibit matched; verify canonical/port alias before adding','not_absent_music':True})
report={'schema_version':1,'scope':'Switch/Switch2 exhibits and explicit Nintendo priorities. MarioKartTour mobile is excluded. These are runtime counts at this catalog checkpoint; soundtrack research in pending modules is separate.','catalog_sha256':hashlib.sha256((ROOT/'content/catalog.json').read_bytes()).hexdigest(),'identified_games':len(found),'games':found,'unmatched_requested_titles':missing}
dest=ROOT/'content/expansion/switch-soundtrack-completeness-gaps.json';dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Switch inventory',len(found),'named gaps',len(missing));print([(r['title'],r['runtime_verified_recordings'],r['expected_published_album_tracks'])for r in found if r['priority']])
