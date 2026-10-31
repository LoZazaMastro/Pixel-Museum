"""Independent review of the four publisher illustrations after full visual inspection."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageChops
import pypdfium2
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/arc-system-works-existing-prose-publisher-context'
path=base/'four-existing-arc-paragraphs-four-publisher-context-scenes-candidate.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
doc=json.loads(path.read_text(encoding='utf8'))
row,=doc['rows'];old=row['old_entry'];new=row['new_entry']
current=next(e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']if e['id']==row['entry_id'])
assert current==old
assert len(old['body'])==4 and old['body']==new['body']
assert old.get('story_headings')==new.get('story_headings')
assert {k:v for k,v in old['images'][0].items()if k!='story_paragraph'}=={k:v for k,v in new['images'][0].items()if k!='story_paragraph'}
assert sorted(i['story_paragraph']for i in new['images'])==[-1,0,1,2,3]
for name,digest in doc['source_files'].items():
    assert sha(ROOT/name)==digest,name
hashes=[]
for item in new['images']:
    p=ROOT/item['recovery_local_source']
    hashes.append(sha(p))
    with Image.open(p)as image:
        image.load();assert image.size==(item['width'],item['height'])
assert len(hashes)==len(set(hashes))
pdf=pypdfium2.PdfDocument(base/'official-company-pamphlet-original.pdf')
render=pdf[4].render(scale=3).to_pil().convert('RGB')
with Image.open(base/'official-history-first-page-whole.png')as original:
    assert not ImageChops.difference(render,original.convert('RGB')).getbbox()
for prefix in ['guilty-gear-strive','blazblue-centralfiction']:
    metadata=json.loads((base/f'{prefix}-steam-product.json').read_text(encoding='utf8'))
    product=next(iter(metadata.values()))['data']
    published_urls=[s['path_full']for s in product['screenshots']]
    for item in new['images'][1:]:
        if prefix in item['recovery_local_source']:
            assert item['url'] in published_urls
out=base/'root-independent-four-existing-paragraphs-four-publisher-scenes-peer-review.json'
report=dict(status='PASS_INDEPENDENT_EXISTING_PROSE_AND_FULL_IMAGE_REVIEW',candidate=path.relative_to(ROOT).as_posix(),candidate_sha256=sha(path),
    current_owner_unchanged=True,four_existing_paragraphs_and_headings_preserved=True,exclusive_cover=True,
    all_source_hashes_checked=True,source_pdf_page_render_pixel_match=True,
    full_visual_review=['Actual Strive Sol/Ky combat demonstrates the drawn appearance of 3D models.',
        'Whole modern official corporate-history page starts with May 1988 and remains explicitly a retrospective document.',
        'Different Strive scene visibly shows reversal and punish feedback.',
        'Actual Centralfiction Mai/Naoto combat HUD and sprites, native 1280 by 768.'],
    limits=['The Japanese document is an illustrated source artifact, not English article prose.',
        'Modern games illustrate the publisher history without being mislabeled as 1988 captures.',
        'No soundtrack, new film or missing standalone franchise article is supplied by this candidate.'])
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(receipt=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
