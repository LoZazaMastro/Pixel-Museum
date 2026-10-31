"""Verify active prose/media/music from the fourth coordinated authoring join."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
GROUP="gba-steamdeck-vr-eve-skyrim-final5-source73"
def load(p):return json.loads((ROOT/p).read_text(encoding="utf8"))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def owners(doc):
    result={}
    for e in doc["entries"]:
        result[e["id"]]=e
        result.update({f["id"]:f for f in e.get("editorial_features",[])})
    return result
master_path="content/catalog.json";runtime_path="build/runtime-preview/content/catalog.json"
master,runtime=load(master_path),load(runtime_path)
old=load("build/research/native-sano3-media15-recoverable/files/content/catalog.json")
mo,ro,oo=owners(master),owners(runtime),owners(old)
prior=load("build/research/sano3-media15-source71-final-proof.json")
records=list(prior["body_records"])
for row in records:
    eid,idx=row["entry_id"],row["index"]
    assert hashlib.sha256(mo[eid]["body"][idx].encode()).hexdigest()==row["body_sha256"]
    assert mo[eid]["body"][idx]==ro[eid]["body"][idx]==oo[eid]["body"][idx]
    assert mo[eid]["story_headings"][idx]==ro[eid]["story_headings"][idx]==oo[eid]["story_headings"][idx]
candidate=load("build/research/playhub-semantic-coverage/wiki-clarity/remaining-semantic-three/five-additional-concrete-cards-candidate.json")
for row in candidate["replacements"]:
    eid,idx=row["entry_id"],row["source_chapter_index"]
    assert mo[eid]["body"][idx]==ro[eid]["body"][idx]==row["body"]
    assert mo[eid]["story_headings"][idx]==ro[eid]["story_headings"][idx]==row["heading"]
    records.append(dict(entry_id=eid,index=idx,body_sha256=row["body_sha256"]))
assert len(records)==186
assert len(master["entries"])==len(runtime["entries"])==1395
assert master["entry_aliases"]==runtime["entry_aliases"]==old["entry_aliases"]
added=[];removed=[]
for eid,e in mo.items():
    previous={i["url"]:i for i in oo[eid].get("images",[])}
    current={i["url"]:i for i in e.get("images",[])}
    for url,i in current.items():
        if url not in previous:
            assert i.get("story_paragraph",-1)>=0
            assert any(j["url"]==url and j.get("story_paragraph")==i["story_paragraph"] for j in ro[eid].get("images",[]))
            added.append(dict(owner=eid,url=url,paragraph=i["story_paragraph"]))
    removed.extend(dict(owner=eid,url=url) for url in previous if url not in current)
assert len(added)==23 and len(removed)==2,(len(added),len(removed))
gba=load("build/research/gba-original-narrative-illustrations/five-original-gba-artifacts-candidate.json")
assert {r["url"] for r in removed}=={u["supersedes_url"] for u in gba["image_updates"] if u.get("supersedes_url")}
assert not mo["workbook-03-21-game-boy-advance"].get("models")
assert sha("content/expansion/soundtrack-multitrack-priority-overrides.json")=="045304c848c9547555f3f392afd2fd6045aa17126acf28160b8e49ed6db93906"
music=load("content/expansion/soundtrack-multitrack-priority-overrides.json")
assert len(music["entries"])==73
music_proof=[]
for source in music["entries"][-2:]:
    for table in (mo,ro):
        soundtrack=table[source["entry_id"]]["soundtrack"]
        assert len(soundtrack["tracks"])==len(source["tracks"])
        for actual,expected in zip(soundtrack["tracks"],source["tracks"]):
            for field in ("youtube_id","url","title","creator","source_page","start_seconds","end_seconds"):
                assert actual.get(field)==expected.get(field),(source["entry_id"],field)
        assert soundtrack["full_album_collection"] is False
        assert soundtrack["coverage_status"]==source["coverage_status"]
        assert soundtrack["album_completeness"]==source["album_completeness"]
    assert mo[source["entry_id"]]["soundtrack"]["tracks"]==source["tracks"]
    music_proof.append(dict(entry_id=source["entry_id"],tracks=len(source["tracks"]),all_tracks_and_bounds_preserved=True,not_exhaustive=True))
assert sum(r["tracks"] for r in music_proof)==140
integrity=load("build/research/"+GROUP+"-integrity.json")
assert integrity["missing_full_or_preview"]==0
models=[model for e in master["entries"] for model in e.get("models",[])]
assert len(models)==30
proof=dict(status="PASS_COHERENT_SOURCE_RUNTIME_AND_LOCAL_MEDIA_NOT_COMPLETION",master_sha256=sha(master_path),runtime_sha256=sha(runtime_path),runtime_bytes=(ROOT/runtime_path).stat().st_size,
    runtime_remaining_bytes=16*1024*1024-(ROOT/runtime_path).stat().st_size,entries=1395,culture=342,aliases=23,models=30,
    active_new_body_records_verified=186,body_records=records,added_image_records=added,removed_exact_old_thumbnails=removed,
    required_local_images=integrity["required_unique_image_urls"],missing_full_or_preview=0,approved_music_source_entries=73,new_music_rooms=music_proof,
    recovery="build/research/native-sano3-media15-recoverable/manifest.json",recovery_manifest_sha256=sha("build/research/native-sano3-media15-recoverable/manifest.json"),
    actual_composition_gap_last_verified=407,composition_gap_scope="Previous third group only; fresh current-runtime scoped profile required. No inferred subtraction.",ready_to_claim_complete=False)
out=ROOT/("build/research/"+GROUP+"-final-proof.json")
out.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps({k:v for k,v in proof.items() if k not in ("body_records","added_image_records")},indent=2))
