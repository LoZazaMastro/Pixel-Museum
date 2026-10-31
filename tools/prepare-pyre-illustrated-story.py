"""Build a source-bound complete illustrated Pyre article for separate review."""
from pathlib import Path
import copy,hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/pyre-illustrated-story'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
page=next(iter(read(OUT/'wikipedia.json')['query']['pages'].values()))
steam=read(OUT/'steam.json')['462770']['data']
assert page['pageid']==50237418 and steam['name']=='Pyre'
lines=page['extract'].splitlines();selected=[0,4,5,10]
body=[lines[n]for n in selected]
inventory=read(OUT/'images-inventory.json')
def record(row,caption,paragraph,title):
    p=ROOT/row['path']
    with Image.open(p)as im:im.load();assert im.size==(row['width'],row['height'])
    assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
    return dict(url=row['url'],title=title,caption=caption,source_page=row.get('source_page','https://store.steampowered.com/app/462770/'),
        creator='Supergiant Games',credit='Supergiant Games / original publisher artwork and screenshots',
        license='Original game artwork, screenshot and illustration rights retained by Supergiant Games and the respective artists; not an open licence.',
        license_url='',width=row['width'],height=row['height'],recovery_local_source=row['path'],
        story_paragraph=paragraph,cover_art=paragraph<0,verification=dict(sha256=row['sha256'],no_upscale=True))
hero=read(OUT/'Pyre_4K_01.png.receipt.json')
room=read(OUT/'Pyre_4K.jpg.receipt.json')
find=lambda name:next(r for r in inventory if Path(r['path']).name==name)
images=[
 record(hero,'Original Pyre ensemble key artwork published by Supergiant Games.',-1,'Pyre / original publisher key artwork'),
 record(room,'A hand-drawn character and the interior of the exiles’ wagon, in the publisher’s original 4K screenshot.',0,'The exiles’ wagon'),
 record(find('screen-6.jpg'),'A conversation with the party at camp, showing the character portraits and on-screen narrative.',1,'Talking with the exiles'),
 record(find('screen-7.jpg'),'Opposing teams face one another across a Rite arena, with the two pyres at opposite ends.',2,'A Rite between two teams'),
 record(find('screen-9.jpg'),'The illustrated overworld presents places along the exiles’ journey between Rites.',3,'Choosing a route through the Downside')]
assert len({i['url']for i in images})==5
poster=record(find('screen-10.jpg'),'Original publisher gameplay image accompanying the launch film; not a claim that this is an extracted film frame.',-1,'Pyre / gameplay image for the launch film')
poster['cover_art']=False;poster['poster_only']=True;images.append(poster)
native_path='build/research/video-discovery/video-9jBbq6c9EEQ.json'
native=read(ROOT/native_path)
assert native['native_compatible_avc_aac'] and native['id']=='9jBbq6c9EEQ'
film=dict(youtube_id='9jBbq6c9EEQ',url='https://www.youtube.com/watch?v=9jBbq6c9EEQ',title='Pyre — Launch Trailer',
    creator='Supergiant Games',source_page='https://www.youtube.com/watch?v=9jBbq6c9EEQ',
    caption='Supergiant Games introduces the exiles, their journey and the Rites in the original English launch film.',
    poster_url=poster['url'],story_paragraph=2,credit='Supergiant Games / original publisher film',
    license='Original film, music and game rights retained by the publisher and credited artists; streamed from the publisher publication.',
    native_metadata_receipt=native_path,verification=native,playback_verified_on_ps5=False)
rev=page['revisions'][0]['revid']
entry=dict(id='wikipedia-50237418',title='Pyre',subtitle='A journey shared by exiles',year=2017,date=dict(month=7,day=25,precision='day',region=''),kind='game',era_id='everywhere',layout='essay',
    summary='An action role-playing game from Supergiant Games that combines a journey through exile with team-based Rites.',
    body=body,story_headings=['Supergiant’s third game','Reading the journey','The Rites','Designing around defeat'],images=images,preferred_image=0,videos=[film],models=[],related_ids=[],
    tags=['Role-playing','Sports','Narrative','Supergiant Games'],explicit_story_media_only=True,editorial_mode='illustrated_reference_story',language='en',
    editorial_credit='Article paragraphs reproduced from English Wikipedia contributors / CC BY-SA4.0; headings and image captions supplied editorially.',
    attribution='Text: English Wikipedia contributors / Creative Commons Attribution-ShareAlike4.0. Images: Supergiant Games and respective artists.',
    sources=[dict(title='Pyre (video game)',url=f'https://en.wikipedia.org/w/index.php?oldid={rev}',publisher='English Wikipedia contributors',license='CC BY-SA4.0',license_url='https://creativecommons.org/licenses/by-sa/4.0/',story_paragraphs=list(range(4))),
        dict(title='Pyre / original game and media',url='https://www.supergiantgames.com/games/pyre/',publisher='Supergiant Games'),
        dict(title='Pyre / publisher Steam listing',url='https://store.steampowered.com/app/462770/',publisher='Supergiant Games / Steam',locator='Release date25July2017 and original publisher full-size screenshots')],
    provenance=dict(wikipedia_revision=rev,wikipedia_page_id=50237418,full_source_line_indices=selected,wikipedia_source_sha256=hashlib.sha256((OUT/'wikipedia.json').read_bytes()).hexdigest(),steam_app_id=462770,publisher_media_visually_reviewed=True))
candidate=dict(schema_version=1,publication_status='awaiting_independent_review',entries=[entry],review_scope='Four complete English Wikipedia paragraphs, four distinct original publisher narrative images, separate4K unbranded key-art cover and English publisher launch film with distinct gameplay poster. No thumbnail upscale, repeated cover, invented development-concept photograph or wrong game edition.')
(OUT/'candidate.json').write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Pyre:',len(body),'full paragraphs,',len(images),'publisher images; candidateSHA',hashlib.sha256((OUT/'candidate.json').read_bytes()).hexdigest())
