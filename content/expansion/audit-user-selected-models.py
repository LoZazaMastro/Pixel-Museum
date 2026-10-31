"""Compile source metadata for the user's exact bulk Sketchfab choices.

This audits public model metadata; authenticated file downloads belong to root.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHOICES = [
    ("odyssey", "1442250a6bba4c70af4fc6b9807bcfdf", "Original Magnavox Odyssey recreation", "Existing1972 platform entry. Public metadata has no download permission or public reuse licence."),
    ("atari-vcs", "f9ec8aa8e4fa454cbbe821a23ca6e83d", "Six-switch Atari2600/VCS scene with controllers and cartridges", "Existing1977 platform entry. Six-switch exterior is visible, but the exact heavy-sixer/light-sixer production subtype is not established by this thumbnail; do not label it as a verified1977 launch-production specimen. High-detail scene reports3,917,069triangles, so check renderer and memory budgets before integration. Authored accessories may be selected without substituting generic geometry."),
    ("snes-pal", "31f4914a42e14631aeba15a539161e62", "European/PAL Super Nintendo with multicolour buttons and Super Mario World cartridge/booklet", "1992 PAL hardware, not the angular North American1991 shell or Japanese1990 Super Famicom launch. Duplicate user input counted once. Scene includes animated content/audio; no public download or licence."),
    ("nes", "3d05bd5b534f4d869934b09e9bf0c224", "Grey front-loading Nintendo Entertainment System", "Use the western NES history beginning in NorthAmerica1985, not Famicom's Japan1983 date. Public source is view-only with a SteamWorkshop/profile reference, not a redistribution licence."),
    ("dreamcast", "f82d99e4739e42f4abfc37cb97918cfc", "Original white Sega Dreamcast with controller and accessories", "Already approved source for the existing Dreamcast entry. Creator's CC BY licence covers their model; description separately credits Sega's SonicAdventure2 music and disc artwork. Do not assume that means permission to redistribute soundtrack audio."),
    ("sega-saturn", "a0eab4c5a35f4ff68e5b83690e4179cd", "Black western Saturn case with original-style oval buttons and controller", "Platform first launched in Japan1994; this black western-style body is not the grey Japanese launch colourway. Public source view-only; SteamWorkshop link is not a standalone reuse licence."),
    ("xbox-halo", "26709a2264264e32856f3e9fddac5a23", "Original black Xbox console with used/dirty finish", "Existing original-Xbox2001 entry, not XboxOne. Creator describes this as an improved version of a previous model. Public source view-only with no licence."),
    ("xbox-one", "8866e33768e84b27b69e07abcde8a593", "Original2013 XboxOne black rectangular console", "Creator explicitly identifies the original2013 body and scale modelling from reference drawings. CC BY-NC4.0; do not relabel as unrestricted CC BY."),
    ("xbox-series-x", "e983b0e9ef984aa6934176e310b7f0f2", "XboxSeriesX pre-release visual mock-up", "Published13December2019. Creator explicitly calls this a quick mock-up of the newly announced console for advertising practice. It predates2020 retail hardware and should be labelled as an artist's pre-release reconstruction, not a measured retail scan. CC BY-NC4.0."),
    ("xbox-series-s", "61a9d3b53ba34841a9272f38e8be736a", "Original white XboxSeriesS with circular black vent", "Original2020 design, not later black1TB revision. Public source view-only with no public download or licence."),
    ("game-boy-advance", "87e049f9c6944166a03a3fc551876545", "Scene contains BOTH original horizontal GameBoyAdvance and red clamshell GameBoyAdvanceSP", "User confirmed this exact target rather than the ambiguous ZeldaSP link. Original GBA platform launched2001; SP redesign2003. If showing both together, caption both revisions rather than calling the SP the2001 original. View-only/no public licence."),
    ("nintendo-dsi", "934fdde060874d5c99b40cdf1dbb37f2", "DS-family artist model identified by its creator as NintendoDSi; defining camera/buttons omitted", "User-selected model is downloadable CC BY4.0. Creator explicitly calls it DSi and admits missing camera/buttons. Associate with the2008DSi story, not an exact2004DS or2006DSLite. Do not claim a complete accurate retail reconstruction."),
    ("nintendo-3ds-zelda-25", "1d7952ea98d844f894ec921722e29659", "Original Nintendo3DS, Legend of Zelda25th Anniversary limited edition", "Special2011 black/gold anniversary edition, not generic launch colourway or New3DS. View-only/no public licence."),
    ("nintendo-3ds", "69fb907885d44d3484521ab7e0fdd750", "Stylised Nintendo3DS artist model from a handheld-history rendering project", "Subsequent user alternative byElijahRobertson(3Dbear); view-only with no public licence. Creator describes rendering handhelds as if rendered on themselves; do not mistake deliberate stylisation for measured retail fidelity."),
    ("game-boy-advance", "ba9435d1e90b4eafbefee53ace5549d4", "Original horizontal Game Boy Advance, textured Substance Painter study", "User's subsequent original-GBA alternative by Skribbl. Current API reports not downloadable and no public licence. Absent from the official Objaverse UID mapping checked here; no historical CC grant was established. Do not extract viewer geometry."),
]


def main():
    import runpy
    spaced_text = runpy.run_path(str(ROOT / "build-hardware-additions.py"))["spaced_text"]
    result = []
    for exhibit, uid, variant, note in CHOICES:
        data = json.loads((ROOT / "wikipedia-cache" / ("sketchfab-" + uid + ".json")).read_text(encoding="utf-8"))
        licence = data.get("license") or {}
        downloadable = bool(data.get("isDownloadable"))
        result.append({"exhibit_id": exhibit, "uid": uid, "title": data["name"], "creator": data["user"]["displayName"],
                       "creator_url": data["user"]["profileUrl"], "source_page": data["viewerUrl"],
                       "api_url": "https://api.sketchfab.com/v3/models/" + uid,
                       "downloadable": downloadable, "ready_for_official_download": downloadable and bool(licence.get("label")),
                       "license": licence.get("label", "No public licence specified"), "license_url": licence.get("url", ""),
                       "license_requirements": licence.get("requirements", "No reuse permission established in the public metadata"),
                       "asset_published_at": data.get("publishedAt"), "reported_triangles": data.get("faceCount"),
                       "reported_vertices": data.get("vertexCount"), "reported_texture_count": data.get("textureCount"),
                       "represented_variant": spaced_text(variant), "notes": spaced_text(note), "visual_inspection": "Official publisher thumbnail inspected",
                       "file_downloaded_in_this_audit": False,
                       "status": "awaiting_root_authenticated_download_and_native_verification" if downloadable else "view_only_no_download_authorization", "checked": "2026-10-20"})
    output = {"schema_version": 1, "records": result, "unique_models": len(result),
              "downloadable_count": sum(e["downloadable"] for e in result), "view_only_count": sum(not e["downloadable"] for e in result),
              "scope": "Exact bulk user choices plus subsequently confirmed portable targets; one duplicated SNES input deduplicated. The two3DS records are successive source choices, not two copies of the same hardware. Metadata audit is not evidence that a file was downloaded or works in the native renderer.",
              "rights_note": "Publicly viewable is not equivalent to downloadable or licensed for reuse. Preserve exact creator/licence and third-party credits. No viewer extraction was performed."}
    (ROOT.parent / "user-selected-models-audit.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output["unique_models"], "unique models;", output["downloadable_count"], "downloadable;", output["view_only_count"], "view-only")


if __name__ == "__main__":
    main()
