"""Build sourced Sony hardware additions without changing the runtime catalogue."""
from __future__ import annotations
import json
from pathlib import Path
import runpy
import urllib.request

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "wikipedia-cache"
HISTORY = "https://www.playstation.com/en-us/playstation-history/"
PRESS = "https://sonyinteractive.com/en/press-releases/"


def source(title, url, publisher="Sony Interactive Entertainment"):
    return {"title": title, "url": url, "publisher": publisher}


STORIES = [
    {
        "id": "playstation-3", "title": "PlayStation 3", "year": 2006, "era_id": "connected",
        "date": {"month": 11, "day": 11, "precision": "day", "region": "Japan: original launch"},
        "release_dates": [{"year": 2006, "month": 11, "day": 11, "region": "Japan"}, {"year": 2006, "month": 11, "day": 17, "region": "North America"}, {"year": 2007, "month": 3, "day": 23, "region": "Europe"}],
        "subtitle": "The console becomes a connected place",
        "summary": "Blu-ray discs, a hard drive and PlayStation Network brought games, films and an expanding online world into one machine.",
        "body": [
            "PlayStation 3 reached Japan on 11 November 2006 and North America six days later. Europe followed on 23 March 2007. There was no single worldwide launch day: players entered this generation at different times, and the software available around the machine changed as the rollout continued.",
            "Sony's ambition extended beyond a faster games console. A Blu-ray drive offered another way to watch high-definition films, while a hard drive and PlayStation Network supported downloadable games and online services. The XrossMediaBar organised this growing collection of activities into rows of icons. The machine could be a disc player, a meeting point and a game library, sometimes in the same evening.",
            "That wider role did not give the generation just one creative direction. Resistance explored a large-scale shooter, Uncharted built an adventure around characters and spectacle, and LittleBigPlanet invited players to make and share levels. The large, curved original console displayed here belongs to the beginning of that story. Smaller redesigns arrived in 2009 and 2012."
        ],
        "tags": ["Japan", "hardware", "Blu-ray", "online communities"], "related_ids": ["playstation-2", "journey"],
        "image_file": "PS3-Fat-Console-Set.jpg", "image_title": "Original PlayStation 3 with Sixaxis controller", "image_creator": "Evan-Amos",
        "sources": [source("PlayStation 3 - regional launches and hardware history", HISTORY + "2007-ps3-ps-vita/"), source("Sony Annual Report 2007 - Game business, page34", "https://www.sony.com/en/SonyInfo/IR/library/ar/SonyAR07-E.pdf")],
        "factual_note": "The chronology date is the Japanese launch, not a worldwide date. The photograph shows an original60GB model; PS2 compatibility and card-reader features varied across later hardware revisions.",
        "requested_model_uid": "d3eb52c6cf144601a52c99f9be78dfec", "requested_model_url": "https://sketchfab.com/3d-models/playstation-3-d3eb52c6cf144601a52c99f9be78dfec", "ready_for_assembly_when_model_attached": True,
    },
    {
        "id": "playstation-4", "title": "PlayStation 4", "year": 2013, "era_id": "everywhere",
        "date": {"month": 11, "day": 15, "precision": "day", "region": "North America: original launch"},
        "release_dates": [{"year": 2013, "month": 11, "day": 15, "region": "North America"}, {"year": 2013, "month": 11, "day": 29, "region": "Europe"}, {"year": 2014, "month": 2, "day": 22, "region": "Japan"}],
        "subtitle": "A moment worth sharing",
        "summary": "A new button on the controller made recording and sharing part of the console's everyday vocabulary.",
        "body": [
            "The DualShock4 carried a small but revealing change: a Share button. PlayStation4 made capturing a surprising moment and showing it to someone else part of the console itself. Live streaming and, later, Share Play extended that idea. Playing a game and being an audience for a game were becoming closely connected experiences.",
            "This was also the first PlayStation home console to reach North America before Japan. It launched there on15November2013, followed by Europe on29November. The Japanese release came on22February2014. Those regional dates are part of its history, rather than interchangeable labels for one global event.",
            "The original machine's sloping black case gave this increasingly social platform a compact physical form. Its library could still offer solitary journeys: Bloodborne, Horizon Zero Dawn and God of War sat alongside experiences built around sharing a world with others. The console's cultural footprint includes both the games people played and the clips, broadcasts and conversations that travelled beyond them."
        ],
        "tags": ["hardware", "sharing", "streaming", "online communities"], "related_ids": ["playstation-3", "journey"],
        "image_file": "PS4-Console-wDS4.jpg", "image_title": "Original PlayStation 4 with DualShock4 controller", "image_creator": "Evan-Amos",
        "sources": [source("PlayStation 4 - regional releases, Share button and games", HISTORY + "2013-ps4-ps-vr/")],
        "factual_note": "The chronology date is the North American launch. The object is the original2013 console, not the later Slim or Pro.",
        "requested_model_uid": "d4d72667ee8244a194b2416ff6de84b7", "requested_model_url": "https://sketchfab.com/3d-models/playstation-4-d4d72667ee8244a194b2416ff6de84b7", "ready_for_assembly_when_model_attached": True,
    },
    {
        "id": "playstation-5", "title": "PlayStation 5", "year": 2020, "era_id": "living-history",
        "date": {"month": 11, "day": 12, "precision": "day", "region": "Initial markets including Japan and North America"},
        "release_dates": [{"year": 2020, "month": 11, "day": 12, "region": "United States, Canada, Mexico, Australia, New Zealand, Japan and South Korea"}, {"year": 2020, "month": 11, "day": 19, "region": "Europe and further announced rollout markets; mainland China followed separately"}],
        "subtitle": "Changing the pace and feel of play",
        "summary": "Fast storage and a new controller shifted attention towards the time spent waiting and the sensations carried through the hands.",
        "body": [
            "A new console generation can change more than the picture. For PlayStation5, Sony emphasised fast solid-state storage,3D audio and the DualSense controller alongside its graphics hardware. The promise concerned the rhythm and feel of play: shorter loading waits, more detailed feedback and a stronger sense of being inside a space.",
            "Two launch versions made the changing place of physical media visible. One included an Ultra HD Blu-ray drive; the Digital Edition omitted it. Both used the same core processor and storage technology. The choice concerned how a library would be acquired and kept, rather than a separate class of game.",
            "The launch was staged. Seven markets, including Japan and the United States, received PS5 on12November2020. Europe and further regions followed on19November. The tall white-and-black original body and DualSense became the recognisable objects of this transition. Here they sit at a still-open end of the museum's timeline: hardware whose history is continuing to be made."
        ],
        "tags": ["hardware", "solid-state storage", "controllers", "digital libraries"], "related_ids": ["playstation-4", "preserving-play"],
        "image_file": "Black and white Playstation 5 base edition with controller.png", "image_title": "Original disc-drive PlayStation5 and DualSense", "image_creator": "Howardcorn33; artistic direction by Lemonix",
        "sources": [source("PS5 - launch markets, two editions and specifications, September2020", PRESS + "2020/playstation-5-launches-this-november-at-399-for-ps5-digital-edition-and-499-for-ps5-with-ultra-hd-blu-ray-disc-drive/"), source("PlayStation5 - hardware and DualSense history", HISTORY + "2020-ps5-ps-vr2/")],
        "factual_note": "The12November2020 date applies to seven initial markets, not every country. The photograph shows the original disc-drive model. Later Slim and Pro designs are different objects.",
        "requested_model_uid": "54810f0b23a441ca93f44a8b06ec937b", "requested_model_url": "https://sketchfab.com/3d-models/playstation-5-54810f0b23a441ca93f44a8b06ec937b", "ready_for_assembly_when_model_attached": True,
    },
    {
        "id": "psp", "title": "PlayStation Portable", "year": 2004, "era_id": "connected",
        "date": {"month": 12, "day": 12, "precision": "day", "region": "Japan: original launch"},
        "release_dates": [{"year": 2004, "month": 12, "day": 12, "region": "Japan"}, {"year": 2005, "month": 3, "day": 24, "region": "North America"}, {"year": 2005, "month": 9, "day": 1, "region": "Europe/PAL"}],
        "subtitle": "The screen leaves the living room",
        "summary": "Sony's first PlayStation handheld combined widescreen games, small optical discs and portable media playback.",
        "body": [
            "PlayStation Portable asked what a PlayStation experience could become when its screen travelled with the player. The original PSP-1000 launched in Japan on12December2004. North America followed on24March2005 and Europe on1September. It was a new branch of the platform, rather than a home console made smaller.",
            "Its UMD format put games and films on small enclosed optical discs. Wireless networking offered local and online connections, while music and video playback gave the hardware uses beyond a single game. The broad screen, speakers and controls presented a compact entertainment device at a time when those jobs had not yet converged around the modern smartphone.",
            "The machine's identity also came from games that suited its particular setting. LocoRoco and Patapon found different ways to organise movement, rhythm and attention on a portable screen. The PSP could carry familiar PlayStation worlds, but it also made room for experiences shaped around a different object in the player's hands."
        ],
        "tags": ["Japan", "hardware", "handhelds", "UMD"], "related_ids": ["playstation-2", "game-boy"],
        "image_file": "PSP-1000.png", "image_title": "Original PSP-1000", "image_creator": "Evan-Amos; derivative image by Alphathon",
        "sources": [source("PSP - Japanese launch announcement,27October2004", PRESS + "2004/psp-enters-the-market-on-december-12-2004-at-19800-yen-in-japan/"), source("PSP - regional dates in October2005 shipment statement", PRESS + "2005/psp-playstationportable-reaches-cumulative-worldwide-shipment-of-10-million-units/"), source("PSP - media format and games retrospective", HISTORY + "2000-ps2-psp/")],
        "factual_note": "The contemporary2004 announcement and2005 shipment statement explicitly give12December2004 for Japan. The current retrospective displays11December; this entry follows the contemporary records.",
        "requested_model_uid": "dca89d10ec304d0cab76837750df7761", "requested_model_url": "https://sketchfab.com/models/dca89d10ec304d0cab76837750df7761",
        "model_selection_note": "User selected this exact classic PSP reconstruction. The Japanese chronology describes the PSP-1000 launch; the artist asset's exact PSP-1000 versus later classic-body subrevision is not authenticated. It is not PSP Go.",
        "ready_for_assembly_when_model_attached": True,
    },
    {
        "id": "playstation-vita", "title": "PlayStation Vita", "year": 2011, "era_id": "everywhere",
        "date": {"month": 12, "day": 17, "precision": "day", "region": "Japan: original launch"},
        "release_dates": [{"year": 2011, "month": 12, "day": 17, "region": "Japan"}, {"year": 2012, "month": 2, "day": 22, "region": "North American and European general launch; some advance bundles earlier"}],
        "subtitle": "A handheld with more ways in",
        "summary": "Two analogue sticks, an OLED screen and touch surfaces on both sides invited different answers to what a portable game could be.",
        "body": [
            "PlayStation Vita arrived in Japan on17December2011. Its North American and European general release followed on22February2012. Sony offered both Wi-Fi and3G/Wi-Fi versions, treating portable play as something that could remain connected beyond the home.",
            "The original machine put two analogue sticks beside a five-inch OLED touchscreen. Behind it was another touch surface; cameras and motion sensors added further possibilities. These were not simply extra specifications. They gave developers several ways to involve the player's hands, position and surroundings, while retaining familiar physical buttons.",
            "That mix became especially tangible in Tearaway, whose papercraft world responded to the handheld's distinctive inputs. Other games used the screen for larger familiar adventures or smaller independent experiences. The Vita is worth examining as a designed object: a device that placed conventional controls and unusual surfaces together, then left developers to decide which combinations mattered."
        ],
        "tags": ["Japan", "hardware", "handhelds", "touch", "OLED"], "related_ids": ["psp", "playstation-3", "journey"],
        "image_file": "PlayStation-Vita-1101-FL.jpg", "image_title": "Original OLED PlayStation Vita PCH-1101", "image_creator": "Evan-Amos",
        "sources": [source("PlayStation Vita - Japanese launch and original specifications", PRESS + "2011/playstationvita-available-in-japan-on-december-17-2011/"), source("PlayStation Vita - February2012 international launch statement", PRESS + "2012/playstationvita-sales-reach-over-12-million-units-worldwide-boosted-by-launch-in-north-and-latin-america-europe-and-pal-territories/"), source("PlayStation Vita - games and input history", HISTORY + "2007-ps3-ps-vita/")],
        "factual_note": "The2011 date is the Japanese launch. February22,2012 is the general North American/European launch. The photograph shows an original OLED PCH-1101, not the later LCD revision.",
        "ready_for_assembly_when_model_attached": False,
    },
    {
        "id": "wii-u", "title": "Wii U", "year": 2012, "era_id": "everywhere",
        "date": {"month": 11, "day": 18, "precision": "day", "region": "North America: original launch"},
        "release_dates": [{"year": 2012, "month": 11, "day": 18, "region": "North America"}, {"year": 2012, "month": 11, "day": 30, "region": "Europe"}, {"year": 2012, "month": 12, "day": 8, "region": "Japan"}],
        "subtitle": "Two screens, different points of view",
        "summary": "A screen inside the controller gave the player holding it information that the rest of the room could not see.",
        "body": [
            "Wii U's most conspicuous object was its GamePad: a controller built around a touchscreen. The idea introduced a practical problem as well as a new canvas. The console had to send pictures and sound wirelessly while responding quickly enough for a button press to feel immediate. The GamePad displayed images produced by the console; it was not a separate handheld running the same game on its own.",
            "That second view could change the relationships between players. In Nintendo Land, the person holding the GamePad could have different information or a different role from people watching the television. Designers were not simply duplicating the picture on a smaller screen. They were deciding what each player should be allowed to know, then using that difference for cooperation or competition.",
            "Nintendo also reworked the controller's shape and grips as it balanced comfort, weight and the appearance of an object intended for the living room. Wii U launched in North America on18November2012, followed by Europe on30November and Japan on8December. Its history joins an unusual physical design to a clear creative question: what becomes possible when people share a game without sharing every view of it?"
        ],
        "tags": ["hardware", "Nintendo", "second screen", "asymmetric multiplayer"], "related_ids": ["wii", "switch"],
        "image_file": "Wii U Console and Gamepad.png", "image_title": "Wii U console and GamePad", "image_creator": "Takimata; edited by Tokyoship",
        "sources": [
            source("Wii U - regional launch dates, Nintendo briefing, page3", "https://www.nintendo.co.jp/ir/pdf/2019/190201_2e.pdf", "Nintendo"),
            source("Wii U - the wireless system challenge", "https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-Wii-U/Wii-U-Wii-U-GamePad/1-The-Wireless-System-Challenge/1-The-Wireless-System-Challenge-654065.html", "Nintendo / Iwata Asks"),
            source("Nintendo Land - development and asymmetric play", "https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-Nintendo-Land/Nintendo-Land/1-Development-Started-with-Wii-U/1-Development-Started-with-Wii-U-692042.html", "Nintendo / Iwata Asks"),
            source("Wii U GamePad - industrial design and grips", "https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-Wii-U/Wii-U-Wii-U-GamePad/4-We-ve-Got-To-Make-a-Controller-/4-We-ve-Got-To-Make-a-Controller--654175.html", "Nintendo / Iwata Asks"),
        ],
        "factual_note": "The chronology date is the North American launch. Europe followed on30November2012 and Japan on8December2012. The GamePad depends on the Wii U console for running games; it is not an independently functioning handheld console.",
        "requested_model_uid": "07bf11be88434b96a5ff5493eb71ab23", "requested_model_url": "https://sketchfab.com/3d-models/wii-u-07bf11be88434b96a5ff5493eb71ab23", "ready_for_assembly_when_model_attached": False,
    },
]


