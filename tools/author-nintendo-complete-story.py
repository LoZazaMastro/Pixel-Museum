"""Prepare Nintendo's researched chronology without rewriting its original chapters."""
from pathlib import Path
from urllib.request import Request,urlopen
import copy,hashlib,html,io,json,re
from urllib.parse import urlencode,urlsplit,urlunsplit
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/nintendo-complete-story'
PLAYHUB=Path('F:/Playhub/Plugin/Playhub/assets/on-this-day/v1')
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
original=read(OUT/'original-story.json')
catalog={r['id']:r for r in read(OUT/'existing-exhibit-artifacts.json')}
history=read(OUT/'history-sections-readable.json')
manifest=read(ROOT/'assets/images/manifest.json')['images']
paragraphs=history['paragraphs']
chapters=[];pictures=[]

def asset(url,title,source,creator='Nintendo',license='Original rights retained',local=None):
    image=dict(url=url,title=title,caption='',source_page=source,creator=creator,
        credit=creator,license=license,license_url='')
    if local:image['recovery_local_source']=str(local)
    return image

def acquire(image):
    local=ROOT/image.get('recovery_local_source','__not_local__')
    if not local.is_file() and image['url'] in manifest:
        local=ROOT/manifest[image['url']]
    if not local.is_file():
        if 'raw.githubusercontent.com/LoZazaMastro/Playhub/' in image['url']:
            local=PLAYHUB/image['url'].rsplit('/',1)[-1]
        if not local.is_file():
            local=OUT/(hashlib.sha256(image['url'].encode()).hexdigest()[:16]+'.image')
            if not local.is_file():
                with urlopen(Request(image['url'],headers={'User-Agent':'PixelMuseum historical collection'}),timeout=20) as response:local.write_bytes(response.read(32<<20))
            image['recovery_local_source']=local.relative_to(ROOT).as_posix()
    with Image.open(local) as im:
        im.load();image.update(width=im.width,height=im.height)
        if max(im.size)<1280:raise ValueError('Insufficient source size: '+image['url'])
    image['source_sha256']=hashlib.sha256(local.read_bytes()).hexdigest()
    return image

def from_catalog(entry_id,n=0):
    image=copy.deepcopy(catalog[entry_id]['images'][n]);image.pop('story_paragraph',None)
    image.pop('feature_id',None);return image

def archive(filename,title):
    prefix='https://raw.githubusercontent.com/LoZazaMastro/Playhub/0c5c103403813431e23b40f90c75fba6d51a9759/assets/on-this-day/v1/'
    return asset(prefix+filename,title,prefix+filename)

def hanafuda():
    path=OUT/'hanafuda-original-commons.json'
    if not path.is_file():
        url='https://commons.wikimedia.org/w/api.php?'+urlencode(dict(action='query',titles='File:Nintendo Hanafuda.jpg',prop='imageinfo',iiprop='url|extmetadata',format='json'))
        with urlopen(Request(url,headers={'User-Agent':'PixelMuseum source research'}),timeout=15) as response:data=json.load(response)
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    data=read(path);info=next(iter(data['query']['pages'].values()))['imageinfo'][0]
    meta=info['extmetadata'];strip=lambda s:html.unescape(re.sub('<[^>]+>','',s))
    url=urlsplit(info['url']);image=asset(urlunsplit((url.scheme,url.netloc,url.path,'','')),
        'Nintendo hanafuda cards, photographed in 2006',info['descriptionurl'],strip(meta['Artist']['value']),strip(meta['LicenseShortName']['value']))
    image['license_url']=meta.get('LicenseUrl',{}).get('value','')
    image['credit']=image['creator']+' / '+image['license'];return image

