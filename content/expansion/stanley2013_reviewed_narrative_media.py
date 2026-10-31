"""Add independently reviewed publisher images of the original 2013 standalone."""
from pathlib import Path
import copy
import hashlib
import json


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply(entries, root):
    root = Path(root)
    folder = root / "build/research/stanley-2013-original-illustrations"
    candidate = folder / "three-original-narrative-images-candidate.json"
    receipt = folder / "independent-three-original-narrative-images-review.json"
    if not candidate.is_file() or not receipt.is_file():
        return dict(status="not_available")
    peer = json.loads(receipt.read_text(encoding="utf8"))
    if peer.get("status") != "PASS":
        return dict(status="not_admitted")
    digest = file_sha(candidate)
    if peer.get("candidate_sha256") != digest:
        raise ValueError("Stanley 2013 publisher image candidate changed after review")
    source = json.loads(candidate.read_text(encoding="utf8"))
    entry = next(item for item in entries if item["id"] == source["entry_id"])
    body_sha = hashlib.sha256(json.dumps(entry["body"], ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    if body_sha != source["body_sha256"]:
        raise ValueError("Stanley 2013 paragraphs changed after image association review")
    primary = source["source"]
    if primary["steam_app_id"] != 221910 or file_sha(root / primary["file"]) != primary["sha256"]:
        raise ValueError("Stanley original-edition publisher source changed")
    data = json.loads((root / primary["file"]).read_text(encoding="utf8"))["221910"]["data"]
    gallery = {image["path_full"] for image in data["screenshots"]}
    hero = entry["images"][entry.get("preferred_image", 0)]["url"]
    if len(source["images"]) != 3 or {image["story_paragraph"] for image in source["images"]} != {0, 1, 2}:
        raise ValueError("Stanley requires three distinct reviewed narrative images")
    old_associations = []
    for removal in source["association_removals"]:
        for image in entry["images"]:
            if image["url"] == removal["url"] and image.get("story_paragraph") == removal["story_paragraph"]:
                old_associations.append(copy.deepcopy(removal))
                image.pop("story_paragraph", None)
    known = {image["url"]: image for image in entry["images"]}
    added = 0
    for image in source["images"]:
        if image["url"] not in gallery or image["url"] == hero:
            raise ValueError("Stanley image must be a unique original-edition publisher screenshot")
        if file_sha(root / image["recovery_local_source"]) != image["verification"]["sha256"]:
            raise ValueError("A Stanley original screenshot changed")
        if image["url"] not in known:
            entry["images"].append(copy.deepcopy(image))
            added += 1
        else:
            known[image["url"]].update(copy.deepcopy(image))
    entry["preferred_image"] = next(i for i, image in enumerate(entry["images"]) if image["url"] == hero)
    entry["story_headings"] = copy.deepcopy(source["story_headings"])
    entry["explicit_story_media_only"] = True
    record = entry.setdefault("provenance", {}).setdefault("stanley2013_reviewed_narrative_media", dict(
        candidate_sha256=digest, independent_review=receipt.relative_to(root).as_posix(),
        reviewed_body_sha256=body_sha, original_packaging_associations=old_associations,
        held=copy.deepcopy(source["held"])))
    if record["candidate_sha256"] != digest:
        raise ValueError("Stanley narrative image provenance does not match current review")
    return dict(status="PASS", entry_id=entry["id"], candidate_sha256=digest,
        narrative_paragraphs=3, illustrated_paragraphs=3, added_images=added)
