#!/usr/bin/env python3
"""Package the verified native Games folder without local caches or sources."""
from pathlib import Path
import argparse
import hashlib
import json
import runpy
import shutil
import subprocess
import sys
import zipfile
from model_artwork_cache import copy_artwork_cache
from package_base_assets import stage_base_assets
from staged_model_pruning import prune_unreferenced_models
from package_native_profile import validate_native_profile
root = Path(__file__).resolve().parents[1]
CATALOG_BYTE_LIMIT = 64 << 20
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--folder-only", action="store_true", help="Stage the app folder without creating a release ZIP")
parser.add_argument("--skip-assemble", action="store_true", help="Package an already verified catalogue")
parser.add_argument("--expected-catalog-sha256")
parser.add_argument("--expected-runtime-sha256")
args = parser.parse_args()
if args.skip_assemble and not (args.expected_catalog_sha256 and args.expected_runtime_sha256):
    parser.error("--skip-assemble requires both verified catalogue hashes")
def digest_file(path):
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        while block:=stream.read(1024*1024):digest.update(block)
    return digest.hexdigest()
param = json.loads((root / "sce_sys/param.json").read_text())
title = param["titleId"]
validate_native_profile(param)
folder = root / "dist" / title
if not (folder / "eboot.bin").is_file():
    raise SystemExit("Build the native application first")
if not args.skip_assemble:
    subprocess.run([sys.executable, str(root / "content/assemble_catalog.py")], check=True)
catalog_bytes = (root / "content/catalog.json").read_bytes()
catalog_digest = hashlib.sha256(catalog_bytes).hexdigest()
if args.expected_catalog_sha256 and catalog_digest != args.expected_catalog_sha256:
    raise SystemExit("The catalogue changed since verification")
assembled = json.loads(catalog_bytes)
# New article/track text must be covered by the actual current font assets.
# A successful native compile alone cannot validate externally loaded fonts.
subprocess.run([sys.executable, str(root / "tools/audit-font-coverage.py")], check=True)
# A content-only build can reuse its validated SELF. Always refresh fonts,
# branding, audio and PS5 artwork rather than inheriting an older dist folder.
from trophy_asset_validation import validate_trophy_assets
validate_trophy_assets(root, root)
stage_base_assets(root, folder)
validate_trophy_assets(root, folder)
shutil.copytree(root / "licenses", folder / "licenses", dirs_exist_ok=True)
for source_licenses in (root / "content/licenses").glob("*"):
    destination = folder / "licenses/media" / source_licenses.name
    if source_licenses.is_dir():
        shutil.copytree(source_licenses, destination, dirs_exist_ok=True)
    elif source_licenses.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_licenses, destination)
(folder / "content").mkdir(exist_ok=True)
# Parse only display data on the console. Research/audit snapshots stay in the
# authoring collection; complete source and media provenance remains in credits.
runtime_join = runpy.run_path(str(root / "tools/runtime-catalog.py"))
runtime = runtime_join["project"](assembled, catalog_digest)
compact = runtime_join["encoded"](runtime)
history_path = root / "content/human-history.json"
if not history_path.is_file():
    raise SystemExit("The culture timeline catalogue is required for the complete museum")
history = json.loads(history_path.read_bytes())
history_compact = runtime_join["encoded"](runtime_join["project"](history))
if len(history_compact) > CATALOG_BYTE_LIMIT:
    raise SystemExit("The culture timeline catalogue exceeds the native reader budget")
if args.expected_runtime_sha256 and hashlib.sha256(compact).hexdigest() != args.expected_runtime_sha256:
    raise SystemExit("Runtime projection differs from the verified catalogue")
if len(compact) > CATALOG_BYTE_LIMIT:
    raise SystemExit("Runtime catalogue exceeds the 64 MiB reader budget")
