"""Illustrate existing Tanktics prose with the creator's hardware and review."""
from pathlib import Path
import copy
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/chronological-tanktics-trek80-atari1977'
source_page='https://erasmatazz.com/library/source-code/kimtanktics/index.html'
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
old=next(e for e in catalog['entries'] if e['id']=='wikipedia-1631185')
new=copy.deepcopy(old)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
observations=dict(source_page=source_page,creator='Chris Crawford',
    source_description='The creator describes a1978-79KimTanktics system: KIM-1microcomputer,4KRAM,custominterfaceandtwotinyterminals, withseparatephysicalplayermaps.',
    acquisition='Ordinary rendered browser image elements downloaded using the browser media-download API. The observed image src/natural dimensions were used; no guessed high-resolution variants.',
    images=[])
for paragraph,name,title,caption in [
    (0,'kimtankticssystem-small_med_hr.png','Chris Crawford\'s KimTanktics system, built in 1978-79',
     'The complete KimTanktics system documented by Chris Crawford on his own site: separate maps, terminals and the central computer enclosure. Crawford dates this hardware to 1978-79; it is not presented as the original 1976 IBM 1130 program.'),
    (3,'kimtankticsclose-small_med_hr.png','The physical map and terminal used for KimTanktics',
     'A closer photograph of one player\'s hex map, counters and terminal in Crawford\'s KimTanktics setup. This documents the later KIM-1 implementation, rather than a graphical display or the 1981 Avalon Hill map.')]:
    path=ROOT/'downloads-original/tanktics-crawford'/name
    with Image.open(path) as image:
        image.load()
        width,height=image.size
        assert width==1024 and height in (605,686)
    url='https://erasmatazz.com/_Media/'+name
    observations['images'].append(dict(url=url,file=path.relative_to(ROOT).as_posix(),width=width,height=height,sha256=sha(path)))
    new['images'].append(dict(url=url,source_page=source_page,title=title,caption=caption,
        creator='KimTanktics designed by Chris Crawford; photograph from the creator\'s published documentation',
        credit='Chris Crawford / KimTanktics personal documentation; original photographic rights retained',
        license='Original creator-site photographs; respective rights retained. No open licence asserted.',
        width=width,height=height,story_paragraph=paragraph,
        recovery_local_source=path.relative_to(ROOT).as_posix(),
        verification=dict(sha256=sha(path),native_dimensions=[width,height],
            processing='Original downloaded PNG retained byte-for-byte with its source transparency; no local crop, enlargement, regeneration or frame.',
            context='Later KIM-1implementation explicitly dated1978-79 by the creator; not mislabelled1976 or AvalonHill1981.')))
review=BASE/'cgw1982-pdf21-0-ImagePart_20.jpg'
with Image.open(review) as image:
    image.load();width,height=image.size
new['images'].append(dict(
    url='https://upload.wikimedia.org/wikipedia/commons/9/90/Computer_Gaming_World_issue_2.1.pdf#page=21&embedded=ImagePart_20.jpg',
    source_page='https://commons.wikimedia.org/wiki/File:Computer_Gaming_World_issue_2.1.pdf',
    title='Tanktics review and BASIC patches, Computer Gaming World, 1982',
    caption='Bob Proctor\'s contemporary Tanktics review, Computer Gaming World vol. 2 no. 1, printed page 19 / PDF page 21. The Programmer\'s Corner lists Apple II patches beside the review of play. The small Select-A-Port advertisement is unrelated to Tanktics.',
    creator='Bob Proctor / Computer Gaming World',
    credit='Computer Gaming World / Bob Proctor, 1982; original magazine scan',
    license='Original magazine, illustration and advertising rights retained. No open licence asserted.',
    width=width,height=height,story_paragraph=5,recovery_local_source=review.relative_to(ROOT).as_posix(),
    verification=dict(sha256=sha(review),native_dimensions=[width,height],
        processing='Original full-page embedded JPEG extracted from the existing magazine PDF; no crop or enlargement.')))
new['images'][0]['story_paragraph']=-1
new['explicit_story_media_only']=True
new['sources']+= [dict(title='KimTanktics: the creator\'s own hardware documentation',url=source_page,
    publisher='Chris Crawford',source_type='Primary creator documentation',story_paragraphs=[0,1,3,4],
    locator='Complete system and closer map photographs; creator explicitly dates this KIM-1 system to 1978-79.'),
    dict(title='Tanktics: Review and Analysis',url='https://upload.wikimedia.org/wikipedia/commons/9/90/Computer_Gaming_World_issue_2.1.pdf',
        publisher='Bob Proctor / Computer Gaming World, vol. 2 no. 1, 1982',source_type='Contemporary published review',
        story_paragraphs=[2,5],locator='Printed pp. 17 and 19 onward; PDF pp. 19 and 21 onward; Programmer\'s Corner on printed p. 19.')]
assert new['body']==old['body'] and new['story_headings']==old['story_headings']
observations_path=BASE/'crawford-primary-browser-original-image-observations.json'
observations_path.write_text(json.dumps(observations,indent=2)+'\n',encoding='utf8')
files=[ROOT/i['recovery_local_source'] for i in new['images'][1:]]
files += [BASE/'cgw1982-2.1-original.pdf',observations_path]
out=BASE/'six-existing-tanktics-paragraphs-three-primary-image-chapters-candidate.json'
doc=dict(schema_version=1,status='CANDIDATE_PENDING_INDEPENDENT_PEER',
    rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
    source_files={p.relative_to(ROOT).as_posix():sha(p) for p in files},
    expected_native_chapters=[[0,1,2],[3,4],[5]],
    scope='All six existing paragraphs/headings and cover retained; three pertinent images and explicit bindings added. No new narrative text.',
    quality_limits=['Two creator photographs document the later1978-79KIM-1hardware, not the1976mainframe release.',
        'The two photographs are distinct original published views of the same setup; no duplicate source URL or image bytes.',
        'The1982magazine is later contemporary criticism of the published game; unrelated advertisement not claimed as game hardware.',
        'Original widths1024 and magazine-native resolution retained; no fake4Kupscale.'])
out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
