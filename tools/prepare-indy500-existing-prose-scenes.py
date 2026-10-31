"""Illustrate existing driving-controller and game-mode paragraphs with Atari's manual."""
from pathlib import Path
import copy,hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/indy500-existing-prose-original-manual'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=next(e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']if e['id']=='wikipedia-6028366')
new=copy.deepcopy(old)
assert len(old['body'])==7 and len(old['images'])==3
new['images'][0]['story_paragraph']=-1
new['images'][1]['story_paragraph']=2
new['explicit_story_media_only']=True
url='https://www.ataricompendium.com/archives/manuals/vcs/indy_500.pdf'
for paragraph,page,title,subject in [
    (1,2,'The original Driving Controller instructions','the endlessly turning driving controller, acceleration and scoring'),
    (3,3,'Race Car and the Grand Prix track','Race Car rules and the Grand Prix track'),
    (4,5,"Crash n\u2019 Score and its two playfields","both Crash n' Score playfields"),
    (5,6,'Tag and the Barrier Chase track','the Tag rules and Barrier Chase track'),
    (6,8,'Ice Race and the Ice Rally track','the Ice Race variants and Ice Rally track'),
]:
    path=base/f'manual-pdf-page-{page}.jpg'
    width,height=Image.open(path).size
    assert (width,height)==(820,1311)
    new['images'].append(dict(url=url+f'#page={page}',source_page=url,title=title,
        caption=f'Complete original Atari Indy 500 instruction page showing {subject}. The printed illustrations are retained as documentation, not presented as a modern game capture.',
        creator='Atari',credit='Atari / Indy 500 game program instructions (1977)',
        license='Original Atari manual text and illustrations; original rights retained. No open licence asserted.',
        width=width,height=height,story_paragraph=paragraph,recovery_local_source=path.relative_to(ROOT).as_posix(),
        verification=dict(sha256=sha(path),source_pdf_sha256=sha(base/'indy-500-original-manual.pdf'),pdf_page=page,
            native_dimensions=[width,height],processing='Exact original embedded JPEG bytes extracted from the publisher manual PDF. No crop, enlargement or retouch.')))
assert new['body']==old['body'] and new.get('story_headings')==old.get('story_headings')
paths=[base/'indy-500-original-manual.pdf',base/'manual-inspection.json']
paths += [ROOT/i['recovery_local_source']for i in new['images'][3:]]
doc=dict(schema_version=1,status='CANDIDATE_PENDING_INDEPENDENT_PEER',rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
    source_files={p.relative_to(ROOT).as_posix():sha(p)for p in paths},expected_main_paragraph_groups=[[i]for i in range(7)],
    scope='Seven existing paragraphs retained verbatim and in order. Distinct original manual pages separate controller and four modes, with the existing box back and film retained.',
    quality_limits=['Original full-page scans retain their native 820 by 1311 pixels; no artificial enlargement.',
        'Existing film remains unchanged; no new YouTube request, soundtrack or experience is introduced.'])
out=base/'seven-existing-indy500-paragraphs-seven-distinct-context-scenes-candidate.json'
out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
