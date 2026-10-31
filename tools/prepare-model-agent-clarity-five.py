"""Freeze fifteen source-exact clarity replacements, never mutate the catalogue."""
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/playhub-semantic-coverage/wiki-clarity/pass4'
OUT = ROOT / 'build/research/playhub-semantic-coverage/wiki-clarity/model-agent-five'
OUT.mkdir(exist_ok=True)


class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = False
        self.skip = 0
        self.parts = []
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.active = True
            self.parts = []
        if self.active and tag == 'sup':
            self.skip += 1

    def handle_endtag(self, tag):
        if tag == 'sup' and self.skip:
            self.skip -= 1
        if tag == 'p' and self.active:
            value = re.sub(r'\s+', ' ', ''.join(self.parts)).strip()
            if value:
                self.paragraphs.append(value)
            self.active = False

    def handle_data(self, data):
        if self.active and not self.skip:
            self.parts.append(data)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def api_source(pageid):
    path = BASE / f'wiki-{pageid}.json'
    data = json.loads(path.read_text(encoding='utf8'))
    page = next(iter(data['query']['pages'].values()))
    return {'title': page['title'], 'page_id': page['pageid'],
            'revision_id': page['revisions'][0]['revid'],
            'lines': page['extract'].splitlines(), 'file': path,
            'retrieval_kind': 'Full Wikipedia API plaintext extract and revision metadata'}


def star_source():
    path = BASE / 'star-soldier-exact-game.html'
    html = path.read_text(encoding='utf8')
    parser = Paragraphs()
    parser.feed(html)
    return {'title': 'Star Soldier (video game)',
            'page_id': int(re.search(r'"wgArticleId":(\d+)', html).group(1)),
            'revision_id': int(re.search(r'"wgRevisionId":(\d+)', html).group(1)),
            'lines': parser.paragraphs, 'file': path,
            'retrieval_kind': 'Actual full Wikipedia article HTML, HTTP200; reference markers omitted from prose'}


sources = {'hogan': api_source(994292), 'larry': api_source(2966250),
           'blaster': api_source(41314448), 'ffa': api_source(52764),
           'star': star_source()}
(OUT / 'full-source-lines.json').write_text(json.dumps({k: {'title': v['title'],
    'page_id': v['page_id'], 'revision_id': v['revision_id'], 'lines': v['lines'],
    'source_file': v['file'].relative_to(ROOT).as_posix(),
    'source_file_sha256': digest(v['file'].read_bytes())} for k, v in sources.items()},
    ensure_ascii=False, indent=2) + '\n', encoding='utf8')

def select(key, line, start=None, end=None):
    original = sources[key]['lines'][line]
    first = original.index(start) if start else 0
    last = original.index(end, first) + len(end) if end else len(original)
    value = original[first:last]
    assert value and value[-1] in '.!?"'
    assert first == 0 or original[first - 2:first] == '. '
    return original, value, first, last


