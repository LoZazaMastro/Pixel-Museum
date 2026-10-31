"""Guarded source-only promotion of two independently reviewed music rooms."""
from pathlib import Path
import copy
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
PATH="content/expansion/soundtrack-multitrack-priority-overrides.json"
OLD="891855a14c335efc73a6eb801aaef6bad013f0bc803923f45a0602acbb388875"
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def load(p):return json.loads((ROOT/p).read_text(encoding="utf8"))
plans=[
    ("build/research/soundtrack-broad/yakuza-zero-public-collection/yakuza-zero-92-public-passages-final-vocals-candidate.json", "77aa4891658cdbd3b72b7a864ce3e03839612e5cb6c1731ef3ba5893495c5c58", "build/research/soundtrack-broad/yakuza-zero-public-collection/root-independent-ninety-two-passages-review.json",92),
    ("build/research/soundtrack-broad/splatoon-original-2015/forty-eight-original-wiiu-publications-candidate.json", "488bad179fe00a3432fea03c585c3483226b67b6123915532d7a833492f7e393", "build/research/soundtrack-broad/splatoon-original-2015/independent-forty-eight-original-wiiu-review.json",48)]
if sha(PATH)!=OLD:
    raise ValueError("Source71 lock changed; refusing a concurrent or repeated promotion")
doc=load(PATH);original=copy.deepcopy(doc["entries"])
assert len(original)==71 and doc["publication_status"]=="validated"
reports=[]
for candidate_path,expected,receipt_path,count in plans:
    assert sha(candidate_path)==expected
    candidate,peer=load(candidate_path),load(receipt_path)
    peer_candidate_sha=peer.get("candidate_sha256",peer.get("candidate",{}).get("sha256"))
    assert peer["status"] in ("PASS","PASS_ALL48_RECORDING_IDENTITIES_AND_NATIVE_METADATA_CORRECTIONS_APPLIED") and peer_candidate_sha==expected
    for source in candidate["source_receipts"]:
        assert sha(source["path"])==source["sha256"],source["path"]
    entry=copy.deepcopy(candidate["entries"][0])
    assert not any(old.get("entry_id")==entry["entry_id"] for old in doc["entries"])
    assert len(entry["tracks"])==count and entry["replace_existing_tracks"] is True and entry["full_album_collection"] is False
    identities=set()
    for track in entry["tracks"]:
        assert track["native_codec_metadata_verified"] is True and track["playback_verified_on_ps5"] is False
        assert (ROOT/track["native_codec_metadata_receipt"]).is_file()
        key=(track["youtube_id"],track.get("start_seconds"),track.get("end_seconds"))
        assert key not in identities
        identities.add(key)
        if "start_seconds" in track:
            assert 0<=track["start_seconds"]<track["end_seconds"]<=track["source_publication_duration_seconds"]
    entry["independent_review_receipt"]=receipt_path
    if count==48:
        entry["album_completeness"]=dict(available_original_wii_u_publications=48,playlist_items_inspected=68,
            excluded_live_or_incidental=19,unavailable_held=1,published_retail_album_tracks=61,
            qualification="Available original Wii U archival music publications; not exact61-track retail Splatune master or exhaustive game-file inventory.",not_exhaustive=True)
    doc["entries"].append(entry)
    reports.append(dict(entry_id=entry["entry_id"],tracks=count,candidate_path=candidate_path,candidate_sha256=expected,independent_review=receipt_path))
assert doc["entries"][:71]==original and len(doc["entries"])==73
staging=ROOT/(PATH+".tmp")
staging.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
staging.replace(ROOT/PATH)
report=dict(status="PASS_SOURCE_ONLY_PROMOTION",previous_source_sha256=OLD,
    source_sha256=sha(PATH),previous_entries=71,current_entries=73,added_recordings=140,
    prior71_entries_exactly_preserved=True,approved=reports,master_modified=False,runtime_modified=False)
out=ROOT/"build/research/yakuza92-splatoon48-source-promotion.json"
out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
print(json.dumps(report,indent=2))
