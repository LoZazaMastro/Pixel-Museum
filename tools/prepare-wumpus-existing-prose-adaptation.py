"""Add the TI adaptation's original illustration to its existing dedicated paragraph."""
from pathlib import Path
import copy,hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/wumpus-existing-prose-ti-adaptation'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=next(e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']if e['id']=='wikipedia-14323')
new=copy.deepcopy(old)
assert len(old['body'])==2 and len(old['images'])==2
new['images'][0]['story_paragraph']=-1
new['explicit_story_media_only']=True
path=base/'ti-manual-cover-original.jpg'
width,height=Image.open(path).size
assert (width,height)==(1626,2370)
url='https://mocagh.org/ti994a/huntwumpus-manual.pdf'
new['images'].append(dict(url=url+'#page=1',source_page=url,title='The Texas Instruments adaptation of Hunt the Wumpus',
    caption='Original Texas Instruments instruction-booklet cover for the later TI-99 home-computer adaptation discussed here. The booklet carries a 1980 copyright; this artwork is not presented as the original 1973 text-based game.',
    creator='Texas Instruments',credit='Texas Instruments / Hunt the Wumpus manual (1980)',
    license='Original publisher illustration and document rights retained. No open licence asserted.',
    width=width,height=height,story_paragraph=1,recovery_local_source=path.relative_to(ROOT).as_posix(),
    verification=dict(sha256=sha(path),source_pdf_sha256=sha(base/'ti-original-hunt-wumpus-manual.pdf'),pdf_page=1,
        native_dimensions=[width,height],processing='Exact embedded original JPEG bytes extracted from the complete publisher PDF. No crop, enlargement or retouch.')))
assert new['body']==old['body'] and new.get('story_headings')==old.get('story_headings')
paths=[base/'ti-original-hunt-wumpus-manual.pdf',base/'manual-inspection.json',path]
doc=dict(status='CANDIDATE_PENDING_INDEPENDENT_PEER',rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
    source_files={p.relative_to(ROOT).as_posix():sha(p)for p in paths},expected_main_paragraph_groups=[[0],[1]],
    scope='Two existing complete paragraphs and headings retained. Exclusive 1975 publication cover and existing film retained; original TI adaptation artwork illustrates the paragraph specifically discussing ports.',
    quality_limits=['Period artifact shown as the later Texas Instruments edition, not original 1973 gameplay.',
        'Full original 1626 by 2370 scan retained; no artificial enlargement.',
        'No extra prose, music, film request or interactive experience added.'])
out=base/'two-existing-wumpus-paragraphs-two-distinct-period-context-scenes-candidate.json'
out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
