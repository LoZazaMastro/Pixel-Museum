"""Wrong inherited subjects are omitted without altering any source writing."""
import copy
import json
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[2]
JOIN = runpy.run_path(str(ROOT / 'content/expansion/integrate_legacy_media_review.py'))


class LegacyMediaReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf-8'))['entries']
        lookup = {entry['id']:entry for entry in cls.entries}
        replacements = ROOT / 'content/legacy-media-replacement-integration-audit.json'
        if replacements.exists():
            for action in json.loads(replacements.read_text(encoding='utf-8'))['actions']:
                images = lookup[action['entry_id']]['images']
                for row in action['same_content_records_superseded']:
                    original = row['original_image']
                    images[:] = [image for image in images if image['url'] != original['url']]
                    images.insert(row['original_index'], copy.deepcopy(original))
        receipt_path = ROOT / 'content/legacy-image-visual-integration-audit.json'
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
            lookup = {entry['id']:entry for entry in cls.entries}
            grouped = {}
            for row in receipt['quarantined_associations']:
                grouped.setdefault(row['entry_id'], []).append(row)
            for identifier, rows in grouped.items():
                for row in sorted(rows, key=lambda r:r['original_image_index']):
                    images = lookup[identifier]['images']
                    if not any(image['url'] == row['original_image']['url'] for image in images):
                        images.insert(row['original_image_index'], copy.deepcopy(row['original_image']))

    def test_wrong_subjects_removed_and_original_writing_preserved(self):
        entries = copy.deepcopy(self.entries)
        before = {e['id']:{k:copy.deepcopy(e.get(k)) for k in
                  ('body','story_headings','date','sources','editorial_features')} for e in entries}
        receipt = JOIN['integrate'](entries, ROOT)
        self.assertEqual(receipt['visually_inspected_distinct_images'], 440)
        self.assertEqual(len(receipt['quarantined_associations']), 60)
        self.assertEqual({row['entry_id'] for row in receipt['quarantined_associations'] if row['index']==343}, {'switch','daily-01-12'})
        self.assertTrue(any(row['index'] == 3 and row['entry_id'] == 'daily-01-20'
                            for row in receipt['quarantined_associations']))
        for e in entries:
            self.assertEqual({k:e.get(k) for k in before[e['id']]}, before[e['id']])
        lookup = {e['id']:e for e in entries}
        for row in receipt['quarantined_associations']:
            self.assertNotIn(row['original_image']['url'], [i['url'] for i in lookup[row['entry_id']]['images']])
        self.assertEqual((receipt['rights_signoffs'], receipt['editorial_signoffs']), (0, 0))

    def test_changed_reviewed_bytes_rejected_without_partial_mutation(self):
        entries = copy.deepcopy(self.entries)
        nebula = next(e for e in entries if e['id'] == 'daily-01-20')['images'][0]
        nebula['verification']['sha256'] = '0' * 64
        before = copy.deepcopy(entries)
        with self.assertRaisesRegex(ValueError, 'Reviewed image bytes changed'):
            JOIN['integrate'](entries, ROOT)
        self.assertEqual(entries, before)

    def test_missing_reviewed_association_rejected_without_partial_mutation(self):
        entries = copy.deepcopy(self.entries)
        next(e for e in entries if e['id'] == 'daily-01-20')['images'].clear()
        before = copy.deepcopy(entries)
        with self.assertRaisesRegex(ValueError, 'association missing'):
            JOIN['integrate'](entries, ROOT)
        self.assertEqual(entries, before)


if __name__ == '__main__':
    unittest.main()
