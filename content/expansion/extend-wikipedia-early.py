"""Add substantive early-game Wikipedia sections without padding short leads.

The main wikipedia-ready.json is never changed. Reuses cached discovery metadata,
fetches full article extracts one at a time, and retains complete prose paragraphs.
"""
from __future__ import annotations

from collections import Counter
import copy
import json
from pathlib import Path
import re
import runpy
import urllib.parse

ROOT = Path(__file__).resolve().parent
helpers = runpy.run_path(str(ROOT / "build-wikipedia-ready.py"))
request, normalized, save, eras = (helpers[k] for k in ("request", "normalized", "save", "eras"))
LICENCE = helpers["LICENCE"]


def selected_prose(extract):
    result = []
    count = 0
    for line in extract.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("="):
            heading = line.strip("= ").casefold()
            if heading in {"references", "notes", "notes and references", "external links", "further reading", "see also", "sources", "bibliography"}:
                break
            continue
        # Exclude tables/list fragments, keeping full prose paragraphs only.
        words = len(line.split())
        if words < 12 or not re.search(r"[.!?\"]$", line):
            continue
        if count >= 450 or (count >= 120 and count + words > 700):
            break
        result.append(line)
        count += words
    return result


def build():
    base = json.loads((ROOT / "wikipedia-ready.json").read_text(encoding="utf-8"))
    exclusions, ids = set(), set()
    for path in (ROOT / "wikipedia-ready.json", ROOT / "playhub-museum-candidates.json", ROOT.parent / "catalog.json"):
        if path.exists():
            for item in json.loads(path.read_text(encoding="utf-8"))["entries"]:
                exclusions.add(normalized(item["title"]))
                ids.add(item["id"])
    candidates = {}
    for path in (ROOT / "wikipedia-cache").glob("articles-*.json"):
        for page in json.loads(path.read_text(encoding="utf-8")).get("query", {}).get("pages", []):
            if "pageid" not in page or "wikipedia-" + str(page["pageid"]) in ids or normalized(page["title"]) in exclusions:
                continue
            years = [int(m.group(1)) for c in page.get("categories", []) if (m := re.fullmatch(r"Category:(\d{4}) video games", c["title"]))]
            if years and 1970 <= min(years) < 1990:
                candidates[page["pageid"]] = (min(years), page)
    # Start with the most substantive short introductions. No article is admitted
    # merely to reach the target; its selected text must still exceed 120 words.
    queue = sorted(candidates.values(), key=lambda x: (x[0] // 10, -len(x[1].get("extract", "").split()), x[1]["title"]))
    current = Counter(e["year"] // 10 * 10 for e in base["entries"])
    need = {1970: max(0, 100 - current[1970]), 1980: max(0, 100 - current[1980])}
    records, rejected = [], []
    counts = Counter()
    for hinted_year, candidate in queue:
        decade = hinted_year // 10 * 10
        if counts[decade] >= need[decade]:
            continue
        try:
            data = request({"action": "query", "pageids": candidate["pageid"],
                            "prop": "extracts|info|revisions|categories|pageimages", "explaintext": 1,
                            "inprop": "url", "rvprop": "ids|timestamp", "cllimit": "max", "piprop": "name"},
                           "full-early-" + str(candidate["pageid"]))
            page = data["query"]["pages"][0]
            years = [int(m.group(1)) for c in page.get("categories", []) if (m := re.fullmatch(r"Category:(\d{4}) video games", c["title"]))]
            # Cached candidate categories are a fallback only for a categories
            # continuation; provenance states the release-year category basis.
            year = min(years) if years else hinted_year
            body = selected_prose(page.get("extract", ""))
            words = sum(len(p.split()) for p in body)
            if words < 120 or not 1970 <= year < 1990:
                rejected.append({"title": page["title"], "words": words, "reason": "Insufficient substantive early article prose"})
                continue
            title = page["title"]
            display_title = re.sub(r" \((?:\d{4} )?(?:video game|arcade game|computer game)\)$", "", title)
            revision = page["revisions"][0]
            permalink = "https://en.wikipedia.org/w/index.php?oldid=" + str(revision["revid"])
            article_url = page.get("canonicalurl", "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")))
            ident = "wikipedia-" + str(page["pageid"])
            item = {"id": ident, "title": display_title, "year": year,
                    "date": {"month": 0, "day": 0, "precision": "year", "region": "Original release year category; regional dates may differ"},
                    "kind": "game", "subtitle": "From the reference collection",
                    "summary": re.split(r"(?<=[.!?])\s+(?=[A-Z])", body[0], maxsplit=1)[0],
                    "body": body, "era_id": eras(year), "tags": ["reference", "Wikipedia"], "related_ids": [],
                    "layout": "editorial", "featured": False, "images": [], "videos": [], "models": [],
                    "sources": [
                        {"title": title + " - article revision", "url": permalink, "publisher": "English Wikipedia contributors"},
                        {"title": "Contributors and article history", "url": article_url + "?action=history", "publisher": "English Wikipedia contributors"},
                        {"title": "Text licence: Creative Commons Attribution-ShareAlike 4.0", "url": LICENCE, "publisher": "Creative Commons"},
                        {"title": str(year) + " video games - release-year category", "url": "https://en.wikipedia.org/wiki/Category:" + str(year) + "_video_games", "publisher": "English Wikipedia contributors"}],
                    "attribution": {"text": "Text reproduced from '" + title + "', by Wikipedia contributors, under CC BY-SA 4.0. Opening and early article sections selected; headings, lists and formatting removed.",
                                    "source_url": permalink, "article_url": article_url, "contributors_url": article_url + "?action=history",
                                    "license": "CC BY-SA 4.0", "license_url": LICENCE, "revision_id": revision["revid"],
                                    "revision_timestamp": revision["timestamp"], "changes": "Complete prose paragraphs selected from opening and early sections; headings, list fragments and formatting removed. Text otherwise reproduced."},
                    "provenance": {"provider": "English Wikipedia", "page_id": page["pageid"], "article_title": title,
                                   "discovery_method": "Annual release tables and release-year categories, followed by full article extracts where leads were short",
                                   "release_year_basis": "Earliest YYYY video games category; no month/day inferred", "page_image_filename": page.get("pageimage"),
                                   "retrieved": "2026-10-20"},
                    "factual_note": "Reference article prose reproduced under its stated licence. Year comes from the article's release-year category; regional/port dates may differ."}
            records.append(item)
            counts[year // 10 * 10] += 1
            exclusions.add(normalized(display_title))
            print("Ready", len(records), year, display_title, words, "words", flush=True)
            save(ROOT / "wikipedia-early-ready.json", {"schema_version": 1, "license_notice": base["license_notice"], "entries": records})
        except Exception as error:
            rejected.append({"title": candidate["title"], "reason": str(error)})
            print("Failed", candidate["title"], error, flush=True)
        if all(counts[d] >= need[d] for d in need):
            break
    save(ROOT / "wikipedia-early-audit.json", {"status": "complete", "ready_count": len(records), "by_decade": dict(counts),
         "total_wikipedia_by_decade": {str(d): current[d] + counts[d] for d in current},
         "word_count": sum(len(p.split()) for e in records for p in e["body"]), "rejected": rejected,
         "quality": "Real full-article prose; >=120 words per entry. Exact revision, contributor history and CC BY-SA 4.0 source links retained."})
    print("Complete", dict(counts), "target", need, flush=True)


if __name__ == "__main__":
    build()
