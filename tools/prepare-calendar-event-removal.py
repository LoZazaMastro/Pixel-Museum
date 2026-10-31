"""Replace unrelated commemorative-day openings with game descriptions."""
from pathlib import Path
import json, hashlib

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/playhub-semantic-coverage/calendar-event-removal'
entries = {e['id']: e for e in json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf8'))['entries']}
specs = [
    ('daily-07-02', 'UFO- Enemy Unknown-full.json', 'X-COM: defending Earth', 1994, 3, 0, 'month', 'March 1994'),
    ('daily-06-05', 'Eco (2018 video game)-full.json', 'Building a civilisation together', 2018, 2, 6, 'day', 'February 6, 2018'),
    ('daily-04-15', 'Chicory- A Colorful Tale.json', 'A magical brush and a world without colour', 2021, 6, 10, 'day', 'June10,2021'),
    ('daily-05-02', 'Dave the Diver-full.json', 'Diving by day, sushi by night', 2023, 6, 28, 'day', 'June 28, 2023'),
]
replacements, dates, removals = [], [], []
for ident, filename, heading, year, month, day, precision, locator in specs:
    path = BASE / filename
    page = next(iter(json.loads(path.read_text(encoding='utf8'))['query']['pages'].values()))
    body = page['extract'].splitlines()[0]
    old = entries[ident]['body'][0]
    replacements.append(dict(entry_id=ident, source_chapter_index=0,
        old_heading=entries[ident]['story_headings'][0], old_body=old, old_body_sha256=hashlib.sha256(old.encode()).hexdigest(),
        heading=heading, body=body, body_sha256=hashlib.sha256(body.encode()).hexdigest(),
        source=dict(title=page['title'], url='https://en.wikipedia.org/w/index.php?oldid=' + str(page['revisions'][0]['revid']),
                    publisher='English Wikipedia contributors', license='Creative Commons Attribution-ShareAlike4.0',
                    license_url='https://creativecommons.org/licenses/by-sa/4.0/', attribution='Complete source paragraph reproduced verbatim; editorial heading.'),
        provenance=dict(source_file=path.relative_to(ROOT).as_posix(), source_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        page_id=page['pageid'], revision_id=page['revisions'][0]['revid'], extract_line_index=0),
        reason='Describe the game itself, without an unrelated international commemorative day.'))
    date = dict(month=month, day=day, precision=precision, region='')
    if entries[ident]['date'] != date:
        dates.append(dict(entry_id=ident, old_date=entries[ident]['date'], date=date, year=year,
                          source_url=replacements[-1]['source']['url'], locator='Release infobox: ' + locator,
                          date_kind='early_access' if ident == 'daily-06-05' else 'release'))

# Bee Simulator has no current English Wikipedia article. Preserve its existing
# concrete explanation rather than fabricating an encyclopaedic citation.
ident = 'daily-05-20'
old = entries[ident]['body'][0]
body = old.split('Bee Simulator provides a concrete video-game connection: ', 1)[1]
assert body.startswith('it ')
body = 'Bee Simulator ' + body[3:]
publisher_path = BASE / 'Bee-Simulator-publisher.html'
replacements.append(dict(entry_id=ident, source_chapter_index=0,
    old_heading=entries[ident]['story_headings'][0], old_body=old, old_body_sha256=hashlib.sha256(old.encode()).hexdigest(),
    heading='A park seen at bee scale', body=body, body_sha256=hashlib.sha256(body.encode()).hexdigest(),
    source=dict(title='Bee Simulator / original publisher listing',
                url='https://www.nintendo.com/en-gb/Games/Nintendo-Switch-games/Bee-Simulator-1650673.html',
                publisher='VARSAV / Bigben Interactive; publisher description hosted by Nintendo',
                license='Existing museum prose retained, supported by publisher product information. No Wikipedia or open text licence claimed.',
                license_url='', attribution='Existing factual paragraph retained after removing the World Bee Day introduction; no publisher prose copied.'),
    provenance=dict(source_file=publisher_path.relative_to(ROOT).as_posix(), source_file_sha256=hashlib.sha256(publisher_path.read_bytes()).hexdigest(),
                    unavailable_wikipedia_article='Bee Simulator (current English title query returned missing)',
                    transformation='Remove World Bee Day sentence and replace the editorial-connection lead with the game name; remaining prose unchanged.'),
    reason='No unrelated World Bee Day framing and no fabricated Wikipedia source.'))
dates.append(dict(entry_id=ident, old_date=entries[ident]['date'], date=dict(month=11, day=14, precision='day', region=''), year=2019,
                  source_url=replacements[-1]['source']['url'], locator='Nintendo original2019 release listing: 14/11/2019.'))

for ident in [s[0] for s in specs] + ['daily-05-20']:
    old_sources = entries[ident]['sources']
    # These two old citations describe a different game formerly sharing the
    # Playhub calendar slot. Keep their original records solely in provenance.
    unrelated = old_sources[:2]
    removals.append(dict(entry_id=ident, source_urls=[s['url'] for s in unrelated],
                         archived_sources=unrelated, reason='Legacy compound-calendar citations refer to a different game, not this entry.'))
out = ROOT / 'content/expansion/museum-calendar-event-removal-candidate.json'
out.write_text(json.dumps(dict(schema_version=1, publication_status='awaiting_independent_review', replacements=replacements,
                              date_corrections=dates, source_removals=removals,
                              review_scope='Five introductory cards, real game release dates and five pairs of unrelated legacy citations only. Other chapters and all existing media preserved.'), ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(out.relative_to(ROOT), hashlib.sha256(out.read_bytes()).hexdigest())