def iwata():
    data=read(OUT/'iwata-original-commons.json')
    page=next(p for p in data['query']['pages'].values() if p['title']=='File:Satoru Iwata GDC 2011.jpg')
    info=page['imageinfo'][0];meta=info['extmetadata'];strip=lambda s:html.unescape(re.sub('<[^>]+>','',s))
    url=urlsplit(info['url']);image=asset(urlunsplit((url.scheme,url.netloc,url.path,'','')),
        'Satoru Iwata speaking at the 2011 Game Developers Conference',info['descriptionurl'],strip(meta['Artist']['value']),strip(meta['LicenseShortName']['value']))
    image['license_url']=meta.get('LicenseUrl',{}).get('value','')
    image['credit']=image['creator']+' / '+image['license'];return image

def early_commons(filename,title):
    data=read(OUT/'early-products-commons.json')
    page=next(p for p in data['query']['pages'].values() if p['title']=='File:'+filename)
    info=page['imageinfo'][0];meta=info['extmetadata'];strip=lambda s:html.unescape(re.sub('<[^>]+>','',s))
    url=urlsplit(info['url']);image=asset(urlunsplit((url.scheme,url.netloc,url.path,'','')),title,
        info['descriptionurl'],strip(meta['Artist']['value']),strip(meta['LicenseShortName']['value']))
    image['license_url']=meta.get('LicenseUrl',{}).get('value','')
    image['credit']=image['creator']+' / '+image['license'];return image

def chapter(title,body,image,source=None,original_index=None):
    n=len(chapters);image=acquire(image);image['story_paragraph']=n
    chapters.append(dict(title=title,body=body,source=source or 'Original published chapter',original_index=original_index))
    pictures.append(image)

wiki='https://en.wikipedia.org/w/index.php?title=History_of_Nintendo&oldid='+str(history['revision'])
official='https://www.nintendo.co.jp/corporate/en/history/index.html'
museum='https://museum.nintendo.com/en/exhibition/index.html'

chapter('1889 / A playing-card workshop',original['body'][0],early_commons('NintendoCards.jpg','Historical Nintendo playing-card catalogue'),original_index=0)
chapter('Playing cards and shared rules',original['body'][1],hanafuda(),original_index=1)
chapter('1966 / Toys that move in your hands',original['body'][2],archive('nintendo-ultra-hand.jpg','Nintendo Ultra Hand with its original packaging'),original_index=2)
chapter('1977 / Games enter the television',original['body'][3],early_commons('Nintendo Color TV game 6 (Cut out).jpg','Nintendo Color TV-Game 6'),original_index=3)
chapter('1980 / A pocket-sized game',original['body'][4],early_commons('Game-and-watch-ball.png','Game & Watch: Ball'),original_index=4)
chapter('1983 / A home for many games',original['body'][5],from_catalog('nes',1),original_index=5)
chapter('1989 / Game Boy and Tetris',paragraphs[43]['text'],from_catalog('game-boy',1),wiki)
chapter('1990 / The Super Famicom generation',paragraphs[44]['text'],from_catalog('daily-11-21'),wiki)
chapter('1996 / Learning to move in three dimensions',
    'Nintendo 64 brought Nintendo\'s major home-console series into three-dimensional spaces. Its cartridge format contrasted with the optical discs used by competitors, creating different trade-offs for developers, manufacturing and storage. Super Mario 64 made the controller\'s analogue stick central to movement. Before building its worlds, Shigeru Miyamoto and the development team concentrated on how Mario should feel to control. Running, jumping and changing direction needed to make sense before the surrounding levels could teach the player what to do with those actions.',from_catalog('nintendo-64'),wiki)
chapter('2001 / Game Boy Advance',
    'Game Boy Advance extended Nintendo\'s handheld line while keeping earlier Game Boy and Game Boy Color cartridges playable. Its wider colour screen and new processor gave developers a different space for games without discarding the existing library. Nintendo also connected the handheld and living-room branches of its business: a link cable let a Game Boy Advance communicate with a GameCube. Compatible games could use the handheld for private information or an additional view, turning the relationship between screens into part of the design.',from_catalog('workbook-03-21-game-boy-advance'),wiki)
