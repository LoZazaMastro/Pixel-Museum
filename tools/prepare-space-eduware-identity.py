"""Correct an archival name collision in a review-only candidate."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/space-eduware-correct-game-identity'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

master = json.loads((ROOT / 'build/research/current1385-native-qa/master.json').read_text())
old = next(e for e in master['entries'] if e['id'] == 'wikipedia-6888212')
new = copy.deepcopy(old)
new['archived_mismatched_media'] = {
    'reason': 'The original cover metadata explicitly identifies Space! by The Code Works on Commodore PET; the film explicitly identifies Greg Erker and Commodore PET. The eight prose paragraphs concern the different Edu-Ware Apple II RPG. Original records and physical files are retained outside reader display.',
    'images': copy.deepcopy(old['images']), 'videos': copy.deepcopy(old['videos'])
}
new['videos'] = []
new['images'] = []
page = 'https://www.retrogamestrove.com/game-232-space/'
for filename, width, height, anchor, title, caption in [
    ('Screenshot-2026-02-24-082714.png', 488, 331, -1, 'Space for the Apple II', 'The actual Edu-Ware Space title screen, showing version 2.5, in a later playthrough. This is the Apple II role-playing game, not the unrelated Commodore PET game Space!; the small published original is retained without enlargement.'),
    ('Screenshot-2026-02-19-143822-1.png', 1113, 764, 0, 'Characters before the adventures', 'The actual Space menu lists Characters, First Blood, Defend, Explore, Trader and High Finance. A later Apple II game capture published in the Retro Games Trove playthrough; not a photograph taken in 1979.'),
    ('Screenshot-2026-02-19-144411-1.png', 1111, 762, 2, 'A career can end during training', 'The actual Apple II game reports that Alec Meteor was killed in a training accident. This later playthrough capture illustrates the character-career system and its risks, not the unrelated PET game.')
]:
    url = f'https://i0.wp.com/www.retrogamestrove.com/wp-content/uploads/2026/02/{filename}?w={width}&ssl=1'
    new['images'].append({'url': url, 'source_page': page, 'title': title, 'caption': caption,
        'creator': 'Edu-Ware Services / Retro Games Trove (game capture)',
        'credit': 'Edu-Ware Services / Retro Games Trove',
        'license': 'Original game and capture rights retained; no open licence asserted.',
        'width': width, 'height': height, 'story_paragraph': anchor,
        'recovery_local_source': str((BASE / filename).relative_to(ROOT)).replace('\\', '/'),
        'verification': {'sha256': sha(BASE / filename), 'processing': 'Published original-size game capture, unchanged; source may include its own emulator scaling. No local upscale, crop or AI detail.'}})
new['images'].append({'url': 'https://www.mocagh.org/miscgame/eduware-80catalog.pdf#page=2',
    'source_page': 'https://www.mocagh.org/miscgame/eduware-80catalog.pdf',
    'title': 'Space and its second set of scenarios',
    'caption': 'The complete original Edu-Ware catalogue spread, dated 1 August 1980, lists Space and Space II, their character system, scenarios and disk requirements. A contemporary publisher document for the development and publication discussion, not a gameplay screenshot.',
    'creator': 'Edu-Ware Services, Inc.', 'credit': 'Edu-Ware Services / Museum of Computer Adventure Game History',
    'license': 'Original publisher document rights retained; no open licence asserted.',
    'width': 2346, 'height': 1798, 'story_paragraph': 4,
    'recovery_local_source': 'build/research/space-eduware-correct-game-identity/eduware1980-space-series-complete-page.png',
    'verification': {'sha256': sha(BASE / 'eduware1980-space-series-complete-page.png'), 'processing': 'Complete PDF page 2 rendered through PDFium at 216dpi, respecting the original page. No crop or invented detail.'}})
new['preferred_image'] = 0
new['explicit_story_media_only'] = True
new['sources'] += [{'title': 'Space: actual Apple II playthrough', 'url': page, 'publisher': 'Retro Games Trove'},
                   {'title': 'Original product catalogue, 1 August 1980', 'url': 'https://www.mocagh.org/miscgame/eduware-80catalog.pdf', 'publisher': 'Edu-Ware Services / Museum of Computer Adventure Game History'}]
files = ['actual-player-publication.html', 'Screenshot-2026-02-24-082714.png', 'Screenshot-2026-02-19-143822-1.png', 'Screenshot-2026-02-19-144411-1.png', 'eduware-original-1980-catalog.pdf', 'eduware1980-space-series-complete-page.png']
candidate = {'status': 'CANDIDATE_PENDING_INDEPENDENT_PEER',
    'rows': [{'entry_id': old['id'], 'old_entry': old, 'new_entry': new}],
    'source_files': {str((BASE / p).relative_to(ROOT)).replace('\\', '/'): sha(BASE / p) for p in files},
    'expected_main_paragraph_groups': [[0, 1], [2, 3], [4, 5, 6, 7]],
    'scope': 'All eight complete prose paragraphs and headings preserved. Correct a proven cross-game cover/video collision, not a cosmetic image swap. Three distinct illustrated chapters; original mismatched media archived, not deleted.',
    'quality_limits': ['Correct exclusive title-screen cover is only 488x331; honest native historical game image, not HD art.', 'Published gameplay captures have their own emulator scaling; no claim of untouched 1979 framebuffer or physical photograph.', 'No new YouTube request. Existing film belongs to a different game and is deliberately absent from display.']}
out = BASE / 'eight-existing-space-eduware-paragraphs-three-correct-game-chapters-candidate.json'
out.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n')
print(out.relative_to(ROOT), sha(out))

