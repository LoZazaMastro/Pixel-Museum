#!/usr/bin/env python3
from model_artwork_cache import checked_artwork_cache
from package_native_profile import validate_native_profile
"""Validate the isolated Games payload and record every transferred byte."""
from pathlib import Path
import hashlib
import json
import zipfile
import argparse
import re

root = Path(__file__).resolve().parents[1]
catalog_limit_match = re.search(r'kCatalogByteLimit\s*=\s*(\d+)u\s*<<\s*(\d+)', (root/'src/museum/catalog.hpp').read_text(encoding='utf-8'))
assert catalog_limit_match, 'Cannot determine the native catalogue byte limit'
catalog_byte_limit = int(catalog_limit_match[1]) << int(catalog_limit_match[2])
parser=argparse.ArgumentParser();parser.add_argument("--vertical-slice",action="store_true");parser.add_argument("--slice-dir",default="dist/vertical-slice-ready");parser.add_argument("--folder-only",action="store_true",help="Verify the complete FileZilla folder without requiring a ZIP");args=parser.parse_args()
parent=root/(args.slice_dir if args.vertical_slice else "dist")
folder = parent / "PPSA70421"
archive = parent / "PPSA70421.zip"
allowed = {"eboot.bin", "assets", "sce_sys", "sce_module", "content", "music", "licenses", "models"}
def stream_digest(stream):
    digest=hashlib.sha256()
    while block:=stream.read(1024*1024):digest.update(block)
    return digest.hexdigest()
def digest_file(path):
    with path.open("rb") as source:return stream_digest(source)
param = json.loads((folder / "sce_sys/param.json").read_text())
validate_native_profile(param)
assert param["localizedParameters"]["defaultLanguage"] == "en-US"
expected_content={"catalog.json", "credits.json", "locales", "ui-locales", "culture-memories.json"}
if not args.vertical_slice or (folder/"content/human-history.json").is_file():expected_content.add("human-history.json")
assert {p.name for p in (folder/"content").iterdir()}==expected_content
for locale in ("en", "it", "es", "fr", "de"):
    for directory in ("locales", "ui-locales"):
        document=json.loads((folder/"content"/directory/(locale+".json")).read_text(encoding="utf-8"))
        assert isinstance(document,dict)
expected_presentation = {"icon0.png", "pic0.dds", "pic1.dds", "param.json"}
if (root / "sce_sys/snd0.at9").is_file():
    expected_presentation.add("snd0.at9")
assert {p.name for p in (folder / "sce_sys").iterdir()} == expected_presentation
assert {p.name for p in (folder / "sce_module").iterdir()} == {"libc.prx"}
assert len(list((folder / "music/eras").glob("*.ogg"))) == 8
if not args.vertical_slice:
    # In particular, never deliver old font atlases with a newer catalogue.
    # Native compilation is independent of these externally loaded assets.
    for source in (root / 'assets').rglob('*'):
        if source.is_file() and source.relative_to(root / 'assets').parts[0] != 'images':
            relative=source.relative_to(root)
            assert (folder/relative).is_file() and digest_file(folder/relative)==digest_file(source), f'Stale base asset: {relative}'
    for name in sorted(expected_presentation):
        assert digest_file(folder/'sce_sys'/name)==digest_file(root/'sce_sys'/name), f'Stale PS5 artwork/metadata: {name}'
files = []
for p in sorted(folder.rglob("*")):
    if not p.is_file():
        continue
    relative = p.relative_to(folder).as_posix()
    assert relative.split("/")[0] in allowed
    assert p.suffix not in {".py", ".sh", ".ps1", ".zip"}
    assert p.name not in {"AGENTS.md", "CLAUDE.md"}
    if relative.startswith("models/"):
        pieces=relative.split("/")
        assert (len(pieces)==2 and (p.suffix==".glb" or p.name=="index.json" or p.name.endswith(".artwork.pmc"))) or (len(pieces)>2 and pieces[1]=="licenses")
    files.append({"path": relative, "bytes": p.stat().st_size, "sha256": digest_file(p)})
if not args.folder_only:
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist()) == {f["path"] for f in files}
        for item in files:
            info = z.getinfo(item["path"])
            assert ((info.external_attr >> 16) & 0o777) == 0o777
            with z.open(info) as source:assert stream_digest(source) == item["sha256"]
