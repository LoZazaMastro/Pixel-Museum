"""Exact-slot, source-bound media replacements. No caller or writer is installed here.

Validate the entire batch before touching the supplied in-memory entries. Only
images[index] is replaced; all prose, dates, associations and other slots stay
byte-for-byte equivalent as JSON values. The caller owns persistence and review.
"""
import copy
import hashlib
import json
import struct
from pathlib import Path


FIELDS = ("title", "subtitle", "summary", "body", "story_headings")


def english_fields_sha256(owner):
    fields = {k: owner.get(k, [] if k in ("body", "story_headings") else "")
              for k in FIELDS}
    return hashlib.sha256(json.dumps(fields, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def _native_dimensions(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return list(struct.unpack(">II", data[16:24]))
    if data[:6] in (b"GIF87a", b"GIF89a") and len(data) >= 10:
        return list(struct.unpack("<HH", data[6:10]))
    if data.startswith(b"\xff\xd8"):
        pos = 2
        while pos < len(data):
            if data[pos] != 255:
                raise ValueError("Malformed reviewed JPEG")
            while pos < len(data) and data[pos] == 255:
                pos += 1
            if pos >= len(data):
                break
            marker = data[pos]
            pos += 1
            if marker in (0xD8, 0xD9, 0x01) or 0xD0 <= marker <= 0xD7:
                continue
            if marker == 0xDA or pos + 2 > len(data):
                break
            length = int.from_bytes(data[pos:pos + 2], "big")
            if length < 2 or pos + length > len(data):
                raise ValueError("Malformed reviewed JPEG segment")
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                          0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                if length < 7:
                    raise ValueError("Malformed reviewed JPEG frame")
                height, width = struct.unpack(">HH", data[pos + 3:pos + 7])
                return [width, height]
            pos += length
    raise ValueError("Unsupported or invalid reviewed image format")


def _inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Reviewed source escapes repository root")
    return path


def apply(entries, root):
    """Validate and apply exactly the batch's image slots; return a receipt dict.

    Does not write files, fetch URLs, change provenance, regenerate credits, or
    alter any source text. Repeated calls are idempotent only for exact after
    dictionaries, not just matching URLs. An invalid later row leaves all rows
    untouched. A changed global catalog hash is allowed only when each scoped
    owner's complete five-field English digest still matches the reviewed row.
    """
    root = Path(root).resolve()
    batch_path = root / "content/expansion/reviewed-early-media-boundary.json"
    raw = batch_path.read_bytes()
    batch = json.loads(raw)
    if batch.get("schema_version") != 1:
        raise ValueError("Unsupported reviewed media boundary schema")
    rows = batch["rows"]
    if batch.get("frozen") is not True or batch.get("planned_row_count") != len(rows):
        raise ValueError("Reviewed media boundary is not a complete frozen batch")
    if not rows or len(rows) != batch["row_count"]:
        raise ValueError("Reviewed media boundary row count differs")
    owners = {}
    def collect(items):
        for owner in items:
            owner_id = owner["id"]
            if owner_id in owners:
                raise ValueError("Duplicate owner id: " + owner_id)
            owners[owner_id] = owner
            collect(owner.get("editorial_features", []))
    collect(entries)
    staged, seen, unchanged = [], set(), 0
    for row in rows:
        owner_id, index = row["owner_id"], row["index"]
        if type(index) is not int or index < 0 or (owner_id, index) in seen:
            raise ValueError("Invalid or duplicate reviewed image slot")
        seen.add((owner_id, index))
        if owner_id not in owners:
            raise ValueError("Reviewed owner missing: " + owner_id)
        owner = owners[owner_id]
        if english_fields_sha256(owner) != row["expected_english_five_fields_sha256"]:
            raise ValueError("Reviewed English changed: " + owner_id)
        images = owner.get("images", [])
        if len(images) != row["expected_image_count"] or index >= len(images):
            raise ValueError("Reviewed image slot missing: " + owner_id)
        before, after = row["before_image"], row["after_image"]
        if before["url"] != row["expected_old_url"]:
            raise ValueError("Inconsistent reviewed old URL")
        if before == after:
            raise ValueError("Reviewed replacement is empty")
        source = row["source"]
        if after.get("recovery_local_source") != source["recovery_local_source"]:
            raise ValueError("Reviewed recovery path differs")
        blob = _inside(root, source["recovery_local_source"]).read_bytes()
        if hashlib.sha256(blob).hexdigest() != source["sha256"]:
            raise ValueError("Reviewed local image changed: " + owner_id)
        native = _native_dimensions(blob)
        if native != source["native_dimensions"] or native != [after["width"], after["height"]]:
            raise ValueError("Reviewed native image dimensions differ")
        for pin, expected in row.get("source_files", {}).items():
            if hashlib.sha256(_inside(root, pin).read_bytes()).hexdigest() != expected:
                raise ValueError("Reviewed source evidence changed: " + pin)
        if images[index] == after:
            unchanged += 1
        elif images[index] == before and images[index].get("url") == row["expected_old_url"]:
            staged.append((images, index, copy.deepcopy(after)))
        else:
            raise ValueError("Reviewed image has unexpected edits: " + owner_id)
    for images, index, after in staged:
        images[index] = after
    return {"status": "PASS", "batch_sha256": hashlib.sha256(raw).hexdigest(),
            "rows": len(rows), "changed_slots": len(staged),
            "already_exact_slots": unchanged, "persistent_writes": False}
