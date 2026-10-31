"""Prepare a source-bound editorial candidate; never mutate production."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/haunt-existing-prose-author-recovery'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

master = json.loads((ROOT / 'build/research/current1385-native-qa/master.json').read_text())
old = next(e for e in master['entries'] if e['id'] == 'wikipedia-19560129')
new = copy.deepcopy(old)
new['body'][2] = (
    'The game ran on DEC-10 & DEC-20 mainframes running TOPS-10 or TOPS-20. '
    'Although Laird once believed HAUNT was lost, his website now credits Jason Dyer '
    'with its recovery and offers a PDP emulator that includes the game.'
)
new['images'][0]['story_paragraph'] = -1
new['images'].append({
    'url': 'https://bluerenga.blog/wp-content/uploads/2018/07/hauntout.png',
    'source_page': 'https://bluerenga.blog/2018/07/26/haunt-the-big-empty/',
    'title': 'Finding a way around the haunted house',
    'caption': "Jason Dyer's map of the grounds, drawn during his 2018 playthrough of the recovered HAUNT. It shows the house, garden, garage and surrounding paths; the author notes that some empty outer rooms are omitted. This is a player-created map, not a game screenshot or an original 1979 document.",
    'creator': 'Jason Dyer',
    'credit': 'Jason Dyer / Renga in Blue',
    'license': 'Original author rights retained; no open licence asserted.',
    'width': 662, 'height': 535, 'story_paragraph': 1,
    'recovery_local_source': 'build/research/haunt-existing-prose-author-recovery/haunt-outside-map-original.png',
    'verification': {'sha256': sha(BASE / 'haunt-outside-map-original.png'),
                     'processing': 'Original published PNG, no enlargement or crop.'}
})
new['explicit_story_media_only'] = True
new['sources'] += [
    {'title': 'Computer Games Research: Haunt (It is Alive!)', 'url': 'https://laird.engin.umich.edu/haunt/', 'publisher': 'John E. Laird / University of Michigan'},
    {'title': 'HAUNT: The Big Empty', 'url': 'https://bluerenga.blog/2018/07/26/haunt-the-big-empty/', 'publisher': 'Jason Dyer / Renga in Blue'}
]
change = 'Paragraph 2 minimally corrected using John E. Laird\'s current recovery notice and Jason Dyer\'s 2018 recovered-game playthrough. The other four paragraphs are unchanged.'
new['attribution']['changes'] += ' ' + change
new['attribution']['text'] = new['attribution']['text'].replace('No substantive text changes; lead paragraphs selected and formatting removed.', change)
new['editorial_credit'] = new['attribution']['text']
new['factual_note'] = change
notice = {'source_url': 'https://laird.engin.umich.edu/haunt/',
          'access': 'Ordinary direct HTTP and web open returned 403; no retry or bypass. Public web search index read on this research turn.',
          'observed_facts': ['Author explicitly states the game lives, credits Jason Dyer, and provides a Windows PDP emulator containing HAUNT.', 'The former lost-game statement is explicitly corrected on the same page.'],
          'independent_local_evidence': 'actual-recovered-game-playthrough-source.html contains Dyer\'s 26 July 2018 account and original map.'}
(BASE / 'primary-author-recovery-notice-research.json').write_text(json.dumps(notice, indent=2) + '\n')
files = ['actual-recovered-game-playthrough-source.html', 'actual-recovered-game-input-source.html', 'haunt-outside-map-original.png', 'primary-author-recovery-notice-research.json']
candidate = {'status': 'CANDIDATE_PENDING_INDEPENDENT_PEER',
             'rows': [{'entry_id': old['id'], 'old_entry': old, 'new_entry': new}],
             'source_files': {str((BASE / p).relative_to(ROOT)).replace('\\', '/'): sha(BASE / p) for p in files},
             'expected_main_paragraph_groups': [[0], [1, 2, 3, 4]],
             'scope': change,
             'quality_limits': ['Map is a modest native 662x535 player-created illustration, not an actual terminal frame.', 'Existing correct longplay retained. Hardware cover exclusive. No new YouTube request, emulator or executable bundled.']}
out = BASE / 'five-haunt-paragraphs-minimal-recovery-correction-and-player-map-candidate.json'
out.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n')
print(out.relative_to(ROOT), sha(out))
