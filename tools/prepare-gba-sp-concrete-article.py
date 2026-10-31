"""Prepare a source-bound launch correction and four concrete hardware cards."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
F = ROOT / 'build/research/gba-sp-launch-and-concrete-article'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
source_path = F / 'wikipedia-original-api.json'
page = next(iter(json.loads(source_path.read_text(encoding='utf8'))['query']['pages'].values()))
assert page['pageid'] == 292722 and page['revisions'][0]['revid'] == 1380880449
paragraphs = page['extract'].splitlines()
assert 'February 14, 2003' in paragraphs[0]
catalog = json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf8'))
entry = next(e for e in catalog['entries'] if e['id'] == 'workbook-01-07-game-boy-advance-sp')
source = {'title': 'Game Boy Advance SP — English Wikipedia',
          'url': 'https://en.wikipedia.org/w/index.php?oldid=1380880449',
          'publisher': 'English Wikipedia contributors',
          'license': 'Creative Commons Attribution-ShareAlike 4.0',
          'license_url': 'https://creativecommons.org/licenses/by-sa/4.0/',
          'attribution': 'Complete English Wikipedia paragraphs reproduced verbatim; card headings supplied editorially.'}
changes = []
for index, (selected, heading) in enumerate([
    ([0, 1], 'Game Boy Advance SP'),
    ([5], 'Satoru Okada and the folding prototype'),
    ([6, 7], 'Illuminating the display'),
    ([19], 'Headphones and the charging port'),
]):
    body = '\n\n'.join(paragraphs[n] for n in selected)
    assert all(paragraphs[n] and not paragraphs[n].startswith('=') for n in selected)
    changes.append({
        'entry_id': entry['id'], 'source_chapter_index': index,
        'old_body': entry['body'][index], 'old_body_sha256': hashlib.sha256(entry['body'][index].encode()).hexdigest(),
        'old_heading': entry['story_headings'][index], 'heading': heading,
        'body': body, 'body_sha256': hashlib.sha256(body.encode()).hexdigest(), 'source': source,
        'provenance': {'source_file': source_path.relative_to(ROOT).as_posix(), 'source_file_sha256': sha(source_path),
                       'page_id': page['pageid'], 'revision_id': page['revisions'][0]['revid'],
                       'paragraph_indices': selected, 'source_paragraphs': [paragraphs[n] for n in selected],
                       'full_paragraph': True, 'adaptations': []},
    })
changes.append({'entry_id': entry['id'], 'old_date': entry['date'], 'year': 2003,
                'date': {'month': 2, 'day': 14, 'precision': 'day', 'region': ''},
                'source': source, 'source_file': source_path.relative_to(ROOT).as_posix(),
                'source_file_sha256': sha(source_path), 'verified_visible_infobox_date': '14 February 2003',
                'reason': 'Replace the announcement date with the actual release date; keep the stable internal ID.'})
for field, value in [
    ('summary', 'An upgraded Game Boy Advance with a folding case, rechargeable battery and integrated screen lighting.'),
    ('subtitle', 'A folding Game Boy Advance'), ('event_semantics', ''),
]:
    old = entry.get(field, '')
    changes.append({'entry_id': entry['id'], 'field': field, 'old_value': old,
                    'old_value_sha256': hashlib.sha256(old.encode()).hexdigest(), 'value': value,
                    'provenance': {'source_file': source_path.relative_to(ROOT).as_posix(), 'source_file_sha256': sha(source_path)},
                    'adaptation': 'Concise editorial summary of the cited hardware facts.'})
candidate = {'schema_version': 1, 'publication_status': 'NEXT_PENDING_INDEPENDENT_PEER',
             'scope': 'Four concrete Wikipedia hardware cards, launch date instead of announcement, and three concise metadata corrections. Original AGS-001 front lighting is explicitly distinguished from the later backlit revision.',
             'changes': changes, 'unchanged_article_card_count': 4, 'no_console_model_added': True}
path = F / 'four-wikipedia-cards-and-real-launch-candidate.json'
path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(path.relative_to(ROOT), sha(path))
