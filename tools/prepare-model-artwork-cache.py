#!/usr/bin/env python3
"""Bake optional GB/PS1 lossless artwork sidecars without changing their GLBs."""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import shlex
import subprocess
ROOT = Path(__file__).resolve().parents[1]
index_path = ROOT / "models/index.json"
index = json.loads(index_path.read_text(encoding="utf-8"))
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--ids",nargs="+",default=["game-boy","playstation"]);parser.add_argument("--format-version",type=int,choices=(1,2),default=1);args=parser.parse_args()
selected = [row for row in index["models"] if row["exhibit_id"] in set(args.ids)]
assert {row["exhibit_id"] for row in selected}==set(args.ids),"Unknown model selection"
paths=[row["asset_file"] for row in selected]
options=["--v2"] if args.format_version==2 else []
def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            result.update(block)
    return result.hexdigest()
for model in selected:
    assert digest(ROOT / model["asset_file"]) == model["sha256"], "Original model source changed"
if platform.system() == "Windows":
    path = "/mnt/" + ROOT.drive[0].lower() + ROOT.as_posix()[2:]
    subprocess.run(["wsl.exe", "bash", "-lc", "cd " + shlex.quote(path) + " && bash tests/object-scene/bake-artwork-cache.sh " + " ".join(shlex.quote(path) for path in options+paths)], check=True)
else:
    subprocess.run(["bash", "tests/object-scene/bake-artwork-cache.sh",*options,*paths], cwd=ROOT, check=True)
for model in selected:
    master = ROOT / model["asset_file"]
    assert digest(master) == model["sha256"], "Offline baking changed original master"
    asset = Path(model["asset_file"]).with_suffix(".artwork.pmc")
    file = ROOT / asset
    content="Offline-derived exact original RGBA8 base pixels and existing colour/data mip chains. Lossless Zstandard frames with verified content checksums; source GLB remains unchanged. Original PNG fallback on cache miss, mismatch or corruption."
    if args.format_version==2:content="Offline-derived exact existing RGBA8/sRGB8, RG8/R8 sampled-channel and verified constant upload payloads/mips. No new quantization, resizing or source change. Source-SHA256 binding and checksummed lossless Zstandard frames; worker-only original RGBA fallback on cache miss, mismatch, corruption or unavailable compact format."
    model["artwork_cache"] = {"asset_file": asset.as_posix(), "format_version": args.format_version, "source_sha256": model["sha256"], "bytes": file.stat().st_size, "sha256": digest(file), "content": content}
    (ROOT / "models/licenses" / (model["exhibit_id"] + ".json")).write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Prepared {len(selected)} source-bound offline sidecars; original GLBs unchanged")
