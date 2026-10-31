"""Admit the independently rendered original silver GameCube scan unchanged."""
from pathlib import Path
import hashlib
import json
import shutil

root = Path(__file__).resolve().parents[1]
source = root / "downloads-original/gamecube_photoscan.glb"
digest = hashlib.sha256(source.read_bytes()).hexdigest()
assert digest == "4b05b22080e6706fa2af26f643243c9d8eba02db0feeada17939bc6218d8a19f"
target = root / "models/gamecube-photoscan.glb"
shutil.copyfile(source, target)
record = {
    "exhibit_id": "nintendo-gamecube",
    "asset_file": "models/gamecube-photoscan.glb",
    "display_caption": "GameCube Platinum",
    "title": "Gamecube Photoscan",
    "creator": "sixonetwo (EvanLegrand)",
    "creator_page": "https://sketchfab.com/evan4129",
    "source_page": "https://sketchfab.com/3d-models/gamecube-photoscan-83049e94c0b748a6a17be20bcf279fc5",
    "license": "CC BY 4.0",
    "license_url": "https://creativecommons.org/licenses/by/4.0/",
    "credit": "Gamecube Photoscan by sixonetwo / EvanLegrand (evan4129) / CC BY 4.0",
    "initial_angle": 2.45,
    "initial_tilt": 0.28,
    "initial_zoom": 1.3,
    "source_z_up": False,
    "sha256": digest,
    "bytes": target.stat().st_size,
    "acquisition": "Authenticated official Sketchfab GLB download, highest official 4K option. Current source UI names the evan4129 account sixonetwo; embedded original asset.extras credits EvanLegrand.",
    "texture_profile": "Original 4096-pixel colour atlas, UVs, geometry and authored material factors retained.",
    "modifications": "None. Original GLB copied byte-for-byte. Source NoAI tag retained in provenance; no generative editing, texture regeneration or geometry reconstruction.",
    "representation_note": "Silver/Platinum GameCube specimen with an open disc lid and inserted game disc. Specimen finish is not represented as the original launch finish; exhibit date belongs to the console launch, not this photographed unit.",
}
index_path = root / "models/index.json"
index = json.loads(index_path.read_text(encoding="utf-8"))
index["models"] = [row for row in index["models"] if row["exhibit_id"] != record["exhibit_id"]] + [record]
index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(root / "models/licenses/nintendo-gamecube.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
receipt = {
    "status": "PASS_original_scan_improves_surface_fidelity_parent_visually_approved",
    "record": record,
    "source_and_selected_bytes_identical": source.read_bytes() == target.read_bytes(),
    "render_output": "downloads-original/gamecube_photoscan.glb-{0,1}.png",
    "render_output_size": [3840, 2160],
    "render_log": "build/research/model-validation/gamecube-photoscan-front-4k.log",
    "limitations": ["Scan waviness at lid and some outer edges", "Baked highlights and natural wear remain in source atlas", "No controller included", "Not an absolute photorealistic geometry or material reproduction"],
    "original_rejected_purple_model_preserved_outside_selected_index": True,
    "physical_ps5_performance_verified": False,
    "console_transfer": False,
}
(root / "build/research/model-validation/gamecube-photoscan-admission.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Admitted {record['exhibit_id']}: {record['bytes']} bytes, {digest}; {len(index['models'])} selected models")
