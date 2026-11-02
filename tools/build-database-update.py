"""Build a cumulative, data-only database update from two reviewed runtimes.

Uploads and publication remain explicit. Use the SAME baseline runtime for all
revisions within a reader generation; clients reuse identical SHA-256 blobs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil

LANGUAGES = ("en", "it", "es", "fr", "de")
CONTENT = ("catalog", "human-history", "culture-memories", "credits",
           "collection-image-supplements")
MAX_FILE = 64 << 20


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def candidates(root: Path):
    for name in CONTENT:
        yield Path("content") / (name + ".json")
    for group in ("locales", "ui-locales"):
        for language in LANGUAGES:
            yield Path("content") / group / (language + ".json")
    for folder, extensions in (("image-supplements", {".png", ".jpg", ".jpeg", ".webp"}),
                               ("culture-audio", {".wav"})):
        directory = root / "assets" / folder
        if directory.is_dir():
            for path in sorted(directory.rglob("*")):
                if path.is_file() and path.suffix.lower() in extensions:
                    yield path.relative_to(root)


def build(args):
    baseline, updated, output = (Path(value).resolve() for value in
                                 (args.baseline, args.updated, args.output))
    if baseline == updated or output in (baseline, updated) or updated in output.parents or baseline in output.parents:
        raise ValueError("Use separate baseline, updated runtime and output folders")
    prefix = "https://github.com/LoZazaMastro/Pixel-Museum/releases/download/"
    if not args.asset_url.startswith(prefix) or not args.asset_url.endswith("/"):
        raise ValueError("--asset-url must be this project's exact GitHub release asset directory")
    if args.revision <= 1:
        raise ValueError("An update revision must be greater than bundled revision 1")
    output.mkdir(parents=True, exist_ok=True)
    files = []
    for relative in candidates(updated):
        path, old = updated / relative, baseline / relative
        if not path.is_file():
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(updated):
            raise ValueError(f"Symlinks and external paths are forbidden: {relative}")
        size = path.stat().st_size
        digest = sha(path)
        if old.is_file() and old.stat().st_size == size and sha(old) == digest:
            continue
        if not 0 < size <= MAX_FILE:
            raise ValueError(f"Invalid database file size: {relative}")
        if path.suffix == ".json":
            if not isinstance(json.loads(path.read_text(encoding="utf-8")), dict):
                raise ValueError(f"Database JSON must be an object: {relative}")
        filename = f"database-{args.revision}-{digest}{path.suffix}"
        target = output / filename
        if not target.exists() or sha(target) != digest:
            shutil.copyfile(path, target)
        files.append(dict(path=relative.as_posix(), url=args.asset_url + filename,
                          sha256=digest, bytes=size))
    if not files:
        raise ValueError("No changed database files were found")
    if len(files) > 16384 or sum(item["bytes"] for item in files) > 4 << 30:
        raise ValueError("Database update exceeds the reader's limits")
    manifest = dict(schema_version=1, database_id="pixel-museum", minimum_reader=1,
                    revision=args.revision, version=args.version, notes={}, files=files)
    if args.notes:
        manifest["notes"] = json.loads(Path(args.notes).read_text(encoding="utf-8"))
        if not isinstance(manifest["notes"], dict) or any(
            key not in LANGUAGES or not isinstance(value, str) or len(value.encode()) > 4096
            for key, value in manifest["notes"].items()
        ):
            raise ValueError("Notes must be an EN/IT/ES/FR/DE text object")
    path = output / "database-update.json"
    path.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(dict(manifest=str(path), changed_files=len(files),
                          download_bytes=sum(item["bytes"] for item in files)), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("baseline", "updated", "output", "asset-url", "version"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--revision", required=True, type=int)
    parser.add_argument("--notes", help="Optional JSON map with localized release notes")
    build(parser.parse_args())
