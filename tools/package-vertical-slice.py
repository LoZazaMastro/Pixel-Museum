#!/usr/bin/env python3
"""Stage a curated console trial without changing the full authoring collection."""
from pathlib import Path
import hashlib
import argparse
import datetime
import json
import runpy
import shutil
import subprocess
import sys
import zipfile
from model_artwork_cache import copy_artwork_cache
from hardware_presentation import photograph_only_console_ids
from package_native_profile import validate_native_profile

ROOT=Path(__file__).resolve().parents[1]
TITLE="PPSA70421"
parser=argparse.ArgumentParser();parser.add_argument("--output-dir",default="dist/vertical-slice-ready");parser.add_argument("--selector",default="content/vertical-slice.json");parser.add_argument("--executable");parser.add_argument("--include-today",action="store_true");parser.add_argument("--include-experiences",action="store_true");parser.add_argument("--use-assembled-catalog",action="store_true",help="Package the frozen, already assembled catalogue without incorporating concurrent research edits.");parser.add_argument("--include-reviewed-locales",action="store_true",help="Include partial story translations only when bound to identical current English text.");args=parser.parse_args()
def read(path):return json.loads(path.read_text(encoding="utf-8"))
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def digest(path):
    result=hashlib.sha256()
    with path.open("rb") as source:
        while block:=source.read(1024*1024):result.update(block)
    return result.hexdigest()

source=ROOT/"dist"/TITLE
selector=read(ROOT/args.selector)
if not args.use_assembled_catalog:
    subprocess.run([sys.executable,str(ROOT/"content/assemble_catalog.py")],check=True)
elif selector.get("source_catalog_sha256")!=digest(ROOT/"content/catalog.json"):
    raise SystemExit("Frozen catalogue does not match the selector's source digest")
full=read(ROOT/"content/catalog.json")
ids=list(selector["entry_ids"])
assert len(ids)==len(set(ids)),"Repeated slice entry"
lookup={entry["id"]:entry for entry in full["entries"]}
if args.include_today:
    today="daily-"+datetime.date.today().strftime("%m-%d")
    if today in lookup and today not in ids:ids.append(today)
if args.include_experiences:
    studies=read(ROOT/"content/experiences.json")
    if isinstance(studies,dict):studies=studies["entries"]
    for row in studies:
        if row["entry_id"] not in ids:ids.append(row["entry_id"])
    for entry in full["entries"]:
        if entry.get("soundtrack",{}).get("tracks") and not entry.get("calendar_only") and entry["id"] not in ids:ids.append(entry["id"])
assert set(ids)<=lookup.keys(),f"Slice entries unavailable: {set(ids)-lookup.keys()}"
catalog={**full,"edition":"Offline museum / development build","initial_id":selector.get("initial_id","game-boy"),"entries":[lookup[key] for key in ids]}
catalog["entries"].sort(key=lambda entry:entry["year"])
for entry in catalog["entries"]:
    entry["related_ids"]=[key for key in entry.get("related_ids",[]) if key in ids]
photo_only_ids=photograph_only_console_ids(ROOT)
assert all(entry.get("models") or (entry["id"] in photo_only_ids and entry.get("images")) for entry in catalog["entries"] if entry["kind"]=="console"),"Slice console lacks bundled 3D or its explicit user-approved photograph"
assert any(entry.get("videos") for entry in catalog["entries"]),"Slice needs archive films"
assert (source/"eboot.bin").is_file(),"Build native app first"
param=read(source/"sce_sys/param.json")
validate_native_profile(param)
assert param.get("downloadDataSize")==1024,"Reserve 1024 MiB for /download0; source staging metadata is stale"
parent=(ROOT/args.output_dir).resolve()
assert parent.is_relative_to((ROOT/"dist").resolve()),"Stage only below this project's dist directory"
folder=parent/TITLE
# Refuse a stale staged tree rather than accidentally shipping old assets.
if folder.exists():
    raise SystemExit(f"A slice is already staged at {folder}; archive or remove that generated folder before rebuilding")
folder.mkdir(parents=True)
for name in ("eboot.bin","sce_sys","sce_module","assets"):
    origin=(ROOT/args.executable).resolve() if name=="eboot.bin" and args.executable else ROOT/name if name=="sce_sys" else source/name;destination=folder/name
    if origin.is_dir():
        if name=="sce_sys":
            destination.mkdir()
            for asset in ("icon0.png","pic0.dds","pic1.dds","param.json","snd0.at9"):
                if (origin/asset).is_file():shutil.copy2(origin/asset,destination/asset)
        else:shutil.copytree(origin,destination)
    else:shutil.copy2(origin,destination)
