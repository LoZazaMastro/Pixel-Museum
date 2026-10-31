"""Attach the independently reviewed original Kinect context illustrations."""
from pathlib import Path
import copy
import hashlib
import json


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply(entries, root):
    root = Path(root)
    folder = root / "build/research/kinect-original-story"
    candidate = folder / "four-original-context-images-candidate.json"
    receipt = folder / "independent-four-context-images-review.json"
    if not candidate.is_file() or not receipt.is_file():
        return dict(status="not_available")
    peer = json.loads(receipt.read_text(encoding="utf8"))
    if peer.get("publication_status") != "PASS":
        return dict(status="not_admitted")
    digest = sha(candidate)
    if peer.get("candidate_sha256") != digest:
        raise ValueError("Kinect illustration candidate changed after review")
    source = json.loads(candidate.read_text(encoding="utf8"))
    entry = next(item for item in entries if item["id"] == source["entry_id"])
    body_sha = hashlib.sha256(json.dumps(entry["body"], ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    if body_sha != source["body_sha256"] or body_sha != peer["body_unchanged_sha256"]:
        raise ValueError("Kinect paragraphs changed after association review")
    hero = entry["images"][entry.get("preferred_image", 0)]["url"]
    if hero != peer["hero_unchanged"]["url"]:
        raise ValueError("Kinect original sensor main image changed")
    for record in peer["source_receipts"]:
        if sha(root / record["source_file"]) != record["source_sha256"]:
            raise ValueError("A Kinect primary source changed")
    images = source["images"]
    if len(images) != 4 or {image["story_paragraph"] for image in images} != set(range(4)):
        raise ValueError("Kinect requires four distinct reviewed associations")
    known = {image["url"]: image for image in entry["images"]}
    added = 0
    for image in images:
        if image["url"] == hero:
            raise ValueError("Kinect main image cannot be repeated internally")
        if sha(root / image["recovery_local_source"]) != image["verification"]["sha256"]:
            raise ValueError("A reviewed Kinect original image changed")
        if image.get("derivation"):
            derivation = image["derivation"]
            if sha(root / derivation["source_pdf"]) != derivation["source_pdf_sha256"]:
                raise ValueError("Kinect original research PDF changed")
        if image["url"] not in known:
            entry["images"].append(copy.deepcopy(image))
            added += 1
        else:
            known[image["url"]].update(copy.deepcopy(image))
    # The main product photograph remains the main image, never paragraph zero.
    next(image for image in entry["images"] if image["url"] == hero).pop("story_paragraph", None)
    entry["preferred_image"] = next(i for i, image in enumerate(entry["images"]) if image["url"] == hero)
    entry["story_headings"] = copy.deepcopy(source["story_headings"])
    entry["explicit_story_media_only"] = True
    entry.setdefault("provenance", {})["kinect_reviewed_narrative_media"] = dict(
        candidate_sha256=digest, independent_review=receipt.relative_to(root).as_posix(),
        reviewed_body_sha256=body_sha, held=copy.deepcopy(source["held"]))
    return dict(status="PASS", entry_id=entry["id"], candidate_sha256=digest,
        narrative_paragraphs=4, illustrated_paragraphs=4, added_images=added)
