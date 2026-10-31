"""Draft a sourced creator profile with specific, distinct contemporary artefacts."""
from pathlib import Path
import copy,hashlib,json,urllib.request
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/yu-suzuki-complete-story'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
catalog=read(ROOT/'content/catalog.json')
original=next(e for e in catalog['entries'] if e['id']=='workbook-06-10-yu-suzuki')
if not (OUT/'original-story.json').exists():
    (OUT/'original-story.json').write_text(json.dumps(original,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
artefacts={e['title']:e for e in read(OUT/'existing-artefacts.json')}
chapters=[
    ('1983 / From programmer to arcade designer',
     'Yu Suzuki joined Sega in 1983 after studying electronic science at Okayama University of Science. Hang-On and Space Harrier followed in 1985. These were games whose machines mattered as much as their screens: motorcycle controls, moving cabinets and rapidly scaled scenery made movement something a player could feel. Space Harrier placed that sense of speed in a strange fantasy landscape rather than on a recognisable road.',
     'Space Harrier',0,['ysnet','suzuki-reference']),
    ('1986 / A driving game with a holiday in mind',
     'Out Run offered a different kind of journey. Suzuki researched European roads, and the game turned driving into a succession of changing landscapes and branching routes. The player raced a clock rather than a championship table. Hiroshi Kawaguchi\'s music was part of that identity: choosing a radio track before setting off helped give the drive its relaxed, aspirational character. The route and the soundtrack made the same car feel like a personal escape.',
     'Out Run',0,['outrun-reference']),
    ('1993 / From a pit crew to two fighters',
     'In Sega\'s twentieth-anniversary interview, Suzuki traced Virtua Fighter back to the pit crew in Virtua Racing. After rendering cars, he wanted to animate a human body with many connected joints. The hardware could not handle a whole football or rugby team, so he narrowed the problem to two people. That technical constraint met the arcade market\'s interest in fighting games. Virtua Fighter emerged from both questions, rather than simply putting polygons over an existing formula.',
     'Virtua Fighter',1,['sega-interview']),
    ('1999 / Giving everyday life a timetable',
     'Shenmue moved Suzuki\'s work from the short arcade session into a neighbourhood the player could inhabit. Ryo Hazuki investigated his father\'s murder in Yokosuka, but progress also involved waiting for a shop to open, asking residents for directions or earning money at the harbour. Daily schedules and changing weather helped the setting feel independent of the investigation. Martial-arts fights and timed action sequences shared space with ordinary routines.',
     'Shenmue',1,['shenmue-reference']),
    ('2001 / The journey reaches Hong Kong',
     'Shenmue II continued Ryo\'s search in Hong Kong before taking him to Kowloon and Guilin. The move widened the first game\'s scale: crowded streets, unfamiliar districts and new companions replaced the familiarity of his home neighbourhood. The story still depended on conversations, work, exploration and martial arts. Its larger setting also made navigation part of the experience; learning how to find someone was a task in its own right.',
     'Shenmue II',1,['shenmue2-reference']),
    ('2008–2019 / Building YS Net and returning to Shenmue',
     'Suzuki founded YS Net in 2008. In 2015, a Kickstarter campaign gave Shenmue III a route back into production after the long gap since the second game. It was released in 2019, continuing Ryo and Shenhua\'s story in rural China. The circumstances were different from Sega\'s Dreamcast era: a new studio and a community of backers helped carry the continuation. Suzuki also received the Golden Joystick Lifetime Achievement award that year.',
     None,None,['ysnet','shenmue3-store']),
]
sources=[
    dict(id='ysnet',title='Yu Suzuki — official YS Net biography',url='https://www.ysnet.games/en/yu-suzuki',publisher='YS Net'),
    dict(id='sega-interview',title='Virtua Fighter twentieth anniversary — Yu Suzuki interview, 11 December 2013',url='https://vf20th.sega.jp/interview131211.html',publisher='Sega'),
    dict(id='suzuki-reference',title='Yu Suzuki',url='https://en.wikipedia.org/wiki/Yu_Suzuki',publisher='Wikipedia contributors',license='CC BY-SA 4.0'),
    dict(id='outrun-reference',title='Out Run — development and soundtrack',url='https://en.wikipedia.org/wiki/Out_Run',publisher='Wikipedia contributors',license='CC BY-SA 4.0'),
    dict(id='shenmue-reference',title='Shenmue — setting and gameplay',url='https://en.wikipedia.org/wiki/Shenmue_(video_game)',publisher='Wikipedia contributors',license='CC BY-SA 4.0'),
    dict(id='shenmue2-reference',title='Shenmue II — plot and gameplay',url='https://en.wikipedia.org/wiki/Shenmue_II',publisher='Wikipedia contributors',license='CC BY-SA 4.0'),
    dict(id='shenmue3-store',title='Shenmue III — developer-published game description and screenshots',url='https://store.steampowered.com/app/878670/Shenmue_III/',publisher='YS Net / ININ',note='Steam-specific 2020 availability is not used as the original 2019 release date.'),
]
images=[copy.deepcopy(original['images'][original.get('preferred_image',0)])]
images[0].pop('story_paragraph',None)
mapping=[]
for n,(heading,body,title,index,citations) in enumerate(chapters):
    if title:
        photo=copy.deepcopy(artefacts[title]['images'][index])
        photo.pop('cover_art',None)
    else:
        store=read(OUT/'shenmue3-steam-actual.json')['878670']['data']
        url=store['screenshots'][0]['path_full'];local=OUT/'shenmue3-original-game.jpg'
        if not local.exists():local.write_bytes(urllib.request.urlopen(url,timeout=30).read())
        width,height=Image.open(local).size
        assert (width,height)==(1920,1080)
        photo=dict(url=url,title='Shenmue III — original game screenshot',width=width,height=height,
            source_page='https://store.steampowered.com/app/878670/Shenmue_III/',credit='YS Net / original game publisher and rights holders',
            license='Original game artwork rights retained; developer-published promotional screenshot.',
            recovery_local_source=str(local.relative_to(ROOT)).replace('\\','/'))
    photo['story_paragraph']=n;images.append(photo)
    if title=='Shenmue II':
        photo['title']='Shenmue II — an interior conversation in the 2018 PC edition'
        photo['caption']='Shenmue II: an interior conversation in the 2018 PC edition.'
    mapping.append(dict(index=n,heading=heading,source_ids=citations,image_url=photo['url']))
assert len({i['url'] for i in images})==7
native={r['id']:r['metadata'] for r in read(OUT/'three-film-native-review.json') if r.get('metadata')}
film_posters=[copy.deepcopy(artefacts['Shenmue']['images'][0])]
store=read(OUT/'shenmue3-steam-actual.json')['878670']['data']
poster_url=store['screenshots'][1]['path_full'];poster_path=OUT/'shenmue3-interview-context.jpg'
if not poster_path.exists():poster_path.write_bytes(urllib.request.urlopen(poster_url,timeout=30).read())
width,height=Image.open(poster_path).size
assert (width,height)==(1920,1080)
film_posters.append(dict(url=poster_url,title='Shenmue III — developer-published game image accompanying the interview',width=width,height=height,
    source_page='https://store.steampowered.com/app/878670/Shenmue_III/',credit='YS Net / original game publisher and rights holders',
    license='Original game artwork rights retained; developer-published promotional screenshot.',
    recovery_local_source=str(poster_path.relative_to(ROOT)).replace('\\','/')))
videos=[]
for video_id,paragraph,title,caption,poster in zip(
        ['3F0RcTBuKHc','VGhIyhUyEo8'],[3,5],
        ['Shenmue at GDC 2000','Yu Suzuki in conversation with Game Informer'],
        ['An archived GDC 2000 conversation about Shenmue, presented by GDC. A contemporary conference record from the original game\'s period.',
         'Game Informer interviews Yu Suzuki during its Shenmue III coverage. A conversation with the creator rather than a promotional trailer.'],film_posters):
    meta=native[video_id]
    assert meta['native_compatible_avc_aac'] and meta['avc_format_count']>0 and meta['aac_format_count']>0
    poster.pop('story_paragraph',None);poster.pop('cover_art',None);images.append(poster)
    videos.append(dict(youtube_id=video_id,url='https://www.youtube.com/watch?v='+video_id,title=title,
        original_publication_title=meta['title'],creator=meta['channel'],source_page='https://www.youtube.com/watch?v='+video_id,
        caption=caption,poster_url=poster['url'],story_paragraph=paragraph,
        credit=meta['channel']+' / original publication',license='Original creator and game-publisher rights retained; streamed from the original publication.',
        verification=meta,native_metadata_receipt='build/research/video-discovery/video-'+video_id+'.json',playback_verified_on_ps5=False))
assert len({i['url'] for i in images})==9
candidate=dict(status='awaiting_independent_editorial_and_image_review',entry_id=original['id'],
    body=[c[1] for c in chapters],story_headings=[c[0] for c in chapters],images=images,preferred_image=0,videos=videos,
    sources=sources,chapter_sources=mapping,
    summary='Yu Suzuki connected arcade hardware, character animation and the everyday rhythms of Shenmue. His career spans Sega\'s simulation cabinets, Virtua Fighter and YS Net.',
    source_preservation='The previous four paragraphs remain frozen in original-story.json; the repetitive template draft is not represented as original archival prose.',
    video_review='The old 320x240 interview is superseded by the GDC archive (720p native AVC) and Game Informer interview (1080p native AVC). Contextual game artwork serves as their poster, not as an asserted frame from the interview. YouTube maxres thumbnails returned404; they were not upscaled or fabricated.')
(OUT/'candidate.json').write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Draft ready: six sourced chapters, nine distinct images and two contextual archive/developer films. Independent editorial and final-image review required.')
