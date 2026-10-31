"""Replace a modern Formula One mod film with the actual 1976 machine's artifacts."""
from pathlib import Path
import copy,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/f1-1976-existing-prose-original-machine'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
entries=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']
old=next(e for e in entries if e['id']=='wikipedia-12647317');new=copy.deepcopy(old)
assert len(old['body'])==3 and old['videos'][0]['youtube_id']=='nwWZw5vb_xs'
new['images']=[copy.deepcopy(old['images'][0])];new['images'][0]['story_paragraph']=-1
new['images'][0].update(creator='Namco / Atari',credit='Namco / Atari; original publisher flyer catalogued by LaunchBox Games Database')
new['videos']=[];new['explicit_story_media_only']=True
p=base/'original-flyer-back.jpg'
new['images'].append(dict(url='https://flyers.arcade-museum.com/arcade-flyers/7/f-1--atari-07639-02.jpg',
 source_page='https://flyers.arcade-museum.com/arcades/show/7648',title='The original F-1 projection machine',
 caption='Original Atari sales leaflet, printed November 1976, describing the Namco-designed projection optics, interchangeable track discs and custom racing cabinet. This is the electromechanical machine, not a modern Formula One racing simulation.',
 creator='Namco / Atari',credit='Namco / Atari / The Arcade Flyer Archive',
 license='Original manufacturer advertisement rights retained; no open licence asserted.',width=850,height=1097,
 story_paragraph=0,recovery_local_source=p.relative_to(ROOT).as_posix(),verification=dict(sha256=sha(p),native_dimensions=[850,1097],processing='Original full-page manufacturer scan, no crop or enlargement.')))
pole=next(e for e in entries if e['id']=='wikipedia-166791');item=copy.deepcopy(pole['images'][1])
item.update(story_paragraph=2,creator='Namco',credit='Namco / original publisher leaflet catalogued by LaunchBox Games Database',
 title='Pole Position follows the mechanical racing spectacle',
 caption='Original 1982 Namco Pole Position leaflet showing the Fuji Speedway course and video-generated road. Later-game context for the existing legacy paragraph, not a display from the 1976 F-1 machine.')
new['images'].append(item)
paths=[base/'original-flyer-source.html',base/'source-downloads.json',p,ROOT/item['recovery_local_source'],ROOT/old['images'][0]['recovery_local_source']]
doc=dict(status='CANDIDATE_PENDING_INDEPENDENT_PEER',rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
 source_files={p.relative_to(ROOT).as_posix():sha(p)for p in paths},expected_main_paragraph_groups=[[0,1],[2]],
 archived_incorrect_film=old['videos'],archived_incorrect_poster=old['images'][1],
 scope='All three complete existing paragraphs/headings/date retained; original cover exclusive. The linked modern Rush Mod F1 1976-season film and matching poster are removed from display and archived here. Original machine and explicitly later Pole Position artifacts create two illustrated chapters.',
 quality_limits=['Actual native 850x1097 and 1280x896 published scans, no artificial enlargement.',
 'Pole Position is explicitly identified as the later 1982 video game, not F-1 gameplay.',
 'No replacement film claimed, no parallel YouTube request, no new prose.'])
out=base/'three-existing-f1-paragraphs-original-machine-and-legacy-candidate.json';out.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
