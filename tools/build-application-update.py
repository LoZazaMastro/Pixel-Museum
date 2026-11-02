"""Prepare the Windows update feed for an immutable, reviewed application ZIP.

This tool never uploads files or publishes a feed. Upload/verify the ZIP first;
publish the output on Pages last. PS5 application updates use ProsperoStore.
"""
from __future__ import annotations
import argparse, hashlib, json, re, stat, zipfile
from pathlib import Path, PurePosixPath


def sha(path):
    with path.open("rb") as stream: return hashlib.file_digest(stream, "sha256").hexdigest()


def build(args):
    archive = Path(args.archive).resolve()
    if not 32 <= archive.stat().st_size < 2 << 30: raise ValueError("Application ZIP exceeds the supported size")
    prefix = "https://github.com/LoZazaMastro/Pixel-Museum/releases/download/"
    if not args.url.startswith(prefix) or not args.url.endswith(".zip") or any(c in args.url for c in "\x00\r\n?#"):
        raise ValueError("Use an immutable ZIP asset URL in the Pixel Museum repository")
    with zipfile.ZipFile(archive) as z:
        names = set(); folded = set(); expanded = 0
        for item in z.infolist():
            if item.is_dir(): continue
            path = PurePosixPath(item.filename)
            if path.is_absolute() or any(part in (".", "..", "") or part.endswith((".", " ")) or ":" in part for part in path.parts) or "\\" in item.filename or stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError(f"Unsafe ZIP path: {item.filename}")
            if item.filename.casefold() in folded: raise ValueError("Duplicate Windows ZIP path")
            folded.add(item.filename.casefold()); names.add(item.filename); expanded += item.file_size
        if len(names) > 100000 or expanded > 4 << 30: raise ValueError("Application ZIP exceeds the reader limits")
        if z.getinfo("application-files.json").file_size > 4 << 20: raise ValueError("Oversized app inventory")
        inventory = json.loads(z.read("application-files.json"))
        version = inventory.get("version", "")
        if inventory.get("schema_version") != 1 or inventory.get("application_id") != "pixel-museum" or inventory.get("platform") != "windows-x64" or not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:[-+][A-Za-z0-9.+-]+)?", version):
            raise ValueError("Invalid application identity/version")
        required = {"Pixel Museum.exe", "tools/windows-updater/Pixel-Museum-Updater.exe", "LICENSE", "THIRD_PARTY_NOTICES.md", "content/collection-packs.json", "content/collection-archive-index.json", "assets/images/manifest.json"}
        if not required <= names: raise ValueError("Application ZIP is missing required runtime/update files")
        rows = inventory.get("files")
        if not isinstance(rows, list) or len(rows) != len(names)-1 or {row.get("path") for row in rows} != names-{"application-files.json"}:
            raise ValueError("Inventory must describe every application ZIP member except itself")
        # Read each member once to verify CRC and its independent inventory hash.
        for row in rows:
            item = z.getinfo(row["path"])
            if item.file_size != row.get("bytes"): raise ValueError(f"Inventory length mismatch: {row['path']}")
            with z.open(item) as stream: digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != row.get("sha256"): raise ValueError(f"Inventory checksum mismatch: {row['path']}")
    notes = json.loads(Path(args.notes).read_text(encoding="utf8")) if args.notes else {}
    if not isinstance(notes, dict) or any(key not in ("en", "it", "es", "fr", "de") or not isinstance(value, str) or len(value.encode()) > 4096 for key, value in notes.items()):
        raise ValueError("Notes must contain short EN/IT/ES/FR/DE strings")
    feed = {"schema_version": 1, "application_id": "pixel-museum", "platforms": {"windows-x64": {"version": version, "available": True, "url": args.url, "sha256": sha(archive), "bytes": archive.stat().st_size, "unpacked_bytes": expanded, "notes": notes}}}
    output = Path(args.output).resolve(); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(feed, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    print(json.dumps({"feed": str(output), "version": version, "archive_bytes": archive.stat().st_size, "unpacked_bytes": expanded, "sha256": feed["platforms"]["windows-x64"]["sha256"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "url", "output"): parser.add_argument("--"+name, required=True)
    parser.add_argument("--notes")
    build(parser.parse_args())
