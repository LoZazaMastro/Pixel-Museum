"""Admit one reviewed primary storefront image; keep the other policy card held."""
from pathlib import Path
import copy
import hashlib
import json


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply(entries, root):
    root = Path(root)
    folder = root / "build/research/preservation-store-continuity"
    candidate = folder / "one-primary-storefront-illustration-candidate.json"
    receipt = folder / "root-independent-one-storefront-review.json"
    if not candidate.is_file() or not receipt.is_file():
        return dict(status="not_available")
    peer = json.loads(receipt.read_text(encoding="utf8"))
    if peer.get("status") != "PASS":
        return dict(status="not_admitted")
    digest = file_sha(candidate)
    if peer.get("candidate_sha256") != digest:
        raise ValueError("Preservation storefront candidate changed after review")
    source = json.loads(candidate.read_text(encoding="utf8"))
    entry = next(item for item in entries if item["id"] == source["entry_id"])
    feature = next(item for item in entry["editorial_features"] if item["id"] == source["feature_id"])
    body_sha = hashlib.sha256(json.dumps(feature["body"], ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    if body_sha != source["feature_body_sha256"]:
        raise ValueError("Preservation policy feature changed after image association review")
    for record in source["source_receipts"]:
        if file_sha(root / record["file"]) != record["sha256"]:
            raise ValueError("A preservation primary publisher source changed")
    added = 0
    known = {image["url"] for image in feature.get("images", [])}
    for image in source["images"]:
        if image["story_paragraph"] != 2:
            raise ValueError("Only the reviewed infrastructure paragraph has an approved image")
        if file_sha(root / image["recovery_local_source"]) != image["verification"]["sha256"]:
            raise ValueError("Preservation publisher screenshot changed")
        if image["url"] not in known:
            feature.setdefault("images", []).append(copy.deepcopy(image))
            known.add(image["url"])
            added += 1
    feature["explicit_story_media_only"] = True
    feature.setdefault("provenance", {})["reviewed_storefront_context_image"] = dict(
        candidate_sha256=digest, independent_review=receipt.relative_to(root).as_posix(),
        reviewed_body_sha256=body_sha, held=copy.deepcopy(source["held"]))
    return dict(status="PASS", entry_id=entry["id"], feature_id=feature["id"],
        candidate_sha256=digest, added_images=added, approved_paragraphs=[2], still_held_paragraphs=[3])
