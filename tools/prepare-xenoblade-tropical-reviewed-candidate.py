"""Prepare original2017/2014 illustrated exhibits; never publish before peer QA."""
from pathlib import Path
import copy,hashlib,json
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'build/research/requested-xenoblade-tropical'
inventory=json.loads((FOLDER/'primary-image-inventory.json').read_text(encoding='utf8'))
rows={Path(r['path']).name:r for r in inventory if 'path'in r}
boxes=json.loads((FOLDER/'tropical-box-inventory.json').read_text(encoding='utf8'))
box=next(r for r in boxes['images']if r.get('width')==1787 and r.get('height')==2521)
rows[Path(box['path']).name]=box

def picture(name,title,caption,source,owner,paragraph):
    row=rows[name];path=ROOT/row['path']
    with Image.open(path)as image:image.load();w,h=image.size
    assert min(w,h)>=600 and max(w,h)>=1200
    digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest==row['sha256']
    return dict(url=row['url'],title=title,caption=caption,source_page=source,creator=owner,
        credit=owner+' / original game artwork and screenshots',
        license='Original game, artwork and screenshot rights retained by the credited developer, publisher and respective artists; no open licence claimed.',
        license_url='',width=w,height=h,story_paragraph=paragraph,cover_art=paragraph<0,
        recovery_local_source=row['path'],verification=dict(sha256=digest,native_dimensions=[w,h],no_upscale=True))

def build(title,filename,indices,headings,year,date,summary,images,release_url,release_note,video_key,video_paragraph):
    path=FOLDER/filename;page=next(iter(json.loads(path.read_text(encoding='utf8'))['query']['pages'].values()))
    lines=page['extract'].splitlines();body=[lines[index]for index in indices]
    assert all(len(b.split())>=50 for b in body)
    revision=page['revisions'][0]['revid'];film=json.loads((FOLDER/(video_key+'-verified-video.json')).read_text(encoding='utf8'))
    video=copy.deepcopy(film['video']);video.update(source_page=video['url'],story_paragraph=video_paragraph,
        caption='Nintendo presents the original game and its systems.'if video_key=='xeno2'else 'Retro Studios discusses the original Wii U game in Nintendo\u2019s Developer Direct.',
        credit='Nintendo / original official English-language presentation',
        license='Original film, game and music rights retained by Nintendo and the respective credited creators; streamed from the publisher publication.',
        native_metadata_receipt='build/research/video-discovery/video-'+video['youtube_id']+'.json',verification=film['metadata'],
        playback_verified_on_ps5=False,poster_url=film['poster']['url'])
    assert film['metadata']['native_compatible_avc_aac']and film['metadata']['channel']=='Nintendo of America'
    images.append(film['poster'])
    assert len({i['verification']['sha256']for i in images})==len(images)
    assert sorted(i['story_paragraph']for i in images if i['story_paragraph']>=0)==list(range(len(body)))
    return dict(id='wikipedia-'+str(page['pageid']),title=title,subtitle='',year=year,
        date=dict(month=date[0],day=date[1],precision='day',region=''),kind='game',era_id='everywhere',layout='essay',summary=summary,
        body=body,story_headings=headings,images=images,preferred_image=0,videos=[video],models=[],related_ids=[],tags=[],language='en',
        explicit_story_media_only=True,editorial_mode='illustrated_reference_story',
        editorial_credit='Complete English Wikipedia paragraphs reproduced under CC BY-SA4.0; headings and captions supplied editorially.',
        sources=[dict(title=page['title'],url='https://en.wikipedia.org/w/index.php?oldid='+str(revision),publisher='English Wikipedia contributors',
            license='CC BY-SA4.0',license_url='https://creativecommons.org/licenses/by-sa/4.0/',story_paragraphs=list(range(len(body)))),
            dict(title=title+' / original Nintendo release listing',url=release_url,publisher='Nintendo',locator=release_note)],
        provenance=dict(wikipedia_revision=revision,wikipedia_page_id=page['pageid'],full_source_line_indices=indices,
            wikipedia_source_file=path.relative_to(ROOT).as_posix(),wikipedia_source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            primary_image_inventory=(FOLDER/'primary-image-inventory.json').relative_to(ROOT).as_posix(),original_edition_only=True))

