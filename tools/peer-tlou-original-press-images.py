"""Independent, read-only semantic/native-file review receipt for seven images."""
from pathlib import Path
from PIL import Image
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/tlou-original-illustrated'
CANDIDATE = BASE / 'seven-original-press-images-candidate.json'
EXPECTED = '9453e166fe69dbea7d1cd967a32b2fd51b932498e3a8494e9bf6b141a2c68e6d'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert sha(CANDIDATE) == EXPECTED
candidate = json.loads(CANDIDATE.read_text(encoding='utf8'))
catalog_path = ROOT / 'content/catalog.json'
catalog = json.loads(catalog_path.read_text(encoding='utf8'))
entry = next(e for e in catalog['entries'] if e['id'] == candidate['entry_id'])
next_path = ROOT / 'content/expansion/museum-playhub-clarity-pass4-candidate.json'
next_text = json.loads(next_path.read_text(encoding='utf8'))
body = list(entry['body'])
for replacement in next_text['replacements']:
    if replacement['entry_id'] != entry['id']:
        continue
    index = replacement['source_chapter_index']
    assert replacement['old_body'] == body[index]
    assert replacement['old_body_sha256'] == hashlib.sha256(body[index].encode()).hexdigest()
    body[index] = replacement['body']
assert len(body) == len(entry['body']) == 7
observations = [
    ('Joel leaps toward a prone opponent. Ellie is not present.',
     'Contextual illustration of close-range combat for the prototype/AI recollection, explicitly not the particular drugstore prototype.',
     'Previously incorrect Ellie-intervention caption corrected; the original candidate SHA19a6a8db… was not approved.'),
    ('Joel grapples with a hooded opponent; Ellie is visible crouched in the background.',
     'Finished character animation illustrates the animation/performance paragraph; does not claim studio rehearsal footage.', ''),
    ('Painted abandoned church interior with broken furnishings and strong warm light through stained glass.',
     'Environment artwork illustrates beauty/brutality contrast; correctly distinguished from a gameplay capture.', ''),
    ('Joel and Ellie stand beside a damaged sheriff car in an overgrown deserted town.',
     'Matches third-person traversal of post-pandemic towns in the pending concrete Wikipedia replacement.', ''),
    ('Crafting menu visibly selects HEALTH KIT with RAG and ALCOHOL ingredients.',
     'Direct visual match for scavenging and crafting health kits in the pending replacement.', ''),
    ('Desaturated Listen Mode image reveals an outlined enemy through a nearby obstacle.',
     'Direct visual match for the Listen Mode outline explanation; original PS3 UI.', ''),
    ('Joel crouches behind an obstacle while an infected opponent approaches.',
     'Combat/cover context for the enemy-reaction paragraph; this frame alone is not evidence of a particular human AI algorithm or companion behaviour.', ''),
]
source_page = BASE / 'gematsu-2013-original-screenshots.html'
html = source_page.read_text(encoding='utf8')
assert '2013-05-17T11:14:06+00:00' in html and 'June 14' in html
inventory = json.loads((BASE / 'native-2013-press-inventory.json').read_text(encoding='utf8'))
inventory_by_url = {i['url']: i for i in inventory}
rows, seen_urls, seen_sha = [], set(), set()
for index, image in enumerate(candidate['images']):
    assert image['story_paragraph'] == index
    path = ROOT / image['recovery_local_source']
    actual_sha = sha(path)
    with Image.open(path) as original:
        size = original.size
        assert size == (1280, 720)
    assert actual_sha == image['verification']['sha256']
    assert [*size] == image['verification']['native_source_dimensions']
    assert (image['width'], image['height']) == size
    assert image['url'] in html
    inventory_image = inventory_by_url[image['url']]
    assert inventory_image['sha256'] == actual_sha and inventory_image['file'] == image['recovery_local_source']
    assert image['url'] not in seen_urls and actual_sha not in seen_sha
    assert image['url'] not in {i['url'] for i in entry['images']}
    seen_urls.add(image['url'])
    seen_sha.add(actual_sha)
    visual, match, note = observations[index]
    rows.append({'story_paragraph': index, 'status': 'PASS', 'file': image['recovery_local_source'],
        'sha256': actual_sha, 'native_dimensions': list(size), 'viewed_full_native_file': True,
        'visual_subject': visual, 'paragraph_association': match, 'correction_note': note,
        'current_body_sha256': hashlib.sha256(entry['body'][index].encode()).hexdigest(),
        'next_body_sha256': hashlib.sha256(body[index].encode()).hexdigest()})
assert len(rows) == 7 and len(seen_sha) == 7
assert candidate['images'][0]['title'] == 'Joel in a close-range combat encounter'
assert 'not Ellie intervening' in candidate['images'][0]['caption']
assert 'artwork' in candidate['images'][2]['caption']
back = next(i for i in entry['images'] if i.get('story_paragraph') == 1)
receipt = {'status': 'PASS_after_required_subject_caption_correction',
    'candidate': CANDIDATE.relative_to(ROOT).as_posix(), 'candidate_sha256': EXPECTED,
    'reviewer': 'model_performance independent of root authoring',
    'entry_id': entry['id'], 'source_catalog_sha256': sha(catalog_path),
    'next_concrete_text_candidate': next_path.relative_to(ROOT).as_posix(),
    'next_concrete_text_candidate_sha256': sha(next_path),
    'source_publication': {'url': 'https://www.gematsu.com/2013/05/the-last-of-us-gameplay-screenshots',
        'title': 'The Last of Us gameplay, screenshots', 'author': 'Sal Romano',
        'date_published': '2013-05-17', 'game_edition': 'Original pre-release PlayStation 3 game',
        'local_html': source_page.relative_to(ROOT).as_posix(), 'html_sha256': sha(source_page),
        'live_web_read_also_confirmed_publication': True},
    'images': rows,
    'preservation_conditions': ['Keep all current prose; apply the separately reviewed pass4 concrete replacements as planned.',
        'Preserve preferred cover and physical PS3 back-cover artifact. Remove only the older back-cover story_paragraph=1 binding so the real animation image can occupy that paragraph.',
        'Keep all seven narrative images distinct and exclude the preferred cover from narrative reuse.',
        'These are actual 1280x720 historical publications; do not call them 4K, generated HD or later remaster captures.',
        'Copyright remains with original game/artwork rights holders; archive attribution is present and no CC licence is invented.',
        'Blocked publisher CDN403/Flickr429 originals remain held; none was retried or admitted.'],
    'preserved_hero_url': entry['images'][entry['preferred_image']]['url'],
    'preserved_back_cover_url': back['url'],
    'master_catalog_or_manifest_modified': False,
    'limits': ['Seven reviewed illustrations and exact pending paragraph associations; this does not establish complete coverage for all Last of Us articles or features.',
        'Photographs of development rehearsals/prototypes were not acquired; gameplay/artwork are captioned as contextual illustrations.']}
output = BASE / 'independent-seven-original-press-images-review.json'
output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(output.relative_to(ROOT), sha(output))
