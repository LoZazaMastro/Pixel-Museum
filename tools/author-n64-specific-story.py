"""Freeze a focused illustrated hardware history for separate review."""
from pathlib import Path
import copy,hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/n64-specific-story'
OUT.mkdir(parents=True,exist_ok=True)
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
old=next(e for e in catalog['entries']if e['id']=='nintendo-64')
kart=next(e for e in catalog['entries']if e['id']=='wikipedia-73963')
pool=json.loads((ROOT/'content/expansion/museum-secondary-artifacts-people.json').read_text(encoding='utf8'))
def find_image(value,fragment):
    if isinstance(value,dict):
        if fragment in value.get('url',''):return copy.deepcopy(value)
        for child in value.values():
            found=find_image(child,fragment)
            if found:return found
    if isinstance(value,list):
        for child in value:
            found=find_image(child,fragment)
            if found:return found
    return None
def image(url,path,title,caption,paragraph,license='Public domain',license_url='https://creativecommons.org/publicdomain/mark/1.0/'):
    p=ROOT/path
    with Image.open(p)as im:im.load();w,h=im.size
    return dict(url=url,source_page='https://commons.wikimedia.org/wiki/File:'+url.rsplit('/',1)[-1],
        title=title,caption=caption,creator='Evan-Amos',credit='Evan-Amos / '+license,
        license=license,license_url=license_url,width=w,height=h,
        recovery_local_source=path,story_paragraph=paragraph,
        verification=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),no_upscale=True))
body=[
"Nintendo 64 reached Japan on23 June1996, with Super Mario64 among its first games. Nintendo's partnership with Silicon Graphics, announced in1993 as Project Reality, had become a home console built around three-dimensional worlds. Beneath the case, its CPU and Reality Coprocessor worked together, sharing the same main memory. The circuit board makes that collaboration tangible: a small collection of chips had to turn geometry, textures, sound and player input into a world that responded immediately.",
"Three grips gave the controller its unusual silhouette. Players could hold its left and right handles for the directional pad, or move one hand to the centre for the analogue stick and the trigger underneath. Super Mario64 made the stick's range easy to understand: a gentle tilt could produce a careful walk, while a stronger push sent Mario running. The change was felt through the hands, as movement through space became something to judge continuously rather than choose one direction at a time.",
"Nintendo kept games on cartridges while PlayStation and Saturn used CDs. Fast access to a cartridge's data suited play with little waiting, but its smaller capacity and higher manufacturing costs brought different constraints. Recorded voices, film sequences and large collections of images all competed for space. Developers compressed material, built scenes from reusable elements or generated more of the presentation in real time. The opened Game Pak shows the physical choice behind those decisions: a game stored on chips rather than an optical disc.",
"Four controller sockets were built into the front of the console. Friends did not need a separate multitap to join a four-player game. Mario Kart 64 divided the television between racers, while its battle arenas made the same shared screen a place to hunt one another. The original packaging pictured the split-screen modes alongside the races. Playing together meant watching your own corner, hearing the people beside you and knowing that everybody could also see what you were doing.",
"The64DD attached beneath the console and reached Japan in1999. Its rewritable magnetic disks offered a different purpose from the familiar cartridge: players could save creations as well as play finished games. Mario Artist explored drawing, modelling and animation, and the Randnet service connected the system to an online network. The package also included the Expansion Pak, increasing the console's main memory from4MB to8MB. Few disks reached shops, but the hardware preserves an unusual branch of Nintendo 64's story, with making and sharing placed beside playing."
]
# Human-readable prose always has normal spacing; numeric typography is not metadata syntax.
import re
body=[re.sub(r'(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])',' ',p).replace('64 DD','64DD')for p in body]
headings=['1996 / Bringing three dimensions home','A controller for moving through space','The cartridge shapes the game','Four players, one television','64DD / Drawing, building and sharing']
controller=find_image(pool,'N64-Controller-Gray.jpg')
cartridge=find_image(pool,'N64-Game-Cartridge.jpg')
assert controller and cartridge
for record,paragraph,path in [(controller,1,'build/research/secondary-people-artifacts/9313a6c1edc17f.jpg'),(cartridge,2,'build/research/secondary-people-artifacts/cb3c88b709890d.jpg')]:
    record['story_paragraph']=paragraph;record['recovery_local_source']=path
    with Image.open(ROOT/path)as im:im.load();record['width'],record['height']=im.size
