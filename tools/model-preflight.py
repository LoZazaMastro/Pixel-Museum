#!/usr/bin/env python3
"""Read-only integrity and provenance check for the selected museum models."""
from pathlib import Path
import hashlib
import json
import sys

root=Path(__file__).resolve().parents[1]
catalog=json.loads((root/"content/catalog.json").read_text(encoding="utf-8"))
index=json.loads((root/"models/index.json").read_text(encoding="utf-8"))
errors=[]
seen=set()
size=0
for item in index["models"]:
    asset=item.get("asset_file","")
    path=Path(asset)
    if not asset.startswith("models/") or len(path.parts)!=2 or path.is_absolute() or ".." in path.parts or path.suffix!=".glb":
        errors.append(f"Unsafe model path: {asset!r}");continue
    if asset in seen:errors.append(f"Duplicate model index path: {asset}")
    seen.add(asset)
    file=root/path
    if not file.is_file():errors.append(f"Missing selected model: {asset}");continue
    size+=file.stat().st_size
    digest=hashlib.sha256()
    with file.open("rb") as source:
        while chunk:=source.read(1024*1024):digest.update(chunk)
    if file.stat().st_size!=item.get("bytes") or digest.hexdigest()!=item.get("sha256"):
        errors.append(f"Size or digest mismatch: {asset}")
    for field in ("creator","credit","license","license_url","source_page"):
        if not item.get(field):errors.append(f"Missing {field}: {asset}")
    notice=root/"models/licenses"/(item.get("exhibit_id","")+".json")
    if not notice.is_file():errors.append(f"Missing individual model notice: {asset}")
    elif json.loads(notice.read_text(encoding="utf-8"))!=item:
        errors.append(f"Individual notice differs from model index: {asset}")
required={m.get("asset_file","") for e in catalog["entries"] for m in e.get("models",[])}
for asset in sorted(required-seen):errors.append(f"Catalog model lacks selected provenance: {asset!r}")
report={"catalog_entries":len(catalog["entries"]),"selected_models":len(seen),"exhibited_models":len(required),"model_bytes":size,
        "ignored_working_glbs":sorted(p.name for p in (root/"models").glob("*.glb") if p.relative_to(root).as_posix() not in seen),"errors":errors}
(root/"build/model-preflight.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2))
sys.exit(bool(errors))