chapter('2001 / A different shape for the living room',
    'GameCube replaced Nintendo\'s home-console cartridges with small optical discs. Its compact case, carrying handle and distinctive controller gave it a different physical identity from its competitors. The software library included Super Smash Bros. Melee, Super Mario Sunshine, The Legend of Zelda: The Wind Waker and Metroid Prime. Game Boy Advance connectivity added another approach to multiplayer and second-screen play. The console\'s commercial difficulties also formed the background to Nintendo\'s subsequent decision to seek a wider audience with Wii.',from_catalog('workbook-09-14-nintendo-gamecube'),wiki)
chapter('2002 / Satoru Iwata becomes president',
    'Satoru Iwata joined Nintendo\'s corporate planning division after leading HAL Laboratory. In 2002, Hiroshi Yamauchi chose him as Nintendo\'s next president, the first president outside the founding Yamauchi family. Iwata brought experience as a working programmer as well as a company leader. The DS and Wii years placed reaching new players alongside serving existing fans. His later Iwata Asks interviews also made the work of designers, programmers, artists and hardware engineers visible through conversations about how Nintendo\'s products were made.',iwata(),wiki)
ds=asset('https://upload.wikimedia.org/wikipedia/commons/a/a3/Nintendo-DS-Fat-Blue.png','Original Nintendo DS in blue','https://commons.wikimedia.org/wiki/File:Nintendo-DS-Fat-Blue.png','Evan-Amos','Public domain')
ds['license_url']='https://creativecommons.org/publicdomain/mark/1.0/'
chapter('2004 / Two screens, one new vocabulary',
    'Nintendo DS combined a conventional game screen with a second screen that could be touched directly. The stylus made pointing, drawing and writing part of the controller, while the microphone and local wireless connection offered further ways to interact. Games such as Nintendogs and Brain Age reached people who did not necessarily think of themselves as console players. The DS also continued to support familiar kinds of play. Its success depended on that combination: new gestures and audiences alongside a substantial library for existing players.',ds,wiki)
chapter('2006 / Wii opens the room',original['body'][6],from_catalog('wii'),original_index=6)
chapter('2011 / Depth without glasses',
    'Nintendo 3DS retained the DS family\'s two-screen arrangement but added stereoscopic depth that could be viewed without special glasses. A slider adjusted the strength of that effect or turned it off. The system also added a circle pad, motion sensors and cameras. Its early sales difficulties led Nintendo to reduce the price, after which the platform built a substantial library over several years. It shows a recurring feature of Nintendo\'s history: introducing a technical idea is only the beginning of making a platform work.',from_catalog('nintendo-3ds',2),wiki)
chapter('2012 / Wii U and the second screen',
    'Wii U brought high-definition output to Nintendo\'s home consoles and placed a touchscreen inside its GamePad controller. A game could put different information in the player\'s hands and on the television, or support play on the controller\'s screen. The idea proved difficult to communicate, and the console did not match Wii\'s commercial success. Its games and experiments nevertheless remained significant: several later reached a much larger audience on Switch, and the relationship between home play and a handheld screen remained an important question.',from_catalog('daily-11-18'),wiki)
chapter('2017 / One library, at home and away',
    'Nintendo Switch joined handheld and television play in a single platform. The tablet-like console could be used on its own or placed in a dock, while its Joy-Con controllers could be attached or removed. The Legend of Zelda: Breath of the Wild launched alongside the system, and Super Mario Odyssey followed in the same year. Instead of maintaining separate handheld and home-console libraries, Nintendo could develop around a shared machine. The change made moving between different places and ways of playing a defining feature of the hardware.',from_catalog('switch'),wiki)
chapter('2024 / The objects become a museum',
    'Nintendo Museum brings playing cards, toys, electronic games and consoles together in Uji, Kyoto. Seeing those objects side by side makes the company\'s changes visible without reducing its history to a row of successful machines. The museum also includes playable installations and a hanafuda workshop. In the accompanying official tour, Shigeru Miyamoto walks through the displays and explains how products from different periods connect. The film is presented here as a guided look at the objects behind this story.',asset('https://museum.nintendo.com/assets/images/exhibition/know/image01.webp','Nintendo Museum historical product displays',museum),museum)
