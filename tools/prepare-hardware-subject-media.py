"""Freeze three visual hardware-photo corrections without writing a catalog."""
from pathlib import Path
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "build/research/hardware-release-consolidation"
catalog = json.loads((ROOT / "content/catalog.json").read_text(encoding="utf8"))
owners = {entry["id"]: entry for entry in catalog["entries"]}
native = json.loads((FOLDER / "super-famicom-native-recovery.json").read_text(encoding="utf8"))
photo = dict(url=native["url"], title="The original Japanese Super Famicom console",
    caption="Japanese Super Famicom hardware introduced in 1990; photographed later.",
    width=native["width"], height=native["height"], creator=native["creator"],
    source_page=native["source_page"], credit=native["creator"] + " / Public domain",
    license="Public domain", license_url="https://commons.wikimedia.org/wiki/Commons:Public_domain",
    recovery_local_source=native["local_source"], story_paragraph=-1,
    quality_verified="Native 3280x2230 transparent PNG, fully decoded and visually inspected; no enlargement or alpha compositing.",
    verification=dict(source_sha256=native["sha256"], no_upscaling=True, alpha_preserved=True))

changes = [dict(entry_id="daily-11-21", remove_urls=[owners["daily-11-21"]["images"][0]["url"]],
    preferred_url=photo["url"], images=[photo],
    reasons=["Legacy photograph has visible gray matte rectangles. Replace it with an authenticated Japanese Super Famicom native RGBA photograph, preserving transparency. PAL photograph remains explicitly assigned to the regional-design story."]),
    dict(entry_id="daily-12-02", remove_urls=[owners["daily-12-02"]["images"][1]["url"]],
        preferred_url=owners["daily-12-02"]["images"][0]["url"], images=[],
        reasons=["The legacy slots photograph repeats the later, explicitly captioned GBA SP/DS Lite comparison already present at image 3. Preserve that attributed image and its paragraph 4 association."]),
    dict(entry_id="nintendo-3ds", remove_urls=[owners["nintendo-3ds"]["images"][0]["url"]],
        preferred_url=owners["nintendo-3ds"]["images"][2]["url"], images=[],
        reasons=["The legacy hero repeats Evan-Amos's Aqua Blue Nintendo 3DS photograph already retained as an attributed Commons image. Select the properly credited image once; preserve the distinct 2010 prototype photograph."],
        metadata_overrides={owners["nintendo-3ds"]["images"][1]["url"]: dict(
            creator="popculturegeek.com", credit="popculturegeek.com / CC BY 2.0",
            license="CC BY 2.0", license_url="https://creativecommons.org/licenses/by/2.0/",
            source_page="https://commons.wikimedia.org/wiki/File:Nintendo_3DS_display_case_at_E3_2010_(front_side_angle).jpg")})]
document = dict(schema_version=1, publication_status="candidate_requires_independent_visual_review", entries=changes,
    source_catalog_sha256=hashlib.sha256((ROOT / "content/catalog.json").read_bytes()).hexdigest(),
    source_metadata_file="build/research/hardware-release-consolidation/commons-subject-corrections-metadata.json",
    source_metadata_sha256=hashlib.sha256((FOLDER / "commons-subject-corrections-metadata.json").read_bytes()).hexdigest(),
    scope="Exact photograph/attribution corrections only; no prose, date, approved model or feature changes.")
path = FOLDER / "hardware-subject-media-candidate.json"
path.write_text(json.dumps(document, ensure_ascii=True, indent=2) + "\n", encoding="utf8")
print(json.dumps(dict(candidate_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), entries=len(changes)), indent=2))