(folder / "content/catalog.json").write_bytes(compact)
(folder / "content/human-history.json").write_bytes(history_compact)
# Separate selective archival cues: never folded into article/OST metadata.
shutil.copy2(root / "content/culture-memories.json", folder / "content/culture-memories.json")
# Ship reviewed translations only while they still match the exact English
# article. Older Playhub overlays are not interchangeable with museum stories.
locale_projection = runpy.run_path(str(root / "tools/project-reviewed-locales.py"))
for language in ("en","it","es","fr","de"):
    localized = {"locale": language, "entries": {}}
    source_locale = root / "content/museum-locales" / (language + ".json")
    if language != "en" and source_locale.is_file():
        localized, locale_audit = locale_projection["project"](
            json.loads(source_locale.read_text(encoding="utf-8")), [assembled, history], language)
        audit_path = folder / "licenses/translations" / (language + "-source-binding.json")
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(json.dumps(locale_audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    localized_bytes = runtime_join["encoded"](localized)
    if len(localized_bytes) > CATALOG_BYTE_LIMIT:
        raise SystemExit("Localized catalogue exceeds the native reader budget: " + language)
    (folder/"content/locales").mkdir(exist_ok=True)
    (folder/"content/locales"/(language+".json")).write_bytes(localized_bytes)
if (root / "content/ui-locales").is_dir():
    shutil.copytree(root / "content/ui-locales", folder / "content/ui-locales", dirs_exist_ok=True)
for metadata in ("credits.json",):
    if (root / "content" / metadata).is_file():
        shutil.copy2(root / "content" / metadata, folder / "content" / metadata)
shutil.copytree(root / "music/eras", folder / "music/eras", dirs_exist_ok=True)
if (root / "music/manifest.json").is_file():
    shutil.copy2(root / "music/manifest.json", folder / "music/manifest.json")
shutil.copy2(root / "music/README.md", folder / "licenses/original-music.md")
catalog=assembled
model_root=root / "models"
required_model_files = {model['asset_file'] for entry in catalog['entries'] for model in (entry.get('models') or [])}
required_model_files.update(model['artwork_cache']['asset_file'] for entry in catalog['entries']
                            for model in (entry.get('models') or []) if model.get('artwork_cache'))
prune_unreferenced_models(root, folder, required_model_files)
if any(entry.get("models") for entry in catalog["entries"]):
    if not (model_root / "index.json").is_file():
        raise SystemExit("Bundled 3D models require models/index.json")
    destination=folder / "models";destination.mkdir(exist_ok=True)
    index=json.loads((model_root / "index.json").read_text(encoding="utf-8"))
    declared={item["asset_file"]:item for item in index["models"]}
    required={model.get("asset_file","") for entry in catalog["entries"] for model in (entry.get("models") or [])}
    if not required.issubset(declared):
        raise SystemExit(f"Catalog models missing provenance: {sorted(required-set(declared))}")
    for asset,item in declared.items():
        path=Path(asset)
        if not asset.startswith("models/") or len(path.parts)!=2 or path.is_absolute() or ".." in path.parts or path.suffix!=".glb":
            raise SystemExit(f"Unsafe model index path: {asset!r}")
        source=root/path
        if not source.is_file() or source.stat().st_size!=item["bytes"] or digest_file(source)!=item["sha256"]:
            raise SystemExit(f"Bundled model does not match its provenance: {asset}")
        shutil.copy2(source,folder/path)
        copy_artwork_cache(root, folder, item)
    shutil.copy2(model_root / "index.json",destination / "index.json")
    if (model_root / "licenses").is_dir():
        shutil.copytree(model_root / "licenses",destination / "licenses",dirs_exist_ok=True)
    for entry in catalog["entries"]:
        for model in (entry.get("models") or []):
            asset=model.get("asset_file","")
            path=Path(asset)
            if not asset.startswith("models/") or path.is_absolute() or ".." in path.parts or path.suffix!=".glb" or not (folder/path).is_file():
                raise SystemExit(f"Exhibit {entry['id']} has no safe bundled model: {asset!r}")
elif (folder / 'models').is_dir():
    # Refresh a previously staged model index without copying archived meshes.
    (folder / 'models/index.json').write_text(json.dumps({'schema_version': 1, 'models': [],
        'catalog_console_models_withdrawn': True}, indent=2) + '\n', encoding='utf8')
runpy.run_path(str(root/"tools/bundled-images.py"))["stage"](assembled,root,folder,additional_catalogs=(history,))
if args.folder_only:
    print(f"App folder ready: {folder}")
    raise SystemExit(0)
archive = root / "dist" / f"{title}.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as output:
    for path in sorted(folder.rglob("*")):
        if path.is_file():
            info = zipfile.ZipInfo.from_file(path, path.relative_to(folder).as_posix())
            info.create_system = 3
            info.external_attr = (0o100777 << 16)
            info.compress_type = zipfile.ZIP_DEFLATED
            with path.open("rb") as source,output.open(info,"w",force_zip64=path.stat().st_size>=2**31) as target:
                shutil.copyfileobj(source,target,length=1024*1024)
digest = digest_file(archive)
(root / "dist" / "SHA256SUMS").write_text(f"{digest}  {archive.name}\n")
print(f"{archive.name}: {digest}")