chapter('2025 / Nintendo Switch 2',
    'Nintendo Switch 2 continues the hybrid design with a larger display and redesigned magnetic Joy-Con 2 controllers. Its controllers can also be used in a mouse-like way in supported software, adding another gesture to the platform\'s vocabulary. Backward compatibility keeps much of the original Switch library in reach, while new games explore the successor\'s capabilities. It belongs to the same long history as the playing cards and mechanical toys: a business repeatedly changing the tools it uses to make games.',from_catalog('switch-2'),'https://www.nintendo.co.jp/corporate/release/2025/250402.html')

video=dict(youtube_id='-CSWjjbWm30',url='https://www.youtube.com/watch?v=-CSWjjbWm30',
    title='Inside Nintendo Museum with Shigeru Miyamoto',creator='Nintendo UK',
    source_page='https://www.nintendo.com/en-gb/News/Nintendo-Direct/2024/Nintendo-Museum-Direct-August-20th-2024-2643142.html',
    caption='Shigeru Miyamoto introduces the museum\'s historical displays, hands-on installations and hanafuda workshop in Nintendo\'s official 2024 tour. The film connects the objects in this exhibition through the people and ideas behind them.',
    credit='Nintendo / original Nintendo UK publication',license='Original Nintendo audiovisual rights retained; streamed from Nintendo UK.',
    official_uploader_verified=True,story_paragraph=17,
    verification=dict(native_codec_metadata_verified=True,receipt='build/research/nintendo-complete-story/museum-direct-native.json',scope='Public native AVC/AAC metadata verified; PS5 playback not yet tested.'))
poster_url='https://i.ytimg.com/vi/-CSWjjbWm30/maxresdefault.jpg'
video['poster_url']=poster_url
poster=acquire(asset(poster_url,'Nintendo Museum Direct: original film preview',video['url'],'Nintendo','Original Nintendo audiovisual and thumbnail rights retained'))
poster['kind']='video-poster';poster['story_paragraph']=-1
cover=copy.deepcopy(original['images'][original.get('preferred_image',0)])
cover.pop('story_paragraph',None)
images=[cover]+pictures+[poster]
assert len({i['url'] for i in images})==len(images)
assert len({i.get('source_sha256') for i in pictures})==len(pictures)
native=read(OUT/'museum-direct-native.json')
assert native['native_compatible_avc_aac'] and native['channel']=='Nintendo UK'
result=dict(status='awaiting_final_visual_review',entry_id='daily-09-23',body=[c['body'] for c in chapters],story_headings=[c['title'] for c in chapters],
    images=images,preferred_image=0,videos=[video],chapter_sources=chapters,
    sources=[dict(title='Nintendo company history',url=official,publisher='Nintendo'),
        dict(title='History of Nintendo',url=wiki,publisher='Wikipedia contributors',license='CC BY-SA 4.0',
             attribution='Selected Game Boy and Super Famicom paragraphs reproduced from the cited revision; additional historical chapters adapted with explicit source references.'),
        dict(title='Nintendo Museum exhibits and official tour',url=museum,publisher='Nintendo'),
        dict(title='Nintendo Switch 2 official announcement',url='https://www.nintendo.co.jp/corporate/release/2025/250402.html',publisher='Nintendo')],
    editorial_note='All seven original published English chapters retained verbatim, ordered chronologically. Additional source-linked chapters and distinct photographs added; no main-block artwork is repeated inside the article.',
    original_source_hash=hashlib.sha256(json.dumps(original['body'],ensure_ascii=False).encode()).hexdigest())
(OUT/'nintendo-complete-candidate.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared',len(chapters),'illustrated narrative chapters, one contextual official film, and',len(images),'distinct image URLs.')
