"""Compile verified reference links and explicit fidelity limits; no model edits."""
import html
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "wikipedia-cache"


def clean(value):
    return html.unescape(re.sub("<[^>]+>", "", value or "")).strip()


photos = {}
for filename in ("hardware-fidelity-images.json", "hardware-fidelity-images-extra.json"):
    for page in json.loads((CACHE / filename).read_text(encoding="utf-8"))["query"]["pages"]:
        if "imageinfo" not in page:
            continue
        info = page["imageinfo"][0]
        meta = info["extmetadata"]
        photos[page["title"].removeprefix("File:")] = {
            "title": page["title"].removeprefix("File:"),
            "url": info["url"].split("?", 1)[0],
            "source_page": info["descriptionurl"],
            "creator": clean(meta.get("Artist", {}).get("value")),
            "license": clean(meta.get("LicenseShortName", {}).get("value")),
            "license_url": clean(meta.get("LicenseUrl", {}).get("value")),
            "description": clean(meta.get("ImageDescription", {}).get("value")),
            "width": info["width"], "height": info["height"],
        }


def ref(title, url, publisher, purpose):
    return {"title": title, "url": url, "publisher": publisher, "purpose": purpose}


def images(*names):
    return [photos[name] for name in names]


entries = [
    {
        "id": "game-boy-advance", "priority": 1,
        "exact_variant": "Original AGB-001, opaque Indigo; AGB-JPN physical specimen AJ10005957 is the reference, not SP/Micro or a modern reshell.",
        "dimensions": {"width_mm": 144.5, "height_mm": 82, "thickness_mm": 24.5, "screen_width_mm": 61.2, "screen_height_mm": 40.8, "status": "Nintendo nominal exterior and active-screen dimensions"},
        "references": [
            ref("Game Boy Advance technical data", "https://www.nintendo.com/en-gb/Support/Legacy-system/Technical-data-619479.html", "Nintendo", "Nominal dimensions, 240x160 display, batteries and connectors"),
            ref("Actual Indigo AGB-JPN specimen AJ10005957", "https://gbhwdb.gekkio.fi/consoles/agb/AJ10005957.html", "Joonas Javanainen / Game Boy hardware database", "Original specimen provenance, assembly week6/2001, board and front/rear photographs"),
            ref("Original Japanese GBA hardware page", "https://www.nintendo.co.jp/n08/hardware/gba/index.html", "Nintendo", "Original reflective display and original horizontal-body product imagery"),
        ],
        "photos": images("Game Boy Advance front.jpg", "Game Boy Advance back.jpg"),
        "wordmarks": images("Game Boy Advance logo.svg", "Nintendo logo.svg"),
        "visually_verified_details": [
            "The shell is opaque, finely textured indigo plastic. Lighting/age shift the photographed colour; no calibrated factory colour value is established.",
            "The Nintendo oval above the lens is moulded into the same indigo plastic, not white printed text. Use the actual oval/vector geometry as a shallow relief, with reference-matched placement.",
            "The white GAME BOY ADVANCE wordmark sits on the lower charcoal lens. Its custom letter shapes are not reproduced by typing a generic italic font. Compare the vector with the real lens, including its spacing and proportions.",
            "A/B buttons and the cross-shaped directional control are light grey with recessed symbols. START/SELECT are small rounded rubber buttons below the directional control; their labels and POWER are moulded on the shell.",
            "Five slanted speaker openings sit below A/B. The power indicator is a small circular lens at upper right, not a large emissive button.",
            "The rear battery cover has a recessed GAME BOY mark. Above it is the contoured regulatory label with AGB-001, AGB-JPN and the actual specimen's serial. Regional labels differ: do not mix the Japanese front/back with an invented US serial label.",
            "The original off-state LCD is a reflective pale grey/green surface, with glass/lens reflections. It is not a black OLED. An illuminated IPS screen would represent a later modification.",
        ],
        "remaining_gaps": ["No orthographic side scan or measured radii supplied. Overall dimensions alone do not establish every curve, button height, screw position or surface roughness."],
    },
    {
        "id": "nintendo-dsi", "priority": 1,
        "exact_variant": "Original small Nintendo DSi TWL-001, matte black; not DS Lite and not DSi XL/LL.",
        "dimensions": {"closed_width_mm": 137.0, "closed_depth_mm": 74.9, "closed_thickness_mm": 18.9, "status": "Nintendo original DSi operations manual"},
        "references": [
            ref("DSi main unit diagram", "https://en-americas-support.nintendo.com/app/answers/detail/p/696/c/188/a_id/6796", "Nintendo", "Authoritative identity and placement of both cameras, buttons, slots and indicators"),
            ref("DSi operations manual", "https://assets.nintendo.eu/image/upload/v1635390257/NAL/Support/DSiOperationsManual.pdf", "Nintendo", "Exterior diagrams, specifications and dimensions; original small DSi only"),
        ],
        "photos": images("Nintendo-DSi-Bl-Open.jpg", "DS Inside Open Comparison.jpg", "DS - Top Side Comparison.jpg", "DS Bottom Side Comparison.jpg"),
        "wordmarks": images("Nintendo DSi logo.svg"),
        "visually_verified_details": [
            "A real black DSi photo shows the inner camera centred on the hinge with a small microphone opening alongside, two narrow speaker apertures, and a separate pale Power/Reset button at lower left.",
            "ABXY form the right-hand diamond: X top, A right, B bottom, Y left. START and SELECT are two small round buttons below them, vertically arranged and correctly labelled.",
            "The outer lid has a second camera and its indicator. The right side has an SD-card cover; the left has volume/brightness buttons. Match the official diagram before placing rear game-card, stylus, shoulder and power connectors.",
            "There is no Game Boy Advance cartridge slot. The DSi front edge must not inherit the broad GBA slot from DS Lite or original DS.",
            "Selected artist source934fdde060874d5c99b40cdf1dbb37f2 mixes revision cues in its authored thumbnail: absent inner camera and lower-left Power button, six-hole speakers, right-hinge indicator and a broad front slot. These are observed thumbnail defects, not a native geometry inspection. Repair the whole hardware identity rather than adding only a camera dot.",
        ],
        "remaining_gaps": ["DS comparison photographs include three revisions. Identify the DSi from the cameras/Power button/no-GBA-slot combination before using a view; do not trace a neighbouring DS Lite."],
    },
    {
        "id": "odyssey", "priority": 2,
        "exact_variant": "Original1972 Magnavox Odyssey, white-and-brown console with separate controllers; not Odyssey200, Odyssey2 or Hanimex7771.",
        "dimensions": {"museum_record_mm_sequence": [100, 370, 227], "controller_record_mm_sequence": [90, 160, 84], "status": "ACMI gives100x370x227mm without naming axes; SMG gives controller90x160x84mm separately. Do not substitute controller dimensions for the console or claim measured CAD tolerances."},
        "references": [
            ref("Magnavox Odyssey console, object100297 / GF000148", "https://www.acmi.net.au/works/100297--magnavox-odyssey-video-game-console/", "ACMI", "Physical museum object and recorded100x370x227mm measurements"),
            ref("Magnavox Odyssey Player Control Unit,2008-5014/3", "https://collection.sciencemuseumgroup.org.uk/objects/co8244669/magnavox-odyssey-player-control-unit", "Science Museum Group", "Separate controller dimensions and materials; catalogue data CC0, other text CC BY4.0"),
            ref("Original Magnavox Odyssey manual scan", "https://www.videogameconsolelibrary.com/images/Manuals/72_Magnavox_Odyssey-Manual.pdf", "Magnavox; scan hosted by Video Game Console Library", "Original control layout and manufacturer lettering; scan not openly licensed merely because accessible"),
        ],
        "photos": images("Magnavox-Odyssey-FL.jpg", "Magnavox-Odyssey-FR.jpg", "Magnavox-Odyssey-BL.jpg", "Magnavox-Odyssey-BR.jpg", "Magnavox-Odyssey-Bottom-FL.jpg"),
        "wordmarks": images("Magnavox Odyssey Logo.svg"),
        "variant_checks": ["White upper shell, brown lower case and inset front panel must follow the multi-angle object photos rather than a generic white box.", "Controller dial arrangement and cabling are part of this specific original system. Later integrated-knob Odyssey consoles are different designs.", "Check each physical label against the original manual/photo; do not combine modern product logos with 1972 placement."],
        "remaining_gaps": ["Photo series metadata verified; all photographs have not been individually visually inspected in this pass. The museum measurement sequence is not an engineering drawing."],
    },
    {
        "id": "nintendo-ds", "priority": 2,
        "exact_variant": "Original2004 NTR-001 Nintendo DS, broad angular body; not DS Lite/DSi/DSi XL.",
        "dimensions": {"closed_width_mm": 148.7, "closed_depth_mm": 84.7, "closed_thickness_mm": 28.9, "status": "Original Nintendo DS specification"},
        "references": [
            ref("Nintendo DS original specifications", "https://www.nintendo.co.jp/ds/series/ds/spec/index.html", "Nintendo", "NTR-era dimensions and original physical specification"),
            ref("Nintendo DS technical specification", "https://www.nintendo.com/fr-fr/Assistance/Nintendo-DS/Informations-produit/Specificites-techniques/Informations-produit-619794.html", "Nintendo", "Original dual slot and headphone/microphone/power connectors"),
        ],
        "photos": images("Nintendo-DS-Fat-Blue.jpg", "Nintendo DS (parte traseira).jpg", "Nintendo DS - Parte de abaixo.jpg", "Nintendo DS azul (pechada).jpg", "DS Inside Open Comparison.jpg"),
        "variant_checks": ["Original broad faceted clamshell and thick hinge are not the rounded thin DS Lite body.", "The original DS has DS and Game Boy Advance cartridge slots and no cameras. A repaired DSi asset cannot serve as this console merely by changing its timeline date.", "Use a consistent blue or silver specimen across all views; these reference photographs include colour variants. Port/control positions are useful across colours, surface colour is not."],
        "remaining_gaps": ["No engineering drawings for hinge angles or key height. Additional physical side measurements are needed before claiming dimensional reconstruction accuracy."],
    },
    {
        "id": "xbox-series-x", "priority": 2,
        "exact_variant": "Retail2020 black1TB Series X with optical drive; not2019 artist mockup,2024 white digital edition or Galaxy Black2TB.",
        "dimensions": {"width_mm": 151, "depth_mm": 151, "height_mm": 301, "status": "Xbox's prelaunch setup guidance lists5.94x5.94x11.85in, consistent with151x151x301mm nominal figures"},
        "references": [
            ref("Designing the next generation of consoles", "https://news.xbox.com/en-us/2020/09/23/designing-the-next-generation-of-consoles-xbox-series-x-and-xbox-series-s/", "Xbox industrial-design team", "Original black/white surface finish, green layer under venting, retail design photographs and rear details"),
            ref("Ten ways to get ready for Xbox Series X|S", "https://news.xbox.com/en-us/2020/11/06/ten-ways-to-get-ready-for-xbox-series-x-and-xbox-series-s/", "Xbox", "Launch-period exterior dimensions"),
        ],
        "photos": images("Xbox Series X 2.jpg", "Xbox series X (50648118708).jpg", "Xbox series X (50648958937).jpg", "Xbox series X (50648958962).jpg"),
        "variant_checks": ["The green seen through the top vent is a physical subsurface colour layer; it is not an emitted green light.", "The retail original includes the front optical-disc slit and eject control, front USB/pairing control, separate round base and rear labelled I/O.", "Xbox's designers describe a low-gloss etched plastic finish. Do not make the tower shiny metal or add speculative prototype ports.", "A current2019 mockup must remain identified as pre-release until actual retail geometry/materials and ports are corrected."],
        "remaining_gaps": ["Official press images retain publisher rights. Commons photos have their own explicit reusable licences. No claim of scan accuracy or per-hole measured vent geometry."],
    },
    {
        "id": "xbox-series-s", "priority": 2,
        "exact_variant": "Original2020 Robot White512GB Series S with black circular vent; not Carbon Black1TB, white1TB later revision or Xbox One S.",
        "dimensions": {"short_mm": 65, "depth_mm": 151, "long_mm": 275, "status": "Width/height axis labels depend on horizontal or vertical orientation; these are Xbox's nominal three exterior dimensions"},
        "references": [
            ref("Series S original/updated hardware specifications", "https://www.xbox.com/en-AU/consoles/xbox-series-s/", "Xbox", "65x151x275mm dimensions; distinguish storage/colour variants"),
            ref("Xbox industrial design account", "https://news.xbox.com/en-us/2020/09/23/designing-the-next-generation-of-consoles-xbox-series-x-and-xbox-series-s/", "Xbox", "Black circular exhaust set into low-gloss white shell; authored product views"),
        ],
        "photos": images("Xbox Series S with controller.jpg"),
        "variant_checks": ["Large black circular exhaust is a grille with physical depth, not a flat black disc sticker.", "No optical drive or eject button. Preserve the small front USB/pair button/power icon arrangement, rear I/O, side perforations and orientation feet.", "Match launch Robot White shell and black vent, not newer Carbon Black materials. Use official rotating/product views for sides and back before building."],
        "remaining_gaps": ["Only one reusable Commons viewpoint verified in this pass. The official source provides supplementary reference views but no blanket CC licence for its images."],
    },
    {
        "id": "playstation-vita", "priority": 2,
        "exact_variant": "Original OLED PCH-1000 family; chosen multi-angle physical specimen PCH-1004 EUR Wi-Fi, distinct from PCH-1101 US3G and PCH-2000 slim.",
        "dimensions": {"width_mm": 182, "height_mm": 83.5, "thickness_mm": 18.6, "status": "Sony original PCH-1000-series specification; excludes maximum protrusions"},
        "references": [
            ref("Sony original Japanese Vita launch specification,2011, table near end", "https://www.sony.com/ja/SonyInfo/IR/news/110914_01.pdf", "Sony Computer Entertainment", "Original182x83.5x18.6mm body,5inch OLED and front/rear cameras"),
            ref("Sony PCH-2000 redesign announcement", "https://sonyinteractive.com/jp/press-releases/2013/130909b/", "Sony Computer Entertainment", "Explicitly different slimmer2013 hardware; do not import slim details into the original"),
        ],
        "photos": images("Sony PlayStation Vita PCH-1004 (EUR) - front view.jpg", "Sony PlayStation Vita PCH-1004 (EUR) - rear view.jpg", "Sony PlayStation Vita PCH-1004 (EUR) - top view.jpg", "PlayStation-Vita-1101-FL.jpg"),
        "variant_checks": ["Original glossy black OLED front and curved body have two analogue sticks, PlayStation-shape face buttons, front camera, rear camera and separate rear capacitive touchpad.", "The rear is a touchpad, not a second display. Existing photo description calling it a rear touchscreen is inaccurate and must not become geometry.", "The PCH-1004 photo sequence is one consistent EUR Wi-Fi specimen. PCH-1101 adds3G identity; avoid mixing its labels/connectors with a fabricated Wi-Fi rear.", "Do not replace Sony/PS/Vita custom logos with typed approximate fonts or copy PCH-2000's different controls/charging port."],
        "remaining_gaps": ["Sony dimensions exclude maximum protrusions. Exact lens contours, glossy layers and button travel are not determined by those dimensions alone."],
    },
    {
        "id": "atari-jaguar", "priority": 3,
        "exact_variant": "Original1993 black Jaguar base console and standard three-fire-button controller; no Jaguar CD add-on or six-button Pro Controller.",
        "dimensions": {"width_in_reported": 9.5, "depth_in_reported": 10, "height_in_reported": 2.5, "status": "Provisional historical FAQ figures only; no manufacturer or museum measurement located in this bounded pass. Not accepted as primary engineering evidence."},
        "references": [
            ref("Jaguar contemporary developer documentation - controllers", "https://asterick.github.io/jag-docs/controllers/controllers.html", "Atari technical manual, modern cross-linked transcription", "Two front controller ports and controller electrical identity; primary manual excerpts explicitly labelled"),
            ref("Historical Jaguar FAQ, technical specification section", "https://static.atariage.com/Jaguar/faq/index.html?SystemID=JAGUAR", "Robert Jung, archived by AtariAge", "Provisional dimensions only; author explicitly independent of Atari"),
        ],
        "photos": images("Atari-Jaguar-Bare-HL.jpg", "Atari-Jaguar-Bare-LL.jpg", "Atari-Jaguar-Bare-LR.jpg", "Atari-Jaguar-Back.jpg", "Atari-Jaguar-Console-Set.png"),
        "wordmarks": images("Atari Jaguar logo.svg"),
        "variant_checks": ["Use the unstacked base console photo series; the CD add-on changes the silhouette substantially.", "Preserve the domed cartridge housing, central slot, red power control, two front controller sockets and actual rear connectors.", "The standard controller has a12-key number pad plus A/B/C, Pause and Option. Six-fire-button Pro Controller and custom rotary controllers are different objects.", "Red custom Jaguar lettering/Atari emblem is a logo, not ordinary font text. Verify against the actual photographed console before applying the vector."],
        "remaining_gaps": ["No primary exterior measurements verified. All selected photo licences verified, but this pass did not visually inspect every Jaguar angle. Do not present a reconstruction as a scan or assert manufacturing-level fidelity."],
    },
]

result = {
    "checked_date": "2026-10-20",
    "purpose": "Evidence for faithful model creation and repair, not a claim that existing models already match these references.",
    "constraints": [
        "A photo-based reconstruction can be carefully referenced but cannot honestly guarantee absolute or scan-level accuracy without measured geometry, calibrated materials and complete views.",
        "Reuse wordmark vector shapes when their metadata permits it, then match the particular physical placement, colour and embossed/printed construction. Public-domain copyright status does not remove brand identity.",
        "Do not use broad product imagery as evidence for an unshown revision. Keep a single declared specimen/colour/region throughout the model and label any reconstruction changes in its attribution.",
        "Photo references stay online. Cached reference photographs are research-only and are not newly authorised distribution assets merely because they were viewed.",
    ],
    "entries": entries,
}
(ROOT.parent / "hardware-fidelity-reference-pack.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Saved", len(entries), "hardware reference records,", sum(len(e.get("photos", [])) for e in entries), "verified photo links")
