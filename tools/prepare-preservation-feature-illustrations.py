"""Freeze selected primary artefacts for the three preservation features."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "build/research/preservation-illustrations"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    catalog = json.loads((ROOT / "content/catalog.json").read_text(encoding="utf8"))
    entry = next(e for e in catalog["entries"] if e["id"] == "preserving-play")
    features = {f["id"]: f for f in entry["editorial_features"]}
    acquired = {r["name"]: r for r in json.loads((FOLDER / "acquired-originals.json").read_text())}
    extraction = json.loads((FOLDER / "chm-logbook-native-extraction.json").read_text())
    extracted = next(r for r in extraction["images"] if r["page"] == 3)
    acquired["chm-logbook-page3"] = dict(name="chm-logbook-page3", path=extracted["path"],
        url=extraction["source_url"] + "#page=3", width=extracted["native_width"],
        height=extracted["native_height"], sha256=extracted["sha256"])
    records = []

    def add(feature, paragraph, name, title, caption, creator, license, source_page, relevance):
        original = acquired[name]
        path = ROOT / original["path"]
        with Image.open(path) as im:
            im.load()
            assert im.size == (original["width"], original["height"])
        assert sha(path) == original["sha256"]
        assert max(original["width"], original["height"]) >= 800
        image = dict(url=original["url"], source_page=source_page, title=title,
            caption=caption, creator=creator, credit=creator, license=license,
            width=original["width"], height=original["height"],
            recovery_local_source=original["path"], story_paragraph=paragraph,
            verification=dict(sha256=original["sha256"], no_upscale=True,
                native_original=True, visually_reviewed=True),
            historical_context=relevance)
        if name == "chm-logbook-page3":
            image["verification"].update(source_pdf_sha256=extraction["source_sha256"],
                native_embedded_image=True, pdf_one_based_page=3)
        records.append(dict(feature_id=feature, image=image))

    reserved = "Copyright retained by the original creators and rights holders; no open licence claimed."
    demo = "feature-demoscene-tools"
    add(demo, 0, "immersion-obelisk", "Immersion: a city emerges",
        "A frame published by Immersion's creators in their making-of account; generated scenery from the real-time Windows intro.",
        "Ctrl-Alt-Test / Immersion's original visual contributors", reserved,
        "https://www.ctrl-alt-test.fr/2018/a-dive-into-the-making-of-immersion/",
        "The exact work discussed in paragraph 0, not a generic city or a photograph of a different demo.")
    add(demo, 1, "immersion-concept", "The submerged-city concept",
        "Beno\u00eet Molenda's concept illustration for Immersion, reproduced in the creators' making-of account.",
        "Beno\u00eet Molenda / Immersion concept artwork", reserved,
        "https://www.ctrl-alt-test.fr/2018/a-dive-into-the-making-of-immersion/",
        "The submerged-city visual target described in paragraph 1. The code repository's MIT licence is not assigned to this artwork.")
    add(demo, 2, "assembly-2006", "Assembly's shared party hall",
        "Assembly 2006 in Helsinki, photographed by Susanna Viljanmaa. This is a later gathering, not the first Assembly in 1992.",
        "Susanna Viljanmaa", "CC BY 4.0, as stated by the hosting living-heritage inventory unless otherwise indicated; no exception is stated on this file page.",
        "https://wiki.aineetonkulttuuriperinto.fi/wiki/Tiedosto:Partyhall_02.hi.jpg",
        "A named Assembly gathering documents the audience and social setting discussed in paragraph 2.")
    add(demo, 3, "ix-2003", "A production kept in the community record",
        "ix by Moppi Productions (2003), a Windows PC demo, as documented in the Finnish demoscene's living-heritage submission.",
        "Moppi Productions / ix", "CC BY 4.0 publication declaration on the hosting inventory file page; underlying demo contributors retain their authorship.",
        "https://wiki.aineetonkulttuuriperinto.fi/wiki/Tiedosto:Ix-moppi.png",
        "An actual community-documented production illustrates transmission and documentation. It is not claimed to show floppy disks or Immersion.")
    study = "feature-commercial-availability-study"
    add(study, 0, "vghf-historical-games", "The study's commercial-availability result",
        "The Video Game History Foundation's published 2023 chart: 13.27% available commercially in the historical-game sample.",
        "Video Game History Foundation / Software Preservation Network", reserved,
        "https://gamehistory.org/87percent/",
        "The actual publisher's quantitative result graphic, accompanying the dated research described in paragraph 0; not a current market measurement.")
    add(study, 1, "vghf-ecosystems", "Three platform ecosystems",
        "The study explainer's ecosystem matrix compares activity and interest around Commodore 64, Game Boy and PlayStation 2.",
        "Video Game History Foundation / Software Preservation Network", reserved,
        "https://gamehistory.org/study-explainer/",
        "A genuine study-method/context illustration alongside paragraph 1. This matrix is not represented as the 13% result chart or as an illustration of Jinxter.")
    repair = "feature-repair-sustainability"
    add(repair, 0, "chm-initial_checklist_whiteboard", "The PDP-1 power-up checklist",
        "The Computer History Museum restoration team's actual power-up checklist, photographed in 2004.",
        "Computer History Museum / PDP-1 restoration collection; photographer not identified on the exhibit page", reserved,
        "https://www.computerhistory.org/pdp-1/restoration/",
        "The specific whiteboard and restoration project discussed in paragraph 0. Native 800 x 690 archival photograph; no 4K-source claim.")
    add(repair, 1, "chm-logbook-page3", "Recording replaced parts before power-up",
        "The restoration log's 18 May 2004 entry records capacitor, wiring, bearing and lamp replacements before the PDP-1's first restored power-on.",
        "Computer History Museum / PDP-1 restoration team operations log", reserved,
        "https://www.computerhistory.org/pdp-1/e41c66b6ba5a6de88efafe1e055af087/",
        "A genuine filled log page documents restoration changes, directly accompanying paragraph 1. It is not the blurred blank form from the exhibit thumbnail.")
    add(repair, 2, "beeb-18657", "Repairing a BBC Micro at Fix-A-Beeb",
        "A participant reconnects a BBC Micro motherboard at the 13 September 2015 Fix-A-Beeb day, photographed and posted by jbnbeeb.",
        "jbnbeeb / original event photograph", reserved,
        "https://stardot.org.uk/forums/viewtopic.php?start=60&t=10038#p120924",
        "A first-person photographic record of the exact event discussed in paragraph 2. The forum is a host, not asserted to own the photograph.")
    add(repair, 3, "beeb-18654", "Working inside another BBC Micro",
        "Component work during the same 2015 Fix-A-Beeb event, in a separate photograph posted by jbnbeeb.",
        "jbnbeeb / original event photograph", reserved,
        "https://stardot.org.uk/forums/viewtopic.php?start=60&t=10038#p120924",
        "Another machine and repair operation from the exact event. The photograph is not claimed to identify which optional ROM or audio modification was removed.")

    files = ["acquired-originals.json", "chm-logbook-native-extraction.json", "chm-restoration-logbook.pdf",
        "chm-restoration.html", "chm-logbook.html", "vghf-study.html", "vghf-87percent.html",
        "beeb-event-primary.html", "finnish-community-primary.html", "assembly-file.html", "ix-file.html"]
    sources = [dict(file=(FOLDER / name).relative_to(ROOT).as_posix(), sha256=sha(FOLDER / name)) for name in files]
    making = ROOT / "build/research/publishing/features-context/batch06/immersion-making.html"
    sources.append(dict(file=making.relative_to(ROOT).as_posix(), sha256=sha(making)))
    document = dict(schema_version=1, publication_status="independent_review_pending",
        entry_id=entry["id"], records=records,
        reviewed_bodies={key: dict(body_sha256=hashlib.sha256(json.dumps(features[key]["body"], ensure_ascii=False,
            separators=(",", ":")).encode()).hexdigest(), paragraphs=len(features[key]["body"]))
            for key in (demo, study, repair)}, source_receipts=sources,
        remaining_holds=[dict(feature_id=study, story_paragraphs=[2, 3],
            reason="Need a specific authentic PlayStation Store/PS3/Vita/PSP commerce artefact. The publisher article's generic PlayStation logo is held rather than substituted.")],
        rejected_research=[dict(path="ps-store-2021.jpg", reason="Generic PlayStation logo; does not illustrate the dated store decision."),
            dict(path="chm-logbook_whitebinder.jpg", reason="Blurred blank cover/form; replaced by the actual native filled log page from the original PDF.")],
        scope="Ten unique primary illustrations for twelve existing feature paragraphs. No body, dates, music, main cover or other features changed. Two commercial-store paragraphs remain explicitly unresolved.")
    out = FOLDER / "ten-primary-feature-illustrations-candidate.json"
    out.write_text(json.dumps(document, ensure_ascii=True, indent=2) + "\n", encoding="utf8")
    canvas = Image.new("RGB", (1560, 5 * 370), "#171c25")
    draw = ImageDraw.Draw(canvas)
    for i, row in enumerate(records):
        x, y = (i % 2) * 780, (i // 2) * 370
        im = Image.open(ROOT / row["image"]["recovery_local_source"]).convert("RGB")
        im.thumbnail((750, 310))
        canvas.paste(im, (x + (780-im.width)//2, y+30))
        draw.text((x+12,y+5), f'{row["feature_id"]} p{row["image"]["story_paragraph"]}', fill="white")
        draw.text((x+12,y+345), row["image"]["title"].encode("ascii", "replace").decode(), fill="white")
    canvas.save(FOLDER / "ten-selected-primary-contact.jpg", quality=92)
    print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(), sha256=sha(out), illustrations=len(records),
                         remaining_feature_paragraphs=2)))


if __name__ == "__main__":
    main()
