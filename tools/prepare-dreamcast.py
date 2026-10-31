#!/usr/bin/env python3
"""Prepare the licensed Dreamcast display material; preserve geometry/images.

SPDX-License-Identifier: GPL-3.0-or-later
Original model: Zerescas, CC BY 4.0. The output model retains that licence.
The source master is never changed. See the emitted modification metadata.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

SOURCE_ID = "f82d99e4739e42f4abfc37cb97918cfc"


def prepare(source: Path, destination: Path):
    data = source.read_bytes()
    if len(data) < 20 or struct.unpack_from("<III", data) != (0x46546C67, 2, len(data)):
        raise ValueError("Expected a complete original GLB 2.0 master")
    cursor, chunks = 12, []
    while cursor < len(data):
        length, kind = struct.unpack_from("<II", data, cursor)
        start = cursor + 8
        if length % 4 or start + length > len(data):
            raise ValueError("Invalid source GLB chunk")
        chunks.append((kind, data[start:start + length]))
        cursor = start + length
    if not chunks or chunks[0][0] != 0x4E4F534A:
        raise ValueError("Source JSON must be the first GLB chunk")
    document = json.loads(chunks[0][1])
    asset = document["asset"]
    if SOURCE_ID not in asset.get("extras", {}).get("source", ""):
        raise ValueError("This script only applies to the credited Zerescas model")
    matches = [m for m in document.get("materials", []) if m.get("name") == "Case"]
    if len(matches) != 1:
        raise ValueError("Expected exactly one original Case material")
    material = matches[0]
    before = {
        "alphaMode": material.get("alphaMode", "OPAQUE"),
        "baseColorFactor": material["pbrMetallicRoughness"].get("baseColorFactor", [1, 1, 1, 1]),
        "transmissionFactor": material.get("extensions", {}).get("KHR_materials_transmission", {}).get("transmissionFactor", 0),
    }
    material["alphaMode"] = "OPAQUE"
    material["pbrMetallicRoughness"]["baseColorFactor"] = [1.0, 1.0, 1.0, 1.0]
    material.setdefault("extensions", {}).setdefault("KHR_materials_transmission", {})["transmissionFactor"] = 0.0
    changes = {
        "material": "Case", "before": before,
        "after": {"alphaMode": "OPAQUE", "baseColorFactor": [1.0, 1.0, 1.0, 1.0], "transmissionFactor": 0.0},
        "reason": "Render the physical opaque white shell seen in the creator's reference thumbnail, correcting the transparent grey export material. Geometry, UVs, images, other materials and original rest pose are unchanged.",
        "source_sha256": hashlib.sha256(data).hexdigest(),
    }
    asset.setdefault("extras", {})["PixelMuseumMaterialCorrection"] = changes
    asset["generator"] = asset.get("generator", "") + "; Pixel Museum documented material correction"
    encoded = json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    encoded += b" " * (-len(encoded) % 4)
    chunks[0] = (0x4E4F534A, encoded)
    output = bytearray(struct.pack("<III", 0x46546C67, 2, 12 + sum(8 + len(body) for _, body in chunks)))
    for kind, body in chunks:
        output += struct.pack("<II", len(body), kind) + body
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(output)
    record = dict(changes, output_sha256=hashlib.sha256(output).hexdigest(), output_bytes=len(output))
    destination.with_suffix(".modifications.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    prepare(args.source, args.destination)
