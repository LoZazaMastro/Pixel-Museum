"""Check editorial joins without network calls, file writes or renderer fixtures."""
import copy
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
module = runpy.run_path(str(ROOT / 'integrate_calendar.py'))


def entry(identifier, title, year, **fields):
    return dict(id=identifier, title=title, year=year, kind='game',
                summary='Original summary.', body=['Original reference paragraph.'],
                sources=[], images=[], videos=[], models=[], related_ids=[], **fields)


canonical = entry('original', 'PlayStation', 1994)
regional = entry('daily-09-09', 'PlayStation', 1995, calendar_only=True,
                 calendar={'month': 9, 'day': 9}, linked_exhibit_id='original')
same = entry('same', 'Example', 2000)
calendar = entry('daily-01-01', 'Example', 2000, calendar_only=True,
                 calendar={'month': 1, 'day': 1}, linked_exhibit_id='same')
records = [canonical, regional, same, calendar]
original_copy = copy.deepcopy(calendar)
revision = dict(id='daily-01-01', summary='A researched summary.',
                body=[' '.join(['Fact'] * 30)] * 3,
                story_headings=['One', 'Two', 'Three'], sources=[{'title': 'Primary', 'url': 'https://example.org'}],
                editorial_mode='researched_calendar_revision')
before = {key: copy.deepcopy(calendar[key]) for key in ('year', 'calendar', 'images', 'videos', 'models')}
applied, archive = module['apply_revisions'](records, [{'entries': [revision]}], {'entries': [original_copy]})
assert applied == ['daily-01-01'] and archive == [original_copy]
assert all(calendar[key] == value for key, value in before.items())
report, old = module['integrate'](records, {})
assert regional['linked_exhibit_id'] == '' and canonical['body'] == ['Original reference paragraph.']
assert same['body'] == revision['body'] and same['summary'] == revision['summary']
assert same['year'] == 2000 and 'date' not in same
assert len(old) == 1 and old[0]['body'] == ['Original reference paragraph.']
for invalid in (dict(revision, year=2001), dict(revision, id='not-reviewed')):
    try:
        module['apply_revisions'](copy.deepcopy(records), [{'entries': [invalid]}], {'entries': [original_copy]})
        raise AssertionError('An invalid editorial override was accepted')
    except ValueError:
        pass
try:
    module['apply_revisions'](copy.deepcopy(records), [{'entries': [revision, revision]}], {'entries': [original_copy]})
    raise AssertionError('Duplicate revision accepted')
except ValueError:
    pass

# A reviewed language-only title correction is one subject, not a new event.
pokemon = entry('pokemon', 'Pokémon Red e Pokémon Green', 1996)
daily = entry('daily-02-27', pokemon['title'], 1996, calendar_only=True,
              calendar={'month': 2, 'day': 27}, linked_exhibit_id='pokemon')
module['apply_revisions']([pokemon, daily], [{'entries': [dict(revision, id=daily['id'], title='Pokémon Red and Green')]}], {'entries': [copy.deepcopy(daily)]})
module['integrate']([pokemon, daily], {})
assert pokemon['title'] == daily['title'] == 'Pokémon Red and Green'
assert daily['linked_exhibit_id'] == 'pokemon'
print('Calendar integration checks passed: immutable chronology/media, complete originals, revised summaries, language-only title correction, distinct regional event, strict reviewed IDs and duplicate rejection.')
