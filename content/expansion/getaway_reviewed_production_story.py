"""Join the independently reviewed original Black Monday production materials."""
from pathlib import Path
import copy
import hashlib
import json


def apply(entries, root):
    root = Path(root)
    folder = root / "build/research/getaway-black-monday-illustrated"
    candidate = folder / "seven-illustrated-production-cards-candidate.json"
    receipt = folder / "independent-seven-production-cards-review.json"
    if not candidate.is_file() or not receipt.is_file():
        return dict(status="not_available")
    review = json.loads(receipt.read_text(encoding="utf8"))
    if review.get("publication_status") != "PASS":
        return dict(status="not_admitted")
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if review.get("candidate_sha256") != digest:
        raise ValueError("Black Monday production story changed after independent review")
    source = json.loads(candidate.read_text(encoding="utf8"))
    entry = next(owner for owner in entries if owner["id"] == source["entry_id"])
    already_applied = entry.get("body") == source["body"]
    if not already_applied:
        old_digest = hashlib.sha256(json.dumps(entry["body"], ensure_ascii=False).encode()).hexdigest()
        if old_digest != source["old_body_sha256"]:
            raise ValueError("Original Black Monday body changed before reviewed admission")
    assert len(source["body"]) == len(source["story_headings"]) == 7
    assert sorted(image["story_paragraph"] for image in source["images"] if "story_paragraph" in image) == list(range(7))
    assert len({image["url"] for image in source["images"]}) == 8
    for image in source["images"]:
        original = root / image["recovery_local_source"]
        if hashlib.sha256(original.read_bytes()).hexdigest() != image["verification"]["sha256"]:
            raise ValueError("Black Monday original press image changed")
    for document in source["source_documents"]:
        for field, digest_field in (("original", "sha256"), ("extracted_text", "extracted_text_sha256")):
            if hashlib.sha256((root / document[field]).read_bytes()).hexdigest() != document[digest_field]:
                raise ValueError("Black Monday original press document changed")
    provenance = entry.setdefault("provenance", {})
    provenance.setdefault("black_monday_previous_record", copy.deepcopy(source["original_record"]))
    provenance["black_monday_reviewed_production_story"] = dict(
        candidate=candidate.relative_to(root).as_posix(), candidate_sha256=digest,
        independent_review=receipt.relative_to(root).as_posix(),
        source_documents=copy.deepcopy(source["source_documents"]), source_iso=copy.deepcopy(source["source_iso"]),
        text_scope=source["text_scope"], rights_scope=source["rights_scope"])
    for field in ("body", "story_headings", "images", "preferred_image"):
        entry[field] = copy.deepcopy(source[field])
    entry["images"][entry["preferred_image"]]["story_paragraph"] = -1
    entry["explicit_story_media_only"] = True
    entry["editorial_mode"] = "illustrated_primary_production_history"
    entry["editorial_credit"] = ("Opening overview and mechanics reproduced from the attributed English Wikipedia revision under its Creative Commons Attribution-ShareAlike licence. "
        "Five production sections are original museum descriptions of Sony's 2004 press materials. Individual publisher, photographic and artwork rights remain with their respective owners.")
    for source_record in source["additional_sources"]:
        if not any(row.get("url") == source_record["url"] for row in entry.get("sources", [])):
            entry.setdefault("sources", []).append(copy.deepcopy(source_record))
    return dict(status="PASS", entry_id=entry["id"], candidate_sha256=digest,
                narrative_paragraphs=7, illustrated_paragraphs=7, unique_images=8,
                films_preserved=len(entry.get("videos", [])), already_applied=already_applied)
