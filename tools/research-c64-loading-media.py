"""Bounded research-only artifact acquisition for the C64 loading feature."""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin
import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/research/c64-loading-media"
OUT.mkdir(parents=True, exist_ok=True)

def fetch(url, name):
    path = OUT / name
    if not path.exists():
        with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as response:
            body = response.read(16 << 20)
        temporary = path.with_suffix(path.suffix + ".part")
        temporary.write_bytes(body)
        temporary.replace(path)
    return path

receipts = []
for name, url in [
    ("hughes-robocop.jpg", "https://www.pauliehughes.com/index_htm_files/3558.jpg"),
    ("hughes-combat-school.jpg", "https://www.pauliehughes.com/index_htm_files/3564.jpg"),
    ("hughes-hit-squad-ad.jpg", "https://www.pauliehughes.com/index_htm_files/3566.jpg"),
    ("dokk-gallery-01.html", "https://www.c64.com/pictures/dokk_gallery/01.php"),
    ("dokk-leviathan.html", "https://www.c64.com/pictures/dokk_gallery/20.php"),
    ("dokk-druid2.html", "https://www.c64.com/pictures/dokk_gallery/10.php"),
    ("collector-c64-scans.html", "https://retro-video-gaming.com/commodore-64-collection/"),
]:
    try:
        path = fetch(url, name)
        record = {"url": url, "path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        if path.suffix == ".jpg":
            with Image.open(path) as picture:
                picture.load()
                record["native_dimensions"] = list(picture.size)
        else:
            text = path.read_text(encoding="latin1")
            record["images"] = [urljoin(url, source) for source in re.findall(r'<img[^>]+src=[\"\x27]([^\"\x27]+)', text, flags=re.I)]
            record["links"] = [urljoin(url, source) for source in re.findall(r'href=[\"\x27]([^\"\x27]+)', text, flags=re.I)]
        receipts.append(record)
    except Exception as error:
        receipts.append({"url": url, "status": "held_fetch_failed", "reason": str(error)})
(OUT / "primary-page-media.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2))
print(json.dumps(receipts, ensure_ascii=False, indent=2), flush=True)

games, images = {}, []
with zipfile.ZipFile(ROOT / "build/research/launchbox/Metadata-range.zip") as archive, archive.open("Metadata.xml") as stream:
    for _, node in ET.iterparse(stream, events=("end",)):
        if node.tag == "Game":
            row = {child.tag: child.text or "" for child in node}
            node.clear()
            if row.get("Platform") == "Commodore 64" and ("druid" in row.get("Name", "").lower() or row.get("Name", "").lower() in ("leviathan", "enlightenment", "robocop", "combat school")):
                games[row["DatabaseID"]] = row
        elif node.tag == "GameImage":
            row = {child.tag: child.text or "" for child in node}
            node.clear()
            if row.get("DatabaseID") in games and row.get("Type") in ("Box - Front", "Box - Back", "Advertisement Flyer - Front", "Cart - Front"):
                images.append({"game": games[row["DatabaseID"]], "image": row})
(OUT / "exact-c64-packaging-candidates.json").write_text(json.dumps({"games": games, "images": images}, ensure_ascii=False, indent=2))
print("Exact original C64 candidates:", [(row["game"]["Name"], row["image"]["Type"], row["image"].get("FileName")) for row in images], flush=True)