catalog = json.loads((folder / "content/catalog.json").read_text(encoding="utf-8"))
assert (folder/"content/catalog.json").stat().st_size<=catalog_byte_limit
image_manifest=json.loads((folder/'assets/images/manifest.json').read_text(encoding='utf-8'))
history_path=folder/"content/human-history.json"
history=json.loads(history_path.read_text(encoding="utf-8")) if history_path.is_file() else {"entries":[]}
locale_owner_ids={owner["id"] for entry in catalog["entries"]+history["entries"]
                  for owner in (entry,*entry.get("editorial_features",[]))}
for path in (folder/"content/locales").glob("*.json"):
    localized=json.loads(path.read_text(encoding="utf-8"))
    assert localized.get("locale")==path.stem
    assert set(localized["entries"])<=locale_owner_ids,"Translation owner absent from packaged museum"
if not args.vertical_slice:assert history["entries"], "The full museum must include its culture timeline"
if history["entries"]:
    assert history_path.stat().st_size<=catalog_byte_limit
    assert min(e["year"] for e in history["entries"])==1833
    assert all(e["kind"]=="history" and len(e["images"])==1 and e.get("sources") and e.get("body") for e in history["entries"])
for entry in catalog['entries']+history['entries']:
    photographs=list(entry.get('images',[]))
    for feature in entry.get('editorial_features',[]):photographs.extend(feature.get('images',[]))
    for photo in photographs:
        for field in ('images','previews'):
            relative=image_manifest[field][photo['url']];path=Path(relative)
            assert not path.is_absolute() and '..' not in path.parts and path.parts[:2]==('assets','images')
            assert (folder/path).is_file(),'Every picture needs a bundled image and preview'
models=[]
for entry in catalog["entries"]:
    for model in (entry.get("models") or []):
        asset=model.get("asset_file","");path=Path(asset)
        assert asset.startswith("models/") and not path.is_absolute() and ".." not in path.parts and path.suffix==".glb"
        assert (folder/path).is_file()
        models.append(asset)
if not models:
    assert not list((folder/'models').glob('*.glb')), 'Unreferenced console mesh in image-only payload'
    assert not list((folder/'models').glob('*.artwork.pmc')), 'Unreferenced console texture cache in image-only payload'
if models:
    assert (folder/"models/index.json").is_file() and (folder/"models/licenses").is_dir()
    model_index=json.loads((folder/"models/index.json").read_text(encoding="utf-8"))
    indexed={item["asset_file"]:item for item in model_index["models"]}
    assert set(models).issubset(indexed), "Every exhibited model needs provenance"
    assert {p.relative_to(folder).as_posix() for p in (folder/"models").glob("*.glb")}==set(indexed), "Unlisted model in payload"
    expected_caches={item["artwork_cache"]["asset_file"] for item in indexed.values() if item.get("artwork_cache")}
    assert {p.relative_to(folder).as_posix() for p in (folder/"models").glob("*.artwork.pmc")}==expected_caches,"Unlisted model artwork cache in payload"
    for asset,item in indexed.items():
        path=Path(asset)
        assert asset.startswith("models/") and len(path.parts)==2 and not path.is_absolute() and ".." not in path.parts
        assert (folder/path).stat().st_size==item["bytes"] and digest_file(folder/path)==item["sha256"]
        checked_artwork_cache(folder, item)
manifest = {"title_id": param["titleId"], "category": "Games", "version": param["contentVersion"],
            "exhibits": len(catalog["entries"]), "files": files, "payload_bytes": sum(f["bytes"] for f in files),
            "archive_bytes": None if args.folder_only else archive.stat().st_size, "archive_sha256": None if args.folder_only else digest_file(archive),"bundled_models":len(set(models)),"delivery":"FileZilla folder" if args.folder_only else "ZIP and folder"}
(root / ("build/PPSA70421-slice-manifest.json" if args.vertical_slice else "build/PPSA70421-payload-manifest.json")).write_text(json.dumps(manifest, indent=2)+"\n")
print(json.dumps({k:v for k,v in manifest.items() if k!="files"}, indent=2))
print(f"Verified {len(files)} payload files" + ("; FileZilla folder references and hashes checked" if args.folder_only else "; ZIP entries match and all have 0777 modes"))
