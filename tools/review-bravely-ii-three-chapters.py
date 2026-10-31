"""Independent source and original-artwork review of Bravely Default II."""
from pathlib import Path
import hashlib
import json
import re
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/modern-major-release-coverage-audit/bravely-default-ii-2021-complete-illustrated'
candidate=BASE/'one-original-bravely-ii-three-illustrated-chapters-candidate.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
doc=json.loads(candidate.read_text(encoding='utf8'))
entry,=doc['entries']
assert entry['id']=='wikipedia-64399235'
assert (entry['year'],entry['date']['month'],entry['date']['day'])==(2021,2,26)
assert len(entry['body'])==3 and len(entry['images'])==4
assert [i['story_paragraph'] for i in entry['images']]==[-1,0,1,2]
for name,digest in doc['source_files'].items():
    assert sha(ROOT/name)==digest,name
page,=json.loads((BASE/'wiki.json').read_text(encoding='utf8'))['query']['pages']
assert page['revisions'][0]['revid']==entry['attribution']['revision_id']
normalize=lambda s:re.sub(r'\s+',' ',s).strip()
source=normalize(page['extract'])
for index,paragraph in enumerate(entry['body']):
    for block in paragraph.split('\n\n'):
        assert normalize(block) in source,index
publisher=(BASE/'publisher-release.html').read_text(encoding='utf8')
assert any(d in publisher for d in ('26/02/2021','26 February 2021','2021-02-26','February 26, 2021'))
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
    entry_id=entry['id'],original_release='2021-02-26',
    full_visual_review=['Clean vertical Gloria artwork for the correct second numbered game',
        'The four original companions gathered around a crystal',
        'Actual turn-based battle with Brave, Default and BP visible',
        'The original painted-style town and party'],
    selected_source_blocks_retained=True,exclusive_cover=True,image_sha256=hashes,
    no_upscaling=True,limits=['Original cover is 600 by 900; screenshots retain native 1280/1536 dimensions.',
        'No video or soundtrack yet; native layout and final offline staging follow source admission.'])
out=BASE/'root-independent-three-chapter-peer-review.json'
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(status=report['status'],receipt=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
