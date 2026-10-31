"""Prepare a bounded review candidate; never changes the catalogues."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[1]
folder = root / 'build/research/gta2-three-concrete-cards'
sha = lambda data: hashlib.sha256(data).hexdigest()
catalog_bytes = (root / 'content/catalog.json').read_bytes()
entry = next(e for e in json.loads(catalog_bytes)['entries'] if e['id'] == 'workbook-10-22-grand-theft-auto-2')
paragraphs = json.loads((folder / 'paragraphs.json').read_text(encoding='utf8'))
specs = [
    (1, 5, 'Jobs on offer', ' Other improvements', 'Three gangs in each district',
     [('but lose it with their chief rivals', 'but loses it with their chief rivals')]),
    (2, 3, 'Like its predecessor, ', None, 'Score targets and police pursuit',
     [('Like its predecessor, the game', 'Grand Theft Auto 2')]),
    (3, 9, 'The game features', ' Emergency vehicles', 'Eleven radio stations across the city', []),
]
source = {
    'title': 'Grand Theft Auto 2',
    'url': 'https://en.wikipedia.org/w/index.php?oldid=1376513985',
    'publisher': 'English Wikipedia contributors',
    'license': 'Creative Commons Attribution-ShareAlike 4.0',
    'license_url': 'https://creativecommons.org/licenses/by-sa/4.0/',
    'attribution': 'Selected English Wikipedia passage; standalone wording and grammar edits explicitly recorded. Headings supplied editorially.',
}
rows = []
for index, source_index, start, end, heading, edits in specs:
    original = paragraphs[source_index]
    begin = original.index(start)
    finish = original.index(end, begin) if end else len(original)
    selected = original[begin:finish]
    body = selected
    for before, after in edits:
        assert body.count(before) == 1
        body = body.replace(before, after)
    rows.append({
        'entry_id': entry['id'], 'source_chapter_index': index,
        'old_body': entry['body'][index], 'old_body_sha256': sha(entry['body'][index].encode()),
        'old_heading': entry['story_headings'][index], 'heading': heading,
        'body': body, 'body_sha256': sha(body.encode()), 'source': source,
        'provenance': {
            'source_file': (folder / 'wikipedia-article.html').relative_to(root).as_posix(),
            'source_file_sha256': sha((folder / 'wikipedia-article.html').read_bytes()),
            'revision_id': 1376513985, 'paragraph_indices': [source_index],
            'source_paragraphs': [original], 'selected_character_span': [begin, finish],
            'full_paragraph': begin == 0 and finish == len(original),
            'adaptations': [{'from': a, 'to': b, 'reason': 'Standalone subject or singular agreement.'} for a, b in edits],
        },
    })
out = {
    'schema_version': 1, 'publication_status': 'candidate_pending_independent_review',
    'scope': 'Only GTA2 body1-3 and headings. Keep intro, dates, all images, soundtrack and video unchanged.',
    'catalog_at_discovery_sha256': sha(catalog_bytes),
    'wording_counts': {'verbatim': 1, 'adapted': 2}, 'replacements': rows,
    'limits': [
        'Current low-resolution box-back at paragraph1 is unchanged, not a newly admitted illustration.',
        'Paragraph2 and3 image gaps remain explicit; this prose review does not claim to complete illustrations.',
        'The API endpoint returned403; source is the successfully fetched full article HTML containing revision1376513985.',
        'Unreferenced emergency-radio and character-selection assertions omitted rather than copied.',
    ],
}
path = folder / 'three-concrete-gta2-cards-candidate.json'
path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(path, sha(path.read_bytes()))
