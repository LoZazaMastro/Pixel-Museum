"""Freeze two original Switch exhibits from complete Wikipedia paragraphs.

All illustrations are the publisher's actual, locally decoded original files.
This creates a review candidate only; admission requires a separate peer receipt.
"""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageOps,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'build/research/requested-switch-two'
WIKI=ROOT/'build/research/playhub-semantic-coverage/wiki-clarity'
inventory=json.loads((FOLDER/'source-images.json').read_text(encoding='utf8'))
byname={Path(row['path']).name:row for row in inventory}

def picture(name,title,caption,source,owner,paragraph,cover=False):
    row=byname[name];path=ROOT/row['path']
    with Image.open(path)as image:image.load();width,height=image.size
    assert max(width,height)>=1200
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest==row['sha256']
    return dict(url=row['url'],title=title,caption=caption,source_page=source,
        creator=owner,credit=owner+' / original publisher artwork and screenshots',
        license='Original game, artwork and screenshot rights reserved by the credited publisher, developer and respective artists. No open licence claimed.',
        license_url='',width=width,height=height,recovery_local_source=row['path'],
        story_paragraph=paragraph,cover_art=cover,
        verification=dict(sha256=digest,native_dimensions=[width,height],no_upscale=True),
        visual_review='Original publisher file visually inspected for the original game edition and stated paragraph subject; no platform strip, cover reuse, advertisement or later edition substituted.')

def article(filename,indices,title,year,date,headings,summary,images,release_url,release_locator):
    path=WIKI/filename;doc=json.loads(path.read_text(encoding='utf8'))
    page=next(iter(doc['query']['pages'].values()))
    paragraphs=[line for line in page['extract'].splitlines()if line.strip()]
    body=[paragraphs[index]for index in indices]
    revision=page['revisions'][0]['revid']
    assert len(body)==len(headings)==len([i for i in images if i['story_paragraph']>=0])
    assert len({i['verification']['sha256']for i in images})==len(images)
    assert sorted(i['story_paragraph']for i in images if i['story_paragraph']>=0)==list(range(len(body)))
    return dict(id='wikipedia-'+str(page['pageid']),title=title,subtitle='',year=year,
        date=dict(month=date[0],day=date[1],precision='day',region=''),kind='game',era_id='everywhere',layout='essay',
        summary=summary,body=body,story_headings=headings,images=images,preferred_image=0,videos=[],models=[],related_ids=[],
        tags=['Nintendo Switch'],language='en',explicit_story_media_only=True,editorial_mode='illustrated_reference_story',
        editorial_credit='Full article paragraphs reproduced verbatim from English Wikipedia contributors under CC BY-SA4.0; card headings and captions supplied editorially.',
        attribution='Text: English Wikipedia contributors / CC BY-SA4.0. Original game images: '+images[0]['creator']+'.',
        sources=[dict(title=page['title'],url='https://en.wikipedia.org/w/index.php?oldid='+str(revision),
            publisher='English Wikipedia contributors',license='CC BY-SA4.0',license_url='https://creativecommons.org/licenses/by-sa/4.0/',story_paragraphs=list(range(len(body)))),
            dict(title=title+' / original release listing',url=release_url,publisher='Nintendo',locator=release_locator)],
        provenance=dict(wikipedia_revision=revision,wikipedia_page_id=page['pageid'],
            full_source_line_indices=[page['extract'].splitlines().index(paragraph)for paragraph in body],
            nonempty_source_paragraph_indices=indices,
            wikipedia_source_file=path.relative_to(ROOT).as_posix(),wikipedia_source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            primary_image_inventory=(FOLDER/'source-images.json').relative_to(ROOT).as_posix(),
            original_edition_only=True))

