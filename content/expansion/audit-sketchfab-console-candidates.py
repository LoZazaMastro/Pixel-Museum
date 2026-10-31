"""Derive a model source manifest from official Sketchfab metadata and GLBs.

Research assets only: this never mutates the runtime catalogue.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "build/research/model-validation"
RESEARCH = DATA / "sketchfab"

CANDIDATES = [
    ("atari-vcs", "2024d933f6214117a399ad4287ede64d", None,
     "Preferred: detailed textured 1977 six-switch Heavy Sixer and peripherals. Official logged-in download required; not present in Objaverse or S3D3C index.", "preferred_official_download_needed"),
    ("atari-vcs", "f9ec8aa8e4fa454cbbe821a23ca6e83d", None,
     "Detailed six-switch console and full peripheral scene. 3.9M triangles in source exceeds current renderer index budget without selection/optimisation; no simplified generic replacement authorised.", "licensed_mirror_available_not_downloaded"),
    ("atari-vcs", "9820673636cb4f7c903b3d5d1fd8d8ec", "atari2600-zygomir",
     "Textured and mirrored, but visually a later four-switch Atari2600 variant; do not label this exact model as the original1977 six-switch console.", "verified_alternative_variant"),
    ("famicom", "b33939368ad04640919570a9d3bdbeda", None,
     "Preferred authored textured Famicom with original controller. Inspected official thumbnail; aged plastic and legible labels. Official logged-in download required; not present in Objaverse or S3D3C index.", "preferred_official_download_needed"),
    ("famicom", "c18c3608d42e4af59f92d5a14eae6be0", "famicom-birdchen",
     "Actual Famicom photogrammetry, visibly rough geometry and scan texture; source expressly calls this a photogrammetry test. Honest fallback only, not equivalent to preferred authored detailed model.", "verified_rough_scan_alternative"),
    ("playstation", "96bed8283f2940d7bb4b1866ab0637a2", "ps1-ceki",
     "Preferred downloaded candidate: detailed original PlayStation geometry, visible logos and front sockets. Official thumbnail inspected. Native renderer still must verify material handling and orientation.", "verified_downloaded_candidate"),
    ("playstation", "314a3d6565994565a7272223bd965348", None,
     "Thumbnail visibly uses inaccurate fictional SONYA/Polistation labels; reject as museum representation despite permissive licence.", "rejected_inaccurate_labels"),
    ("playstation-2", "b53f858aa1584229a7f906239fc158a2", "ps2-dolgov",
     "Alternative downloaded candidate: textured SCPH-30001 PS2 with controllers, memory card and case. Official thumbnail inspected; museum may select console/accessory nodes without substituting geometry. User subsequently selected Smoggybeard's exact model.", "verified_downloaded_alternative"),
    ("playstation-2", "8c992e9f5c86496ca7bd7dfe109d3cc2", "ps2-user-smoggybeard",
     "Exact model selected by the user. Detailed textured original PS2. Downloaded from official Objaverse mirror and verified. Licence is CC BY-NC-SA4.0: noncommercial use and ShareAlike apply to adaptations; preserve this specific licence rather than relabelling it CC BY.", "user_selected_verified_download"),
    ("playstation-2", "501b56286b144eff89745e97cdc5d08c", None,
     "Alternative detailed textured PS2 and black/silver accessories. Legal Objaverse mirror available. Preferred Dolgov candidate already downloaded.", "licensed_mirror_available_not_downloaded"),
    ("wii", "7214f7b100874ef3aad664feb0d5c4e4", None,
     "Preferred: detailed Wii with Remote and Nunchuk, 4K textures and visibly correct labels. Official logged-in download required; not present in Objaverse or S3D3C index.", "preferred_official_download_needed"),
    ("wii", "258447f719e84a2ca8b245d3d823c9ec", "wii-libblekibble",
     "Detailed geometry with Wii labels and multiple controllers but zero embedded textures. Thumbnail inspected. Does not fulfil the preference for a fully textured model as well as MacDrawz's version.", "verified_untextured_alternative"),
    ("wii", "84d7958819f34ab6ad4d30dbbaed11c3", None,
     "Original RVL-001 with many geometric details, but official metadata reports zero textures. Alternative only.", "licensed_mirror_available_not_downloaded"),
]


def main():
    paths = json.loads((DATA / "objaverse-paths.json").read_text(encoding="utf-8"))
    s3d3c = (DATA / "s3d3c-model-paths.txt").read_text(encoding="utf-8")
    output = []
    for exhibit, uid, local_stem, note, status in CANDIDATES:
        metadata = json.loads((RESEARCH / (uid + ".json")).read_text(encoding="utf-8"))
        licence = metadata["license"]
        record = {"exhibit_id": exhibit, "uid": uid, "title": metadata["name"],
                  "author": metadata["user"]["displayName"], "author_url": metadata["user"].get("profileUrl"),
                  "source_page": metadata["viewerUrl"], "metadata_url": "https://api.sketchfab.com/v3/models/" + uid,
                  "license": licence["label"], "license_url": licence["url"],
                  "downloadable": metadata["isDownloadable"], "published_at": metadata.get("publishedAt"),
                  "reported_triangles": metadata["faceCount"], "reported_vertices": metadata["vertexCount"],
                  "reported_texture_count": metadata.get("textureCount"),
                  "status": status, "visual_review": note,
                  "objaverse_path": paths.get(uid), "s3d3c_paths": [x for x in s3d3c.splitlines() if uid in x],
                  "direct_model_url": "https://huggingface.co/datasets/allenai/objaverse/resolve/main/" + paths[uid] if uid in paths else None,
                  "local_thumbnail": str((RESEARCH / (uid + ".jpg")).relative_to(ROOT)),
                  "credits": metadata["name"] + " by " + metadata["user"]["displayName"] + " / Sketchfab / " + licence["label"]}
        if local_stem:
            file = RESEARCH / (local_stem + ".glb")
            data = file.read_bytes()
            length = struct.unpack_from("<I", data, 12)[0]
            gltf = json.loads(data[20:20 + length])
            triangles = sum(gltf["accessors"][p["indices"]]["count"] // 3 if "indices" in p else gltf["accessors"][p["attributes"]["POSITION"]]["count"] // 3 for m in gltf["meshes"] for p in m["primitives"])
            record["download_verification"] = {"file": str(file.relative_to(ROOT)), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                                                "triangles": triangles, "meshes": len(gltf["meshes"]), "embedded_images": len(gltf.get("images", [])),
                                                "extensions_required": gltf.get("extensionsRequired", []), "magic": data[:4].decode("ascii")}
        output.append(record)
    result = {"schema_version": 1, "verified": "2026-10-20", "entries": output,
              "scope": "Source audit and research downloads only. The museum runtime catalogue is unchanged by this manifest.",
              "rights_note": "Preserve creator, Sketchfab source URL and exact licence when distributing or displaying these model assets. Manufacturer logos remain their owners' property. Mirrors are official Objaverse dataset files, not viewer extraction.",
              "s3d3c_source": "https://osf.io/w2qu9/", "s3d3c_index_url": "https://osf.io/download/egc96/"}
    (ROOT / "content/model-candidates-sketchfab-curation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Audited", len(output), "candidates; downloaded", sum("download_verification" in x for x in output))


if __name__ == "__main__":
    main()