controller['title']='The original Nintendo 64 controller';controller['caption']='The three-grip Nintendo 64 controller, photographed later by Evan-Amos.'
cartridge['title']='Inside a Nintendo 64 Game Pak';cartridge['caption']='The cartridge casing and circuit board, photographed later by Evan-Amos.'
cover=copy.deepcopy(old['images'][0]);cover['story_paragraph']=-1;cover['cover_art']=True
poster=copy.deepcopy(old['images'][1])
board=image('https://upload.wikimedia.org/wikipedia/commons/3/36/Nintendo-N64-Motherboard-Top.jpg',
    'build/research/n64-source-recovery-editorial/Nintendo-N64-Motherboard-Top.jpg',
    'Inside Nintendo 64','The NUS-CPU-03 motherboard, photographed in 2015; original 1996 hardware.',0)
multiplayer=copy.deepcopy(next(i for i in kart['images']if 'dd42acf2' in i['url']))
multiplayer.update(title='Mario Kart 64: four players on one screen',caption='Original European packaging showing the split-screen racing and battle modes.',story_paragraph=3)
dd=image('https://upload.wikimedia.org/wikipedia/commons/0/07/64DD-Attached.png',
    'build/research/n64-source-recovery-editorial/64DD-Attached.png',
    'Nintendo 64 with 64DD','The Japan-only disk-drive accessory attached beneath Nintendo 64, photographed later.',4,
    'CC BY-SA 3.0','https://creativecommons.org/licenses/by-sa/3.0/')
dd['verification']['alpha_handling']='Preserve original PNG; existing image bundler composites RGBA onto white with its actual alpha mask. Hidden RGB must never be exposed by blind convert(RGB).'
videos=copy.deepcopy(old['videos']);videos[0]['story_paragraph']=0
source=dict(publication_status='awaiting_independent_review',entry_id=old['id'],body=body,story_headings=headings,
    summary='Nintendo 64 makes movement through 3D worlds tactile, and brings four players together around one television.',
    images=[cover,board,controller,cartridge,multiplayer,dd,poster],preferred_image=0,videos=videos,
    sources=old['sources'][:3]+[
        dict(title='Introduction to the Nintendo 64, chapter 1: architecture, memory and controller connections',url='https://ultra64.ca/files/documentation/nintendo/Nintendo_64_Intro_to_the_N64.pdf',publisher='Nintendo; original developer documentation preserved by ultra64.ca'),
        dict(title='Nintendo 64',url='https://en.wikipedia.org/wiki/Nintendo_64',publisher='Wikipedia contributors',license='CC BY-SA 4.0'),
        dict(title='Nintendo 64 controller',url='https://en.wikipedia.org/wiki/Nintendo_64_controller',publisher='Wikipedia contributors',license='CC BY-SA 4.0'),
        dict(title='64DD',url='https://en.wikipedia.org/wiki/64DD',publisher='Wikipedia contributors',license='CC BY-SA 4.0'),
        dict(title='Mario Kart 64 original European packaging',url='https://gamesdb.launchbox-app.com/games/details/266',publisher='Nintendo; scan catalogued by LaunchBox Games Database')],
    editorial_credit='',factual_note='',explicit_story_media_only=True,
    attribution='Historical text adapted from the cited Wikipedia articles (CC BY-SA 4.0) and Nintendo documentation; image and film rights individually attributed.',
    provenance=dict(previous_draft={k:copy.deepcopy(old.get(k))for k in ('body','story_headings','images','videos','sources','factual_note')},
        review_scope='Repeated Project Reality and controller drafts consolidated into five distinct chapters. Main-block photograph excluded from narrative cards. No 3D asset or launch-date change.'))
(OUT/'candidate.json').write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('N64 candidate:',len(body),'illustrated chapters;',sum(len(p.split())for p in body),'words')
print(hashlib.sha256((OUT/'candidate.json').read_bytes()).hexdigest())