shutil.copytree(ROOT/"assets/brand",folder/"assets/brand",dirs_exist_ok=True)
history_path=ROOT/"content/human-history.json"
history=read(history_path) if history_path.is_file() else {"entries":[]}
bundled_image_count=runpy.run_path(str(ROOT/"tools/bundled-images.py"))["stage"]({"entries":catalog["entries"]+history["entries"]},ROOT,folder)
if (ROOT/"assets/audio/museum-navigation").is_dir():shutil.copytree(ROOT/"assets/audio/museum-navigation",folder/"assets/audio/museum-navigation",dirs_exist_ok=True)
shutil.copytree(ROOT/"licenses",folder/"licenses",dirs_exist_ok=True)
if (ROOT/"content/licenses").exists():shutil.copytree(ROOT/"content/licenses",folder/"licenses/media",dirs_exist_ok=True)
shutil.copytree(ROOT/"music/eras",folder/"music/eras")
if (ROOT/"music/manifest.json").is_file():shutil.copy2(ROOT/"music/manifest.json",folder/"music/manifest.json")
shutil.copy2(ROOT/"music/README.md",folder/"licenses/original-music.md")
runtime_join=runpy.run_path(str(ROOT/"tools/runtime-catalog.py"))
runtime=runtime_join["project"](catalog,digest(ROOT/"content/catalog.json"))
compact=runtime_join["encoded"](runtime)
assert len(compact)<=16<<20,"Runtime catalogue exceeds16MiB"
(folder/"content/catalog.json").parent.mkdir(parents=True,exist_ok=True)
(folder/"content/catalog.json").write_bytes(compact)
shutil.copy2(ROOT/"content/culture-memories.json",folder/"content/culture-memories.json")
if history["entries"]:
    history_compact=runtime_join["encoded"](runtime_join["project"](history,digest(history_path)))
    assert len(history_compact)<=16<<20,"Historical catalogue exceeds16MiB"
    (folder/"content/human-history.json").write_bytes(history_compact)
# Legacy story overlays are intentionally excluded. Newly reviewed overlays are
# source-bound per owner so an edited article never receives an older translation.
locale_projection=runpy.run_path(str(ROOT/"tools/project-reviewed-locales.py"))
for language in ("en","it","es","fr","de"):
    localized={"locale":language,"entries":{}}
    source_locale=ROOT/"content/museum-locales"/(language+".json")
    if args.include_reviewed_locales and language!="en" and source_locale.is_file():
        localized,locale_audit=locale_projection["project"](read(source_locale),[catalog,history],language)
        write(folder/"licenses/translations"/(language+"-source-binding.json"),locale_audit)
        assert len(runtime_join["encoded"](localized))<=16<<20,"Localized catalogue exceeds16MiB"
    write(folder/"content/locales"/(language+".json"),localized)
shutil.copytree(ROOT/"content/ui-locales",folder/"content/ui-locales",dirs_exist_ok=True)
credits=read(ROOT/"content/credits.json")
credited_ids=set(ids)|{entry["id"] for entry in history["entries"]}
for key in ("sources","media","translations"):
    credits[key]=[row for row in credits.get(key,[]) if row.get("exhibit_id") in credited_ids]
write(folder/"content/credits.json",credits)
index=read(ROOT/"models/index.json")
required={model["asset_file"] for entry in catalog["entries"] for model in entry.get("models",[])}
index["models"]=[model for model in index["models"] if model["asset_file"] in required]
assert {model["asset_file"] for model in index["models"]}==required
for model in index["models"]:
    path=Path(model["asset_file"])
    assert len(path.parts)==2 and path.parts[0]=="models" and path.suffix==".glb" and ".." not in path.parts
    origin=ROOT/path
    assert origin.stat().st_size==model["bytes"] and digest(origin)==model["sha256"]
    (folder/path).parent.mkdir(exist_ok=True);shutil.copy2(origin,folder/path)
    copy_artwork_cache(ROOT, folder, model)
    write(folder/"models/licenses"/(model["exhibit_id"]+".json"),model)
write(folder/"models/index.json",index)
shutil.copytree(ROOT/"models/licenses",folder/"models/licenses",dirs_exist_ok=True)
archive=parent/(TITLE+".zip")
files=[]
with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as output:
    for path in sorted(folder.rglob("*")):
        if not path.is_file():continue
        relative=path.relative_to(folder).as_posix()
        info=zipfile.ZipInfo.from_file(path,relative);info.create_system=3;info.external_attr=0o100777<<16;info.compress_type=zipfile.ZIP_DEFLATED
        with path.open("rb") as src,output.open(info,"w",force_zip64=path.stat().st_size>=2**31) as dst:shutil.copyfileobj(src,dst,1024*1024)
        files.append({"path":relative,"bytes":path.stat().st_size,"sha256":digest(path)})
manifest={"title_id":TITLE,"edition":"vertical-slice","exhibits":len(ids),"chronology_exhibits":sum(not e.get("calendar_only",False) for e in catalog["entries"]),"calendar_features":sum(e.get("calendar_only",False) for e in catalog["entries"]),"remote_images":0,"bundled_images":bundled_image_count,"attached_features":sum(len(e.get("editorial_features",[])) for e in catalog["entries"]),"new_feature_cards":sum(sum(len(f["body"]) for f in e.get("editorial_features",[]))+(len(e["body"]) if e.get("editorial_mode")=="original_additive_feature" else 0) for e in catalog["entries"]),"models":len(required),"payload_bytes":sum(row["bytes"] for row in files),"archive_bytes":archive.stat().st_size,"archive_sha256":digest(archive),"files":files}
write(parent/"payload-manifest.json",manifest)
(parent/"SHA256SUMS").write_text(manifest["archive_sha256"]+"  "+archive.name+"\n")
print(json.dumps({key:value for key,value in manifest.items() if key!="files"},indent=2))
