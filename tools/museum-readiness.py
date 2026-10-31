"""Snapshot content coverage without treating host checks as a console test."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import runpy
import re
import unicodedata
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    path = ROOT / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


catalog = read("content/catalog.json")
entries = catalog["entries"]
history = read("content/human-history.json")
history_entries = history.get("entries", [])
history_target = max(340, read("content/expansion/human-history-seeds-extra.json").get("minimum_admitted_target", 340))
history_duplicate_ids = sorted(key for key, count in Counter(
    entry["id"] for entry in history_entries).items() if count > 1)
curation = read("content/expansion/human-history-curation.json")
history_excluded_titles = sorted({entry["title"] for entry in history_entries
                                if entry["title"] in curation.get("excluded_subjects", {})})
def subject_key(value):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower())


rejected_history_images = []
for hold_path in (ROOT / "content/expansion").glob("human-history-image-holds*.json"):
    for subject, held in json.loads(hold_path.read_text(encoding="utf-8")).get("entries", {}).items():
        if held.get("url"):
            rejected_history_images.append((subject, held))
history_rejected_images = [{"entry_id": entry["id"], "url": picture["url"]}
                           for entry in history_entries for picture in entry.get("images", [])
                           if any(picture.get("url") == held["url"] and
                                  (entry["id"] == held.get("entry_id") or subject_key(subject) in
                                   {subject_key(entry.get("title", "")),
                                    subject_key(entry.get("provenance", {}).get("seed_title", "")),
                                    subject_key(entry.get("provenance", {}).get("article_title", ""))})
                                  for subject, held in rejected_history_images)]
games = [entry for entry in entries if entry.get("kind") == "game"]
manifest = read("assets/images/manifest.json")
selector = read("content/full-museum-selector.json")
urls = set()
for entry in entries + history_entries:
    for owner in [entry, *entry.get("editorial_features", [])]:
        urls.update(image["url"] for image in owner.get("images", []) if image.get("url"))
missing = []
for url in sorted(urls):
    for kind in ("images", "previews"):
        relative = manifest.get(kind, {}).get(url)
        if not relative or not (ROOT / relative).is_file():
            missing.append({"url": url, "kind": kind})

projection = runpy.run_path(str(ROOT / "tools/runtime-catalog.py"))
runtime = projection["encoded"](projection["project"](catalog))
history_runtime = projection["encoded"](projection["project"](history))
history_incomplete = [entry["id"] for entry in history_entries
                      if not entry.get("body") or len(entry.get("images", [])) != 1 or not entry.get("sources")]
music = [entry for entry in games if entry.get("soundtrack", {}).get("tracks")]
music_priorities = read("content/expansion/user-soundtrack-priorities.json")
music_minimum = max(522, music_priorities.get("minimum_games_with_soundtrack", 522))
image_quality = read("build/research/local-image-resolution-audit.json")
weak_preferred_images = sorted({owner["id"] for image in image_quality.get("weak_images", [])
                                for owner in image.get("owners", []) if owner.get("cover")})
video = [entry for entry in games if entry.get("videos")]
music_candidates = read("content/expansion/soundtrack-broad-selections.json")
video_candidates = read("content/expansion/museum-video-selections.json")
video_approved = read("content/expansion/museum-video-approved-checkpoint.json")
issues = ["Historical timeline curation and period-image review are still in progress."]
if len(history_entries) < history_target:
    issues.append(f"Historical timeline contains {len(history_entries)} of at least {history_target} required events.")
if history_incomplete:
    issues.append("Historical entries are missing text, a single representative image or source attribution.")
if history_duplicate_ids:
    issues.append("Historical milestones share duplicate identifiers.")
if history_excluded_titles:
    issues.append("Explicitly excluded cultural subjects remain in the catalogue.")
if history_rejected_images:
    issues.append("Rejected cultural image URLs remain in the catalogue.")
if len(history_runtime) > 16 << 20:
    issues.append("Historical catalogue exceeds the native reader budget.")
if missing:
    issues.append("Referenced local images or previews are missing.")
if len(music) * 2 <= len(games):
    issues.append("Soundtrack rooms do not yet cover a majority of games.")
if len(music) < music_minimum:
    issues.append(f"Soundtrack rooms cover {len(music)} of at least {music_minimum} requested distinct games.")
if weak_preferred_images:
    issues.append("Preferred exhibit images still include small originals requiring individual quality review.")
if len(runtime) > 16 << 20:
    issues.append("Runtime catalogue exceeds the native reader budget.")
if music_candidates.get("publication_status") != "validated":
    issues.append("Expanded soundtrack candidates remain quarantined for identity review.")
if len(video_candidates.get("entries", [])) > len(video_approved.get("entries", [])):
    issues.append("Expanded video candidates exceed the approved checkpoint and remain under review.")
if video_approved.get("publication_status") != "semantic_validated":
    issues.append("Expanded video checkpoint has not passed its complete edition-identity review.")

report = {
    "checked_utc": datetime.now(timezone.utc).isoformat(),
    "authoring_sha256": hashlib.sha256((ROOT / "content/catalog.json").read_bytes()).hexdigest(),
    "entries": len(entries),
    "games": len(games),
    "historical_entries": len(history_entries),
    "historical_minimum_target": history_target,
    "historical_incomplete_entries": history_incomplete,
    "historical_duplicate_ids": history_duplicate_ids,
    "historical_excluded_titles": history_excluded_titles,
    "historical_rejected_images": history_rejected_images,
    "historical_runtime_bytes": len(history_runtime),
    "selected_entries": len(selector.get("entry_ids", [])),
    "explicit_asset_holds": selector.get("held", []),
    "entries_without_cover": [entry["id"] for entry in entries if not entry.get("images")],
    "unique_image_urls": len(urls),
    "missing_local_images_or_previews": missing,
    "runtime_bytes": len(runtime),
    "game_soundtrack_rooms": len(music),
    "minimum_requested_game_soundtrack_rooms": music_minimum,
    "game_soundtrack_percent": round(len(music) * 100 / max(1, len(games)), 2),
    "games_with_video": len(video),
    "games_with_video_percent": round(len(video) * 100 / max(1, len(games)), 2),
    "preferred_images_below_800_edge": weak_preferred_images,
    "candidate_batches_are_not_catalogue_coverage": {
        "soundtrack_status": music_candidates.get("publication_status", "absent"),
        "soundtrack_candidates": len(music_candidates.get("entries", [])),
        "video_candidates": len(video_candidates.get("entries", [])),
        "video_checkpoint_status": video_approved.get("publication_status", "absent"),
        "video_approved_checkpoint": len(video_approved.get("entries", [])),
    },
    "paragraph_illustration_audit": "content/editorial-image-coverage.json",
    "story_scene_prose_order_check": "build/preview-scenes-28.log",
    "console_verification": {
        "current_build_transferred": False,
        "120hz_and_frame_pacing_verified": False,
        "all_experiences_played_on_console": False,
        "dualsense_output_felt_on_console": False,
        "youtube_metadata_checks_are_not_playback_tests": True,
    },
    "open_content_gates": issues,
    "ready_to_claim_complete": False,
}
destination = ROOT / "build/research/museum-readiness.json"
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: value for key, value in report.items()
                  if key not in ("missing_local_images_or_previews", "console_verification")}, indent=2))
