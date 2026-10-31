#!/usr/bin/env python3
"""Prepare the licensed Xbox 360 display material without changing geometry.

SPDX-License-Identifier: GPL-3.0-or-later
Original model: Rob Bryant, Jr / robbryantjr, CC BY 4.0.
The source master remains untouched; the derived model retains CC BY 4.0.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

SOURCE_ID = "f65ac4721fd34dd8a8b63adfa712f5b8"


def prepare(source: Path, destination: Path):
    data = source.read_bytes()
    if len(data) < 20 or struct.unpack_from("<III", data) != (0x46546C67, 2, len(data)):
        raise ValueError("Expected a complete original GLB 2.0 master")
    chunks, cursor = [], 12
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
        raise ValueError("This correction applies only to the credited Rob Bryant model")
    materials = document.get("materials", [])
    if len(materials) != 1 or materials[0].get("name") != "material_0":
        raise ValueError("Expected the original single material")
    material = materials[0]["pbrMetallicRoughness"]
    before = material.get("baseColorFactor", [1, 1, 1, 1])
    if before != [0, 0, 0, 1]:
        raise ValueError("Expected the original literal-zero black base colour")
    material["baseColorFactor"] = [.018, .018, .018, 1.0]
    changes = {
        "material": "material_0",
        "property": "pbrMetallicRoughness.baseColorFactor",
        "before": before,
        "after": material["baseColorFactor"],
        "reason": "Replace mathematically non-reflecting zero black with physically plausible dark charcoal for the creator's black Xbox 360 appearance. Geometry, normals, UVs, metallic factor 0.18, roughness factor 0.34 and all other authored properties remain unchanged.",
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
