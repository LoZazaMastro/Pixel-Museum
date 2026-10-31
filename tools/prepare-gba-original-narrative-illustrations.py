"""Freeze original AGB-001 artifacts for independent review, without admission."""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = "build/research/gba-original-narrative-illustrations/"
def sha(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf8"))
entry = next(e for e in load("content/catalog.json")["entries"] if e["id"] == "workbook-03-21-game-boy-advance")
manual = "https://www.nintendo.com/eu/media/downloads/support_1/game_boy_advance_4/GBA_Manual_UK_DE_FR.pdf"
def artifact(file, url, page, title, caption, creator, license, license_url, paragraph):
    path = BASE + file
    with Image.open(ROOT/path) as image:
        image.load()
        width, height = image.size
    return dict(url=url, source_page=page, title=title, caption=caption,
        creator=creator, credit=creator+" / "+license, license=license,
        license_url=license_url, width=width, height=height,
        recovery_local_source=path, story_paragraph=paragraph,
        verification=dict(verified=True, sha256=sha(path), width=width, height=height),
        quality_verified="Original file fully decoded and individually viewed. Native photograph or direct vector-page rendering, with no raster enlargement.")
images = [artifact("manual-original-component-diagram.png", manual+"#pdf-page=3&printed-page=7&artifact=components", manual,
    "The original Game Boy Advance controls and components",
    "The AGB-001 layout in Nintendo's European support manual: screen, shoulder buttons, cartridge slot and connectors. This is the manual revision dated 26 September 2007, illustrating the original 2001 hardware; its COPY watermark is retained.",
    "Nintendo", "Copyright Nintendo; original hardware manual artwork, rights reserved.", manual, 0),
    artifact("manual-four-player-link-diagram.png", manual+"#pdf-page=6&printed-page=12&artifact=four-player-link", manual,
    "Four original Game Boy Advance systems connected for multiplayer",
    "Nintendo's four-player link-cable diagram, excerpted from printed page 12 of the later European AGB support manual. It shows the cable chain and the four Game Paks; supported single-cartridge modes depend on the software, as explained in the accompanying story. The original COPY watermark remains visible.",
    "Nintendo", "Copyright Nintendo; original hardware manual artwork, rights reserved.", manual, 2),
    artifact("original-agb-jpn-back.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/0/0e/Game_Boy_Advance_back.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original",
    "https://commons.wikimedia.org/wiki/File:Game_Boy_Advance_back.jpg",
    "The rear of the original AGB-001 handheld",
    "An original Indigo Game Boy Advance AGB-001, showing the wide shell and rear cartridge slot. The documented Japanese unit was assembled in week 6 of 2001; the date of this later photograph is unknown. This is a hardware view alongside the design account, rather than a portrait of its designer.",
    "gekkio (Joonas Javanainen)", "CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/", 3)]
updates = [dict(kind="add_narrative_image", image=i) for i in images]
inventory = load(BASE+"existing-two-artifacts-native-inventory.json")
for row, paragraph in zip(inventory, [4, 1]):
    old = next(i for i in entry["images"] if i.get("story_paragraph") == paragraph)
    image = dict(old)
    for obsolete in ("original_url", "quality_verified"):
        image.pop(obsolete, None)
    image.update(url=row["url"], recovery_local_source=row["file"], width=row["width"], height=row["height"],
        verification=dict(verified=True, sha256=row["sha256"], width=row["width"], height=row["height"]),
        quality_verified="Original native-resolution file of the same previously admitted photograph; no enlargement. Photographer's source modifications, including the blank cartridge label, are preserved.")
    updates.append(dict(kind="replace_exact_thumbnail", supersedes_url=old["url"], old_image=old, image=image))
source_files = ["primary-manual-receipt.json", "nintendo-gba-original-hardware-manual.pdf", "gba-back-commons-fileinfo.json", "existing-two-artifacts-native-fileinfo.json"]
doc = dict(schema_version=1, publication_status="research_candidate_only", entry_id=entry["id"],
    scope="Three missing original-GBA narrative illustrations plus native-resolution replacements for two already used photographs. No prose, hero, model, date, video or soundtrack changes.",
    body_sha256=hashlib.sha256(json.dumps(entry["body"], ensure_ascii=False, separators=(",", ":")).encode()).hexdigest(),
    original_body=entry["body"], original_headings=entry["story_headings"],
    source_files=[dict(file=BASE+f, sha256=sha(BASE+f)) for f in source_files], image_updates=updates,
    vector_derivations=[dict(file=BASE+"manual-original-component-diagram.png", pdf_page=3, printed_page=7,
        poppler_arguments=["-f", "3", "-l", "3", "-scale-to", "3200", "-x", "1580", "-y", "300", "-W", "1420", "-H", "1660", "-png", "-singlefile"]),
        dict(file=BASE+"manual-four-player-link-diagram.png", pdf_page=6, printed_page=12,
        poppler_arguments=["-f", "6", "-l", "6", "-scale-to", "9600", "-x", "3360", "-y", "2970", "-W", "1260", "-H", "1410", "-png", "-singlefile"])],
    preservation_notes=["The official PDF contains vector diagrams, not low-resolution embedded photographs. Selected diagrams are rendered directly from vectors.",
        "No removal of COPY watermarks or registration marks. Manual revision 2007 is explicit rather than falsely claiming a launch-2001 printing.",
        "The two original-photograph upgrades supersede the exact old thumbnails; they must not remain as duplicate gallery images.",
        "Original AGB-001 hero and explicit user preference for photography instead of 3D stay unchanged."])
path = ROOT / BASE / "five-original-gba-artifacts-candidate.json"
path.write_text(json.dumps(doc, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
print(json.dumps(dict(candidate=path.relative_to(ROOT).as_posix(), sha256=sha(path.relative_to(ROOT)), updates=len(updates)), indent=2))
