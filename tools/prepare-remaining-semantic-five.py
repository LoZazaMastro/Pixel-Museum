"""Replace five further discursive cards with concrete Wikipedia passages."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'build/research/playhub-semantic-coverage/wiki-clarity/remaining-semantic-three'
load = lambda path: json.loads(path.read_text(encoding='utf8'))
sha = lambda data: hashlib.sha256(data).hexdigest()
entries = {e['id']: e for e in load(ROOT / 'content/catalog.json')['entries']}
plan = [
    ('workbook-10-08-mortal-kombat', 'Mortal Kombat (1992 video game).json', 2, 7, 'Five buttons, shared attacks and blocking'),
    ('workbook-10-08-mortal-kombat', 'Mortal Kombat (1992 video game).json', 3, 14, 'Shang Tsung, Goro and the tournament'),
    ('workbook-10-08-mortal-kombat', 'Mortal Kombat (1992 video game).json', 4, 8, 'Juggling and Fatalities'),
    ('workbook-01-23-parappa-the-rapper-2', 'PaRappa the Rapper 2.json', 3, 6, 'Bonus stages, remixed lessons and versus play'),
    ('workbook-09-27-code-vein', 'three-full-wikipedia-extracts.json', 3, 18, 'Vestiges preserve memories and Blood Codes'),
]
changes = []
for identifier, filename, index, line, heading in plan:
    source_path = FOLDER / filename
    pages = load(source_path)['query']['pages'].values()
    page = next(p for p in pages if p['title'] == ('Code Vein' if filename.startswith('three-') else filename[:-5]))
    paragraph = page['extract'].splitlines()[line]
    text = paragraph
    adaptations = []
    if identifier == 'workbook-09-27-code-vein':
        # Select complete opening sentences, before later plot revelations.
        end = paragraph.index(' On their search for the source of Blood Beads,')
        text = paragraph[:end]
        adaptations.append({'type': 'complete_sentence_selection', 'source_character_span': [0, end]})
        text = text.replace('a steady a supply', 'a steady supply')
        adaptations.append({'type': 'grammar_correction', 'old': 'a steady a supply', 'new': 'a steady supply'})
    entry = entries[identifier]
    changes.append({
        'entry_id': identifier, 'source_chapter_index': index,
        'old_body': entry['body'][index], 'old_body_sha256': sha(entry['body'][index].encode()),
        'old_heading': entry['story_headings'][index], 'heading': heading, 'body': text,
        'body_sha256': sha(text.encode()),
        'source': {'title': page['title'], 'url': 'https://en.wikipedia.org/w/index.php?oldid=' + str(page['revisions'][0]['revid']),
                   'publisher': 'English Wikipedia contributors', 'license': 'Creative Commons Attribution-ShareAlike 4.0',
                   'license_url': 'https://creativecommons.org/licenses/by-sa/4.0/',
                   'attribution': 'Adapted from the English Wikipedia article.' if adaptations else 'Complete English Wikipedia paragraph reproduced verbatim; heading supplied editorially.'},
        'provenance': {'source_file': source_path.relative_to(ROOT).as_posix(), 'source_file_sha256': sha(source_path.read_bytes()),
                       'page_id': page['pageid'], 'revision_id': page['revisions'][0]['revid'],
                       'paragraph_indices': [line], 'source_paragraphs': [paragraph],
                       'full_paragraph': not bool(adaptations), 'adaptations': adaptations},
    })
document = {'schema_version': 1, 'publication_status': 'candidate_pending_independent_review',
            'scope': 'Five additional over-discursive Playhub cards. Preserve all other prose, introductions, dates, images, music and video. Four verbatim source paragraphs, one complete-sentence selection with a declared grammar repair.',
            'replacements': changes}
path = FOLDER / 'five-additional-concrete-cards-candidate.json'
path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path.read_bytes()), 'cards': len(changes)}))
