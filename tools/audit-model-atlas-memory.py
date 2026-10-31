"""Read-only exact source-pixel/channel audit for admitted heavy consoles."""
from pathlib import Path
import hashlib
import io
import json
import struct
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/research/model-memory-audit"
OUT.mkdir(parents=True, exist_ok=True)

def audit(name):
    source = ROOT / "models" / (name + ".glb")
    raw = source.read_bytes()
    json_bytes, kind = struct.unpack_from("<II", raw, 12)
    assert kind == 0x4E4F534A
    doc = json.loads(raw[20:20 + json_bytes])
    binary = 20 + json_bytes + 8
    records = []
    for n, item in enumerate(doc.get("images", [])):
        view = doc["bufferViews"][item["bufferView"]]
        encoded = raw[binary + view.get("byteOffset", 0):binary + view.get("byteOffset", 0) + view["byteLength"]]
        with Image.open(io.BytesIO(encoded)) as image:
            rgba = image.convert("RGBA")
            data = rgba.tobytes()
            channels = rgba.split()
            record = {"image": n, "name": item.get("name", ""), "size": list(rgba.size),
                      "encoded_bytes": len(encoded), "encoded_sha256": hashlib.sha256(encoded).hexdigest(),
                      "rgba_sha256": hashlib.sha256(data).hexdigest(),
                      "extrema": rgba.getextrema(), "channel_sha256": [hashlib.sha256(c.tobytes()).hexdigest() for c in channels],
                      "materials": []}
            w, h = rgba.size
            texels = 0
            while True:
                texels += w * h
                if w == h == 1:
                    break
                w, h = max(1, w // 2), max(1, h // 2)
            record["mip_texels"] = texels
            records.append(record)
    for m, material in enumerate(doc.get("materials", [])):
        pbr = material.get("pbrMetallicRoughness", {})
        for role, value in [("base", pbr.get("baseColorTexture")), ("orm", pbr.get("metallicRoughnessTexture")),
                            ("normal", material.get("normalTexture")), ("emission", material.get("emissiveTexture")),
                            ("ao", material.get("occlusionTexture"))]:
            if value:
                texture = doc["textures"][value["index"]]
                records[texture["source"]]["materials"].append({"index": m, "name": material.get("name", ""), "role": role,
                                                               "sampler": doc.get("samplers", [])[texture["sampler"]] if "sampler" in texture else "default"})
    duplicates = [[a["image"], b["image"]] for a in records for b in records if a["image"] < b["image"] and a["size"] == b["size"] and a["rgba_sha256"] == b["rgba_sha256"]]
    return {"asset": str(source.relative_to(ROOT)), "source_sha256": hashlib.sha256(raw).hexdigest(),
            "source_unchanged": True, "decoded_identical_image_pairs": duplicates, "images": records}

result = {name: audit(name) for name in ("playstation-5", "wii-u-gamepad")}
(OUT / "heavy-atlas-exact-pixel-audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
for name, model in result.items():
    print(name, "decoded identical pairs", model["decoded_identical_image_pairs"])
    for item in model["images"]:
        print(" image", item["image"], item["size"], item["extrema"], [(v["name"], v["role"]) for v in item["materials"]])
