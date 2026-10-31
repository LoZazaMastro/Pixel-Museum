"""Prepare bounded, source-backed C64 media associations without editing catalog."""
from pathlib import Path
import copy, hashlib, json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/c64-illustrated-story'
entry = next(e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries'] if e['id']=='commodore-64')
manifest = json.loads((ROOT/'assets/images/manifest.json').read_text(encoding='utf8'))['images']

def picture(name, url, source, title, caption, paragraph, creator, license, **extra):
    p = BASE/name
    with Image.open(p) as im:
        im.load()
        width, height = im.size
    return dict(url=url, source_page=source, title=title, caption=caption,
                creator=creator, credit=creator+' / '+license, license=license,
                width=width, height=height, story_paragraph=paragraph,
                recovery_local_source=p.relative_to(ROOT).as_posix(),
                verification=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                                  visual_review=True, no_generated_enlargement=True), **extra)

main=[]
for index, paragraph in [(1,0),(2,1)]:
    a=copy.deepcopy(entry['images'][index]); a['story_paragraph']=paragraph
    local=ROOT/manifest[a['url']]
    with Image.open(local) as im: a['width'],a['height']=im.size
    a['recovery_local_source']=local.relative_to(ROOT).as_posix()
    a['verification']={'sha256':hashlib.sha256(local.read_bytes()).hexdigest(),'visual_review':True,'no_generated_enlargement':True}
    main.append(a)

portrait=picture('Rob_Hubbard.jpg','https://upload.wikimedia.org/wikipedia/commons/1/1e/Rob_Hubbard.jpg',
    'https://commons.wikimedia.org/wiki/File:Rob_Hubbard.jpg','Rob Hubbard at X-Party, 2023',
    'A later portrait of the composer, photographed at X-Party in 2023; not a 1980s development-session photograph.',2,
    'C64Scener','CC BY-SA 4.0',license_url='https://creativecommons.org/licenses/by-sa/4.0/')
album=picture('back-in-time3-booklet-front.jpg',
    'https://archive.org/download/back-in-time-3/Back%20in%20Time%203/Extras/BIT3%20Booklet%20-%201.jpg',
    'https://remix64.com/albums/back-in-time-3/','Back in Time 3: A Space Odyssey',
    'The actual 2001 album booklet front. The collection includes War, arranged by Rob Hubbard and Steve Scherer. It is not the later 8-Bit Symphony box.',3,
    'Mat Recardo, Arvid Weber and Steve Barrett / C64Audio.com',
    'Original artwork and album rights retained; no open licence claimed.',
    archive_source='https://archive.org/details/back-in-time-3',
    source_relationship='The album page links to this public archive as its album download.')

sid=[picture('SID_chips.jpg','https://upload.wikimedia.org/wikipedia/commons/a/a7/SID_chips.jpg',
    'https://commons.wikimedia.org/wiki/File:SID_chips.jpg','Two revisions of the SID sound chip',
    'MOS 6581 and 8580 R5 chips photographed by Taras Young. These later production examples illustrate the sound hardware, not the original prototype.',0,
    'Taras Young','CC BY-SA 4.0',license_url='https://creativecommons.org/licenses/by-sa/4.0/')]
manual='https://csclub.uwaterloo.ca/~pbarfuss/C64_Programmers_Reference_Guide.pdf'
for pdf_page, printed, paragraph, title in [(215,196,1,'The envelope generator: attack, decay, sustain and release'),
    (204,185,2,'A BASIC program plays a melody'),(211,192,3,'Changing waveforms in the sound program')]:
    sid.append(picture(f'manual-page-{pdf_page}.png',manual+f'#page={pdf_page}',manual,title,
        f'Commodore 64 Programmer\'s Reference Guide, printed page {printed}. A rendered excerpt of the original programming manual; original print and raster detail retained.',
        paragraph,'Commodore Business Machines / Commodore 64 Programmer\'s Reference Guide',
        'Copyright Commodore Business Machines, 1982; no open licence claimed.',
        source_pdf_sha256='2443142849c62022d1b6c67dc87fdf71997541810f7139a477993fe617d7693d',
        source_pdf_page=pdf_page,printed_page=printed))

out={'schema_version':1,'publication_status':'independent_review_pending',
     'scope':'Eight reviewed paragraph associations: two existing main photographs, two Hubbard images and four distinct SID images. No prose, cover, date, film or loading-screen feature changed.',
     'entry_id':'commodore-64','main_images':main,
     'feature_images':[
         {'feature_id':'feature-rob-hubbard-c64','operation':'append','images':[portrait,album]},
         {'feature_id':'feature-c64-sid-instrument','operation':'replace','images':sid}],
     'duplicate_removal':'Replace the SID feature photograph already used in the Hubbard feature with a different, independently attributed chip photograph.'}
p=BASE/'eight-paragraph-media-candidate.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(p.relative_to(ROOT),hashlib.sha256(p.read_bytes()).hexdigest())
