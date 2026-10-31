"""Regression checks for the actual source-bound historical-date correction."""
import copy
import json
import runpy
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE = runpy.run_path(str(HERE / "integrate_calendar_events.py"))


class EventCorrectionChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = json.loads((HERE.parent / "catalog.json").read_text(encoding="utf-8"))["entries"]

    def test_verified_event_and_calendar_are_separate(self):
        entries = copy.deepcopy(self.entries)
        original = copy.deepcopy(entries)
        MODULE["integrate"](entries, HERE)
        self.assertEqual(entries, original)  # Already-assembled join is idempotent.
        by = {entry["id"]: entry for entry in entries}
        self.assertEqual(by["workbook-11-02-alex-kidd-in-miracle-world"]["date"]["day"], 1)
        self.assertEqual(by["daily-11-02"]["calendar"]["month"], 11)
        self.assertEqual(by["daily-11-02"]["calendar"]["day"], 2)
        self.assertEqual(by["workbook-01-08-pok-mon-x-and-y"]["event_semantics"], "announcement")
        self.assertEqual(by["pac-man"]["date"]["precision"], "year")
        for before, after in zip(original, entries):
            for field in ("body", "story_headings", "images", "models", "videos", "year", "kind"):
                self.assertEqual(before.get(field), after.get(field), (before["id"], field))

    def test_changed_source_rejects_atomically(self):
        entries = copy.deepcopy(self.entries)
        by = {entry["id"]: entry for entry in entries}
        by["daily-11-02"]["body"][0] += " Unreviewed replacement."
        before = copy.deepcopy(entries)
        with self.assertRaisesRegex(ValueError, "snapshot changed"):
            MODULE["integrate"](entries, HERE)
        self.assertEqual(entries, before)

    def test_declaration_cannot_change_prose_or_guess_date_precision(self):
        for change in ("body", "precision"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                document = json.loads((HERE / MODULE["FILENAME"]).read_text(encoding="utf-8"))
                if change == "body":
                    document["cases"][0]["proposed_daily_updates"] = {"body": ["Not authorised."]}
                else:
                    case = next(case for case in document["cases"] if case["edition_id"] == "daily-05-22")
                    case["proposed_canonical_updates"] = {"date": {"precision": "day", "month": 5, "day": 22, "region": "Japan"}}
                (directory / MODULE["FILENAME"]).write_text(json.dumps(document), encoding="utf-8")
                (directory / "calendar-features.json").write_bytes((HERE / "calendar-features.json").read_bytes())
                # Use the expected pre-correction metadata so rejection exercises
                # the field/precision gate rather than a changed receipt hash.
                entries = copy.deepcopy(self.entries)
                by = {entry["id"]: entry for entry in entries}
                for case in document["cases"]:
                    for role in ("daily", "canonical"):
                        expected = case["expected_" + role + "_snapshot"]
                        entry = by[expected["entry_id"]]
                        for field in ("title", "year", "kind", "date", "event_semantics"):
                            if expected[field] is None:
                                entry.pop(field, None)
                            else:
                                entry[field] = copy.deepcopy(expected[field])
                        entry.pop("event_metadata_review", None)
                before = copy.deepcopy(entries)
                with self.assertRaises(ValueError):
                    MODULE["integrate"](entries, directory)
                self.assertEqual(entries, before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
