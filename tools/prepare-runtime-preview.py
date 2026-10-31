"""Use the console packaging projection for local production-UI previews.

Run in WSL: large source assets are linked, not copied or recompressed. Only the
generated preview directory is written. Original authoring and locale files are
never used as mutable preview data.
"""
from pathlib import Path
import hashlib
import json
import os
import runpy

ROOT = Path(__file__).resolve().parents[1]
target = ROOT / "build/runtime-preview"
(target / "content").mkdir(parents=True, exist_ok=True)
projection = runpy.run_path(str(ROOT / "tools/runtime-catalog.py"))
source = (ROOT / "content/catalog.json").read_bytes()
runtime = projection["project"](json.loads(source), hashlib.sha256(source).hexdigest())
payload = projection["encoded"](runtime)
if len(payload) > 64 << 20:
    raise SystemExit("Projected preview catalogue exceeds the native reader budget")
history=ROOT/"content/human-history.json"
if history.is_file():
    history_payload=projection["encoded"](projection["project"](json.loads(history.read_bytes())))
    if len(history_payload)>64<<20:raise ValueError("History catalogue exceeds the native reader budget")
    (target/"content/human-history.json").write_bytes(history_payload)

destination = target / "content/catalog.json"
temporary = destination.with_suffix(".tmp")
temporary.write_bytes(payload)
temporary.replace(destination)


def link(source_path, destination_path):
    if destination_path.is_symlink():
        if destination_path.resolve() != source_path.resolve():
            raise ValueError("Preview link points at an unexpected source: " + str(destination_path))
        return
    if destination_path.exists():
        raise ValueError("Refusing to replace a non-link preview asset: " + str(destination_path))
    os.symlink(source_path.resolve(), destination_path, target_is_directory=source_path.is_dir())


for name in ("assets", "models", "music", "licenses"):
    link(ROOT / name, target / name)
locales=target/"content/locales"
if locales.is_symlink():locales.unlink()
locales.mkdir(exist_ok=True)
for language in ("en","it","es","fr","de"):
    (locales/(language+".json")).write_text(json.dumps({"locale":language,"entries":{}})+"\n",encoding="utf-8")
link(ROOT / "content/ui-locales", target / "content/ui-locales")
link(ROOT / "content/culture-memories.json", target / "content/culture-memories.json")
link(ROOT / "content/credits.json", target / "content/credits.json")
print("Production runtime preview:", len(runtime["entries"]), "entries,", len(payload), "catalogue bytes")
