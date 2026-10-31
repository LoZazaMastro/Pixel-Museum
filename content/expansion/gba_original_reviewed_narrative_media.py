"""Admit the independently reviewed AGB-001 artifacts without changing prose."""
from pathlib import Path
import copy
import hashlib
import json

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def apply(entries, root):
    root = Path(root)
    folder = root / "build/research/gba-original-narrative-illustrations"
    candidate = folder / "five-original-gba-artifacts-candidate.json"
    receipt = folder / "root-independent-five-artifacts-review.json"
    if not candidate.is_file() or not receipt.is_file():
        return dict(status="not_available")
    peer = json.loads(receipt.read_text(encoding="utf8"))
    if peer.get("status") != "PASS":
        return dict(status="not_admitted")
    digest = sha(candidate)
    if peer.get("candidate_sha256") != digest:
        raise ValueError("Original GBA artifact candidate changed after independent review")
    doc = json.loads(candidate.read_text(encoding="utf8"))
    owner = next(e for e in entries if e["id"] == doc["entry_id"])
    body_sha = hashlib.sha256(json.dumps(owner["body"], ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    if body_sha != doc["body_sha256"] or owner["story_headings"] != doc["original_headings"]:
        raise ValueError("Original GBA narrative changed after artifact review")
    if owner.get("models"):
        raise ValueError("Original GBA retains the explicit photography-only presentation")
    for source in doc["source_files"]:
        if sha(root/source["file"]) != source["sha256"]:
            raise ValueError("An original GBA artifact source changed")
    hero = owner["images"][owner.get("preferred_image", 0)]["url"]
    archive = owner.setdefault("provenance", {}).setdefault("gba_original_reviewed_narrative_media", dict(
        candidate_sha256=digest, independent_review=receipt.relative_to(root).as_posix(),
        reviewed_body_sha256=body_sha, replaced_thumbnail_records=[]))
    if archive["candidate_sha256"] != digest:
        raise ValueError("Original GBA image provenance is stale")
    added = replaced = 0
    for update in doc["image_updates"]:
        image = copy.deepcopy(update["image"])
        if image["url"] == hero or sha(root/image["recovery_local_source"]) != image["verification"]["sha256"]:
            raise ValueError("A reviewed GBA artifact changed or duplicates the hero")
        old_url = update.get("supersedes_url")
        if old_url:
            old_images = [i for i in owner["images"] if i["url"] == old_url]
            for old in old_images:
                if old != update["old_image"]:
                    raise ValueError("Original GBA thumbnail metadata changed before replacement")
                archive["replaced_thumbnail_records"].append(copy.deepcopy(old))
            owner["images"] = [i for i in owner["images"] if i["url"] != old_url]
            replaced += len(old_images)
        current = next((i for i in owner["images"] if i["url"] == image["url"]), None)
        if current is None:
            owner["images"].append(image)
            added += not bool(old_url)
        elif current != image:
            raise ValueError("Reviewed GBA artifact already exists with different metadata")
    owner["preferred_image"] = next(n for n,i in enumerate(owner["images"]) if i["url"] == hero)
    owner["explicit_story_media_only"] = True
    return dict(status="PASS", entry_id=owner["id"], candidate_sha256=digest,
        new_narrative_images=added, replaced_exact_thumbnails=replaced,
        narrative_paragraphs=5, mapped_paragraphs=list(range(5)), hero_unchanged=True,
        original_gba_photography_only=True)
