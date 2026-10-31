"""Review-only reuse and original researcher photographs for Warrior."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/warrior-existing-prose-real-vector-game'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

master = json.loads((ROOT / 'build/research/current1387-after-storage-native-qa/master.json').read_text())
old = next(e for e in master['entries'] if e['id'] == 'wikipedia-7655526')
new = copy.deepcopy(old)
new['images'][0]['story_paragraph'] = -1
new['images'][1]['title'] = 'Vector knights and a printed castle'
new['images'][1]['caption'] = 'The original Vectorbeam/Cinematronics Warrior leaflet shows the cabinet, its illustrated surroundings and a game view. A contemporary publisher artifact, distinct from the exclusive illustrated front cover.'
for name, width, height, anchor, title, caption in [
    ('Figure-1.png', 520, 666, 0, 'The vector knight on a real display', "Knight 2 during attract mode on an actual Warrior machine, in a frame from Thomas H. Rousse's research video published in 2015. The vector figure is visible over the physical backdrop. This is a later documentation of original hardware, not a photograph made in 1979."),
    ('Figure-4.png', 1430, 953, 2, 'The two sticks and the reflected scenery', "Thomas H. Rousse's photograph of Warrior's physical controls and illustrated backdrop. The original sticks and reflected castle artwork remain visible; this later research photograph is not an image of the game's 1979 development or a claim that a failed prototype is shown.")
]:
    new['images'].append({'url': 'https://www.kinephanos.ca/wp-content/files/' + name,
        'source_page': 'https://www.kinephanos.ca/2015/reconstructing-warrior/',
        'title': title, 'caption': caption, 'creator': 'Thomas H. Rousse / Vectorbeam game and cabinet artwork',
        'credit': 'Thomas H. Rousse / Kinephanos; Warrior by Vectorbeam/Cinematronics',
        'license': 'Kinephanos article published under CC BY-NC-ND 4.0; original game and cabinet-art rights remain with their respective holders. Complete author-published figure retained unchanged.',
        'license_url': 'https://creativecommons.org/licenses/by-nc-nd/4.0/',
        'width': width, 'height': height, 'story_paragraph': anchor,
        'recovery_local_source': str((BASE / name).relative_to(ROOT)).replace('\\', '/'),
        'verification': {'sha256': sha(BASE / name), 'processing': 'Original author-published figure, no crop, enlargement or retouching.'}})
new['explicit_story_media_only'] = True
new['sources'].append({'title': 'Reconstructing WARRIOR: Vectorbeams, Natural Magick & Business Intrigue',
    'url': 'https://www.kinephanos.ca/2015/reconstructing-warrior/', 'publisher': 'Thomas H. Rousse / Kinephanos, 2015'})
files = [BASE / 'primary-researcher-game-publication.html', BASE / 'Figure-1.png', BASE / 'Figure-4.png']
files += [ROOT / im['recovery_local_source'] for im in old['images']]
candidate = {'status': 'CANDIDATE_PENDING_INDEPENDENT_PEER',
    'rows': [{'entry_id': old['id'], 'old_entry': old, 'new_entry': new}],
    'source_files': {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in files},
    'expected_main_paragraph_groups': [[0], [1], [2, 3]],
    'scope': 'All four complete paragraphs preserved verbatim and in order. Existing front cover remains exclusive, existing back leaflet retained at paragraph1; two whole original researcher figures provide actual game/hardware context.',
    'quality_limits': ['Actual game frame is only520x666 and has real camera noise; no HD or1979-photo claim.', 'The controls photograph is later field research, not a photograph of Skelly developing the game.', 'Museum gameplay-image HTTP403 was not retried; different primary research publication used. No YouTube request.']}
out = BASE / 'four-existing-warrior-paragraphs-three-real-game-and-hardware-chapters-candidate.json'
out.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n')
print(out.relative_to(ROOT), sha(out))
