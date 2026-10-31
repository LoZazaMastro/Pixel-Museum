"""Select three genuine original-edition publisher images without altering prose."""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "build/research/stanley-2013-original-illustrations"


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode("utf8")).hexdigest()


def main():
    catalog = json.loads((ROOT / "content/catalog.json").read_text(encoding="utf8"))
    entry = next(item for item in catalog["entries"] if item["id"] == "stanley-parable-standalone-2013")
    source_file = FOLDER / "steam-original-221910.json"
    data = json.loads(source_file.read_text(encoding="utf8"))["221910"]["data"]
    assert data["name"] == "The Stanley Parable"
    assert data["release_date"]["date"] == "17 Oct, 2013"
    assert "Galactic Cafe" in data["developers"]
    gallery = {item["id"]: item["path_full"] for item in data["screenshots"]}
    inventory = {item["id"]: item for item in json.loads((FOLDER / "original-image-inventory.json").read_text(encoding="utf8"))}
    plans = [
        (0, 2, "The empty office in the original standalone game", "An office area with doors numbered 420 and 425 in the original 2013 edition, from its publisher gallery."),
        (1, 4, "A furnished room in the 2013 standalone game", "A library and lounge in the 2013 standalone edition. This gallery image illustrates that edition's environment artwork."),
        (2, 6, "Beyond the office: an industrial service area", "A red-lit doorway and industrial service area in the original 2013 edition, from the same publisher gallery."),
    ]
    images = []
    for paragraph, image_id, title, caption in plans:
        record = inventory[image_id]
        assert record["url"] == gallery[image_id]
        file = ROOT / record["file"]
        assert sha(file.read_bytes()) == record["sha256"]
        with Image.open(file) as image:
            image.load()
            assert image.size == (1920, 1080)
        images.append(dict(url=record["url"], source_page="https://store.steampowered.com/app/221910/The_Stanley_Parable/",
            title=title, caption=caption, creator="Galactic Cafe", credit="Galactic Cafe / Original game artwork rights retained",
            license="Original game artwork copyright retained; no open licence claimed.", license_url="",
            width=1920, height=1080, story_paragraph=paragraph, recovery_local_source=record["file"],
            verification=dict(sha256=record["sha256"], native_dimensions=[1920, 1080], no_crop=True, no_upscale=True, visually_reviewed=True),
            identity_evidence=dict(steam_app_id=221910, edition="Original 2013 standalone game", publisher_gallery_image_id=image_id,
                source_file=source_file.relative_to(ROOT).as_posix(), source_file_sha256=sha(source_file.read_bytes()))))
    assert len({image["url"] for image in images}) == 3
    hero = entry["images"][entry.get("preferred_image", 0)]["url"]
    assert all(image["url"] != hero for image in images)
    candidate = dict(schema_version=1, publication_status="candidate_pending_independent_review", entry_id=entry["id"],
        body_sha256=sha(json.dumps(entry["body"], ensure_ascii=False, separators=(",", ":"))),
        body_unchanged=True, preferred_hero_unchanged=True,
        source=dict(file=source_file.relative_to(ROOT).as_posix(), sha256=sha(source_file.read_bytes()), steam_app_id=221910,
            name=data["name"], release_date=data["release_date"], developers=data["developers"]),
        story_headings=["Following or disobeying the narrator", "From the 2011 mod to the 2013 standalone game", "Critical reception and player choice"],
        images=images,
        association_removals=[dict(url=image["url"], story_paragraph=image["story_paragraph"], reason="Keep the original packaging in its gallery; assign the narrative to a distinct publisher screenshot instead.")
            for image in entry["images"] if image.get("story_paragraph") == 0],
        held=[dict(source="Steam publisher launch and promotional trailers", reason="Research metadata only; no video playback record added or codec/playback verification claimed."),
            dict(source="The Stanley Parable: Ultra Deluxe (2022)", reason="Separate later edition; no Ultra Deluxe artwork used to illustrate this original 2013 entry.")],
        source_catalog_sha256=sha((ROOT / "content/catalog.json").read_bytes()), master_modified=False)
    file = FOLDER / "three-original-narrative-images-candidate.json"
    file.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps(dict(candidate=file.relative_to(ROOT).as_posix(), candidate_sha256=sha(file.read_bytes()), paragraphs=len(entry["body"]), images=len(images))))


if __name__ == "__main__":
    main()
