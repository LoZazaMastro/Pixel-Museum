"""Prepare six distinct publisher/source artifacts; no catalogue admission."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parents[1]
BASE="build/research/steam-deck-original-narrative-illustrations/"
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def load(path):return json.loads((ROOT/path).read_text(encoding="utf8"))
def body_sha(body):return hashlib.sha256(json.dumps(body,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
entry=next(e for e in load("content/catalog.json")["entries"] if e["id"]=="steam-deck")
feature=next(f for f in entry["editorial_features"] if f["id"]=="feature-portable-pc-return")
inventory={Path(i["file"]).name:i for i in load(BASE+"publisher-acquisition-inventory.json")}
press="https://www.steamdeck.com/en/press"
verified="https://www.steamdeck.com/en/verified"
def image(name,title,caption,paragraph,source_page):
    data=inventory[name]
    return dict(url=data["url"],source_page=source_page,title=title,caption=caption,
        creator="Valve; individual photographer or rendering artist not identified",
        credit="Valve / official Steam Deck publication; game artwork belongs to its respective owners",
        license="Copyright Valve and respective game rights holders; original publisher publicity imagery, no open image licence asserted.",
        license_url="",width=data["width"],height=data["height"],story_paragraph=paragraph,
        recovery_local_source=data["file"],verification=dict(source_sha256=data["sha256"],native_dimensions=[data["width"],data["height"]],
        visual_review="Original individually viewed in full; no enlargement or image alterations."))
main=[image("lcd-hollow-knight-original.jpg","Playing a PC game on the original Steam Deck",
    "Valve's original LCD-model press photograph shows Hollow Knight being played on the handheld, with its sticks, trackpads and buttons visible. Game imagery: Team Cherry. This is a manufacturer publicity photograph, not a performance test.",0,press),
    image("library-original.jpg","Compatibility categories in the Steam Deck library",
    "Valve's published library example displays a compatibility badge and the category filters beneath the games. The pictured interface and ratings are a historical website example, rather than a new assessment of those games.",1,verified)]
prototypes=image("prototype-original.jpg","Exploring the shape of Steam Deck",
    "Valve's prototype archive brings together physical mock-ups, control arrangements and development hardware. These are design iterations published by the manufacturer, rather than separately dated retail models.",0,press)
controller_info=next(p["imageinfo"][0] for p in load(BASE+"controller-original-commons-query.json")["query"]["pages"].values() if p["title"]=="File:Steam controller, front. (22623957899).jpg")
controller=dict(url=controller_info["url"],source_page="https://commons.wikimedia.org/wiki/File:Steam_controller,_front._(22623957899).jpg",
    title="The earlier Steam Controller",caption="The 2015 Steam Controller, photographed by Yixiao Wen on 11 November 2015. Its two trackpads illustrate the earlier control work that Valve's 2022 booklet identifies as a foundation for Steam Input and Steam Deck.",
    creator="Yixiao Wen",credit="Yixiao Wen / CC BY-SA 2.0",license="CC BY-SA 2.0",license_url="https://creativecommons.org/licenses/by-sa/2.0/",
    width=6000,height=3376,story_paragraph=1,recovery_local_source=BASE+"steam-controller-original-front.jpg",
    verification=dict(source_sha256=sha(BASE+"steam-controller-original-front.jpg"),native_dimensions=[6000,3376],visual_review="Full original viewed, original2015 controller; no enlargement."))
controls=image("lcd-controls-render.jpg","Sticks and trackpads on the original LCD Steam Deck",
    "Valve's original LCD-model rendering places the two square trackpads beneath the sticks, beside the conventional buttons. It illustrates the physical input choices discussed in the chapter; no motion-sensor operation can be inferred from a still image.",2,press)
detail=image("compatibility-detail-original.jpg","Reading the compatibility review",
    "Valve's published Elden Ring example lists controller support, icons, text legibility and graphics settings in the compatibility panel. It shows how the review is communicated to players; its historical rating is not presented as a fresh test or a guarantee for every game.",3,verified)
feature_images=[prototypes,controller,controls,detail]
all_images=main+feature_images
rgb=[]
for item in all_images:
    with Image.open(ROOT/item["recovery_local_source"]) as im:
        im.load();assert im.size==(item["width"],item["height"])
        rgb.append(hashlib.sha256(ImageOps.exif_transpose(im).convert("RGB").tobytes()).hexdigest())
assert len(set(rgb))==6
doc=dict(schema_version=1,status="pending_independent_review",scope="Two main and four feature narrative illustrations for the original Steam Deck. All text, hero, video, model, dates and music remain unchanged.",
    catalog_sha256=sha("content/catalog.json"),entries={"steam-deck":main},
    article_guards={"steam-deck":dict(body_sha256=body_sha(entry["body"]),original_body=entry["body"],original_headings=entry["story_headings"])},
    feature_entries=[dict(entry_id="steam-deck",feature_id=feature["id"],feature_body_sha256=body_sha(feature["body"]),feature_body=feature["body"],images=feature_images)],
    source_receipts=[dict(path=BASE+p,sha256=sha(BASE+p)) for p in ["press.html","verified.html","controller-original-commons-query.json"]]+[dict(path="build/research/editorial12/deckbook.pdf",sha256=sha("build/research/editorial12/deckbook.pdf"))],
    source_limits=["Press page explicitly separates LCD from OLED and each selected product photograph/render is listed under LCD. No OLED hardware substituted for the original2022 story.",
        "1280x800 native compatibility examples retained at source resolution. They illustrate the publisher's historical UI, not current ratings or app performance.",
        "Booklet page14 includes two684px pictures: not enlarged or selected. Its larger ValveIndex photograph is not selected because that subject is absent from the corresponding current paragraph.",
        "All six selected images individually viewed; source payloads and decoded RGB differ. Cover photograph is not reused."])
path=ROOT/BASE/"six-original-steam-deck-narrative-images-candidate.json"
path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(dict(candidate=path.relative_to(ROOT).as_posix(),sha256=sha(path.relative_to(ROOT)),images=6),indent=2))
