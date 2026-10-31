"""Unicode inventory of fields consumed by the native catalogue/locale UI.

Research receipts, ingestion notes, raw Wikipedia markup, URL search queries,
unused metadata and source-language snapshots are deliberately not UI copy.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
ENTRY_TEXT = ("title", "subtitle", "summary", "editorial_credit", "body", "story_headings")
IMAGE_TEXT = ("title", "caption", "creator", "license", "credit", "source_page")
VIDEO_TEXT = ("title", "caption", "creator", "source_page")
MODEL_TEXT = ("title", "creator", "license", "credit", "source_page", "display_caption")
SOURCE_TEXT = ("title", "url", "publisher", "license", "attribution")


def collect(root=ROOT):
    root=Path(root)
    records, files = [], {}

    def add(value, file, entry, field):
        if isinstance(value, str):
            records.append({"file": file, "entry_id": entry, "field": field, "text": value})
        elif isinstance(value, list):
            for n, item in enumerate(value):
                add(item, file, entry, f"{field}[{n}]")

    def fields(row, names, file, entry, prefix=""):
        for key in names:
            if key in row:
                add(row[key], file, entry, prefix + key)

    def article(row, file, identity=None, prefix=""):
        entry = identity or row.get("id", "")
        fields(row, ENTRY_TEXT, file, entry, prefix)
        for group, names in (("images", IMAGE_TEXT), ("videos", VIDEO_TEXT), ("models", MODEL_TEXT), ("sources", SOURCE_TEXT)):
            for n, item in enumerate(row.get(group) or []):
                fields(item, names, file, entry, f"{prefix}{group}[{n}].")
        rooms = ([row["soundtrack"]] if row.get("soundtrack") else []) + row.get("soundtrack_rooms", [])
        for n, room in enumerate(rooms):
            fields(room, ("title", "composer", "curator_note"), file, entry, f"{prefix}music[{n}].")
            for track, item in enumerate(room.get("tracks", [])):
                fields(item, VIDEO_TEXT, file, entry, f"{prefix}music[{n}].tracks[{track}].")
        features = row.get("editorial_features", [])
        for n, feature in (features.items() if isinstance(features, dict) else enumerate(features)):
            article(feature, file, entry, f"{prefix}features[{n}].")

    paths = [root / "content/catalog.json", root / "content/human-history.json"]
    paths += sorted((root / "content/ui-locales").glob("*.json"))
    paths += sorted((root / "content/museum-locales").glob("*.json"))
    for path in paths:
        if not path.exists():
            continue
        data = path.read_bytes()
        file = path.relative_to(root).as_posix()
        files[file] = hashlib.sha256(data).hexdigest()
        document = json.loads(data)
        if "ui-locales/" in file:
            for group in ("strings", "music_strings"):
                prefix = "" if group == "strings" else "music."
                for key, value in document.get(group, {}).items():
                    add(key, file, "interface", prefix + "source")
                    add(value, file, "interface", prefix + "translation")
        else:
            fields(document, ("title", "subtitle"), file, "collection")
            for era in document.get("eras", []):
                fields(era, ("title", "summary"), file, era.get("id", "era"))
            entries = document.get("entries", [])
            for identity, row in (entries.items() if isinstance(entries, dict) else ((r.get("id", ""), r) for r in entries)):
                article(row, file, identity)
    points = {ord(char) for record in records for char in record["text"] if ord(char) > 127}
    return points, records, files


def script_class(codepoint):
    if 0x0900 <= codepoint <= 0x0DFF or 0x0E00 <= codepoint <= 0x0EFF or 0x1780 <= codepoint <= 0x17FF:
        return "complex_script_requires_shaping"
    if 0x0590 <= codepoint <= 0x08FF or 0xFB1D <= codepoint <= 0xFDFF or 0xFE70 <= codepoint <= 0xFEFF:
        return "bidi_or_shaping_requires_review"
    return "ordinary_glyph"


def complex_runs(records):
    pattern=r"[\u0590-\u08ff\u0900-\u0dff\u0e00-\u0eff\u1780-\u17ff]+(?:[ \u00a0]+[\u0590-\u08ff\u0900-\u0dff\u0e00-\u0eff\u1780-\u17ff]+)*"
    return sorted({run for record in records for run in re.findall(pattern,record["text"])})
