"""Finite-pair quarantine: do not mistake generated copy for translation."""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from editorial_translation_quarantine import REGISTRY, load_quarantine, quarantined


class KnownTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_quarantine()
        cls.rows = json.loads(REGISTRY.read_text(encoding='utf-8'))['units']

    def test_every_frozen_observed_pair_is_rejected(self):
        for row in self.rows:
            with self.subTest(owner=row['owner_id'], locale=row['locale'], field=row['field']):
                self.assertTrue(quarantined(row['english'], row['translated'], row['locale'], row['field'], self.registry))

    def test_carmack_heading_is_not_accepted_merely_because_english_matches(self):
        row = next(row for row in self.rows if row['owner_id'] == 'workbook-08-20-john-carmack' and row['locale'] == 'fr' and row['field'] == 'story_headings')
        options = [row['translated']]
        # The old exact-English matcher accepted this sole, unrelated candidate.
        self.assertEqual(len(set(options)), 1)
        safe = [value for value in options if not quarantined(row['english'], value, 'fr', 'story_headings', self.registry)]
        self.assertEqual(safe, [])

    def test_corrected_translation_of_same_english_is_not_quarantined(self):
        row = next(row for row in self.rows if row['owner_id'] == 'workbook-07-31-tecmo' and row['locale'] == 'es' and row['field'] == 'summary')
        good = 'El 31 de julio de 1967 se funda Nippon Yacht, la empresa que pasa por el nombre Tehkan antes de adoptar Tecmo.'
        self.assertFalse(quarantined(row['english'], good, 'es', 'summary', self.registry))

    def test_calendar_and_technology_vocabulary_are_not_banned(self):
        self.assertFalse(quarantined('The calendar becomes a mechanic.', 'El calendario se convierte en mecánica.', 'es', 'story_headings', self.registry))
        self.assertFalse(quarantined('Technology, production and tools shape this game.', 'La technologie, la production et les outils façonnent ce jeu.', 'fr', 'body', self.registry))

    def test_alternate_reference_template_and_its_topic_heading_are_quarantined(self):
        rows = [r for r in self.rows if r['owner_id'] == 'daily-04-17' and r['locale'] == 'es']
        self.assertTrue(any(r['field'] == 'body' and 'Referencias como' in r['translated'] for r in rows))
        self.assertTrue(any(r['field'] == 'story_headings' for r in rows))
        for row in rows:
            self.assertTrue(quarantined(row['english'], row['translated'], 'es', row['field'], self.registry))

    def test_wrong_game_bowser_translation_and_french_subject_template_are_rejected(self):
        wrong = next(r for r in self.rows if r['owner_id'] == 'workbook-02-12-super-mario-3d-world-bowser-s-fury' and r['locale'] == 'es' and r['field'] == 'body')
        self.assertIn('2021', wrong['english'])
        self.assertIn('Alpha Centauri', wrong['translated'])
        self.assertTrue(quarantined(wrong['english'], wrong['translated'], 'es', 'body', self.registry))
        french = next(r for r in self.rows if r['owner_id'] == 'workbook-05-30-capcom' and r['locale'] == 'fr' and r['field'] == 'body')
        self.assertTrue(quarantined(french['english'], french['translated'], 'fr', 'body', self.registry))

    def test_exact_pair_scope_does_not_spread_across_source_or_field(self):
        row = self.rows[0]
        self.assertFalse(quarantined(row['english'] + ' A different source.', row['translated'], row['locale'], row['field'], self.registry))
        self.assertFalse(quarantined(row['english'], row['translated'], row['locale'], 'title', self.registry))

    def test_eighteen_observed_current_tarn_pairs_are_rejected(self):
        path = ROOT / 'build/research/tarn-adams1978-four-language-completion/eighteen-observed-exact-source-bad-pairs-immutable-evidence.json'
        pairs = json.loads(path.read_text(encoding='utf-8'))['pairs']
        self.assertEqual(len(pairs), 18)
        for row in pairs:
            self.assertTrue(quarantined(row['english'], row['translated'], row['locale'], row['field'], self.registry))
        wrong = next(r for r in pairs if r['locale'] == 'it' and r['field'] == 'summary')
        self.assertIn('1978', wrong['english'])
        self.assertIn('Yakuza 6', wrong['translated'])

    def test_faithful_tarn_correction_and_untouched_good_reuse_are_allowed(self):
        source = 'Tarn Adams was born on April 17, 1978 and grew up programming alongside his brother Zach.'
        good = 'Tarn Adams nacque il 17 aprile 1978 e crebbe programmando insieme al fratello Zach.'
        self.assertFalse(quarantined(source, good, 'it', 'summary', self.registry))
        # This is an existing faithful unit from another current owner.
        self.assertFalse(quarantined('On July 25, 1978 Yōichi and Keiko Erikawa founded Koei.',
                                     'Il 25 luglio 1978 Yōichi e Keiko Erikawa fondano Koei.',
                                     'it', 'summary', self.registry))


if __name__ == '__main__':
    unittest.main()
