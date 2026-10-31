"""Separate dated original games from imported franchise/series wrappers."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import copy,hashlib,importlib.util,io,json,re
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('major',HERE/'major-release-additions.py');major=importlib.util.module_from_spec(spec);spec.loader.exec_module(major)
research=json.loads((ROOT/'build/research/major-releases/series-split-research.json').read_text(encoding='utf-8'))
nine=next(p for p in research['wikipedia']['query']['pages'] if p.get('pageid')==77040235)
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf-8'))['entries']
vamp=next((e for e in catalog if e['id']=='wikipedia-65079310'),None)
if vamp is None:
    previous=json.loads((HERE/'museum-series-splits.json').read_text(encoding='utf-8'))['entries']
    vamp=next(e for e in previous if e['id']=='vampire-night-road')
records=[]
def cover(appid,title,owner):
    for filename in ['library_600x900_2x.jpg','library_600x900.jpg']:
        url=f'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/{filename}';cache=major.QUALITY/(hashlib.sha256(url.encode()).hexdigest()[:16]+'.jpg')
        try:
            raw=cache.read_bytes() if cache.exists() else major.fetch(url)
            with Image.open(io.BytesIO(raw)) as image:image.load();w,h=image.size
            if w<600 or h<900:continue
            cache.write_bytes(raw)
            return {'url':url,'source_page':f'https://store.steampowered.com/app/{appid}/','title':title+': original publisher library cover',
                'creator':owner,'credit':owner+' / official publisher Steam media','license':'Original game and artwork rights retained by their publishers.',
                'width':w,'height':h,'native_long_edge':max(w,h),'cover_role':True,'kind':'cover','story_paragraph':0,
                'quality_verified':'Publisher original decoded at native resolution; not enlarged.',
                'verification':{'appid':appid,'sha256':hashlib.sha256(raw).hexdigest(),'checked_utc':datetime.now(timezone.utc).isoformat()}}
        except Exception:continue
    raise ValueError('No original cover for '+title)
def base(identifier,title,year,month,day,body,headings,appid,owner):
    entry={'id':identifier,'title':title,'year':year,'date':{'month':month,'day':day,'precision':'day','region':''},'kind':'game',
        'subtitle':headings[0],'summary':body[0],'body':body,'story_headings':headings,'era_id':'everywhere','tags':['Interactive narrative'],
        'related_ids':[],'layout':'editorial','images':[cover(appid,title,owner)],'preferred_image':0,'videos':[],'models':[],
        'explicit_story_media_only':True,'featured':False,'calendar_only':False,'sources':[{'title':'Publisher game and release information','url':f'https://store.steampowered.com/app/{appid}/','publisher':owner}]}
    major.context_images(entry)
    return entry
nine_titles=['Kokonotsu Kokonoka Kokonoiro','Sorairo Sorauta Soranooto','Haruiro Harukoi Harunokaze','Yukiiro Yukihana Yukinoato']
sections=re.split(r'\n9-nine - ',nine['extract'])
episode_paragraphs=[]
for section in sections[1:5]:
    content=section.split('\n',1)[1];content=content.split('\n\n')[0]
    content=content.replace('This game can be played on its own without knowledge of the other series instalments.','').strip()
    episode_paragraphs.append(content)
for n,(appid,year,day) in enumerate([(976390,2017,28),(1033420,2018,27),(1142830,2019,26),(1424660,2020,24)]):
    title='9-nine-: Episode '+str(n+1)
    body=[episode_paragraphs[n],
        'Shiromitsugawa City connects an ordinary student setting to a supernatural mystery. An earthquake breaks a sacred object at Hakuda Tsukumo Shrine, and artifacts from another world give people unusual abilities. Kakeru Niimi investigates a series of petrifications alongside the people drawn into that disturbance.',
        'The visual novel presents the mystery through illustrated scenes, dialogue and a changing point of view. This episode is one dated release within that larger structure. Its Japanese title is '+nine_titles[n]+', and its original Windows release precedes the later English Steam edition and the combined console editions.']
    entry=base('9-nine-episode-'+str(n+1),title,year,4,day,body,['A different route through the mystery','A town connected to another world','An episode with its own release'],appid,'Palette / Sekai Project')
    rev=nine['revisions'][0]
    entry['attribution']={'text':'Adapted from the episode plot and release information in 9-Nine, by Wikipedia contributors; additional exhibition framing.','source_url':'https://en.wikipedia.org/w/index.php?oldid='+str(rev['revid']),'article_url':'https://en.wikipedia.org/wiki/9-Nine','contributors_url':'https://en.wikipedia.org/wiki/9-Nine?action=history','revision_id':rev['revid'],'revision_timestamp':rev['timestamp'],'license':'CC BY-SA 4.0','license_url':major.LICENCE,'changes':'Episode section selected, contextual prose adapted; separate original-release chronology.'}
    entry['sources'].append({'title':'9-Nine: original Japanese episode release dates','url':entry['attribution']['source_url'],'publisher':'Wikipedia contributors'})
    entry['provenance']={'provider':'Wikipedia / publisher','article_title':'9-Nine','source_group_id':'wikipedia-77040235','date_basis':'Exact episode-specific original Japanese Windows infobox; not the later Steam release'}
    records.append(entry)
extra=base('9-nine-new-episode','9-nine-: New Episode',2021,4,23,
    ['New Episode returns to the four heroines after the events of the preceding releases. Short after-stories revisit Miyako, Sora, Haruka and Noa, while a further scenario addresses the unfinished task that remains for Kakeru.',
     'The Japanese release is titled Shinsho. Rather than introducing another separate starting route, it acts as an epilogue to the earlier episodes. Familiar characters and unresolved events become material for a conclusion that assumes knowledge of the preceding mysteries.',
     'The after-story format changes the pace of the visual novel. Instead of beginning another investigation with an unfamiliar cast, it returns to people the reader already knows. Smaller scenes and the consequences of earlier events give the series room to consider what remains after its central mystery.'],
    ['Returning after the mystery','An epilogue across the routes','Time after the ending'],1890120,'Palette / Sekai Project')
extra['attribution']=copy.deepcopy(records[-1]['attribution']);extra['attribution']['changes']='Final episode section and original-release infobox adapted; separate exhibition framing.'
extra['sources'].append({'title':'9-Nine: original Shinsho release information','url':extra['attribution']['source_url'],'publisher':'Wikipedia contributors'})
extra['provenance']={'provider':'Wikipedia / publisher','article_title':'9-Nine','source_group_id':'wikipedia-77040235','date_basis':'Original Japanese Windows release; later English Steam edition is not a separate timeline entry'}
records.append(extra)
vampires=[
    ('night-road','Night Road',1290270,2020,9,24,'Kyle Marquis',
     'Night Road follows a vampire courier across the Southwestern United States. Delivering the elders\' secrets means navigating factions, other vampires and the danger that arrives with daylight. The road connects private decisions to a larger political world.',
     'Marquis stays close to the tabletop game\'s rules. Character creation and abilities shape the available choices, while the courier premise lets the narrative move between communities rather than remaining inside a single city.'),
    ('out-for-blood','Out for Blood',1290350,2021,7,29,'Jim Dattilo',
     'Out for Blood changes the perspective from vampire to human hunter. A threatened town becomes the setting for gathering allies, investigating the supernatural and deciding how to confront creatures with far more power than an ordinary person.',
     'The difference in viewpoint matters: the same World of Darkness setting becomes a place to investigate and survive from outside its ruling supernatural society. Knowledge of opponents and relationships with other people help define the choices available to the player.'),
    ('parliament-of-knives','Parliament of Knives',1266100,2021,10,28,'Jeffrey Dean',
     'Parliament of Knives places a vampire inside the unstable politics of Ottawa. The disappearance of the city\'s Prince creates an opening for competing loyalties, personal ambition and betrayal within an undead hierarchy.',
     'Dean adapts the tabletop mechanics more loosely than Night Road. Alliances and judgments about other characters give the political setting its structure. The player\'s decisions become a way to explore how authority survives when everyone around it has a different interest.'),
    ('sins-of-the-sires','Sins of the Sires',1523990,2022,3,24,'Natalia Theodoridou',
     'Sins of the Sires follows a vampire in Athens, where an ancient vampire plans to rule over humans as a god. Its Greek setting places personal identity and the pressures of undead society alongside a struggle over power.',
     'The interactive novel gives its protagonist choices about relationships, allegiance and the self they want to preserve. Its setting offers another viewpoint within the shared World of Darkness rather than continuing the courier, hunter or Ottawa stories directly.')]
def vampire_record(spec):
    slug,name,appid,year,month,day,author,premise,design=spec
    meta=major.api('https://store.steampowered.com/api/appdetails',{'appids':str(appid),'l':'english'},'steam').get(str(appid),{}).get('data',{})
    assert name.lower() in meta.get('name','').lower(),name
    date=meta.get('release_date',{}).get('date','');assert str(year) in date,date
    body=[premise,design,'Written by '+author+' and published by Choice of Games, this is a text-based interactive novel. The player creates a character and selects responses that change the direction of the story. Choices and character information carry the action; a conventional moving game world is replaced by a narrative the reader helps shape.']
    entry=base('vampire-'+slug,'Vampire: The Masquerade - '+name,year,month,day,body,['A place within the World of Darkness','Perspective shapes the choices','An interactive novel'],appid,'Choice of Games / World of Darkness')
    entry['sources']+=copy.deepcopy(vamp.get('sources',[]));entry['attribution']=copy.deepcopy(vamp.get('attribution',{}))
    entry['attribution']['text']='Exhibition text adapted from the specific game descriptions and development discussion in Vampire: The Masquerade (Choice of Games), by Wikipedia contributors, with publisher release verification.'
    entry['attribution']['license']='CC BY-SA 4.0';entry['attribution']['license_url']=major.LICENCE
    entry['provenance']={'provider':'Wikipedia / publisher','source_group_id':'wikipedia-65079310','date_basis':'Publisher Steam original standalone release; exact title and year verified'}
    return entry
with ThreadPoolExecutor(max_workers=4) as pool:records.extend(pool.map(vampire_record,vampires))
replace={'wikipedia-77040235':[e['id'] for e in records if e['id'].startswith('9-nine')],'wikipedia-65079310':[e['id'] for e in records if e['id'].startswith('vampire-')]}
out=HERE/'museum-series-splits.json';out.write_text(json.dumps({'schema_version':1,'entries':records,'replace_map':replace,'context_only':['wikipedia-32470667']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'entries':len(records),'images':sum(len(e['images']) for e in records),'replace_map':replace},indent=2))
