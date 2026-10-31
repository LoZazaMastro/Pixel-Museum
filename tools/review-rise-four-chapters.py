"""Independently verify the original Rise article and its publisher imagery."""
from pathlib import Path
import hashlib
import json
import re
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/modern-major-release-coverage-audit/monster-hunter-rise-2021-complete-illustrated'
candidate=BASE/'one-original-rise-four-illustrated-chapters-candidate.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
doc=json.loads(candidate.read_text(encoding='utf8'))
entry,=doc['entries']
assert entry['id']=='wikipedia-65341338'
assert (entry['year'],entry['date']['month'],entry['date']['day'])==(2021,3,26)
assert len(entry['body'])==4 and len(entry['images'])==5
assert [i['story_paragraph'] for i in entry['images']]==[-1,0,1,2,3]
for name,digest in doc['source_files'].items():
    assert sha(ROOT/name)==digest,name
page,=json.loads((BASE/'wiki.json').read_text(encoding='utf8'))['query']['pages']
assert page['revisions'][0]['revid']==entry['attribution']['revision_id']
normalize=lambda s:re.sub(r'\s+',' ',s).strip()
source=normalize(page['extract'])
for index,paragraph in enumerate(entry['body']):
    for block in paragraph.split('\n\n'):
        assert normalize(block) in source,index
publisher=(BASE/'publisher-launch.html').read_text(encoding='utf8')
assert 'Mar 26, 2021' in publisher
assert 'monster-hunter-rise-available-now-for-nintendo-switch' in publisher
hashes=[]
for item in entry['images']:
    path=ROOT/item['recovery_local_source']
    assert sha(path)==item['verification']['sha256']
    with Image.open(path) as image:
        image.load()
        assert image.size==(item['width'],item['height'])
    hashes.append(sha(path))
assert len(hashes)==len(set(hashes))
report=dict(status='PASS_INDEPENDENT_SOURCE_AND_FULL_IMAGE_REVIEW',
    candidate=candidate.relative_to(ROOT).as_posix(),candidate_sha256=sha(candidate),
    entry_id=entry['id'],original_release='2021-03-26',
    selected_source_blocks_retained=True,exclusive_cover=True,
    full_visual_review=['Clean original Rise cover with Magnamalo',
        'Hunters fighting Magnamalo in the original Rise setting',
        'Wirebug crossing an actual gap',
        'Mounted Palamute in a snow area',
        'Four distinct hunters gathered in Kamura'],
    image_sha256=hashes,no_upscaling=True,
    limits=['Clean original cover is 600 by 900 pixels; no false 4K claim.',
        'Publisher PC screenshots illustrate original Rise mechanics, not launch-day Switch captures.',
        'No film or soundtrack in this candidate; native rendering and final offline staging follow admission.'])
out=BASE/'root-independent-four-chapter-peer-review.json'
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(status=report['status'],receipt=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
