"""Append a source-bound, independently reviewed chronological proposal.

Local authoring only. Does not assemble, alter originals or touch dist.
"""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("year", type=int)
parser.add_argument("candidate")
parser.add_argument("peer")
args = parser.parse_args()
cp = ROOT / args.candidate
pp = ROOT / args.peer
candidate, peer = load(cp), load(pp)
assert peer["status"].startswith("PASS"), "Independent review has not passed"
assert peer["candidate_sha256"] == sha(cp), "Peer belongs to different proposal"
assert candidate["old_entry"]["year"] == args.year, "Wrong chronological manifest"
mp = ROOT / "content/expansion" / f"museum-chronological-{args.year}-reviewed.json"
plan = load(mp)
assert plan["publication_status"] == "independently_reviewed"
assert candidate["entry_id"] not in [r["entry_id"] for r in plan["rows"]], "Already admitted"
assert not (set(candidate["old_entry"]) - set(candidate["new_entry"])), "Top-level deletion requires explicit handling"
for path, digest in candidate["source_files"].items():
    assert sha(ROOT / path) == digest, "Source changed: " + path
    existing = next((x for x in plan["extra_sources"] if x["path"] == path), None)
    assert existing is None or existing["sha256"] == digest, "Conflicting source pin"
    if existing is None:
        plan["extra_sources"].append(dict(path=path, sha256=digest))
old, new = candidate["old_entry"], candidate["new_entry"]
plan["rows"].append(dict(entry_id=candidate["entry_id"], old_entry=old,
    changes={key: value for key, value in new.items() if old.get(key) != value},
    candidate_path=cp.relative_to(ROOT).as_posix(), candidate_sha256=sha(cp),
    peer_path=pp.relative_to(ROOT).as_posix(), peer_sha256=sha(pp)))
temporary = mp.with_suffix(".json.tmp")
temporary.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
temporary.replace(mp)
print(json.dumps(dict(status="QUEUED_REVIEWED_LOCAL_PROPOSAL", entry_id=candidate["entry_id"], year=args.year)))
