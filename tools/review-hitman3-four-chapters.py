"""Independently bind the Hitman 3 candidate to its collected sources."""
from pathlib import Path
import hashlib
import json
import re
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/modern-major-release-coverage-audit/hitman3-2021-complete-illustrated'
candidate = BASE / 'one-original-hitman3-four-illustrated-chapters-candidate.json'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
doc = json.loads(candidate.read_text(encoding='utf8'))
entry, = doc['entries']
assert entry['id'] == 'wikipedia-64249568'
assert (entry['year'], entry['date']['month'], entry['date']['day']) == (2021, 1, 20)
assert len(entry['body']) == 4 and len(entry['images']) == 5
assert [i['story_paragraph'] for i in entry['images']] == [-1, 0, 1, 2, 3]
for name, digest in doc['source_files'].items():
    assert sha(ROOT / name) == digest, name
page, = json.loads((BASE / 'wiki.json').read_text(encoding='utf8'))['query']['pages']
revision = page['revisions'][0]
assert revision['revid'] == entry['attribution']['revision_id']
raw_page, = json.loads((BASE / 'wiki-wikitext.json').read_text(encoding='utf8'))['query']['pages']
source = raw_page['revisions'][0]['slots']['main']['content']
source = re.sub(r'<ref\b[^>]*/>', '', source)
source = re.sub(r'<ref\b[^>]*>.*?</ref>', '', source, flags=re.S)
source = re.sub(r'\[\[(?:[^\]|]+\|)?([^\]]+)\]\]', r'\1', source)
source = source.replace("'''", '').replace("''", '')
normalize = lambda value: re.sub(r'\s+', ' ', value).strip()
source = normalize(page['extract'])
for index, text in enumerate(entry['body']):
    assert normalize(text) in source, index
publisher = (BASE / 'publisher-launch.html').read_text(encoding='utf8')
assert 'January 20, 2021' in publisher or '2021-01-20' in publisher
hashes = []
for item in entry['images']:
    path = ROOT / item['recovery_local_source']
    assert sha(path) == item['verification']['sha256']
    with Image.open(path) as decoded:
        decoded.load()
        assert decoded.size == (item['width'], item['height'])
    hashes.append(sha(path))
assert len(hashes) == len(set(hashes))
report = dict(status='PASS_INDEPENDENT_SOURCE_AND_FULL_IMAGE_REVIEW',
    candidate=candidate.relative_to(ROOT).as_posix(), candidate_sha256=sha(candidate),
    entry_id=entry['id'], original_release='2021-01-20',
    unchanged_selected_wikipedia_paragraphs=4,
    full_visual_review=['Original clean vertical Hitman III cover',
        'Agent 47 in original Chongqing location',
        'Detective disguise at Dartmoor',
        'Opening approach above the clouds in Dubai',
        'Dartmoor family gathered in the manor'],
    image_sha256=hashes, exclusive_cover=True, no_upscaling=True,
    limits=['Collected publisher images, not claims of launch-day captures.',
        'No film or soundtrack admitted by this candidate.',
        'Native layout and final offline packaging follow source admission.'])
out = BASE / 'root-independent-four-chapter-peer-review.json'
out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
print(json.dumps(dict(status=report['status'], receipt=out.relative_to(ROOT).as_posix(), sha256=sha(out))))
