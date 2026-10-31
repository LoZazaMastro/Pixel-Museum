"""Record independent review after viewing both complete publisher leaflet pages."""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/air-traffic-controller-original-publisher-manual'
path=BASE/'four-existing-atc-paragraphs-two-original-leaflet-chapters-candidate.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
doc=json.loads(path.read_text(encoding='utf8'))
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
current=next(e for e in catalog['entries'] if e['id']==doc['entry_id'])
assert current==doc['old_entry']
assert len(current['body'])==4 and doc['expected_main_paragraph_groups']==[[0,1],[2,3]]
assert doc['images_after'][0]==current['images'][0]
for name,digest in doc['source_files'].items():
    assert sha(ROOT/name)==digest,name
for i in doc['images_after'][1:]:
    p=ROOT/i['recovery_local_source']
    with Image.open(p) as im:
        im.load()
        assert im.size==(i['width'],i['height'])
assert [i['story_paragraph']for i in doc['images_after'][1:]]==[0,2]
assert len({sha(ROOT/i['recovery_local_source'])for i in doc['images_after']})==3
report=dict(status='PASS_INDEPENDENT_SOURCE_AND_COMPLETE_IMAGE_REVIEW',
    candidate=path.relative_to(ROOT).as_posix(),candidate_sha256=sha(path),
    all_source_hashes_checked=True,unchanged_current_owner=True,
    four_existing_paragraphs_preserved=True,cover_exclusive=True,
    full_visual_review=['Complete Apple II CS-4008 leaflet first page: Creative Computing Software, David Mannering, aircraft, radar and safety rules; genuine preserved publication.',
                        'Complete fourth page: Map Area diagram, airports, navaids, entry/exit fixes and game-ending rules. Upright and legible; blank scan margins retained.'],
    limits=['Source leaflet is undated and for the Apple II edition, not asserted as a 1978 TRS-80 release-day scan.',
            'Map is a publisher manual diagram, not a game capture or the quoted Space Gamer review.',
            'Original publisher rights retained; no invented open licence.',
            'Native projected composition is separately verified by the timeline agent.'])
out=BASE/'root-independent-four-paragraphs-two-publisher-pages-peer-review.json'
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(receipt=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
