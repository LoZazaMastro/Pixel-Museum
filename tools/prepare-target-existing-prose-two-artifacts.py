"""Bind Target's existing three paragraphs to two identified historical artifacts."""
from pathlib import Path
import copy
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/target-1977-existing-prose-primary-artifacts'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
old=next(e for e in catalog['entries'] if e['id']=='wikipedia-60355975')
new=copy.deepcopy(old)
assert len(old['body'])==3 and len(old['images'])==1
new['images'][0]['story_paragraph']=-1
new['explicit_story_media_only']=True
photo=BASE/'sol20-original.jpg'
manual=BASE/'gamepac1-target-printed8.png'
for path,size in [(photo,(1422,1079)),(manual,(2448,3168))]:
    with Image.open(path) as image:
        image.load()
        assert image.size==size
new['images'].append(dict(
    url='https://upload.wikimedia.org/wikipedia/commons/5/5e/Processor_Technology_SOL_20_Computer.jpg',
    source_page='https://commons.wikimedia.org/wiki/File:Processor_Technology_SOL_20_Computer.jpg',
    title='The Processor Technology Sol-20',
    caption='A preserved Sol-20 photographed by Michael Holley at the 2006 Vintage Computer Festival. It is the historical computer family used to demonstrate Target, not a photograph of The Tomorrow Show.',
    creator='Michael Holley / Swtpc6800',credit='Michael Holley / Public domain',
    license='Public domain',license_url='https://creativecommons.org/publicdomain/mark/1.0/',
    width=1422,height=1079,story_paragraph=0,
    recovery_local_source=photo.relative_to(ROOT).as_posix(),
    verification=dict(sha256=sha(photo),native_dimensions=[1422,1079],no_upscale=True)))
new['images'].append(dict(
    url='https://www.sol20.org/manuals/gamepac1.pdf#page=12',
    source_page='https://www.sol20.org/manuals/gamepac1.pdf',
    title='Target in the preserved Gamepac 1 manual',
    caption='Printed page 8 of the preserved Gamepac 1 manual identifies Steve Dompier, version 2.4 dated January 7, 1977, and explains the targets and scoring. This is the archive PDF page, not a gameplay screenshot or an original-paper photograph.',
    creator='Processor Technology / Software Technology Corporation',
    credit='Processor Technology / Software Technology Corporation; manual preserved by Sol20.org',
    license='Original manual copyright retained. No open licence asserted.',
    width=2448,height=3168,story_paragraph=1,
    recovery_local_source=manual.relative_to(ROOT).as_posix(),
    verification=dict(sha256=sha(manual),source_pdf_sha256=sha(BASE/'gamepac1-original.pdf'),
        pdf_page=12,printed_page=8,vector_render_scale=4,
        processing='Full vector PDF page rasterized at 288 DPI with PDFium. No crop, text alteration, generated art or raster enlargement.' )))
new['sources'].append(dict(title='Gamepac 1 user manual: original Target instructions',
    url='https://www.sol20.org/manuals/gamepac1.pdf',publisher='Processor Technology / Sol20.org'))
assert new['body']==old['body'] and new['story_headings']==old['story_headings']
out=BASE/'three-existing-target-paragraphs-two-archival-scenes-candidate.json'
paths=[p for p in BASE.iterdir() if p.is_file() and p!=out]
doc=dict(schema_version=1,status='CANDIDATE_PENDING_INDEPENDENT_PEER',
    rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
    source_files={p.relative_to(ROOT).as_posix():sha(p) for p in paths},
    expected_main_paragraph_groups=[[0],[1,2]],
    scope='Existing three Wikipedia paragraphs and headings remain unchanged. Two illustrations added, with the hardware cover exclusive.',
    quality_limits=['No verified original gameplay capture or Tomorrow Show frame yet.',
        'Archive PDF is a preserved digital text edition, not asserted to be a scanned 1977 sheet.',
        'Later Sol photograph is explicitly dated 2006; no false period-photo claim.'])
out.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
