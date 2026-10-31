"""Attach six independently inspected publisher illustrations to Horizon 6."""
from pathlib import Path
import copy
import hashlib
import json


def apply(entries, root):
    root = Path(root)
    folder = root / "build/research/fh6-illustrated-story"
    candidate = folder / "six-original-narrative-images-candidate.json"
    receipt = folder / "independent-six-original-images-review.json"
    if not candidate.is_file() or not receipt.is_file():
        return dict(status="not_available")
    peer = json.loads(receipt.read_text(encoding="utf8"))
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if peer.get("status") != "PASS":
        return dict(status="not_admitted")
    if peer.get("candidate_sha256") != digest:
        raise ValueError("FH6 narrative media changed after independent review")
    source = json.loads(candidate.read_text(encoding="utf8"))
    entry = next(owner for owner in entries if owner["id"] == source["entry_id"])
    body_sha = hashlib.sha256(json.dumps(entry["body"], ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    if peer.get("reviewed_body_sha256") != body_sha:
        raise ValueError("FH6 prose changed after its paragraph associations were reviewed")
    assert len(entry["body"]) == len(source["story_headings"]) == 7
    preferred = entry["images"][entry.get("preferred_image", 0)]["url"]
    for record in source["source_receipts"]:
        if hashlib.sha256((root / record["file"]).read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError("FH6 original publisher payload changed")
    known = {image["url"] for image in entry["images"]}
    added = 0
    for image in source["images"]:
        if image["url"] == preferred:
            raise ValueError("A main cover cannot be reused as a narrative picture")
        if hashlib.sha256((root / image["recovery_local_source"]).read_bytes()).hexdigest() != image["verification"]["sha256"]:
            raise ValueError("FH6 original publisher photograph changed")
        if image["url"] not in known:
            entry["images"].append(copy.deepcopy(image))
            known.add(image["url"])
            added += 1
    entry["preferred_image"] = next(index for index, image in enumerate(entry["images"]) if image["url"] == preferred)
    provenance = entry.setdefault("provenance", {})
    provenance.setdefault("fh6_previous_headings", copy.deepcopy(entry.get("story_headings", [])))
    provenance["fh6_reviewed_narrative_media"] = dict(candidate_sha256=digest,
        independent_review=receipt.relative_to(root).as_posix(), reviewed_body_sha256=body_sha,
        remaining_gap=copy.deepcopy(source["remaining_gap"]))
    entry["story_headings"] = copy.deepcopy(source["story_headings"])
    entry["explicit_story_media_only"] = True
    for url, title in (("https://forza.net/media", "Forza Horizon 6: original publisher media gallery"),
                       (source["primary_portrait_evidence"]["url"], "Forza Horizon 6: interview with cultural adviser Kyoko Yamashita")):
        if not any(record.get("url") == url for record in entry.get("sources", [])):
            entry.setdefault("sources", []).append(dict(url=url, title=title, publisher="Xbox Game Studios / Playground Games"))
    return dict(status="PASS", entry_id=entry["id"], candidate_sha256=digest,
                added_images=added, specific_illustrations=6, narrative_paragraphs=7,
                remaining_unillustrated_paragraphs=[3], whole_story_complete=False)
