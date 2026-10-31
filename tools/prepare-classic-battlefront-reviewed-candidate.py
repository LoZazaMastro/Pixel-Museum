"""Prepare a research candidate; never modify the production catalogue."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/research/explicit-zero-music-rooms"
records = json.loads((OUT / "bf2005-public-metadata/results.json").read_text(encoding="utf-8"))
catalog = json.loads((ROOT / "content/catalog.json").read_text(encoding="utf-8"))
owner = next(e for e in catalog["entries"] if e["id"] == "wikipedia-1965591")
holds = {
    "EpuvEvPGTw4": "Fan-created thirty-minute extension",
    "wD8ePd6kAjc": "Interactive menu video",
    "JmHU-hY_44M": "Short sting lacks proof distinguishing the 2004 and 2005 games",
    "hy8SlwjuXlM": "Short sting lacks proof distinguishing the 2004 and 2005 games",
}
tracks = []
excluded = []
for record in records:
    identity = record.get("id") or record["requested_id"]
    if record["status"] != "verified_public_native_metadata" or identity in holds:
        excluded.append({"id": identity, "reason": holds.get(identity, "Public native formats unavailable")})
        continue
    title = re.sub(r"^Battlefront 2 \(2005\) Soundtrack HD\s*-\s*|^Star Wars: Battlefront II Soundtrack\s*-\s*", "", record["title"])
    assert title and identity not in {t["youtube_id"] for t in tracks}
    tracks.append({
        "youtube_id": identity,
        "url": "https://www.youtube.com/watch?v=" + identity,
        "title": title,
        "creator": "John Williams",
        "uploader": record["channel"],
        "channel_url": record.get("channel_url"),
        "source_page": "https://www.youtube.com/watch?v=" + identity,
        "official_uploader_verified": False,
        "publishing_kind": "public_classic_game_score_archive",
        "duration_seconds": record["duration"],
        "native_codec_metadata_verified": True,
        "native_codec_metadata_receipt": "build/research/explicit-zero-music-rooms/bf2005-public-metadata/" + identity + ".json",
        "recording_version": "Original Star Wars film-score music and game edits associated with Pandemic's 2005 game. Public archive recording, not the 2017 score.",
        "rights": "Original composition and recording rights remain with their respective owners. Archive uploader credited separately.",
        "playback_verified_on_ps5": False,
    })
assert len(tracks) == 116
row = {
    "entry_id": owner["id"], "match_title": owner["title"], "match_year": owner["year"],
    "title": "Star Wars: Battlefront II", "composer": "John Williams",
    "curator_note": "Listen to the music of John Williams\nStar Wars: Battlefront II",
    "tracks": tracks, "replace_existing_tracks": True, "full_album_collection": False,
    "album_completeness": "116 available original-game archive recordings. Six unavailable, extended, interactive or edition-ambiguous sources held. Archive coverage, not a commercial album completeness claim.",
}
candidate = {
    "status": "READY_FOR_INDEPENDENT_FINAL_CANDIDATE_PEER",
    "source_playlist": "https://www.youtube.com/playlist?list=PLon7WNA0Cke7O1FnbEFUNJ5LjEC-tBZ2B",
    "old_music_fields": {key: owner.get(key) for key in ("soundtrack", "soundtrack_rooms")},
    "row": row, "held": excluded,
    "credit_evidence": "Original Steam app6060 manual PDF page14, printed25: John Williams original music; Jesse Harlin music editing and implementation. Independent source review held separately.",
    "scope": "Research candidate only. No catalogue, soundtrack source or package mutated. Native public metadata verified, no audio fingerprint or physical PS5 playback claim.",
}
path = OUT / "battlefront2005-116-public-original-game-archive-candidate.json"
path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(hashlib.sha256(path.read_bytes()).hexdigest())
