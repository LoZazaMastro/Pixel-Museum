"""Prepare an additive image-only plan; never modify article text or catalogues."""
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / (sys.argv[1] if len(sys.argv) > 1 else 'build/research/steam-original-gameplay-multi-story')
assert WORK.resolve().is_relative_to((ROOT / 'build/research').resolve())
PLANS = {
    '2270': [(0, 0), (1, 4)],
    '38400': [(0, 0), (1, 1), (2, 2), (3, 4)],
    '6800': [(0, 0), (1, 2), (2, 4), (3, 5)],
    '70': [(0, 4), (2, 5), (3, 3), (4, 2), (5, 0), (6, 1)],
    '10': [(0, 2), (1, 4), (2, 5), (3, 3)],
    '377840': [(0, 0), (1, 1), (2, 3), (3, 5)],
    '12130': [(0, 1), (1, 0)],
    '9050': [(0, 0), (1, 4), (2, 2), (3, 1)],
    '254700': [(0, 2), (1, 1), (2, 4), (3, 3)],
    '7110': [(0, 0), (1, 2), (2, 1), (3, 5)],
    '7670': [(0, 2), (1, 0), (2, 5), (3, 1), (5, 4), (6, 3)],
    '7940': [(0, 4), (1, 1), (3, 5), (4, 0), (5, 3), (6, 2)],
    '17460': [(0, 4), (1, 3), (2, 5), (4, 0), (5, 1)],
    '292120': [(0, 4), (1, 0), (2, 5), (3, 2)],
    '24980': [(0, 2), (2, 4), (3, 1)],
    '105600': [(0, 0), (1, 2)],
    '235460': [(0, 5), (1, 3), (2, 1)],
    '219740': [(0, 1), (1, 3)],
    '391540': [(0, 0), (1, 2), (2, 5), (3, 3), (4, 1)],
}
QUALIFIERS = {
    '377840': 'Original-game PC port published in 2016; not a PlayStation launch capture.',
    '254700': 'Original 2005 game in its 2014 PC HD edition; not the 2023 remake.',
    '7110': 'PC Special Edition of the original Jade Empire; not an Xbox launch capture.',
    '292120': 'PC edition of the original game; not a PlayStation 3 capture.',
    '105600': 'Current publisher PC screenshots of the original evolving game; not the 2011 launch build.',
}
if len(sys.argv) > 2:
    configuration = json.loads((ROOT / sys.argv[2]).read_text(encoding='utf8'))
    PLANS = configuration['plans']
    QUALIFIERS.update(configuration.get('qualifiers', {}))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

catalogue_path = ROOT / 'content/catalog.json'
before = digest(catalogue_path)
entries = {e['id']: e for e in json.loads(catalogue_path.read_bytes())['entries']}
targets = json.loads((WORK / 'targets.json').read_bytes())
result = {'status': 'ADDITIVE_IMAGE_ONLY_REVIEW_PLAN', 'bindings': [], 'source_files': []}
for target in targets:
    app = next(iter(target['appids']), '')
    if app not in PLANS:
        continue
    entry = entries[target['entry_id']]
    meta = WORK / app / 'publisher.json'
    data = json.loads(meta.read_bytes())[app]['data']
    body_hash = hashlib.sha256(json.dumps(entry['body'], ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    result['source_files'].append({'path': meta.relative_to(ROOT).as_posix(), 'sha256': digest(meta)})
    seen = set()
    for paragraph, index in PLANS[app]:
        assert 0 <= paragraph < len(entry['body'])
        shot = next(s for s in data['screenshots'] if s['id'] == index)
        path = WORK / app / ('screen-' + str(index) + '.jpg')
        file_hash = digest(path)
        assert file_hash not in seen
        seen.add(file_hash)
        with Image.open(path) as image:
            image.load()
            width, height = image.size
        publisher = ' / '.join(data.get('publishers', []))
        image = {
            'url': shot['path_full'], 'source_page': 'https://store.steampowered.com/app/' + app + '/',
            'title': entry['title'] + ': publisher gameplay image ' + str(index + 1),
            'caption': QUALIFIERS.get(app, 'Official publisher screenshot of the original game, not a later remake.'),
            'creator': publisher, 'credit': publisher,
            'license': 'Original game and screenshot rights retained by their respective owners. No open licence claimed.',
            'width': width, 'height': height, 'native_long_edge': max(width, height),
            'kind': 'gameplay', 'story_paragraph': paragraph,
            'recovery_local_source': path.relative_to(ROOT).as_posix(),
            'verification': {'sha256': file_hash, 'visual_review': 'Source images viewed in per-game contact sheets; original file pixels unchanged.'},
        }
        result['bindings'].append({'entry_id': entry['id'], 'body_sha256': body_hash, 'image': image})
assert digest(catalogue_path) == before
destination = WORK / 'additive-original-gameplay-image-plan.json'
destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(len(PLANS), len(result['bindings']), digest(destination))
