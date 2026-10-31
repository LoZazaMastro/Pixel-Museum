"""Read-only assertions for the third source71 editorial checkpoint."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
def read(p):
    return json.loads((ROOT / p).read_text(encoding="utf8"))
def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def owners(doc):
    result = {}
    for entry in doc["entries"]:
        result[entry["id"]] = entry
        result.update({f["id"]: f for f in entry.get("editorial_features", [])})
    return result

master_path = "content/catalog.json"
runtime_path = "build/runtime-preview/content/catalog.json"
master, runtime = read(master_path), read(runtime_path)
old = read("build/research/native-final16-media22-recoverable/files/content/catalog.json")
mo, ro, oo = owners(master), owners(runtime), owners(old)
prior = read("build/research/final16-media22-source71-final-proof.json")
records = list(prior["body_records"])
for row in records:
    eid, idx = row["entry_id"], row["index"]
    assert hashlib.sha256(mo[eid]["body"][idx].encode()).hexdigest() == row["body_sha256"]
    assert mo[eid]["body"][idx] == ro[eid]["body"][idx] == oo[eid]["body"][idx]
    assert mo[eid]["story_headings"][idx] == ro[eid]["story_headings"][idx] == oo[eid]["story_headings"][idx]
candidate = read("build/research/nobuyoshi-sano-primary-portrait/three-concrete-career-cards-candidate.json")
for row in candidate["replacements"]:
    eid, idx = row["entry_id"], row["source_chapter_index"]
    assert mo[eid]["body"][idx] == ro[eid]["body"][idx] == row["body"]
    assert mo[eid]["story_headings"][idx] == ro[eid]["story_headings"][idx] == row["heading"]
    records.append(dict(entry_id=eid, index=idx, body_sha256=row["body_sha256"]))
assert len(records) == 181
assert master["entry_aliases"] == runtime["entry_aliases"] == old["entry_aliases"]
assert len(master["entries"]) == len(runtime["entries"]) == len(old["entries"]) == 1395

# Compare actual attached media records, rather than the provenance archives.
added = []
for eid, entry in mo.items():
    previous = {i.get("url") for i in oo[eid].get("images", [])}
    for image in entry.get("images", []):
        if image.get("url") not in previous:
            assert image.get("story_paragraph", -1) >= 0
            runtime_images = ro[eid].get("images", [])
            assert any(i.get("url") == image["url"] and i.get("story_paragraph") == image["story_paragraph"] for i in runtime_images)
            added.append(dict(owner_id=eid, url=image["url"], paragraph=image["story_paragraph"]))
assert len(added) == 15, len(added)
assert sha("content/expansion/soundtrack-multitrack-priority-overrides.json") == "891855a14c335efc73a6eb801aaef6bad013f0bc803923f45a0602acbb388875"
integrity = read("build/research/sano3-media15-source71-integrity.json")
assert integrity["missing_full_or_preview"] == 0
proof = dict(status="PASS_COHERENT_SOURCE_RUNTIME_AND_LOCAL_MEDIA_NOT_COMPLETION",
    master_sha256=sha(master_path), runtime_sha256=sha(runtime_path),
    runtime_bytes=(ROOT/runtime_path).stat().st_size,
    runtime_remaining_bytes=16*1024*1024-(ROOT/runtime_path).stat().st_size,
    entries=len(master["entries"]), culture=342, aliases=len(master["entry_aliases"]),
    active_new_body_records_verified=len(records), body_records=records,
    new_media_in_third_group=added, required_local_images=integrity["required_unique_image_urls"],
    missing_full_or_preview=0, music_source71_unchanged=True,
    recovery="build/research/native-final16-media22-recoverable/manifest.json",
    recovery_manifest_sha256=sha("build/research/native-final16-media22-recoverable/manifest.json"),
    actual_composition_gap_last_verified=419,
    composition_gap_scope="Prior checkpoint only; fresh current-runtime composition profile requested, no inferred subtraction.",
    ready_to_claim_complete=False)
output = ROOT / "build/research/sano3-media15-source71-final-proof.json"
output.write_text(json.dumps(proof, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
print(json.dumps({k:v for k,v in proof.items() if k not in ("body_records", "new_media_in_third_group")}, indent=2))
