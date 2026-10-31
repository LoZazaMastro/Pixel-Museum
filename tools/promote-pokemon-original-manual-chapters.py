"""Four original, distinct trainer-guide pages for four specific design topics."""
from pathlib import Path
from urllib.parse import quote
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'build/research/playhub-semantic-coverage/native-images/pokemon-original-manual'
path=ROOT/'content/expansion/playhub-theme-semantic-restorations.json'
doc=json.loads(path.read_text(encoding='utf8'))
row=next(r for r in doc['restorations']if r['theme_id']=='pokemon')
manual='https://www.videogamemanual.com/gameboy/'+quote('Pokemon - Red Version (USA).pdf')
items=[(0,31,'Keeping a team and changing its nicknames','Original1998US trainer guide, printed page29: nickname changes and stopping evolution.'),
       (2,16,'Pallet Town: the journey begins at home','Original1998US trainer guide, printed page14: home, rival and Professor Oak\'s laboratory.'),
       (3,25,'Pikachu in the original trainer guide','Original1998US trainer guide, printed page23: Pikachu artwork and the Game Boy party screen. This is not a photograph of its designers.'),
       (4,17,'Choosing a first partner','Original1998US trainer guide, printed page15: Professor Oak, the three starters and advice for beginning players.')]
records=[]
for index,page,title,caption in items:
    local=folder/('page%02d-Im0.jpg'%page)
    with Image.open(local)as im:im.load();assert im.size==(1920,1920)
    image=dict(url=manual+'#page='+str(page)+'&embedded=Im0.jpg',source_page=manual,
        title='Pok\u00e9mon Red and Blue: '+title,caption=caption,
        creator='Nintendo / Game Freak / Creatures',
        credit='Nintendo / Game Freak / Creatures; original1998US trainer guide preserved by Video Game Manual',
        license='Original manual, game artwork and publisher copyright retained. No open licence claimed.',
        width=1920,height=1920,recovery_local_source=local.relative_to(ROOT).as_posix(),
        verification=dict(sha256=hashlib.sha256(local.read_bytes()).hexdigest(),native_dimensions=[1920,1920],no_upscale=True),
        identity_evidence=dict(game='Pok\u00e9mon Red and Blue',artifact='Original US1998printed trainer guide',
                               first_game_release='Japanese Red and Green1996',pdf_page=page,printed_page=page-2),
        visual_review='Full native JPEG actually viewed; exact original manual page and chapter relationship also approved independently by parent reviewer on22October2026.')
    chapter=next(c for c in row['chapters']if c['source_chapter_index']==index)
    chapter['images']=[image];chapter['existing_image_urls']=[]
    chapter['illustration_status']='reviewed_original_manual_page_1998_us_context_explicit'
    records.append(dict(source_chapter_index=index,image=image))
if manual not in row['historical_sources']:row['historical_sources'].append(manual)
path.write_text(json.dumps(doc,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
(folder/'four-original-manual-pages-review.json').write_text(json.dumps(dict(status='PASS',
    scope='Original embedded1920x1920JPEG scans, extracted directly without page rendering or enlargement; old print texture and original pixel graphics retained.',
    manual_url=manual,manual_sha256=hashlib.sha256((folder/'pokemon-red-original-us-manual.pdf').read_bytes()).hexdigest(),
    records=records,prose_unchanged=True),ensure_ascii=True,indent=2)+'\n',encoding='utf8')
print('Four Pokemon source chapters illustrated with distinct original manual pages.')
