"""Archive the verified third payload before the next grouped authoring join."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"build/research/native-sano3-media15-recoverable"
PREVIOUS=ROOT/"build/research/native-final16-media22-recoverable"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((ROOT/"build/research/sano3-media15-font-scoped/verification.json").read_text(encoding="utf8"))
for label in ("master","runtime","native_unchanged"):
    item=proof[label]
    assert sha(ROOT/item["path"])==item["sha256"]
if (OUT/"manifest.json").exists():
    manifest=json.loads((OUT/"manifest.json").read_text(encoding="utf8"))
    for name,record in manifest["files"].items():assert sha(OUT/"files"/name)==record["sha256"]
    print("Already archived:",sha(OUT/"manifest.json"),len(manifest["files"]))
    raise SystemExit(0)
old=json.loads((PREVIOUS/"manifest.json").read_text(encoding="utf8"))
names=set(old["files"])
names.update([
    "build/research/sano3-media15-source71-final-proof.json",
    "build/research/sano3-media15-source71-final-status.json",
    "build/research/sano3-media15-source71-integrity.json",
    "build/research/sano3-media15-source71-input-freeze.json",
    "build/research/sano3-media15-source71-isolated-admission.json",
    "content/expansion/stanley2013_reviewed_narrative_media.py",
    "content/expansion/preservation_store_reviewed_feature_media.py",
    "content/expansion/reviewed_story_gap_images.py"])
names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/"build/research/sano3-media15-font-scoped").glob("*.json"))
frozen_source={"content/assemble_catalog.py","content/expansion/reviewed_clarity_next.py"}
records={}
for name in sorted(names):
    source=(PREVIOUS/"files"/name) if name in frozen_source else ROOT/name
    target=OUT/"files"/name
    assert ROOT.resolve() in target.resolve().parents
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
    value=sha(source)
    assert sha(target)==value
    records[name]=dict(bytes=target.stat().st_size,sha256=value)
manifest=dict(status="PASS_RECOVERABLE_VERIFIED_THIRD_PAYLOAD",restore="Restore compiled catalogue/runtime, credits, selectors, fonts and ELF together from files/. Large immutable local image/model assets remain at their recorded workspace paths. Source files for the third assembler/clarity join are copied from its exact preassembly recovery, not later NEXT edits. This is a payload recovery snapshot, not a complete repository checkout.",
    verified_master_sha256=proof["master"]["sha256"],verified_runtime_sha256=proof["runtime"]["sha256"],
    scoped_verification_sha256=sha(ROOT/"build/research/sano3-media15-font-scoped/verification.json"),files=records)
path=OUT/"manifest.json";path.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf8")
print(path.relative_to(ROOT),sha(path),len(records))
