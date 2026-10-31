"""Freeze the two reviewed hardware-identity candidates; never publish a catalog."""
from pathlib import Path
import copy
import hashlib
import json
import runpy

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "build/research/hardware-release-consolidation"
catalog = json.loads((ROOT / "content/catalog.json").read_text(encoding="utf8"))
entries = {entry["id"]: entry for entry in catalog["entries"]}
helper = runpy.run_path(str(ROOT / "content/expansion/hardware_family_consolidation.py"))
wiki_path = FOLDER / "wikipedia-hardware-introductions.json"
wiki = json.loads(wiki_path.read_text(encoding="utf8"))
nes_page = next(page for page in wiki["query"]["pages"].values()
                if page["title"] == "Nintendo Entertainment System")


def write(path, document):
    path.write_text(json.dumps(document, ensure_ascii=True, indent=2) + "\n", encoding="utf8")


def paragraph(identifier, index, heading, remove=()):
    old = entries[identifier]["body"][index]
    body = old
    for text in remove:
        assert text in body, (identifier, index, text)
        body = body.replace(text, "", 1)
    body = body.strip()
    assert body and len(body.split()) >= 20
    # Each retained segment has exact offsets in its original paragraph.
    segments = []
    cursor = 0
    retained = [old]
    for text in remove:
        retained = [segment for part in retained for segment in part.split(text)]
    for segment in retained:
        segment = segment.strip()
        if not segment:
            continue
        start = old.index(segment, cursor)
        segments.append([start, start + len(segment)])
        cursor = start + len(segment)
    assert " ".join(old[start:end] for start, end in segments) == body
    return dict(entry_id=identifier, paragraph_index=index, old_body=old,
                body=body, heading=heading, selected_character_spans=segments,
                removed_only=bool(remove), removed_sentences=list(remove))


def merge(canonical, retired, title, year, date, rows):
    return dict(canonical_id=canonical, retired_id=retired,
        old_body_sha256={identifier: helper["body_digest"](entries[identifier])
                        for identifier in (canonical, retired)},
        fields=dict(title=title, year=year, date=date, kind="console"), paragraphs=rows,
        excluded_image_urls=[], excluded_source_urls=[], replacement_images=[],
        image_associations={}, model_captions={})


psp = merge("psp", "workbook-05-13-playstation-portable-psp", "PlayStation Portable", 2004,
            dict(month=12, day=12, precision="day", region=""), [
    paragraph("workbook-05-13-playstation-portable-psp", 0, "Sony's first PlayStation handheld"),
    paragraph("workbook-05-13-playstation-portable-psp", 1, "The original PSP-1000 hardware"),
    paragraph("workbook-05-13-playstation-portable-psp", 2, "Games and films on UMD"),
    paragraph("psp", 1, "Wireless links, music and video"),
    paragraph("workbook-05-13-playstation-portable-psp", 3, "The widescreen display"),
    paragraph("psp", 2, "LocoRoco and Patapon")])
psp["fields"]["summary"] = entries["workbook-05-13-playstation-portable-psp"]["summary"]
psp["omitted_paragraphs"] = [dict(entry_id="psp", paragraph_index=0,
    reason="Old introductory framing and regional release list duplicate the clearer reviewed introduction and the sole release-date field. Full old record retained in provenance.")]
psp["image_associations"][entries["psp"]["images"][1]["url"]] = 1
psp["release_source"] = next(source for source in entries["psp"]["sources"]
    if "2004/psp-enters" in source["url"])

rows = [
    paragraph("famicom", 0, "The Family Computer"),
    paragraph("famicom", 1, "Donkey Kong, Donkey Kong Jr. and Popeye", [
        "Donkey Kong, Donkey Kong Jr. and Popeye accompany the Famicom's launch on July 15, 1983. "]),
    paragraph("famicom", 2, "The red-and-white console and its controllers"),
    paragraph("famicom", 3, "Making the controls more durable"),
    paragraph("nes", 0, "The NES front-loading design", [
        " They should not be mistaken for the red-and-white machine's earlier Japanese debut."]),
    paragraph("nes", 1, "Mario, Zelda and Metroid at home"),
    paragraph("nes", 2, "The system reaches Europe", [
        " The machine's history is therefore more than one release date or one claim to have transformed a market."]),
    paragraph("nes", 3, "Bringing a console back into American shops", [
        "October 18, 1985 is not yet a nationwide launch. ",
        " The NES does not conquer North America in a single day: October 18 marks the documented beginning of an expansion that will continue in 1986."]),
    paragraph("nes", 4, "A new case and a new name for the same platform"),
    paragraph("nes", 5, "R.O.B. and the Zapper"),
    paragraph("nes", 6, "The directional pad and two action buttons"),
    paragraph("nes", 7, "A library of different games", [
        " Reconstructing the 1985 launch through documentary evidence, however, requires caution: even the exact availability of Super Mario Bros. on the date indicated by Nintendo is difficult to prove with a complete commercial record.",
        " For this reason, the value of the catalog is best understood as part of the test-market phase, not as a rigidly certified list for one particular morning."]),
    paragraph("nes", 8, "Distribution, software and third-party publishers", [
        "The historical value of October 18 is measured above all by what happens afterward. ",
        " The New York test then appears as a starting point, not an isolated event."])]
family = merge("famicom", "nes", "Famicom / NES", 1983,
               dict(month=7, day=15, precision="day", region=""), rows)