def spaced_text(text):
    # Source strings remain ordinary prose even where dates were entered compactly.
    import re
    text = re.sub(r"(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])", " ", text)
    text = re.sub(r"(?<=\d),(?=\d{4})", ", ", text)
    text = re.sub(r"\bPS ([1-5])\b", r"PS\1", text)
    text = text.replace("3 D", "3D").replace("3 G", "3G")
    for compact, expanded in (("SeriesX", "Series X"), ("SeriesS", "Series S"), ("OneS", "One S"), ("OneX", "One X")):
        text = text.replace(compact, expanded)
    text = re.sub(r",(?=\S)", ", ", text)
    return text


def main():
    pages = {}
    for name in ("hardware-sony-images.json", "hardware-sony-images-extra.json", "hardware-nintendo-images.json", "hardware-bulk-images.json", "hardware-bulk-images-extra.json", "hardware-portable-images.json", "hardware-more-images.json", "hardware-new-batch-images.json"):
        for page in json.loads((CACHE / name).read_text(encoding="utf-8"))["query"]["pages"]:
            if "imageinfo" in page:
                pages[page["title"].removeprefix("File:")] = page["imageinfo"][0]
    records = []
    stories = STORIES + runpy.run_path(str(ROOT / "hardware-bulk-stories.py"))["BULK_STORIES"] + runpy.run_path(str(ROOT / "hardware-portable-stories.py"))["PORTABLE_STORIES"] + runpy.run_path(str(ROOT / "hardware-more-stories.py"))["MORE_STORIES"] + runpy.run_path(str(ROOT / "hardware-new-batch-stories.py"))["NEW_BATCH_STORIES"]
    for raw in stories:
        item = dict(raw)
        image_file = item.pop("image_file")
        image_title = item.pop("image_title")
        artist = item.pop("image_creator")
        info = pages[image_file]
        meta = info["extmetadata"]
        license_name = meta["LicenseShortName"]["value"]
        item["images"] = [{"url": info.get("thumburl", info["url"]).split("?", 1)[0], "original_url": info["url"].split("?", 1)[0],
                           "source_page": info["descriptionurl"], "title": spaced_text(image_title), "creator": artist,
                           "license": license_name, "license_url": meta.get("LicenseUrl", {}).get("value", ""),
                           "credit": artist + " / Wikimedia Commons / " + license_name, "width": info["width"], "height": info["height"]}]
        uid = item.pop("requested_model_uid", None)
        page = item.pop("requested_model_url", None)
        selection_note = item.pop("model_selection_note", "User selected this exact model. Root attaches the verified official download; a viewer URL is not an importable model URL.")
        if uid:
            path = CACHE / ("sketchfab-" + uid + ".json")
            if not path.exists():
                request = urllib.request.Request("https://api.sketchfab.com/v3/models/" + uid, headers={"User-Agent": "PixelMuseumResearch/1.0"})
                path.write_bytes(urllib.request.urlopen(request, timeout=30).read())
            model = json.loads(path.read_text(encoding="utf-8"))
            licence = model.get("license") or {}
            item["requested_model"] = {"uid": uid, "source_page": page, "title": model["name"], "creator": model["user"]["displayName"],
                                       "license": licence.get("label", "No public licence specified"), "license_url": licence.get("url", ""),
                                       "downloadable": bool(model.get("isDownloadable")),
                                       "direct_asset_pending": True, "note": selection_note}
            if not model.get("isDownloadable"):
                item["ready_for_assembly_when_model_attached"] = False
                item["requested_model"]["note"] = "Selected source is view-only according to its public metadata. No downloadable asset obtained or approved; keep this entry pending a usable model."
        item.update({"kind": "console", "layout": "object", "videos": [], "models": [], "featured": False,
                     "editorial_mode": "curated_story", "editorial_credit": "Original exhibition text for Pixel Museum."})
        item["body"] = [spaced_text(p) for p in item["body"]]
        for key in ("factual_note", "summary", "subtitle"):
            item[key] = spaced_text(item[key])
        for s in item["sources"]:
            s["title"] = spaced_text(s["title"])
        records.append(item)
    result = {"schema_version": 1, "entries": records,
              "integration_note": "Every hardware entry remains conditional on root attaching an actual usable licensed 3D asset matching the represented revision. View-only model pages are research records, never importable models. Downloadable alternatives are proposals requiring user selection; none are silently substituted. DSi is the 2008 revision, not the original 2004 DS. Series X source is a 2019 pre-release artist mockup, not a scan of the 2020 retail object. No runtime catalogue was modified."}
    (ROOT / "hardware-additions.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for item in records:
        print(item["id"], sum(len(p.split()) for p in item["body"]), "words", item["date"], "image", item["images"][0]["license"])


if __name__ == "__main__":
    main()
