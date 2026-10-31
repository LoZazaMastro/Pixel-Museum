"""Apply exact subject-photo corrections from a separately reviewed candidate."""
from pathlib import Path
import copy
import hashlib
import json

FOLDER = "build/research/hardware-release-consolidation"


def apply(entries, root):
    root = Path(root)
    path = root / FOLDER / "hardware-subject-media-candidate.json"
    review_path = root / FOLDER / "subject-media-root-review.json"
    if not path.is_file() or not review_path.is_file():
        return {"status": "not_admitted"}
    receipt = json.loads(review_path.read_text(encoding="utf8"))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if receipt.get("status") != "PASS":
        return {"status": "not_admitted"}
    if receipt.get("candidate_sha256") != digest:
        raise ValueError("Hardware subject-media candidate changed after peer")
    document = json.loads(path.read_text(encoding="utf8"))
    owners = {entry["id"]: entry for entry in entries}
    admitted = []
    for change in document["entries"]:
        owner = owners[change["entry_id"]]
        original = copy.deepcopy(owner["images"])
        image_by_url = {image["url"]: image for image in original}
        rejected = [image for image in original if image["url"] in change["remove_urls"]]
        additions = []
        for image in change.get("images", []):
            source = root / image["recovery_local_source"]
            if hashlib.sha256(source.read_bytes()).hexdigest() != image["verification"]["source_sha256"]:
                raise ValueError("Hardware photograph source hash changed")
            if image["url"] not in image_by_url:
                additions.append(copy.deepcopy(image))
        owner["images"] = [image for image in owner["images"] if image["url"] not in change["remove_urls"]] + additions
        for image in owner["images"]:
            image.update(copy.deepcopy(change.get("metadata_overrides", {}).get(image["url"], {})))
        preferred = change["preferred_url"]
        owner["preferred_image"] = next(index for index, image in enumerate(owner["images"]) if image["url"] == preferred)
        owner["images"][owner["preferred_image"]]["story_paragraph"] = -1
        if rejected or additions:
            owner.setdefault("provenance", {}).setdefault("reviewed_hardware_subject_media", []).append(dict(
                removed_images=rejected, reasons=copy.deepcopy(change["reasons"]),
                candidate_sha256=digest, independent_review=review_path.relative_to(root).as_posix()))
        admitted.append(dict(entry_id=owner["id"], removed=len(rejected), added=len(additions), preferred_url=preferred))
    return dict(status="PASS", candidate_sha256=digest, entries=admitted)
