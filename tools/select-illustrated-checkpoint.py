#!/usr/bin/env python3
"""Select an illustrated development checkpoint, without editing source stories."""
from pathlib import Path
import hashlib
import json
from hardware_presentation import photograph_only_console_ids

ROOT = Path(__file__).resolve().parents[1]
PHOTO_ONLY_IDS = photograph_only_console_ids(ROOT)


def select(catalog):
    entries = catalog["entries"]
    canonical = {entry["id"]: entry for entry in entries
                 if not entry.get("calendar_only")}

    def alias_parent(entry):
        parent = canonical.get(entry.get("linked_exhibit_id"))
        return parent if (entry.get("calendar_only") and parent
                          and parent["year"] == entry["year"]) else None

    def illustrated(entry):
        if not entry.get("body"):
            return False
        if entry["kind"] == "console" and not entry.get("models") and entry['id'] not in PHOTO_ONLY_IDS:
            return False
        return bool(entry.get("models")) or any(
            max(image.get("width", 0), image.get("height", 0)) >= 1600
            and min(image.get("width", 0), image.get("height", 0)) >= 800
            for image in entry.get("images", []))

    independent = [entry for entry in entries
                   if not alias_parent(entry) and illustrated(entry)]
    owners = {entry["id"] for entry in independent}
    selected = [entry for entry in entries if entry["id"] in owners or (
        alias_parent(entry) and alias_parent(entry)["id"] in owners)]
    return selected, independent


def main():
    source = ROOT / "content/catalog.json"
    catalog = json.loads(source.read_text(encoding="utf-8"))
    selected, independent = select(catalog)
    result = {
        "schema_version": 1,
        "edition": "Expanded illustrated development checkpoint",
        "initial_id": "game-boy",
        "source_catalog_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "entry_ids": [entry["id"] for entry in selected],
        "selection_policy": "A real bundled model, or a base-gallery image with explicit native dimensions at least1600long/800short. Console stops require bundled3D except the explicit original Game Boy Advance photograph preference. Canonical calendar aliases follow only included parents. No finished-production claim; full writing, media and translation work remains saved outside this trial.",
        "selection_counts": {
            "records": len(selected),
            "independent_timeline_subjects": len(independent),
            "models": len({model["asset_file"] for entry in selected
                           for model in entry.get("models", [])}),
        },
    }
    assert "game-boy" in result["entry_ids"]
    output = ROOT / "content/expanded-checkpoint-selector.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(json.dumps(result["selection_counts"], indent=2))


if __name__ == "__main__":
    main()
