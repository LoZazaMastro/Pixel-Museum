"""Independent mechanical evidence supporting the individually viewed VR/EVE media."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
BASE = "build/research/story-text-profile/priority-original-illustrations/"
def digest(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf8"))
master = load("content/catalog.json")
owners = {e["id"]: e for e in master["entries"]}
plans = [
    ("vr-feature/four-historical-vr-feature-illustrations-credit-corrected-candidate.json", "879920d01331f8620fa3f815859121b8a6c6c801a9d1f91072312a2c5e93fb83", "vr-feature/independent-four-historical-vr-feature-illustrations-review.json"),
    ("eve-feature/four-community-work-illustrations-candidate.json", "56312060f616f69915dfc04f31bec1ca4a6f25afa057017c3fe9fa5b538d4359", "eve-feature/independent-four-community-work-illustrations-review.json")]
for relative, expected, output in plans:
    path = BASE+relative
    assert digest(path) == expected
    doc = load(path)
    rows = []
    for source in doc["source_receipts"]:
        assert digest(source["path"]) == source["sha256"]
    for feature in doc["feature_entries"]:
        entry = owners[feature["entry_id"]]
        actual = next(f for f in entry["editorial_features"] if f["id"] == feature["feature_id"])
        assert actual["body"] == feature["feature_body"]
        body_sha = hashlib.sha256(json.dumps(actual["body"], ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        assert body_sha == feature["feature_body_sha256"]
        rgb_hashes = []
        for image in feature["images"]:
            filename = image["recovery_local_source"]
            assert digest(filename) == image["verification"]["source_sha256"]
            with Image.open(ROOT/filename) as im:
                im.load()
                original = im.size
                displayed = ImageOps.exif_transpose(im).convert("RGB")
                assert list(original) == image["verification"]["native_dimensions"]
                assert displayed.size == (image["width"], image["height"])
                rgb_sha = hashlib.sha256(displayed.tobytes()).hexdigest()
            rgb_hashes.append(rgb_sha)
            rows.append(dict(paragraph=image["story_paragraph"], source_file=filename,
                sha256=digest(filename), original_dimensions=original,
                display_dimensions=[image["width"],image["height"]], decoded_rgb_sha256=rgb_sha,
                visual_review="Full original individually opened; subject and paragraph association checked."))
        assert len(set(rgb_hashes)) == 4
        existing = doc["same_article_distinct_image_check"]["checked_existing"]
        for old in existing:
            assert digest(old["path"]) == old["sha256"]
            with Image.open(ROOT/old["path"]) as im:
                old_rgb = ImageOps.exif_transpose(im).convert("RGB")
                assert hashlib.sha256(old_rgb.tobytes()).hexdigest() not in rgb_hashes
    if relative.startswith("vr"):
        embedded = load(BASE+"vr-feature/independent-pdf-embedded-check.json")
        for image in doc["feature_entries"][0]["images"][2:]:
            v=image["verification"]
            assert any(r["page"] == v["pdf_page"] and r["name"] == v["embedded_image_name"] and r["sha256"] == v["source_sha256"] for r in embedded)
        observations = [
            "GDC photograph shows Morpheus prototype and physical DualShock 4. Commons records20March2014 and a confirmed CC BY2.0 publication; participant not identified as Ashforth. EXIF rotation handled correctly.",
            "Sony19March2014 article contains the exact1920x600 prototype asset and describes tracked head orientation. No laterPSVR2/Alyx equipment substitution.",
            "PDFslides4/5/9/15 inspected:90Hz11.11ms is historical Vive Developer Edition specification. Both selected image payloads match embedded bytes exactly. Fullslide15 rerendered/viewed and its NOT optimal explanatory-pipeline note checked.",
            "Room-scale figure depicts2015 tracking volume and movement. Unknown illustrator is explicitly not invented. No application performance, universal comfort or medical efficacy claim is approved."]
    else:
        observations = [
            "Both native3840x2160 screenshots show the actual Create Project and Duplicate Project interfaces; exact publisher asset URLs occur in CCP Stronger Organizations source dated1November2023.",
            "Full rescue poster visibly describes caches with launchers/probes. Public community guide embeds this exact poster; login-required filepage is not used to invent a CreativeCommons licence or individual artist.",
            "KatiaSae2March2024 forum post independently checked:5000th rescue is explicitly the organisation's own milestone, not proven by the poster.",
            "1222x900 screenshot shows Thera/Turnur connections, lifetimes and public in-game contributors. Exact original source is in2December2023 SignalCartel website announcement, credited KatiaSae/SkyDiamond engineering. CCP17January2025 report confirms anniversary/bookmark context. Historical routes are not current navigational advice."]
    receipt = dict(status="PASS", candidate_path=path, candidate_sha256=expected,
        checked_catalog_sha256=digest("content/catalog.json"), images=rows,
        reviewed_feature_paragraphs=4, observations=observations,
        source_receipts_verified=len(doc["source_receipts"]), same_article_unique_images=True,
        scope="Bounded source/rights/dimensions/pixels/subject/period/feature-association review. Does not certify whole-catalog completeness or application performance.",
        master_modified=False)
    (ROOT/(BASE+output)).write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    print(output, digest(BASE+output))
