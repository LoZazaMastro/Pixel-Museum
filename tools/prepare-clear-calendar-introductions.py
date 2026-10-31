"""Prepare direct Wikipedia introductions without calendar-event framing."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/playhub-semantic-coverage/wiki-clarity'
entries = {e['id']: e for e in json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf8'))['entries']}
specs = [
    ('daily-02-02', 'Frogger', 'Crossing the road and river', [(0, None)]),
    ('workbook-09-26-castlevania', 'Castlevania (1986 video game)', 'Simon Belmont enters Dracula\'s castle', [(0, 'Castlevania, known in Japan as Akumajō Dracula, is a 1986 platform game developed and published by Konami.'), (2, "Players control Simon Belmont, descendant of a legendary vampire hunter, who enters the castle of Count Dracula to destroy him when he suddenly reappears 100 years after Simon's ancestor vanquished him.")]),
    ('workbook-11-02-alex-kidd-in-miracle-world', 'Alex Kidd in Miracle World', 'A platform adventure for the Master System', [(0, 'Alex Kidd in Miracle World is a platform game developed and published by Sega for the Master System.'), (5, 'The player must finish levels and overcome obstacles and puzzles in both scrolling and single-screen environments. Throughout the 17 stages, Alex faces many monsters and the three henchmen of Janken the Great, before facing Janken himself.')]),
]
replacements = []
for entry_id, title, heading, selections in specs:
    path = BASE / (title + '.json')
    page = next(iter(json.loads(path.read_text(encoding='utf8'))['query']['pages'].values()))
    lines = page['extract'].splitlines()
    fragments = []
    spans = []
    for index, selected in selections:
        selected = lines[index] if selected is None else selected
        offset = lines[index].index(selected)
        fragments.append(selected)
        spans.append(dict(extract_line_index=index, start=offset, end=offset + len(selected)))
    body = ' '.join(fragments)
    old = entries[entry_id]['body'][0]
    replacements.append(dict(
        entry_id=entry_id, source_chapter_index=0,
        old_heading=entries[entry_id]['story_headings'][0], old_body=old,
        old_body_sha256=hashlib.sha256(old.encode()).hexdigest(), heading=heading,
        body=body, body_sha256=hashlib.sha256(body.encode()).hexdigest(),
        source=dict(title=title, url='https://en.wikipedia.org/w/index.php?oldid=' + str(page['revisions'][0]['revid']),
                    publisher='English Wikipedia contributors', license='Creative Commons Attribution-ShareAlike4.0',
                    license_url='https://creativecommons.org/licenses/by-sa/4.0/',
                    attribution='Verbatim Wikipedia paragraphs or complete selected sentences; editorial heading. No paraphrase or fabricated connective text.'),
        provenance=dict(source_file=path.relative_to(ROOT).as_posix(), source_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        page_id=page['pageid'], revision_id=page['revisions'][0]['revid'], source_text_spans=spans),
        reason='Introduce the actual game directly, without an unrelated commemorative day, editorial-date correction or regional-version warning. Other narrative paragraphs and media remain intact.'
    ))
out = ROOT / 'content/expansion/museum-clear-calendar-introductions-candidate.json'
out.write_text(json.dumps(dict(schema_version=1, publication_status='awaiting_independent_review', replacements=replacements,
                              date_corrections=[dict(entry_id='daily-02-02', old_date=entries['daily-02-02']['date'],
                                                     date=dict(month=8, day=0, precision='month', region=''), year=1981,
                                                     source_url='https://en.wikipedia.org/w/index.php?oldid=1380097033',
                                                     locator='Original arcade release infobox: August1981. February2 belongs to World Wetlands Day, not this game. No exact launch day invented.')],
                              review_scope='Three introductory paragraphs only, plus removal of the artificial Frogger anniversary date. All other chapters, images, videos and music retained.'), ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(out.relative_to(ROOT), hashlib.sha256(out.read_bytes()).hexdigest())