family["fields"]["subtitle"] = "Nintendo's cartridge console and its later NES design"
family["fields"]["summary"] = "Nintendo's Family Computer brought arcade games to Japanese homes in 1983. Redesigned as the NES, the same platform introduced millions more players to Mario, Zelda and Metroid."
family["model_captions"] = {"models/famicom.glb": "Family Computer / Famicom", "models/nes.glb": "Nintendo Entertainment System / NES"}
family["release_source"] = dict(title=nes_page["title"],
    url="https://en.wikipedia.org/w/index.php?oldid=" + str(nes_page["revisions"][0]["revid"]),
    publisher="English Wikipedia contributors", attribution="Bibliographic identity and release-date reference; introduction confirms Family Computer, Japan, July15,1983.")
family["additional_sources"] = [family["release_source"]]
family["release_evidence"] = dict(source_file=wiki_path.relative_to(ROOT).as_posix(),
    source_file_sha256=hashlib.sha256(wiki_path.read_bytes()).hexdigest(),
    revision_id=nes_page["revisions"][0]["revid"], extract=nes_page["extract"].splitlines()[0])
bad_image = entries["nes"]["images"][2]["url"]
family["excluded_image_urls"] = [bad_image]
family["exclusion_reasons"] = {bad_image: "Batman: Arkham City screenshot from an unrelated multi-game date wrapper. Seen directly in the frozen contact sheet; not an NES image."}
family["excluded_image_urls"].append(entries["nes"]["images"][3]["url"])
family["exclusion_reasons"][entries["nes"]["images"][3]["url"]] = "The same NES console photograph already retained as its original transparent native master. Alternate background is not a second illustration."
family["excluded_source_urls"] = [source["url"] for source in entries["nes"]["sources"] if "shadow-of-the-colossus" in source["url"]]
family["image_associations"].update({
    entries["nes"]["images"][0]["url"]: 4,
    entries["nes"]["images"][4]["url"]: 8,
    entries["nes"]["images"][5]["url"]: 9,
    entries["nes"]["images"][6]["url"]: 10,
})
family["image_metadata_overrides"] = {}
for index, title, creator, license_name, source_title, license_url in [
    (4, "Nintendo Advanced Video System prototype and accessories", "Russell Bernice and Chris Donlan; composite derived from their photographs", "CC BY 2.0", "Nintendo_Advanced_Video_System_(retouched).jpg", "https://creativecommons.org/licenses/by/2.0/"),
    (5, "The gray NES Zapper light gun", "Evan-Amos", "Public domain", "Nintendo-Entertainment-System-NES-Zapper-Gray-R.jpg", "https://commons.wikimedia.org/wiki/Commons:Public_domain"),
    (6, "The NES directional-pad controller", "Evan-Amos", "Public domain", "Nintendo-Entertainment-System-NES-Controller-FL.jpg", "https://commons.wikimedia.org/wiki/Commons:Public_domain")]:
    family["image_metadata_overrides"][entries["nes"]["images"][index]["url"]] = dict(
        title=title, caption=title + ("; an unreleased prototype, not the retail NES." if index == 4 else "; photographed later."),
        creator=creator, credit=creator + " / " + license_name, license=license_name,
        license_url=license_url, source_page="https://commons.wikimedia.org/wiki/File:" + source_title)

# Prefer the authentic native master over the old archived derivative. No
# resizing, alpha compositing, generative edits or platform-label removal.
acquired = json.loads((FOLDER / "original-hardware-images.json").read_text(encoding="utf8"))
for title, old_index, association, caption in [
    ("File:NES-Console-Set.png", 1, 8, "The later front-loading NES design, photographed by Evan-Amos."),
    ("File:NES-Cartridge.jpg", 7, 11, "An NES Game Pak cartridge, shown without a game label.")]:
    item = next(row for row in acquired if row["title"] == title)
    family["excluded_image_urls"].append(entries["nes"]["images"][old_index]["url"])
    family["exclusion_reasons"][entries["nes"]["images"][old_index]["url"]] = "Replaced by its authentic Commons native master, with source metadata and unmodified pixels."
    family["replacement_images"].append(dict(url=item["url"], title=caption, caption=caption,
        width=item["width"], height=item["height"], creator="Evan-Amos", credit="Evan-Amos / Public domain",
        source_page="https://commons.wikimedia.org/wiki/" + title.replace(" ", "_"),
        license="Public domain", license_url="https://commons.wikimedia.org/wiki/Commons:Public_domain",
        story_paragraph=association, recovery_local_source=item["path"],
        verification=dict(source_sha256=item["sha256"], original_width=item["width"],
                          original_height=item["height"], no_upscaling=True)))

document = dict(schema_version=1, publication_status="research_candidate_requires_independent_review",
    source_catalog_sha256=hashlib.sha256((ROOT / "content/catalog.json").read_bytes()).hexdigest(),
    merges=[psp, family], policy="Only true duplicate introductory material and date-warning framing are removed; every unique substantive paragraph, feature, valid image and approved model remains. Old records are archived whole.")
candidate = FOLDER / "family-consolidation-candidate.json"
write(candidate, document)
projected = copy.deepcopy(catalog["entries"])
report = helper["project"](projected, document, hashlib.sha256(candidate.read_bytes()).hexdigest())
write(FOLDER / "family-consolidation-projected-records.json", dict(entries=[entry for entry in projected if entry["id"] in ("psp", "famicom")]))
write(FOLDER / "family-consolidation-projection-check.json", report)
selected = []
for plan in document["merges"]:
    selected += ["\n" + plan["fields"]["title"]]
    for index, row in enumerate(plan["paragraphs"]):
        selected += [str(index) + " / " + row["heading"], row["body"],
                     "REMOVED: " + repr(row["removed_sentences"])]
(FOLDER / "family-consolidation-readable.txt").write_text("\n\n".join(selected), encoding="utf8")
print(json.dumps(report, ensure_ascii=True, indent=2))
