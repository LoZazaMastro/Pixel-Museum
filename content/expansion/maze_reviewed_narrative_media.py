"""Attach the two independently reviewed original Maze context artefacts."""
from pathlib import Path
import copy
import hashlib
import json


def apply(entries, root):
    root = Path(root)
    folder = root / "build/research/maze-original-context"
    candidate = folder / "two-original-narrative-images-candidate.json"
    receipt = folder / "independent-two-original-narrative-images-review.json"
    if not candidate.is_file() or not receipt.is_file():
        return dict(status="not_available")
    peer = json.loads(receipt.read_text(encoding="utf8"))
    if peer.get("status") != "PASS":
        return dict(status="not_admitted")
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if peer.get("candidate_sha256") != digest:
        raise ValueError("Maze narrative illustrations changed after review")
    source = json.loads(candidate.read_text(encoding="utf8"))
    entry = next(e for e in entries if e["id"] == source["entry_id"])
    body_sha = hashlib.sha256(json.dumps(entry["body"], ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    if body_sha != source["body_sha256"] or body_sha != peer["reviewed_body_sha256"]:
        raise ValueError("Maze prose changed after illustration association review")
    assert len(entry["body"]) == len(source["images"]) == 2
    for record in peer["source_receipts"]:
        if hashlib.sha256((root / record["file"]).read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError("A Maze primary museum source changed")
    hero = entry["images"][entry.get("preferred_image", 0)]["url"]
    known = {image["url"] for image in entry["images"]}
    added = 0
    for image in source["images"]:
        if image["url"] == hero:
            raise ValueError("Maze main image cannot be repeated internally")
        if hashlib.sha256((root / image["recovery_local_source"]).read_bytes()).hexdigest() != image["verification"]["sha256"]:
            raise ValueError("A Maze original image changed")
        if image["url"] not in known:
            entry["images"].append(copy.deepcopy(image))
            known.add(image["url"])
            added += 1
    entry["preferred_image"] = next(i for i, image in enumerate(entry["images"]) if image["url"] == hero)
    entry["explicit_story_media_only"] = True
    entry.setdefault("provenance", {})["maze_reviewed_narrative_media"] = dict(
        candidate_sha256=digest, independent_review=receipt.relative_to(root).as_posix(),
        reviewed_body_sha256=body_sha, held=copy.deepcopy(source["held"]))
    for record in source["sources"]:
        if not any(item.get("url") == record["url"] for item in entry.get("sources", [])):
            entry.setdefault("sources", []).append(copy.deepcopy(record))
    return dict(status="PASS", entry_id=entry["id"], candidate_sha256=digest,
        narrative_paragraphs=2, illustrated_paragraphs=2, added_images=added)
