"""Separate Space Race's existing development/history prose using its period publisher artifact."""
from pathlib import Path
import copy,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
gran=sys.argv[1:]==['gran-trak10']
base=ROOT/'build/research'/('gran-trak10-existing-prose-period-flyer'if gran else'space-race-existing-prose-period-flyer')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=next(e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']if e['id']==('wikipedia-3426165'if gran else'wikipedia-6336052'))
new=copy.deepcopy(old)
assert len(old['body'])==3 and len(old['images'])==2
new['images'][0]['story_paragraph']=-1;new['explicit_story_media_only']=True
path=base/'original-flyer-back.jpg';source='https://flyers.arcade-museum.com/videogames/show/5119'
if gran:source='https://flyers.arcade-museum.com/videogames/show/434'
new['images'].append(dict(url='https://flyers.arcade-museum.com/videogame-flyers/5/space-race-05112-02.jpg',source_page=source,
    title='Atari presents Space Race to arcade operators',
    caption='Back of an original 1973 Atari Space Race sales flyer, showing the conventional cabinet dimensions, game timing and operator sales pitch. It is a contemporary publisher document, not an image of the rare fiberglass cabinet.',
    creator='Atari',credit='Atari / The Arcade Flyer Archive; scan contributed by Dphower',
    license='Original Atari advertisement and illustration rights retained; no open licence asserted.',
    width=850,height=1100,story_paragraph=1,recovery_local_source=path.relative_to(ROOT).as_posix(),
    verification=dict(sha256=sha(path),native_dimensions=[850,1100],processing='Original published full-page JPEG retained without crop, enlargement or retouch.')))
assert new['body']==old['body'] and new.get('story_headings')==old.get('story_headings')
paths=[base/'flyer-original-source.html',base/'source-downloads.json',path]
doc=dict(status='CANDIDATE_PENDING_INDEPENDENT_PEER',rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
    source_files={p.relative_to(ROOT).as_posix():sha(p)for p in paths},expected_main_paragraph_groups=[[0],[1,2]],
    scope='All three existing paragraphs remain complete and in order. Exclusive cover and first gameplay film preserved; distinct original 1973 publisher flyer illustrates the development and commercial-history chapter.',
    quality_limits=['Native 850 by 1100 period scan; no artificial enlargement.',
        'The cabinet diagram is the conventional cabinet, not misidentified as Faraco\'s rare fiberglass version.',
        'No new text, film request, soundtrack or experience added.'])
out=base/'three-existing-space-race-paragraphs-two-period-scenes-candidate.json'
if gran:
    item=new['images'][-1]
    item.update(url='https://flyers.arcade-museum.com/videogame-flyers/0/gran-trak-10-00435-02.jpg',
        title='The original Gran Trak 10 cabinet and course',height=1109,
        caption='Back of the original 1974 Atari sales flyer, showing the race-course photograph, steering wheel, gear stick, pedals and cabinet dimensions. The page is printed 2/74; it is a period sales document, not a modern recreation or Gran Trak 20.')
    item['verification']['native_dimensions']=[850,1109]
    doc['quality_limits']=['Native 850 by 1109 period scan retained without artificial enlargement.',
        'Original Gran Trak 10, not its two-player sequel or a modern racing cabinet.',
        'Publisher sales material accompanies existing history without introducing unsupported engineering claims.']
    doc['scope']='All three existing Gran Trak 10 paragraphs and headings retained complete and in order. Exclusive cover and existing gameplay film preserved; distinct original publisher back illustrates development and commercial history.'
    out=base/'three-existing-gran-trak10-paragraphs-two-period-scenes-candidate.json'
out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
