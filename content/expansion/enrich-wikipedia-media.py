"""Add only explicitly freely licensed page images to Wikipedia reference records.

Nonfree covers, missing ownership, NC/ND licences and unverified metadata are
recorded in the audit rather than silently advertised as Creative Commons.
"""
from __future__ import annotations
import html
import json
from pathlib import Path
import re
import runpy
import urllib.parse

ROOT = Path(__file__).resolve().parent
helper = runpy.run_path(str(ROOT / "build-wikipedia-ready.py"))
request = helper["request"]
save = helper["save"]


def plain(value):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value or "")).split())


def url_without_tracking(value):
    return (value or "").split("?", 1)[0]


def build():
    path = ROOT / "wikipedia-ready.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    names = sorted({"File:" + e["provenance"]["page_image_filename"]
                    for e in document["entries"] if e["provenance"].get("page_image_filename")})
    images = {}
    rejected = []
    for start in range(0, len(names), 20):
        data = request({"action": "query", "titles": "|".join(names[start:start + 20]),
                        "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 1280}, f"imageinfo-{start:04}")
        for page in data.get("query", {}).get("pages", []):
            if not page.get("imageinfo"):
                rejected.append({"file": page["title"], "reason": "No image metadata"})
                continue
            info = page["imageinfo"][0]
            metadata = info.get("extmetadata", {})
            get = lambda k: metadata.get(k, {}).get("value", "")
            licence = plain(get("LicenseShortName"))
            creator = plain(get("Artist"))
            allowed = (licence.startswith("CC BY") or licence.startswith("CC0") or
                       licence.lower().startswith("public domain") or licence.startswith("PD-"))
            if not allowed or any(term in licence.upper() for term in ("-NC", "-ND")) or not creator:
                rejected.append({"file": page["title"], "license": licence,
                                 "source_page": info.get("descriptionurl"), "reason": "Not an explicitly free licence with identified creator"})
                continue
            # A Wikimedia photo licence does not imply the underlying game/marks
            # are public domain; retain both the source page and its warning.
            images[page["title"].removeprefix("File:").replace("_", " ")] = {
                "url": url_without_tracking(info.get("thumburl", info["url"])),
                "original_url": url_without_tracking(info["url"]),
                "source_page": info["descriptionurl"], "title": plain(get("ObjectName")) or page["title"].removeprefix("File:"),
                "creator": creator, "license": licence,
                "license_url": get("LicenseUrl"),
                "credit": creator + " / Wikimedia Commons / " + licence,
                "width": info.get("width", 0), "height": info.get("height", 0),
                "provenance": "English Wikipedia page image; creator and licence verified through Wikimedia imageinfo. Underlying game art and trademarks retain their respective rights."
            }
        print(f"Image batch {start // 20 + 1}: {len(images)} eligible images", flush=True)
    count = 0
    for entry in document["entries"]:
        filename = (entry["provenance"].get("page_image_filename") or "").replace("_", " ")
        history = entry["attribution"]["contributors_url"]
        licence = entry["attribution"]["license_url"]
        for source in [{"title": "Contributors and article history", "url": history, "publisher": "English Wikipedia contributors"},
                       {"title": "Text licence: Creative Commons Attribution-ShareAlike 4.0", "url": licence, "publisher": "Creative Commons"}]:
            if not any(s["url"] == source["url"] for s in entry["sources"]):
                entry["sources"].append(source)
        if filename in images:
            entry["images"] = [images[filename]]
            count += 1
    save(path, document)
    save(ROOT / "wikipedia-media-audit.json", {"entries": len(document["entries"]), "illustrated_entries": count,
         "distinct_verified_free_images": len(images), "missing_or_nonfree": rejected,
         "policy": "No locally hosted or nonfree cover artwork is automatically inserted. Missing images remain empty; no open licence is inferred from Wikipedia text licensing."})
    print(f"Ready: {count}/{len(document['entries'])} entries illustrated with verified free images", flush=True)


if __name__ == "__main__":
    build()
