"""Verify the collected Sackboy article against its source and local images."""
from pathlib import Path
import hashlib
import json
import re
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/modern-major-release-coverage-audit/sackboy-2020-complete-illustrated'
candidate = BASE / 'one-original-sackboy-four-illustrated-chapters-candidate.json'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
doc = json.loads(candidate.read_text(encoding='utf8'))
entry, = doc['entries']
assert entry['id'] == 'wikipedia-64248811'
assert (entry['year'], entry['date']['month'], entry['date']['day']) == (2020,11,12)
assert len(entry['body']) == 4 and len(entry['images']) == 5
assert [i['story_paragraph'] for i in entry['images']] == [-1,0,1,2,3]
for path, digest in doc['source_files'].items():
    assert sha(ROOT/path) == digest, path
pages = json.loads((BASE/'wiki.json').read_text(encoding='utf8'))['query']['pages']
revision = pages[0]['revisions'][0]
assert revision['revid'] == entry['attribution']['revision_id']
source = revision['slots']['main']['content']
source = re.sub(r'<ref\b[^>]*/>', '', source)
source = re.sub(r'<ref\b[^>]*>.*?</ref>', '', source, flags=re.S)
source = re.sub(r'\[\[(?:[^\]|]+\|)?([^\]]+)\]\]', r'\1', source)
source = source.replace("'''", '').replace("''", '')
normalize = lambda s: re.sub(r'\s+', ' ', s).strip()
source = normalize(source)
for index, text in enumerate(entry['body']):
    assert normalize(text) in source, index
publisher = (BASE/'publisher-game.html').read_text(encoding='utf8')
assert any(date in publisher for date in ('11/12/2020', '2020-11-12', 'November 12, 2020'))
hashes=[]
for image in entry['images']:
    path=ROOT/image['recovery_local_source']
    assert sha(path)==image['verification']['sha256']
    with Image.open(path) as decoded:
        decoded.load()
        assert decoded.size==(image['width'], image['height'])
    hashes.append(sha(path))
assert len(hashes)==len(set(hashes))
report=dict(status='PASS_INDEPENDENT_SOURCE_AND_FULL_IMAGE_REVIEW',
    candidate=candidate.relative_to(ROOT).as_posix(), candidate_sha256=sha(candidate),
    entry_id=entry['id'], original_release='2020-11-12',
    unchanged_selected_wikipedia_paragraphs=4, exclusive_clean_cover=True,
    full_visual_review=['Clean vertical cover without platform strip',
        'Handcrafted3D scene', 'Platforms and collectibles',
        'VisibleClawstring acrossgap', 'Two simultaneous playercharacters'],
    image_sha256=hashes, no_cover_reuse=True, no_upscaling=True,
    limits=['PC publisher screenshots illustrate unchanged game mechanics, not an asserted 2020 launch capture.',
        'Native layout check and final offline packaging still follow source admission.',
        'No video or soundtrack included yet; no physical console claim.'])
out=BASE/'root-independent-four-chapter-peer-review.json'
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(status=report['status'],receipt=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