# Only consecutive complete source sentences, never splice half-sentences.
plans = [
    ('workbook-06-12-hogan-s-alley', 'hogan', [
        (1, 'Recognising the hostile targets', 6, None, None),
        (2, 'Three modes and the bouncing cans', 13, 'There are three modes:', 'unlimited ammunition supply.'),
        (3, 'Which mistakes end a round', 13, 'An on-screen "MISS" counter', '10 or higher.'),
    ]),
    ('workbook-06-13-star-soldier', 'star', [
        (1, 'Piloting Caesar through sixteen stages', 4, None, 'foreground elements.'),
        (2, 'Flying under the station and finding capsules', 4, 'With the scrolling background', 'one bullet at a time.'),
        (3, 'More firing directions, a shield and Starbrain', 4, 'If two capsules are collected', None),
    ]),
    ('workbook-06-04-leisure-suit-larry-in-the-land-of-the-lounge-lizards', 'larry', [
        (1, 'Larry Laffer arrives in Lost Wages', 1, None, None),
        (2, 'Walking and typing commands', 10, None, None),
        (3, 'Taxis, money and the casino', 12, None, 'blackjack and slots.'),
    ]),
    ('workbook-06-17-blaster-master', 'blaster', [
        (1, 'Two viewpoints across eight connected levels', 10, None, None),
        (2, 'SOPHIA\u2019s cannon and limited special weapons', 12, None, None),
        (3, 'Leaving the tank to earn new abilities', 13, None, 'hover above the ground.'),
    ]),
    ('workbook-06-28-final-fantasy-adventure', 'ffa', [
        (4, 'Exploring the world and visiting its towns', 8, None, 'items and equipment.'),
        (5, 'Magic, experience and a charging attack', 9, None, None),
        (6, 'Weapons clear a path through dungeons', 8, 'A variety of enemies', None),
    ]),
]
catalog_path = ROOT / 'content/catalog.json'
catalog = json.loads(catalog_path.read_text(encoding='utf8'))
replacements, invariants = [], []
for entry_id, key, plan in plans:
    entry = next(e for e in catalog['entries'] if e['id'] == entry_id)
    source = sources[key]
    preserved = {k: v for k, v in entry.items() if k not in ('body', 'story_headings', 'sources')}
    invariants.append({'entry_id': entry_id, 'body_count': len(entry['body']),
        'changed_indices': [v[0] for v in plan],
        'preserved_body': {str(i): v for i, v in enumerate(entry['body']) if i not in [x[0] for x in plan]},
        'all_other_entry_fields_sha256': digest(json.dumps(preserved, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())})
    for target, heading, line, start, end in plan:
        original, body, first, last = select(key, line, start, end)
        assert body not in entry['body']
        replacements.append({'entry_id': entry_id, 'source_chapter_index': target,
            'index_semantics': 'Absolute active body index; existing concrete introduction and primary reporting preserved.',
            'old_heading': entry['story_headings'][target], 'old_body': entry['body'][target],
            'old_body_sha256': digest(entry['body'][target].encode()),
            'heading': heading, 'body': body, 'body_sha256': digest(body.encode()),
            'source': {'title': source['title'],
                'url': 'https://en.wikipedia.org/w/index.php?oldid=' + str(source['revision_id']),
                'publisher': 'English Wikipedia contributors', 'license': 'Creative Commons Attribution-ShareAlike 4.0',
                'license_url': 'https://creativecommons.org/licenses/by-sa/4.0/',
                'attribution': ('Complete source paragraph reproduced verbatim; card heading supplied editorially.' if body == original else
                    'Consecutive complete source sentences reproduced verbatim; remaining paragraph omitted and heading supplied editorially.')},
            'provenance': {'source_file': source['file'].relative_to(ROOT).as_posix(),
                'source_file_sha256': digest(source['file'].read_bytes()), 'page_id': source['page_id'],
                'revision_id': source['revision_id'], 'retrieval_kind': source['retrieval_kind'],
                'extract_line_indices': [line], 'source_paragraphs': [original],
                'selected_character_span': [first, last]}})
candidate = {'schema_version': 1, 'publication_status': 'awaiting_independent_review_not_admitted',
    'source_catalog_sha256': digest(catalog_path.read_bytes()),
    'scope': 'Replace fifteen generic templated cards across five original games. Preserve dates, body/card counts, all images and associations, videos, music, models and the concrete existing introductions. Final Fantasy Adventure indices0..3 and their primary reporting remain untouched.',
    'replacements': replacements, 'entry_invariants': invariants,
    'research_notes': ['Hogan\u2019s Alley selection uses the NES modes/miss counter in the release section, avoiding the conflicting arcade life/limited-ammunition text elsewhere in the same article.',
        'Star Soldier source is specifically the original video game (page25644305), not the similarly named series or later remake. Only original-game gameplay is selected.',
        'Larry selection excludes 1991 remake descriptions; Blaster Master selection excludes the grenade-pause exploit and later sequels.',
        'Final Fantasy Adventure source spans have no overlap; new text explains navigation, progression and route tools without repeating the preserved primary creator interviews.']}
path = OUT / 'candidate.json'
path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
assert len(replacements) == 15 and len({r['entry_id'] for r in replacements}) == 5
assert len({(r['entry_id'], r['source_chapter_index']) for r in replacements}) == 15
for row in replacements:
    start, end = row['provenance']['selected_character_span']
    assert row['body'] == row['provenance']['source_paragraphs'][0][start:end]
print(path.relative_to(ROOT), len(replacements), digest(path.read_bytes()))
print('New words:', sum(len(r['body'].split()) for r in replacements))
