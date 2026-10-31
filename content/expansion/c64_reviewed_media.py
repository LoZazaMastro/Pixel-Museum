"""Apply independently reviewed C64 paragraph media without changing prose."""
from pathlib import Path
import copy
import hashlib
import json


def apply(entries, root):
    root = Path(root)
    folder = root / "build/research/c64-illustrated-story"
    path = folder / "eight-paragraph-media-candidate.json"
    receipt = folder / "independent-eight-media-review.json"
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    review = json.loads(receipt.read_text(encoding="utf8"))
    if review.get("status") != "PASS" or review.get("candidate_sha256") != digest:
        raise ValueError("C64 media candidate has no matching independent review")
    candidate = json.loads(data)
    owner = next(entry for entry in entries if entry["id"] == candidate["entry_id"])
    features = {feature["id"]: feature for feature in owner.get("editorial_features", [])}
    groups = [(owner, "append", candidate["main_images"])]
    groups += [(features[row["feature_id"]], row["operation"], row["images"])
               for row in candidate["feature_images"]]
    count = 0
    for destination, operation, photographs in groups:
        for photo in photographs:
            source = root / photo["recovery_local_source"]
            if hashlib.sha256(source.read_bytes()).hexdigest() != photo["verification"]["sha256"]:
                raise ValueError("Reviewed C64 image changed: " + str(source))
            if not 0 <= photo["story_paragraph"] < len(destination["body"]):
                raise ValueError("Reviewed C64 paragraph association is invalid")
        provenance = destination.setdefault("provenance", {})
        if not isinstance(provenance, dict):
            destination["provenance"] = {"original_record": provenance}
            provenance = destination["provenance"]
        if operation == "replace":
            provenance.setdefault("c64_previous_feature_images", copy.deepcopy(destination.get("images", [])))
            destination["images"] = copy.deepcopy(photographs)
        else:
            images = destination.setdefault("images", [])
            for photo in photographs:
                old = next((image for image in images if image["url"] == photo["url"]), None)
                if old is None:
                    images.append(copy.deepcopy(photo))
                else:
                    old.update(copy.deepcopy(photo))
        destination["explicit_story_media_only"] = True
        provenance["c64_eight_media_review"] = {
            "candidate_sha256": digest,
            "receipt": receipt.relative_to(root).as_posix(),
            "scope": "Media association only; prose, cover and release date unchanged."}
        count += len(photographs)
    loading_path = root / "build/research/c64-loading-media/four-physical-artifacts-candidate.json"
    loading_receipt = loading_path.parent / "independent-four-media-review.json"
    loading_data = loading_path.read_bytes()
    loading_digest = hashlib.sha256(loading_data).hexdigest()
    loading_review = json.loads(loading_receipt.read_text(encoding="utf8"))
    if loading_review.get("status") != "PASS" or loading_review.get("candidate_sha256") != loading_digest:
        raise ValueError("C64 loading artifact candidate has no matching independent review")
    loading = json.loads(loading_data)
    feature = features[loading["feature_id"]]
    body_digest = hashlib.sha256(json.dumps(feature["body"], ensure_ascii=False,
                                           separators=(",", ":")).encode()).hexdigest()
    if body_digest != loading["source_feature_body_sha256"]:
        raise ValueError("C64 loading prose changed after media review")
    for original in loading["images"]:
        source = root / original["recovery_local_source"]
        if hashlib.sha256(source.read_bytes()).hexdigest() != original["sha256"]:
            raise ValueError("C64 loading source image changed")
        image = copy.deepcopy(original)
        image.update(width=image["source_width"], height=image["source_height"],
                     credit=image["creator"],
                     verification={"sha256": image["sha256"], "no_upscale": True},
                     independent_review=loading_receipt.relative_to(root).as_posix())
        photographs = feature.setdefault("images", [])
        old = next((p for p in photographs if p["url"] == image["url"]), None)
        if old is None:
            photographs.append(image)
        else:
            old.update(image)
    feature["explicit_story_media_only"] = True
    feature.setdefault("provenance", {})["c64_loading_media_review"] = {
        "candidate_sha256": loading_digest,
        "receipt": loading_receipt.relative_to(root).as_posix()}
    return {"status": "PASS", "candidate_sha256": digest, "associations": count,
            "loading_candidate_sha256": loading_digest, "loading_associations": 4}
