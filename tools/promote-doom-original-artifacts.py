"""Admit the five source-bound, independently reviewed DOOM illustrations."""
from pathlib import Path
import copy
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "build/research/doom-illustrated-history"
candidate_path = FOLDER / "five-original-artifacts-candidate.json"
candidate_bytes = candidate_path.read_bytes()
digest = hashlib.sha256(candidate_bytes).hexdigest()
candidate = json.loads(candidate_bytes)
review_path = FOLDER / "root-independent-five-artifacts-review.json"
review = json.loads(review_path.read_text(encoding="utf8"))
if review.get("status") != "PASS" or review.get("candidate_sha256") != digest:
    raise ValueError("DOOM artifact review does not match the frozen candidate")

path = ROOT / "content/expansion/museum-story-illustrations-editorial-reviewed.json"
document = json.loads(path.read_text(encoding="utf8"))
for record in candidate["records"]:
    image = copy.deepcopy(record["image"])
    source = ROOT / image["recovery_local_source"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != image["verification"]["sha256"]:
        raise ValueError("DOOM source image changed: " + str(source))
    with Image.open(source) as decoded:
        decoded.load()
        if list(decoded.size) != [image["width"], image["height"]]:
            raise ValueError("DOOM source dimensions changed: " + str(source))
    image["independent_review"] = review_path.relative_to(ROOT).as_posix()
    image["reviewed_candidate_sha256"] = digest
    image["visual_review"] = review["visual_review"]
    images = document["entries"].setdefault(record["entry_id"], [])
    images[:] = [old for old in images if old.get("url") != image["url"]]
    images.append(image)

path.write_text(json.dumps(document, ensure_ascii=True, indent=2) + "\n", encoding="utf8")
(FOLDER / "five-original-artifacts-admission.json").write_text(
    json.dumps({"status": "PASS_SOURCE_ONLY", "candidate_sha256": digest,
                "admitted_images": len(candidate["records"]),
                "prose_changed": False, "master_catalog_changed": False,
                "remaining_subjects": candidate["remaining_unillustrated_subjects"]},
               ensure_ascii=True, indent=2) + "\n", encoding="utf8")
print("Five reviewed DOOM illustrations admitted to source module; master unchanged.")