koei='https://www.gamecity.ne.jp/zelda-yakusai/'
calamity_release='https://www.nintendo.com/en-gb/Games/Nintendo-Switch-games/Hyrule-Warriors-Age-of-Calamity-1838129.html'
cowner='Nintendo / Koei Tecmo Games'
calamity=article('Hyrule Warriors- Age of Calamity.json',[0,1,4,5,14],
    'Hyrule Warriors: Age of Calamity',2020,(11,20),
    ['Zelda meets the Warriors battlefield','Hyrule before the Calamity','Fighting across large battlefields','The Sheikah Slate and playable allies','Nintendo and Koei Tecmo collaborate'],
    'A Warriors action game set in the world of Breath of the Wild, with Link, Zelda and their allies fighting across large battlefields.',[
        picture('calamity.jpg','Age of Calamity / original ensemble artwork','Original key artwork for the 2020 Nintendo Switch game.',koei,cowner,-1,True),
        picture('calamity-battle-1.jpg','Hyrule Castle','The castle and surrounding Hyrule landscape in the original publisher screenshot.',koei+'feature/',cowner,0),
        picture('calamity-battle-4.jpg','Link and Zelda in a story scene','Link and Zelda in an original Age of Calamity story scene.',koei+'feature/',cowner,1),
        picture('HWAoC_Overview_FftA_01.jpg','Link fights a group of enemies','Link sends a group of enemies into the air during a large-scale battle.',calamity_release,cowner,2),
        picture('HWAoC_Overview_FftA_02.jpg','Zelda uses the Sheikah Slate','Zelda manipulates a metal block with the Sheikah Slate in battle.',calamity_release,cowner,3),
        picture('calamity-link.png','Link / original Age of Calamity character artwork','Link in the visual style shared with Breath of the Wild, in original Age of Calamity character artwork.',koei+'world/',cowner,4)],
    calamity_release,'Release date20/11/2020; original Nintendo Switch edition.')

kirby_release='https://www.nintendo.com/en-gb/Games/Nintendo-Switch-games/Kirby-and-the-Forgotten-Land-2045110.html'
kirby_us='https://www.nintendo.com/us/store/products/kirby-and-the-forgotten-land-switch/'
kowner='HAL Laboratory / Nintendo'
kirby=article('Kirby and the Forgotten Land.json',[0,4,8,18],
    'Kirby and the Forgotten Land',2022,(3,25),
    ['Kirby in a three-dimensional world','Copy abilities and Mouthful Mode','An unfamiliar world of ruins','Making attacks readable in 3D'],
    'Kirby explores a three-dimensional world, rescues Waddle Dees and uses copy abilities and Mouthful Mode to overcome its obstacles.',[
        picture('kirby-desktop.jpg','Kirby and the Forgotten Land / original artwork','Original 2022 publisher artwork, without platform branding or later-edition labels.','https://www.nintendo.com/jp/switch/arzga/',kowner,-1,True),
        picture('kirby-us-master-01.bin','Kirby at Wondaria','Kirby explores the abandoned amusement park in the original 2022 Nintendo Switch game.',kirby_us,kowner,0),
        picture('kirby-us-master-02.bin','The Drill copy ability','Kirby uses the Drill ability on a beach in the original publisher screenshot.',kirby_us,kowner,1),
        picture('kirby-us-master-06.bin','A ruined city reclaimed by the environment','An original screenshot of the deserted city landscape in the forgotten land.',kirby_us,kowner,2),
        picture('kirby-us-master-04.bin','Facing Gorimondo','Kirby faces Gorimondo in a three-dimensional boss arena.',kirby_us,kowner,3)],
    kirby_release,'Release date25/03/2022; original Nintendo Switch edition, not the Switch2 Star-Crossed World campaign.')

output=dict(schema_version=1,publication_status='awaiting_independent_review',entries=[calamity,kirby],
    review_scope='Nine complete English Wikipedia paragraphs and eleven unique original publisher images. Cover artwork is separate from each narrative illustration; original2020/2022 releases only. No weak town image, promotional demo banner or later-edition screenshot admitted.')
candidate=FOLDER/'candidate.json'
candidate.write_text(json.dumps(output,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
for entry in output['entries']:
    canvas=Image.new('RGB',(1000,320*((len(entry['images'])+1)//2)),(24,24,24));draw=ImageDraw.Draw(canvas)
    for n,record in enumerate(entry['images']):
        im=Image.open(ROOT/record['recovery_local_source']).convert('RGBA')
        thumb=ImageOps.contain(im,(490,265));base=Image.new('RGBA',thumb.size,(65,65,65,255));base.alpha_composite(thumb)
        x=(n%2)*500;y=(n//2)*320;canvas.paste(base.convert('RGB'),(x,y));draw.text((x+5,y+270),str(record['story_paragraph'])+' '+record['title'],fill='white')
    canvas.save(FOLDER/(entry['id']+'-review.jpg'),quality=92)
print(json.dumps(dict(candidate=candidate.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),entries=len(output['entries']),paragraphs=sum(len(e['body'])for e in output['entries']),images=sum(len(e['images'])for e in output['entries']))))
