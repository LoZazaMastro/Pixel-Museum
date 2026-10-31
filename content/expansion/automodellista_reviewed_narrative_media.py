"""Admit seven independently reviewed original Auto Modellista artefacts."""
from pathlib import Path
import copy
import hashlib
import json


def apply(entries, root):
    root = Path(root)
    folder = root / "build/research/automodellista-original-press"
    candidate = folder / "seven-original-illustrations-candidate.json"
    receipt = folder / "independent-seven-original-illustrations-review.json"
    if not candidate.is_file() or not receipt.is_file():
        return dict(status="not_available")
    peer = json.loads(receipt.read_text(encoding="utf8"))
    if peer.get("status") != "PASS":
        return dict(status="not_admitted")
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if peer.get("candidate_sha256") != digest:
        raise ValueError("Auto Modellista artefacts changed after independent review")
    source = json.loads(candidate.read_text(encoding="utf8"))
    entry = next(e for e in entries if e["id"] == source["entry_id"])
    body_sha = hashlib.sha256(json.dumps(entry["body"], ensure_ascii=False,
        separators=(",", ":")).encode()).hexdigest()
    if peer.get("reviewed_body_sha256") != body_sha:
        raise ValueError("Auto Modellista prose changed after media association review")
    for record in source["source_receipts"]:
        if hashlib.sha256((root / record["file"]).read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError("An original Auto Modellista press/manual source changed")
    assert len(source["images"]) == len(entry["body"]) == len(source["story_headings"]) == 7
    assert sorted(image["story_paragraph"] for image in source["images"]) == list(range(7))
    hero = entry["images"][entry.get("preferred_image", 0)]["url"]
    known = {image["url"] for image in entry["images"]}
    added = 0
    for image in source["images"]:
        if image["url"] == hero:
            raise ValueError("Auto Modellista main cover cannot be reused internally")
        if hashlib.sha256((root / image["recovery_local_source"]).read_bytes()).hexdigest() != image["verification"]["sha256"]:
            raise ValueError("An original Auto Modellista image changed")
        if image["url"] not in known:
            entry["images"].append(copy.deepcopy(image))
            known.add(image["url"])
            added += 1
    entry["preferred_image"] = next(i for i, image in enumerate(entry["images"]) if image["url"] == hero)
    provenance = entry.setdefault("provenance", {})
    provenance.setdefault("automodellista_previous_headings", copy.deepcopy(entry.get("story_headings", [])))
    provenance["automodellista_reviewed_original_media"] = dict(candidate_sha256=digest,
        independent_review=receipt.relative_to(root).as_posix(), reviewed_body_sha256=body_sha)
    entry["story_headings"] = copy.deepcopy(source["story_headings"])
    entry["explicit_story_media_only"] = True
    for record in source["additional_sources"]:
        if not any(item.get("url") == record["url"] for item in entry.get("sources", [])):
            entry.setdefault("sources", []).append(copy.deepcopy(record))
    return dict(status="PASS", entry_id=entry["id"], candidate_sha256=digest,
        added_images=added, illustrated_paragraphs=7, narrative_paragraphs=7)
