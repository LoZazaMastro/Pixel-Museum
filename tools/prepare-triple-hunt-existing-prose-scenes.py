"""Split the three game modes using their actual original manual diagrams."""
from pathlib import Path
import copy
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/triple-hunt-existing-prose-original-manual'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
old=next(e for e in catalog['entries']if e['id']=='wikipedia-37849828')
new=copy.deepcopy(old)
assert len(old['body'])==5 and len(old['images'])==2
new['explicit_story_media_only']=True
new['images'][0]['story_paragraph']=-1
new['images'][1]['story_paragraph']=0
source='https://www.arcade-museum.com/manuals-videogames/T/TripleHunt.pdf'
for paragraph,page,printed,title,caption in [
    (2,24,19,'Hit the Bear in the original Atari instructions',
     'Complete original manual page 19, showing the bear\'s motion, hit location and attract/play displays. These are Atari\'s annotated manual illustrations, not a modern gameplay capture.'),
    (3,25,20,'Raccoon Hunt and its climbing targets',
     'Complete original manual page 20, with the Raccoon Hunt rules and annotated displays. The same page also finishes the bear-mode explanation; it is retained intact.'),
    (4,26,21,'Witch Hunt and the haunted-house targets',
     'Complete original manual page 21, illustrating witches, ghosts and bats and their different scores. The upper-left illustration finishes Raccoon Hunt; the page is not cropped or presented as a standalone screenshot.'),
]:
    path=BASE/f'original-manual-pdf{page}-image0.png'
    width,height=Image.open(path).size
    new['images'].append(dict(url=source+f'#page={page}',source_page=source,
        title=title,caption=caption,creator='Atari',
        credit=f'Atari / Triple Hunt operation, maintenance and service manual, page {printed}',
        license='Original Atari manual text and illustrations; original rights retained. No open licence asserted.',
        width=width,height=height,story_paragraph=paragraph,
        recovery_local_source=path.relative_to(ROOT).as_posix(),
        verification=dict(sha256=sha(path),source_pdf_sha256=sha(BASE/'atari-triple-hunt-original-manual.pdf'),
            pdf_page=page,printed_page=printed,
            processing='Complete original PDF page rendered at 300 dpi with its indexed PDF colour table respected. No crop, retouch or artistic colour inversion.',
            source_raster_dimensions=[2544,3300],native_dimensions=[width,height])))
assert new['body']==old['body']
assert new.get('story_headings')==old.get('story_headings')
paths=[BASE/'atari-triple-hunt-original-manual.pdf',BASE/'original-manual-inspection.json']
paths += [ROOT/i['recovery_local_source']for i in new['images'][2:]]
out=BASE/'five-existing-triple-hunt-paragraphs-four-authentic-game-chapters-candidate.json'
doc=dict(schema_version=1,status='CANDIDATE_PENDING_INDEPENDENT_PEER',
    rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
    source_files={p.relative_to(ROOT).as_posix():sha(p)for p in paths},
    expected_main_paragraph_groups=[[0,1],[2],[3],[4]],
    scope='Five existing paragraphs preserved. Existing exclusive flyer front and distinct back retained; three actual manual pages separate the three game modes.',
    quality_limits=['Images are complete original 1977 Atari documentation, not photographed restored cabinets or modern game screenshots.',
                    'The source images use an indexed colour table; authoritative PDF page rendering avoids the negative-colour appearance of raw CCITT extraction.',
                    'Earlier incorrectly named raw TIFF diagnostic files are not admitted.',
                    'No extra history, film, soundtrack or experience is added in this editorial redistribution.'])
out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
