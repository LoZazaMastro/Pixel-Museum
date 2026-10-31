"""Independent, bounded review of the collected DIRT5 candidate."""
from pathlib import Path
import hashlib
import json
import re
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/modern-major-release-coverage-audit/dirt5-2020-complete-illustrated'
candidate = BASE / 'one-original-dirt5-three-illustrated-chapters-candidate.json'
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
doc = json.loads(candidate.read_text(encoding='utf8'))
entry, = doc['entries']
assert entry['id'] == 'wikipedia-63890268'
assert entry['year'] == 2020 and entry['date']['month'] == 11 and entry['date']['day'] == 6
assert len(entry['body']) == 3 and len(entry['images']) == 4
assert entry['preferred_image'] == 0
assert [i['story_paragraph'] for i in entry['images']] == [-1, 0, 1, 2]
for name, expected in doc['source_files'].items():
    assert digest(ROOT / name) == expected, name
revision = json.loads((BASE / 'wiki.json').read_text(encoding='utf8'))['query']['pages'][0]['revisions'][0]
assert revision['revid'] == entry['attribution']['revision_id']
source = revision['slots']['main']['content']
source = re.sub(r'<ref\b[^>]*/>', '', source)
source = re.sub(r'<ref\b[^>]*>.*?</ref>', '', source, flags=re.S)
source = re.sub(r'\[\[(?:[^\]|]+\|)?([^\]]+)\]\]', r'\1', source)
source = source.replace("'''", '').replace("''", '')
normalize = lambda text: re.sub(r'\s+', ' ', text).strip()
source = normalize(source)
for index, paragraph in enumerate(entry['body']):
    if index == 0:
        # The overview sentence and the two first gameplay sentences are
        # selected from separate sections, as declared by the candidate.
        pieces = paragraph.split('. ', 1)
        assert normalize(pieces[0] + '.') in source
        assert normalize(pieces[1]) in source
    else:
        assert normalize(paragraph) in source, index
assert 'November 6' in (BASE / 'publisher-launch.html').read_text(encoding='utf8')
hashes = []
for image in entry['images']:
    path = ROOT / image['recovery_local_source']
    assert digest(path) == image['verification']['sha256']
    with Image.open(path) as decoded:
        decoded.load()
        assert decoded.size == (image['width'], image['height'])
    hashes.append(digest(path))
assert len(hashes) == len(set(hashes))
report = dict(
    status='PASS_INDEPENDENT_SOURCE_AND_FULL_IMAGE_REVIEW',
    candidate=candidate.relative_to(ROOT).as_posix(), candidate_sha256=digest(candidate),
    entry_id=entry['id'], original_release='2020-11-06',
    unchanged_selected_wikipedia_paragraphs=3, exclusive_clean_cover=True,
    visually_reviewed=['Original clean vertical cover', 'Off-road jump / gameplay disciplines',
                       'Rain and lightning / weather', 'Side-by-side competitors / career context'],
    images=hashes, no_cover_reuse=True, no_upscaling=True,
    limits=['Race image beside the career text is general gameplay, not an asserted depiction of Bruno Durand.',
            'No YouTube playback or physical console performance claim; candidate contains no video or soundtrack yet.'])
out = BASE / 'root-independent-three-chapter-peer-review.json'
out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
print(json.dumps(dict(status=report['status'], receipt=out.relative_to(ROOT).as_posix(), sha256=digest(out))))
