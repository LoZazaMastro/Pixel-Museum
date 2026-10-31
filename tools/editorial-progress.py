#!/usr/bin/env python3
"""Reconcile commissioned writing with real draft files and runtime placement.

A source list, outline or paragraph count never qualifies as a finished article.
This report distinguishes written prose, admitted text, media and final review.
"""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    plan_path = CONTENT / "editorial/history-backlog.json"
    catalog_path = CONTENT / "catalog.json"
    plan, catalog = read(plan_path), read(catalog_path)
    planned = {row["id"]: row for row in plan["entries"]}
    assert len(planned) == len(plan["entries"]), "Duplicate commission ID"
    drafts, source_files = {}, {}
    # These are actual authored batches. Research-only leads and JSON plans
    # elsewhere are intentionally excluded from the written-prose inventory.
    for path in sorted((CONTENT / "expansion").glob("editorial-*.json")):
        document = read(path)
        source_files[str(path.relative_to(ROOT)).replace("\\", "/")] = sha(path)
        for draft in document.get("entries", []):
            identifier = draft.get("id")
            if identifier not in planned:
                raise ValueError("Unplanned authored feature needs an explicit commission: " + str(identifier))
            if identifier in drafts:
                raise ValueError("Duplicate authored commission: " + identifier)
            body, headings, cards = (draft.get(key, []) for key in ("body", "story_headings", "cards"))
            if not (body and len(body) == len(headings) == len(cards)):
                raise ValueError("Incomplete authored card sequence: " + identifier)
            if any(not isinstance(text, str) or not text.strip() for text in body + headings):
                raise ValueError("Empty authored prose: " + identifier)
            source_ids = {source["id"] for source in draft.get("sources", [])}
            for index, card in enumerate(cards):
                if card.get("body_index", card.get("index")) != index or card.get("heading") != headings[index]:
                    raise ValueError("Card ordering differs from prose: " + identifier)
                citations = card.get("citations", [])
                if not citations or any(c.get("source_id") not in source_ids or not c.get("locator") for c in citations):
                    raise ValueError("Card lacks a resolving source locator: " + identifier)
            drafts[identifier] = (draft, str(path.relative_to(ROOT)).replace("\\", "/"))
    runtime = {}
    for entry in catalog["entries"]:
        if entry["id"] in planned:
            runtime[entry["id"]] = (entry, entry["id"])
        for feature in entry.get("editorial_features", []):
            if feature["id"] in runtime:
                raise ValueError("Duplicate runtime commission: " + feature["id"])
            runtime[feature["id"]] = (feature, entry["id"])
    records = []
    for identifier, commission in planned.items():
        authored, filename = drafts.get(identifier, ({}, None))
        admitted, destination = runtime.get(identifier, ({}, None))
        if admitted and (admitted["body"] != authored.get("body") or
                         admitted["story_headings"] != authored.get("story_headings")):
            raise ValueError("Runtime narrative differs from authored commission: " + identifier)
        images = admitted.get("images", [])
        mapped = sorted({image["story_paragraph"] for image in images
                         if type(image.get("story_paragraph")) is int and
                         0 <= image["story_paragraph"] < len(authored.get("body", []))})
        records.append({
            "commission_id": identifier,
            "title": authored.get("title", commission.get("proposed_title")),
            "draft_file": filename,
            "draft_body_sha256": hashlib.sha256(json.dumps(authored["body"], ensure_ascii=False).encode()).hexdigest() if authored else None,
            "written_cards": len(authored.get("body", [])),
            "runtime_destination": destination,
            "runtime_text_admitted": bool(admitted),
            "mapped_image_sections": mapped,
            "majority_cards_illustrated": len(mapped) * 2 > len(authored.get("body", [])) if authored else False,
            "editorial_signoff": False,
            "status": "written_requires_full_production_review" if authored else "research_and_writing_required",
        })
    report = {
        "schema_version": 1,
        "status": "production_incomplete",
        "scope": "Commissioned original features only; imported reference articles and original Playhub editions are accounted for separately in production-plan.json.",
        "catalog_sha256": sha(catalog_path),
        "plan_sha256": sha(plan_path),
        "authored_source_sha256": source_files,
        "counts": {
            "commissions": len(records),
            "with_written_prose": sum(bool(row["written_cards"]) for row in records),
            "research_and_writing_remaining": sum(not row["written_cards"] for row in records),
            "written_cards": sum(row["written_cards"] for row in records),
            "runtime_text_admitted": sum(row["runtime_text_admitted"] for row in records),
            "majority_cards_illustrated": sum(row["majority_cards_illustrated"] for row in records),
            "editorial_signoffs": 0,
        },
        "entries": records,
        "completion_rule": "Written prose is an intermediate state. A finished destination also needs source and date review, exact contextual media, language review, native presentation review and explicit sign-off. No final completion is inferred here.",
    }
    output = CONTENT / "editorial/commission-progress.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"], indent=2))


if __name__ == "__main__":
    build()
