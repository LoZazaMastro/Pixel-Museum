"""Verify the real biographies, minimal correction and exact source archives."""
import copy
import json
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / 'content'
MODULE = runpy.run_path(str(CONTENT / 'expansion/integrate_calendar_prose_05.py'))
DOCUMENT = MODULE['checked_document'](ROOT / MODULE['DECLARATION'])


def baseline():
    entries = json.loads((CONTENT / 'catalog.json').read_text(encoding='utf-8'))['entries']
    languages = {path.stem: json.loads(path.read_text(encoding='utf-8')) for path in (CONTENT / 'locales').glob('*.json')}
    path = CONTENT / 'calendar-prose-restoration-audit-05.json'
    if path.exists():
        audit = json.loads(path.read_text(encoding='utf-8'))
        by_id = {row['id']: row for row in entries}
        for record in audit['original_records']:
            daily = record['original_daily']
            by_id[daily['id']] = daily
            case = next(row for row in DOCUMENT['biography_cases'] + DOCUMENT['english_correction_cases'] if row['edition_id'] == daily['id'])
            old = record['original_canonical']
            if old is None:
                by_id.pop(case['target_canonical_id'], None)
            else:
                by_id[old['id']] = old
        entries = list(by_id.values())
        for row in audit['removed_canonical_locale_overlays']:
            languages[row['locale']]['entries'][row['entry_id']] = row['record']
    return entries, languages


class Prose05Tests(unittest.TestCase):
    def test_biographies_and_one_clause_preserve_every_archival_language(self):
        entries, languages = baseline()
        original = copy.deepcopy(entries)
        source_languages = copy.deepcopy(languages)
        result = MODULE['integrate'](entries, languages, DOCUMENT)
        lookup = {row['id']: row for row in entries}
        self.assertEqual(len(entries), len(original) + 1)
        self.assertEqual(result['new_subjects_claimed'], 0)
        for case in DOCUMENT['biography_cases']:
            canonical = lookup[case['target_canonical_id']]
            self.assertEqual(canonical['body'], case['proposed_canonical']['body'])
            self.assertEqual(canonical['year'], case['proposed_canonical']['year'])
            self.assertEqual(canonical['images'], [])
            self.assertEqual(canonical['attribution']['license'], 'CC BY-SA 4.0')
        old = next(row for row in original if row['id'] == 'workbook-11-08-death-stranding')
        new = lookup[old['id']]
        self.assertEqual(new['body'][4], old['body'][4].replace('two first-party studios', 'an independent studio and a Sony-owned team'))
        self.assertEqual(new['body'][:4] + new['body'][5:], old['body'][:4] + old['body'][5:])
        for field in ('story_headings', 'images', 'videos', 'models', 'date'):
            self.assertEqual(new[field], old[field])
        for language, document in languages.items():
            for key, row in document['entries'].items():
                self.assertEqual(row, source_languages[language]['entries'][key], (language, key))
        affected = {case['edition_id'] for case in DOCUMENT['biography_cases'] + DOCUMENT['english_correction_cases']}
        affected |= {case['target_canonical_id'] for case in DOCUMENT['biography_cases'] + DOCUMENT['english_correction_cases']}
        for row in original:
            if row['id'] not in affected:
                self.assertEqual(row, lookup[row['id']])

    def test_late_source_drift_leaves_both_inputs_untouched(self):
        entries, languages = baseline()
        next(row for row in entries if row['id'] == 'workbook-11-08-death-stranding')['body'][4] += ' changed'
        original = copy.deepcopy((entries, languages))
        with self.assertRaises(ValueError):
            MODULE['integrate'](entries, languages, DOCUMENT)
        self.assertEqual((entries, languages), original)

    def test_unreviewed_proposal_and_stale_translation_are_rejected(self):
        entries, languages = baseline()
        proposal = copy.deepcopy(DOCUMENT)
        proposal['biography_cases'][0]['proposed_canonical']['body'][0] += ' extra'
        with self.assertRaises(ValueError):
            MODULE['integrate'](entries, languages, proposal)
        languages['it']['entries']['daily-02-22']['body'][0] += ' extra'
        with self.assertRaises(ValueError):
            MODULE['integrate'](entries, languages, DOCUMENT)


if __name__ == '__main__':
    unittest.main(verbosity=2)
