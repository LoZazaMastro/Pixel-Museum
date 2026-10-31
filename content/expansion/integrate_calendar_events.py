"""Apply reviewed event metadata without rewriting published narratives.

Both source and affected runtime fields are bound to the review declaration.
A failed check leaves the caller's entries unchanged.
"""
from __future__ import annotations

import copy
import hashlib
import json

FILENAME = "calendar-event-semantics-corrections-04.json"
DECLARATION_SHA256 = "a5c766b1ac5033022249b6d385d67323637d1c64fa4f0ddc0a618ebc9062b26d"
EDITIONS = frozenset(("daily-01-07", "daily-01-08", "daily-01-12",
                      "daily-05-13", "daily-05-22", "daily-11-02"))
UPDATE_FIELDS = frozenset(("date", "event_semantics"))


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")).hexdigest()


def snapshot(entry):
    date = entry.get("date", {})
    return {"entry_id": entry["id"], "title": entry["title"],
            "year": entry["year"], "kind": entry["kind"],
            "date": {"month": date.get("month", 0), "day": date.get("day", 0),
                     "precision": date.get("precision", "year"),
                     "region": date.get("region", "")},
            "event_semantics": entry.get("event_semantics"),
            "body_sha256": digest(entry.get("body", [])),
            "headings_sha256": digest(entry.get("story_headings", []))}


def integrate(entries, directory):
    raw = (directory / FILENAME).read_bytes()
    document = json.loads(raw)
    declaration_hash = hashlib.sha256(raw).hexdigest()
    if declaration_hash != DECLARATION_SHA256:
        raise ValueError("Event declaration changed since independent review")
    if (document.get("schema_version") != 1
            or {case["edition_id"] for case in document["cases"]} != EDITIONS
            or len(document["cases"]) != len(EDITIONS)):
        raise ValueError("Unexpected reviewed event case set")
    if hashlib.sha256((directory / "calendar-features.json").read_bytes()).hexdigest() != document["source_import_sha256"]:
        raise ValueError("Published source changed since event review")
    sources = {row["id"]: row for row in document["evidence"]}
    working = copy.deepcopy(entries)
    by_id = {entry["id"]: entry for entry in working}
    if len(by_id) != len(working):
        raise ValueError("Duplicate article before event correction")
    updates_by_id = {}
    for case in document["cases"]:
        for role in ("daily", "canonical"):
            identifier = case["expected_" + role + "_snapshot"]["entry_id"]
            combined = updates_by_id.setdefault(identifier, {})
            for key, value in case["proposed_" + role + "_updates"].items():
                if key in combined and combined[key] != value:
                    raise ValueError("Conflicting reviewed updates for " + identifier)
                combined[key] = copy.deepcopy(value)
    report = {"schema_version": 1, "review_file": FILENAME,
              "declaration_sha256": declaration_hash, "cases": [],
              "published_prose_changes": 0, "calendar_slot_changes": 0,
              "localized_prose_changes": 0, "expanded_date_precision": 0}
    for case in document["cases"]:
        checked, changed = [], []
        for role in ("daily", "canonical"):
            expected = case["expected_" + role + "_snapshot"]
            updates = case["proposed_" + role + "_updates"]
            if not set(updates) <= UPDATE_FIELDS:
                raise ValueError("Event review attempts an unapproved field change")
            entry = by_id.get(expected["entry_id"])
            if not entry:
                raise ValueError("Event review owner missing: " + expected["entry_id"])
            after = copy.deepcopy(expected)
            after.update(updates_by_id[expected["entry_id"]])
            actual = snapshot(entry)
            prior = entry.get("event_metadata_review", {})
            if actual != expected and not (actual == after and prior.get("declaration_sha256") == declaration_hash):
                raise ValueError("Event review source/snapshot changed: " + entry["id"])
            checked.append(entry["id"])
            if not updates:
                continue
            if (expected["date"]["precision"] != "day"
                    and updates.get("date", {}).get("precision") == "day"):
                raise ValueError("Calendar slot cannot expand historical date precision")
            evidence = [sources[identifier] for identifier in case["evidence_ids"]]
            before = {key: copy.deepcopy(expected[key]) for key in updates}
            entry.update(copy.deepcopy(updates))
            entry["event_metadata_review"] = {
                "review_file": "content/expansion/" + FILENAME,
                "declaration_sha256": declaration_hash,
                "source_edition_id": case["edition_id"],
                "original_fields": before,
                "evidence_urls": [source["url"] for source in evidence],
                "published_body_unchanged": True,
                "scheduled_month_day_unchanged": True}
            known = {source["url"] for source in entry.get("sources", [])}
            for source in evidence:
                if source["url"] not in known:
                    entry.setdefault("sources", []).append({
                        "title": "Primary event record: " + source["id"],
                        "url": source["url"],
                        "publisher": "Original manufacturer / preserved publisher record",
                        "attribution": "Bibliographic event/date evidence; no artwork licence implied."})
                    known.add(source["url"])
            changed.append(entry["id"])
        report["cases"].append({"edition_id": case["edition_id"],
                                "checked_entries": sorted(set(checked)),
                                "changed_entries": sorted(set(changed))})
    entries[:] = working
    report["changed_entries"] = len({identifier for case in report["cases"]
                                     for identifier in case["changed_entries"]})
    return report
