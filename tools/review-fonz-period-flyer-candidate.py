"""Independent Fonz source/image review after viewing the complete flyer back."""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/fonz-existing-eight-paragraphs-period-flyer'
path=BASE/'eight-existing-fonz-paragraphs-two-illustrated-chapters-candidate.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
doc=json.loads(path.read_text(encoding='utf8'))
current=next(e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries'] if e['id']==doc['entry_id'])
assert current==doc['old_entry']
assert len(current['body'])==8
assert doc['expected_main_paragraph_groups']==[[0,1,2,3],[4,5,6,7]]
for name,digest in doc['source_files'].items():
    assert sha(ROOT/name)==digest,name
item=doc['images_after'][-1]
assert item['url'] in (BASE/'original-flyer-archive-source.html').read_text(encoding='utf8')
assert doc['images_after'][:-1]==current['images']
assert item['story_paragraph']==4
with Image.open(ROOT/item['recovery_local_source'])as image:
    image.load()
    assert image.size==(850,1104)==(item['width'],item['height'])
assert len({sha(ROOT/i['recovery_local_source'])for i in doc['images_after']})==3
report=dict(status='PASS_INDEPENDENT_PERIOD_ARTIFACT_AND_PARAGRAPH_REVIEW',
            candidate=path.relative_to(ROOT).as_posix(),candidate_sha256=sha(path),
            current_owner_unchanged=True,eight_existing_paragraphs_and_headings_preserved=True,
            exclusive_cover=True,all_source_hashes_checked=True,
            full_visual_review='Original Sega Fonz flyer back: actual cabinet, television imagery, handlebar controls, perspective and sound descriptions, Sega of America footer and distributor stamp. Upright complete published scan, distinct from cover front.',
            limits=['Native 850 by 1104 archival scan, not a new HD photograph.',
                    'Original Sega/television rights retained; no invented CC licence.',
                    'Existing film retained; no new YouTube availability request made.',
                    'Two-scene actual native projection verified separately by timeline agent.'])
out=BASE/'root-independent-eight-paragraphs-original-flyer-peer-review.json'
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(receipt=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