xeno_url='https://www.nintendo.com/en-gb/Games/Nintendo-Switch-games/Xenoblade-Chronicles-2-1233955.html'
owner='Nintendo / Monolith Soft'
xeno=build('Xenoblade Chronicles 2','Xenoblade-Chronicles-2-full.json',[0,1,7,12],
    ['A story-driven role-playing game','Rex, Pyra and the Titans of Alrest','Travelling between living worlds','Arts, Blades and combat combinations'],2017,(12,1),
    'Rex and Pyra travel through Alrest, a world of living Titans, in Monolith Soft\u2019s story-driven role-playing game.',[
        picture('xeno2-hero.jpg','Xenoblade Chronicles 2 / original key artwork','Original 2017 publisher key artwork.',xeno_url,owner,-1),
        picture('xeno2-uk-NSwitch_XenobladeChronicles2_09.jpg','Rex in an original game scene','Rex in an original2017 Nintendo Switch scene.',xeno_url,owner,0),
        picture('xeno2-uk-NSwitch_XenobladeChronicles2_10.jpg','A settlement on a Titan','People live on and travel between the Titans of Alrest.',xeno_url,owner,1),
        picture('xeno2-uk-NSwitch_XenobladeChronicles2_03_enGB.jpg','Crossing Greatspine Boundary','The party crosses a bridge in an original exploration screenshot.',xeno_url,owner,2),
        picture('xeno2-uk-NSwitch_XenobladeChronicles2_01_enGB.jpg','Arts in a real-time battle','The battle interface displays Arts and party actions in the original game.',xeno_url,owner,3)],
    xeno_url,'Original Nintendo Switch release01/12/2017.','xeno2',2)

tropical_url='https://www.nintendo.com/en-gb/Games/Wii-U-games/Donkey-Kong-Country-Tropical-Freeze-765383.html'
owner='Nintendo / Retro Studios'
cover=picture(Path(box['path']).name,'Donkey Kong Country: Tropical Freeze / original Wii U cover',
    'Original North American Wii U packaging for the2014 game, without Nintendo Selects branding.',
    'https://gamesdb.launchbox-app.com/games/details/'+box['DatabaseID'],owner,-1)
cover['credit']='Nintendo / Retro Studios / original Wii U packaging scan preserved by LaunchBox Games Database'
cover['identity_evidence']=dict(game='Donkey Kong Country: Tropical Freeze',platform='Nintendo Wii U',release_year=2014,
    database_id=box['DatabaseID'],region=box.get('Region'),image_type='Box - Front')
tropical=build('Donkey Kong Country: Tropical Freeze','Donkey-Kong-Country-Tropical-Freeze-full.json',[0,6,7,26],
    ['Retro Studios returns to Donkey Kong Country','Partners change the platforming','Funky\u2019s shop and replay challenges','Building levels around a moving camera'],2014,(2,13),
    'Donkey Kong and his partners cross islands reclaimed by the Snowmads, combining precise platforming with distinct companion abilities.',[
        cover,
        picture('tropical-uk-WiiU_DonkeyKongCountryTropicalFreeze_19.jpg','Donkey Kong Island under the Snowmads','An original Wii U screenshot of the frozen island.',tropical_url,owner,0),
        picture('tropical-uk-WiiU_DonkeyKongCountryTropicalFreeze_12.jpg','Platforming with the Kongs','An original2014 Wii U stage with platforms, enemies and moving obstacles.',tropical_url,owner,1),
        picture('tropical-uk-WiiU_DonkeyKongCountryTropicalFreeze_11.jpg','Funky Kong\u2019s item shop','Funky sells support items in the original Wii U game.',tropical_url,owner,2),
        picture('tropical-uk-WiiU_DonkeyKongCountryTropicalFreeze_18.jpg','A mine-cart route through a three-dimensional landscape','Original Wii U mine-cart gameplay shows the depth and camera perspectives discussed in the development account.',tropical_url,owner,3)],
    'https://www.nintendo.co.jp/wiiu/arkj/detail/index.html','Original Japanese Wii U release2014.2.13; one game entry, not a separate2018 Switch-port stop.','tropical',3)

candidate=FOLDER/'candidate.json';doc=dict(schema_version=1,publication_status='awaiting_independent_review',entries=[xeno,tropical],
    review_scope='Two missing original games; eight full Wikipedia paragraphs with native publisher narrative screenshots and distinct original covers. Original2014 Wii U Tropical Freeze, not FunkyMode2018; original2017 Xenoblade2, not Torna or a later port. Two official English Nintendo presentations with positive native AVC/AAC metadata, no PS5 playback claim.')
candidate.write_text(json.dumps(doc,indent=2,ensure_ascii=True)+'\n',encoding='utf8')
for entry in doc['entries']:
    canvas=Image.new('RGB',(1200,350*((len(entry['images'])+1)//2)),(25,25,25));draw=ImageDraw.Draw(canvas)
    for n,image in enumerate(entry['images']):
        im=Image.open(ROOT/image['recovery_local_source']).convert('RGB');thumbnail=ImageOps.contain(im,(590,300));x=n%2*600;y=n//2*350
        canvas.paste(thumbnail,(x,y));draw.text((x+5,y+305),str(image['story_paragraph'])+' '+image['title'],fill='white')
    canvas.save(FOLDER/(entry['id']+'-review.jpg'),quality=93)
print(json.dumps(dict(candidate=candidate.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),entries=2,paragraphs=8,images=sum(len(e['images'])for e in doc['entries']))))
