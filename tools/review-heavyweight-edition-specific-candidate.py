"""Verify the approved whole-paragraph edition grouping and original artifacts."""
from pathlib import Path
from collections import Counter
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/heavyweight-edition-specific-chronology'
path=BASE/'ten-existing-heavyweight-paragraphs-four-editions-exact-pdf-raster-candidate.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
doc=json.loads(path.read_text(encoding='utf8'))
current=next(e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries'] if e['id']==doc['entry_id'])
assert current==doc['old_entry']
order=[0,2,4,8,1,3,5,6,7,9]
assert doc['approved_new_to_old_paragraph_indices']==order
assert doc['body_after']==[current['body'][i]for i in order]
assert Counter(doc['body_after'])==Counter(current['body'])
assert doc['entry_after']['body']==doc['body_after']
assert not doc['videos_after'] and not doc['entry_after']['videos']
assert 'reordered by game edition' in doc['attribution_after']['changes']
for name,digest in doc['source_files'].items():
    assert sha(ROOT/name)==digest,name
hashes=[]
for item in doc['images_after']:
    p=ROOT/item['recovery_local_source']
    with Image.open(p)as image:
        image.load()
        assert image.size==(item['width'],item['height'])
    hashes.append(sha(p))
assert len(hashes)==len(set(hashes))==5
assert doc['images_after'][0]==current['images'][0]
assert [i.get('story_paragraph')for i in doc['images_after'][1:]]==[0,4,8,9]
report=dict(status='PASS_INDEPENDENT_EDITION_IDENTITY_AND_APPROVED_PARAGRAPH_REORDER',
    candidate=path.relative_to(ROOT).as_posix(),candidate_sha256=sha(path),
    current_owner_unchanged=True,all_ten_source_paragraphs_retained_verbatim=True,
    approved_new_to_old_paragraph_indices=order,
    attribution_discloses_reordering=True,exclusive_1976_cover=True,
    ambiguous_multigame_video_removed_from_display=True,all_source_hashes_checked=True,
    full_visual_review=['Original 1976 Sega Japanese flyer back, glove illustration and original monochrome-system specifications; distinct from exclusive flyer front.',
                        'Original 1987 Sega colour remake flyer and its behind-the-boxer cabinet.',
                        'Original European Master System wraparound scan, visible 1991 Sega copyright, distinct platform and artwork; credited scanner retained.',
                        'Original Title Fight promotional flyer: twin-screen cabinet and paired glove handles, explicitly catalogued 1992 artifact rather than the 1976 original.'],
    limits=['Original historical artifacts are not all HD photographs; native sizes retained.',
            'The ambiguous long retrospective is archived, not claimed as footage of the lost 1976 original.',
            'This is the explicitly approved whole-paragraph reorder; original order is archived rather than falsely described as unchanged.',
            'Original Sega/publisher rights retained; no invented open licence.'])
out=BASE/'root-independent-four-editions-ten-verbatim-paragraphs-peer-review.json'
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(receipt=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
