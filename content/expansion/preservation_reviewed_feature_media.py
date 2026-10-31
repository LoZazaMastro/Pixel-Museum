"""Admit source-bound preservation artefacts only after independent review."""
from pathlib import Path
import copy
import hashlib
import json


def apply(entries, root):
    root = Path(root)
    folder = root / "build/research/preservation-illustrations"
    candidate = folder / "ten-primary-feature-illustrations-candidate.json"
    receipt = folder / "root-independent-ten-primary-illustrations-review.json"
    if not candidate.is_file() or not receipt.is_file():
        return dict(status="not_available")
    peer = json.loads(receipt.read_text(encoding="utf8"))
    if peer.get("status") != "PASS":
        return dict(status="not_admitted")
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if peer.get("candidate_sha256") != digest:
        raise ValueError("Preservation illustrations changed after independent review")
    source = json.loads(candidate.read_text(encoding="utf8"))
    owner = next(e for e in entries if e["id"] == source["entry_id"])
    features = {f["id"]: f for f in owner["editorial_features"]}
    for feature_id, reviewed in source["reviewed_bodies"].items():
        body = features[feature_id]["body"]
        body_sha = hashlib.sha256(json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        if body_sha != reviewed["body_sha256"] or len(body) != reviewed["paragraphs"]:
            raise ValueError("A preservation feature changed after image association review")
    for record in source["source_receipts"]:
        if hashlib.sha256((root / record["file"]).read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError("A preservation primary source changed")
    assert len(source["records"]) == len({r["image"]["verification"]["sha256"] for r in source["records"]}) == 10
    added = 0
    for record in source["records"]:
        feature = features[record["feature_id"]]
        image = record["image"]
        if hashlib.sha256((root / image["recovery_local_source"]).read_bytes()).hexdigest() != image["verification"]["sha256"]:
            raise ValueError("An original preservation illustration changed")
        if not any(existing["url"] == image["url"] for existing in feature.setdefault("images", [])):
            feature["images"].append(copy.deepcopy(image))
            added += 1
        feature["explicit_story_media_only"] = True
        if not any(item.get("url") == image["source_page"] for item in feature.get("sources", [])):
            feature.setdefault("sources", []).append(dict(url=image["source_page"],
                title=image["title"], publisher=image["creator"], story_paragraphs=[image["story_paragraph"]]))
    owner.setdefault("provenance", {})["preservation_reviewed_feature_illustrations"] = dict(
        candidate_sha256=digest, independent_review=receipt.relative_to(root).as_posix(),
        remaining_holds=copy.deepcopy(source["remaining_holds"]))
    return dict(status="PASS", entry_id=owner["id"], candidate_sha256=digest,
        added_images=added, illustrated_feature_paragraphs=10, total_feature_paragraphs=12,
        remaining_feature_paragraphs=2, whole_article_complete=False)
