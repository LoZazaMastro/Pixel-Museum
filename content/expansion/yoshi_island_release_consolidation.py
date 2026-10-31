"""One release stop for the original 1995 game, with retired-ID navigation."""
from pathlib import Path
import copy
import hashlib
import json
import runpy

FOLDER = "build/research/yoshi-island-consolidation"


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def project(entries, source, candidate_sha256="research_projection"):
    canonical, retired = source["canonical_id"], source["retired_id"]
    by_id = {entry["id"]: entry for entry in entries}
    target = by_id[canonical]
    if retired not in by_id:
        if target.get("provenance", {}).get("yoshi_island_release_consolidation", {}).get("candidate_sha256") != candidate_sha256:
            raise ValueError("Yoshi's Island retired source is missing before reviewed admission")
        return dict(status="PASS", aliases={retired: canonical}, already_applied=True)
    old_source, old_target = copy.deepcopy(by_id[retired]), copy.deepcopy(target)
    for entry_id, body_sha in source["old_body_sha256"].items():
        if digest(by_id[entry_id]["body"]) != body_sha:
            raise ValueError("Yoshi's Island source text changed after merge review")
    target["body"] = [paragraph["body"] for paragraph in source["paragraphs"]]
    target["story_headings"] = [paragraph["heading"] for paragraph in source["paragraphs"]]
    target["title"] = source["title"]
    maps = source["paragraph_maps"]
    excluded = set(source["excluded_duplicate_cover_urls"])
    target["images"] = []
    seen = set()
    for original in (old_target, old_source):
        for image in original.get("images", []):
            if image["url"] in seen or image["url"] in excluded:
                continue
            image = copy.deepcopy(image)
            old_position = image.get("story_paragraph")
            image["story_paragraph"] = maps[original["id"]].get(str(old_position), -1) if isinstance(old_position, int) and old_position >= 0 else -1
            if image["url"] in source["image_associations"]:
                image["story_paragraph"] = source["image_associations"][image["url"]]
            target["images"].append(image)
            seen.add(image["url"])
    hero = old_target["images"][old_target.get("preferred_image", 0)]["url"]
    target["preferred_image"] = next(i for i, image in enumerate(target["images"]) if image["url"] == hero)
    target["images"][target["preferred_image"]]["story_paragraph"] = -1
    for field, key in (("sources", "url"), ("videos", "youtube_id"), ("models", "asset_file"), ("editorial_features", "id")):
        values, known = [], set()
        for original in (old_target, old_source):
            for value in original.get(field, []):
                identity = value.get(key)
                if identity in known:
                    continue
                value = copy.deepcopy(value)
                if field == "videos" and isinstance(value.get("story_paragraph"), int) and value["story_paragraph"] >= 0:
                    value["story_paragraph"] = maps[original["id"]].get(str(value["story_paragraph"]), -1)
                if field == "sources" and isinstance(value.get("story_paragraphs"), list):
                    value["story_paragraphs"] = sorted({maps[original["id"]][str(i)] for i in value["story_paragraphs"] if str(i) in maps[original["id"]]})
                values.append(value)
                known.add(identity)
        target[field] = values
    # Keep every real recording; never discard an alternative room to satisfy a merge.
    for field in ("soundtrack", "soundtrack_rooms", "experience", "experiences"):
        if not target.get(field) and old_source.get(field):
            target[field] = copy.deepcopy(old_source[field])
        elif field == "soundtrack" and target.get(field) and old_source.get(field):
            tracks = target[field].setdefault("tracks", [])
            known = {(r.get("youtube_id"), r.get("start_seconds"), r.get("end_seconds")) for r in tracks}
            for track in old_source[field].get("tracks", []):
                key = (track.get("youtube_id"), track.get("start_seconds"), track.get("end_seconds"))
                if key not in known:
                    tracks.append(copy.deepcopy(track))
                    known.add(key)
        elif field == "soundtrack_rooms" and target.get(field) and old_source.get(field):
            for room in old_source[field]:
                if room not in target[field]:
                    target[field].append(copy.deepcopy(room))
    target["related_ids"] = list(dict.fromkeys(old_target.get("related_ids", []) + old_source.get("related_ids", [])))
    target["tags"] = list(dict.fromkeys(old_target.get("tags", []) + old_source.get("tags", [])))
    target["explicit_story_media_only"] = True
    target["editorial_credit"] = ("Seven full paragraphs reproduced from the attributed English Wikipedia revision under CC BY-SA 4.0. "
        "Card headings supplied editorially. Original records, abstract previous descriptions and removed duplicate scans retained in provenance.")
    target.setdefault("attribution", {})["changes"] = ("Four original lead paragraphs retained at body indices 0, 1, 5 and 6. "
        "Three full gameplay paragraphs from the same frozen revision added at indices 2, 3 and 4; "
        "reference superscripts and layout whitespace removed. Card headings supplied editorially.")
    target.setdefault("provenance", {})["yoshi_island_release_consolidation"] = dict(
        candidate_sha256=candidate_sha256, prior_records=[old_target, old_source],
        aliases={retired: canonical}, paragraph_maps=copy.deepcopy(maps),
        paragraph_selection=copy.deepcopy(source["paragraphs"]),
        removed_redundant_material=copy.deepcopy(source["removed_redundant_material"]),
        excluded_duplicate_cover_urls=list(excluded))
    entries[:] = [entry for entry in entries if entry["id"] != retired]
    return dict(status="PASS", aliases={retired: canonical}, already_applied=False,
        canonical_id=canonical, paragraphs=len(target["body"]), images=len(target["images"]),
        videos=len(target["videos"]), music_tracks=len(target.get("soundtrack", {}).get("tracks", [])))


def apply(entries, root):
    root = Path(root)
    folder = root / FOLDER
    candidate, receipt = folder / "candidate.json", folder / "root-independent-review.json"
    if not candidate.is_file() or not receipt.is_file():
        return dict(status="not_available", aliases={})
    peer = json.loads(receipt.read_text(encoding="utf8"))
    if peer.get("status") != "PASS":
        return dict(status="not_admitted", aliases={})
    sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if peer.get("candidate_sha256") != sha:
        raise ValueError("Yoshi's Island merge changed after independent review")
    source = json.loads(candidate.read_text(encoding="utf8"))
    frozen = source["wikipedia_source_receipt"]
    if hashlib.sha256((root / frozen["file"]).read_bytes()).hexdigest() != frozen["sha256"]:
        raise ValueError("Yoshi's Island frozen gameplay revision changed")
    for original in source["original_images"]:
        if hashlib.sha256((root / original["file"]).read_bytes()).hexdigest() != original["sha256"]:
            raise ValueError("Yoshi's Island reviewed original image changed")
    result = project(entries, source, sha)
    redirects = runpy.run_path(str(root / "content/expansion/hardware_family_consolidation.py"))["redirect_references"]
    result["rewritten_references"] = redirects(entries, result["aliases"])
    for entry in entries:
        entry["related_ids"] = [item for item in entry.get("related_ids", []) if item != entry["id"]]
    return result
