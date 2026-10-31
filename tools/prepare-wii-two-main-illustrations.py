"""Freeze two original Wii illustrations; the four feature gaps remain open."""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE="build/research/wii-original-narrative-illustrations/"
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def load(p):return json.loads((ROOT/p).read_text(encoding="utf8"))
entry=next(e for e in load("content/catalog.json")["entries"] if e["id"]=="wii")
inventory={r["title"]:r for r in load(BASE+"four-original-photo-inventory.json")}
rows=[]
for title,paragraph,display,caption,creator,license,url in [
    ("File:Wiimote-in-Hands.jpg",0,"The Wii Remote and Nunchuk held for play",
     "An original Wii Remote and Nunchuk held in the hands, with the wrist strap attached. Evan-Amos photographed this hardware in November 2010; this is not presented as a photograph of the 2006 launch or of a specific motion-control experiment.",
     "Evan-Amos","Public domain","https://creativecommons.org/publicdomain/mark/1.0/"),
    ("File:Duo playing Wii Sports.jpg",1,"Two people playing Wii Sports, December 2006",
     "Two players holding Wii Remotes and Nunchuks for Wii Sports, photographed by david murphy on 10 December 2006. The original photograph records the movement of their hands; the players are not identified as Nintendo developers or participants in the cited interviews.",
     "david murphy","CC BY-SA 2.0","https://creativecommons.org/licenses/by-sa/2.0/")]:
    record=inventory[title]
    with Image.open(ROOT/record["file"]) as im:im.load();assert im.size==(record["width"],record["height"])
    rows.append(dict(url=record["url"],source_page="https://commons.wikimedia.org/wiki/"+title.replace(" ","_"),title=display,caption=caption,
        creator=creator,credit=creator+" / "+license,license=license,license_url=url,
        width=record["width"],height=record["height"],story_paragraph=paragraph,recovery_local_source=record["file"],
        verification=dict(source_sha256=sha(record["file"]),native_dimensions=[record["width"],record["height"]],
        visual_review="Full native original individually viewed; no enlargement, sharpening or reconstruction. Natural camera motion in the second photo is retained.")))
doc=dict(schema_version=1,status="pending_independent_review",scope="Two main Wii narrative illustrations only. All four feature-wii-social-design paragraphs remain without new admitted media; no completeness claim.",
    catalog_sha256=sha("content/catalog.json"),entries={"wii":rows},article_guards={"wii":dict(body_sha256=hashlib.sha256(json.dumps(entry["body"],ensure_ascii=False,separators=(",",":")).encode()).hexdigest(),original_body=entry["body"],original_headings=entry["story_headings"])},
    source_receipts=[dict(path=BASE+p,sha256=sha(BASE+p)) for p in ["straps-commons-query.json","playing-commons-query.json"]],
    held=[dict(source="Nintendo Iwata Asks originals",reason="Original header780x240 and developer portrait167x212 were retrieved, inspected as source metadata and not enlarged/admitted."),
          dict(source="CPSC2006 strap recall page",reason="Web reader and one normal directGET returned403; no page image was acquired or invented."),
          dict(source="Two other Commons photos",reason="At least one normal acquisition returned429 and two photographs were not acquired; individual error codes were not retained by the concurrent first attempt. No immediate retry, guessed URL or substitute pixel payload.")],
    unchanged_fields=["body","story_headings","hero","date","models","videos","soundtrack","editorial_features"])
path=ROOT/BASE/"two-original-wii-main-illustrations-candidate.json"
path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(path.relative_to(ROOT),sha(path.relative_to(ROOT)))
