"""Freeze a lossless factual merge; archive duplicated introductions and framing."""
from pathlib import Path
import copy
import hashlib
import json
import re
import runpy
from html.parser import HTMLParser
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "build/research/yoshi-island-consolidation"


class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside, self.skip, self.text, self.paragraphs = False, 0, [], []

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.inside, self.text = True, []
        if self.inside and tag == "sup":
            self.skip += 1

    def handle_endtag(self, tag):
        if tag == "sup" and self.skip:
            self.skip -= 1
        if tag == "p" and self.inside:
            self.inside = False
            text = re.sub(r"\s+", " ", "".join(self.text)).strip()
            if text:
                self.paragraphs.append(text)

    def handle_data(self, data):
        if self.inside and not self.skip:
            self.text.append(data)


def main():
    FOLDER.mkdir(parents=True, exist_ok=True)
    doc = json.loads((ROOT / "content/catalog.json").read_text(encoding="utf8"))
    canonical, retired = "wikipedia-83554", "workbook-08-05-super-mario-world-2-yoshi-s-island"
    by_id = {entry["id"]: entry for entry in doc["entries"]}
    target, old = by_id[canonical], by_id[retired]
    paragraphs = []
    def add(entry_id, index, heading, selected=None):
        original = by_id[entry_id]["body"][index]
        if selected is None:
            selected = original
        assert selected in original
        start = original.index(selected)
        paragraphs.append(dict(entry_id=entry_id, paragraph_index=index, original=original,
            original_sha256=hashlib.sha256(original.encode()).hexdigest(), body=selected,
            heading=heading, selected_character_spans=[[start, start + len(selected)]],
            full_paragraph=selected == original))
    add(canonical, 0, "Yoshi carries Baby Mario")
    add(canonical, 1, "Hand-drawn artwork and Super FX2")
    full_source = FOLDER / "gameplay-full-original-revision.json"
    full = json.loads(full_source.read_text(encoding="utf8"))
    assert full["parse"]["revid"] == target["attribution"]["revision_id"] == 1380113586
    parser = Paragraphs()
    parser.feed(full["parse"]["text"])
    (FOLDER / "full-revision-paragraphs.json").write_text(json.dumps(parser.paragraphs,
        ensure_ascii=True, indent=2) + "\n", encoding="utf8")
    for index, heading in ((5, "Exploring worlds and finding collectibles"),
                           (6, "Aiming eggs and transforming Yoshi"),
                           (7, "Recovering Baby Mario before time runs out")):
        text = parser.paragraphs[index]
        paragraphs.append(dict(entry_id=canonical, paragraph_index=None, body=text,
            heading=heading, full_paragraph=True,
            wikipedia_source=dict(page_id=83554, revision_id=1380113586,
                file=full_source.relative_to(ROOT).as_posix(),
                file_sha256=hashlib.sha256(full_source.read_bytes()).hexdigest(),
                locator="Non-empty HTML p element index after reference superscripts and layout whitespace removal",
                paragraph_index=index, body_sha256=hashlib.sha256(text.encode()).hexdigest())))
    add(canonical, 2, "Release and reception")
    add(canonical, 3, "Later editions and rereleases")
    manifest = json.loads((ROOT / "assets/images/manifest.json").read_text(encoding="utf8"))
    originals = []
    for e in (target, old):
        for image in e["images"]:
            path = ROOT / image.get("recovery_local_source", manifest["images"][image["url"]])
            originals.append(dict(url=image["url"], file=path.relative_to(ROOT).as_posix(),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    digest = lambda body: hashlib.sha256(json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    candidate = dict(schema_version=1, publication_status="independent_review_pending", canonical_id=canonical,
        retired_id=retired, title="Super Mario World 2: Yoshi's Island", paragraphs=paragraphs,
        old_body_sha256={identifier: digest(by_id[identifier]["body"]) for identifier in (canonical, retired)},
        paragraph_maps={canonical: {"0": 0, "1": 1, "2": 5, "3": 6}, retired: {"0": 0, "1": 2, "2": 3, "3": 4}},
        image_associations={target["images"][1]["url"]: 1, target["images"][2]["url"]: 3},
        excluded_duplicate_cover_urls=[old["images"][old.get("preferred_image", 0)]["url"]],
        original_images=originals,
        wikipedia_source_receipt=dict(file=full_source.relative_to(ROOT).as_posix(),
            sha256=hashlib.sha256(full_source.read_bytes()).hexdigest(), revision_id=1380113586),
        removed_redundant_material=dict(duplicate_intro=dict(body=old["body"][0],
            reason="Release date remains in the field; art, eggs, flutter jumps and Baby Mario are retained in the clear overview/development/design paragraphs."),
            abstract_editorial_replaced=[dict(paragraph_index=i, body=old["body"][i],
                reason="Replace abstract grammar/rhythm/framing with complete concrete gameplay paragraphs from the same frozen Wikipedia revision.") for i in (1,2,3)],
            duplicate_cover="Two scans depict the same original North American front packaging; keep the larger native scan as the one cover, archive the other."),
        preservation_scope="All four existing full Wikipedia paragraphs plus three full gameplay paragraphs from the same original revision. Concrete mechanics include exploration, collectibles, eggs, transformations and recovering Baby Mario; abstract editorial archived. All unique photographs/backs, both videos and all real music preserved. Sole date remains 5 August 1995. No GBA port or remake substituted.")
    path = FOLDER / "candidate.json"
    path.write_text(json.dumps(candidate, ensure_ascii=True, indent=2) + "\n", encoding="utf8")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    projected = copy.deepcopy(doc["entries"])
    result = runpy.run_path(str(ROOT / "content/expansion/yoshi_island_release_consolidation.py"))["project"](projected, candidate, sha)
    entry = next(e for e in projected if e["id"] == canonical)
    (FOLDER / "projected-entry.json").write_text(json.dumps(entry, ensure_ascii=True, indent=2) + "\n", encoding="utf8")
    (FOLDER / "projection-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    (FOLDER / "projected-story.txt").write_text("\n\n".join(f'{i}. {h}\n{b}' for i, (h,b) in enumerate(zip(entry["story_headings"],entry["body"]))), encoding="utf8")
    images = [im for im in entry["images"] if im.get("kind") != "video-poster"]
    canvas = Image.new("RGB", (1800, 520), "#171c25")
    draw = ImageDraw.Draw(canvas)
    for i, image in enumerate(images):
        im = Image.open(ROOT / image.get("recovery_local_source", manifest["images"][image["url"]])).convert("RGB")
        im.thumbnail((580, 450))
        canvas.paste(im, (600*i+(600-im.width)//2, 35))
        draw.text((600*i+12,10), f'image{i}: paragraph {image.get("story_paragraph", -1)}', fill="white")
    canvas.save(FOLDER / "projected-images-contact.jpg", quality=92)
    print(json.dumps(dict(candidate=path.relative_to(ROOT).as_posix(), sha256=sha, projection=result)))


if __name__ == "__main__":
    main()
