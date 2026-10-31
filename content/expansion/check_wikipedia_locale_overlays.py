#!/usr/bin/env python3
"""Read-only regression tests for the reviewed reference translation join."""
from pathlib import Path
import copy
import importlib.util
import json
import tempfile
import unittest

PATH = Path(__file__).with_name("integrate_wikipedia_locales.py")
SPEC = importlib.util.spec_from_file_location("reference_locales", PATH)
JOIN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(JOIN)
CONTENT = PATH.parents[1]


class OverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = JOIN.read(CONTENT / "catalog.json")
        cls.base = {language: JOIN.read(CONTENT / "locales" / f"{language}.json") for language in JOIN.LANGUAGES}
        cls.batches = {name: JOIN.read(CONTENT / "expansion" / name) for name in JOIN.BATCH_IDS}
        cls.original_bytes = {path: JOIN.file_digest(CONTENT / path) for path in JOIN.source_paths(CONTENT)}

    def test_exact_join_and_preservation(self):
        catalog, base, batches = copy.deepcopy((self.catalog, self.base, self.batches))
        result, audit = JOIN.build(catalog, base, batches)
        self.assertEqual((audit["reference_entries"], audit["translation_pairs"], audit["translated_paragraphs"], audit["translated_existing_headings"]), (40, 160, 492, 264))
        self.assertEqual((catalog, base, batches), (self.catalog, self.base, self.batches))
        allowed = set.union(*JOIN.BATCH_IDS.values())
        for language in JOIN.LANGUAGES:
            original = self.base[language]
            self.assertTrue(all(result[language]["entries"][key] == value for key, value in original["entries"].items()))
            self.assertEqual(set(result[language]["entries"]) - set(original["entries"]), allowed if language in JOIN.TARGETS else set())
            if language not in JOIN.TARGETS:
                self.assertEqual(result[language], original)
        for language in JOIN.TARGETS:
            for entry_id in allowed:
                row = result[language]["entries"][entry_id]
                self.assertEqual(row["editorial_credit"], row["attribution"]["text"])
                self.assertNotIn("No substantive text changes", row["editorial_credit"])
                self.assertFalse(row["provenance"]["native_language_and_layout_signoff"])

    def test_source_field_drift_rejects(self):
        for field in JOIN.FIELDS:
            with self.subTest(field=field):
                catalog = copy.deepcopy(self.catalog)
                row = next(e for e in catalog["entries"] if e["id"] == "wikipedia-453246")
                row[field] = row[field] + (["changed"] if isinstance(row[field], list) else " changed")
                with self.assertRaisesRegex(ValueError, "stale English"):
                    JOIN.build(catalog, self.base, self.batches)

    def test_revision_and_attribution_drift_reject(self):
        for field in ("revision_id", "contributors_url", "license_url"):
            catalog = copy.deepcopy(self.catalog)
            row = next(e for e in catalog["entries"] if e["id"] == "wikipedia-101230")
            row["attribution"][field] = "changed"
            with self.assertRaisesRegex(ValueError, "stale source attribution"):
                JOIN.build(catalog, self.base, self.batches)

    def test_playhub_collision_and_nonreference_reject(self):
        base = copy.deepcopy(self.base)
        base["pt"]["entries"]["wikipedia-453246"] = {"body": ["protected"]}
        with self.assertRaisesRegex(ValueError, "cannot overwrite a Playhub"):
            JOIN.build(self.catalog, base, self.batches)
        catalog = copy.deepcopy(self.catalog)
        next(e for e in catalog["entries"] if e["id"] == "wikipedia-453246")["editorial_mode"] = "original_additive_feature"
        with self.assertRaisesRegex(ValueError, "not an English reference"):
            JOIN.build(catalog, self.base, self.batches)

    def test_bad_translation_structure_and_credit_reject(self):
        for field, value in (("body", ["shortened"]), ("story_headings", []), ("title", "bad\0title"),
                             ("summary", "x" * 16385), ("editorial_credit", "unchanged English")):
            batches = copy.deepcopy(self.batches)
            row = batches["wikipedia-locales-breakout-elite.json"]["entries"][0]["translations"]["it"]
            row[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                JOIN.build(self.catalog, self.base, batches)
        batches = copy.deepcopy(self.batches)
        batches["wikipedia-locales-rez-bastion.json"]["entries"].append(copy.deepcopy(batches["wikipedia-locales-rez-bastion.json"]["entries"][0]))
        with self.assertRaisesRegex(ValueError, "repeated"):
            JOIN.build(self.catalog, self.base, batches)

    def test_derived_snapshot_and_tamper_detection(self):
        # A temporary isolated content tree exercises writer/package contracts.
        with tempfile.TemporaryDirectory(prefix="reference-locales-") as folder:
            content = Path(folder)
            for relative in JOIN.source_paths(CONTENT):
                target = content / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                if relative == "catalog.json":
                    ids = set.union(*JOIN.BATCH_IDS.values())
                    target.write_bytes(JOIN.encoded({"entries": [e for e in self.catalog["entries"] if e["id"] in ids]}))
                else:
                    target.write_bytes((CONTENT / relative).read_bytes())
            before = {path: JOIN.file_digest(content / path) for path in JOIN.source_paths(content)}
            JOIN.generate(content)
            self.assertEqual(JOIN.verified_runtime_directory(content), content / "runtime-locales")
            self.assertEqual(before, {path: JOIN.file_digest(content / path) for path in before})
            with self.assertRaisesRegex(ValueError, "Never write original"):
                JOIN.generate(content, content / "locales")
            output = content / "runtime-locales/it.json"
            output.write_bytes(output.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "locale hash mismatch"):
                JOIN.verified_runtime_directory(content)
            JOIN.generate(content)
            source = content / "expansion/wikipedia-locales-breakout-elite.json"
            source.write_bytes(source.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "stale"):
                JOIN.verified_runtime_directory(content)
            with self.assertRaisesRegex(ValueError, "changed since independent"):
                JOIN.generate(content)

    @classmethod
    def tearDownClass(cls):
        after = {path: JOIN.file_digest(CONTENT / path) for path in cls.original_bytes}
        if after != cls.original_bytes:
            raise AssertionError("Read-only tests changed an authoring source")


if __name__ == "__main__":
    unittest.main(verbosity=2)
