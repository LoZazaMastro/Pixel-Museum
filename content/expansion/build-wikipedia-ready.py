"""Build attributed museum reference records from live English Wikipedia revisions.

Only this script's wikipedia-* files are written. Annual lists provide discovery;
article categories provide release years. No exact day is inferred from an index.
"""
from __future__ import annotations

import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "wikipedia-cache"
CACHE.mkdir(exist_ok=True)
API = "https://en.wikipedia.org/w/api.php"
AGENT = "PixelMuseumResearch/1.0 (educational museum; https://github.com/LoZazaMastro)"
LAST = 0.0
LICENCE = "https://creativecommons.org/licenses/by-sa/4.0/"
YEARS = range(1970, 2026)
TARGET_PER_DECADE = 110


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def first_sentence(text):
    """Keep personal initials and common abbreviations inside the source sentence."""
    value = text.replace("\n", " ")
    # Name prefixes require a following name. Product/company suffixes such as
    # Bros. and Inc. may genuinely end a sentence and must not swallow the next.
    name_prefixes = {"dr.", "mr.", "mrs.", "ms.", "prof."}
    for boundary in re.finditer(r"(?<=[.!?])\s+(?=[A-Z0-9])", value):
        candidate = value[:boundary.start()]
        token = candidate.rsplit(None, 1)[-1].rstrip('\"\')]}')
        if token.lower() in name_prefixes or re.fullmatch(r"[A-Za-z]\.", token):
            continue
        return candidate
    return value


def request(params, tag, api=API):
    global LAST
    key = hashlib.sha256((api + json.dumps(params, sort_keys=True)).encode()).hexdigest()[:20]
    path = CACHE / (tag + "-" + key + ".json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    wait = 1.05 - (time.monotonic() - LAST)
    if wait > 0:
        time.sleep(wait)
    url = api + "?" + urllib.parse.urlencode({"format": "json", "formatversion": 2, **params})
    LAST = time.monotonic()
    req = urllib.request.Request(url, headers={"User-Agent": AGENT})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=40) as response:
                data = json.load(response)
            if "error" in data:
                raise RuntimeError(data["error"])
            save(path, data)
            return data
        except urllib.error.HTTPError as error:
            if error.code not in (429, 503) or attempt:
                raise
            time.sleep(min(15, int(error.headers.get("Retry-After", 8))))
    raise RuntimeError("No response")


def normalized(title):
    title = html.unescape(title).casefold().replace("&", "and")
    title = re.sub(r"\([^)]*\)", "", title)
    return re.sub(r"[^a-z0-9]", "", title)


class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.tables = []
        self.table = []
        self.row = []
        self.cell = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self.depth += 1
            if self.depth == 1:
                self.table = []
        if self.depth != 1:
            return
        if tag == "tr":
            self.row = []
        elif tag in ("th", "td"):
            self.cell = {"text": "", "links": [], "header": tag == "th"}
        elif tag == "a" and self.cell is not None:
            href = a.get("href", "")
            title = a.get("title", "")
            if not title and "/wiki/" in href:
                title = urllib.parse.unquote(href.split("/wiki/", 1)[1]).replace("_", " ")
            if title and not any(title.startswith(x) for x in ("File:", "Category:", "Help:", "Wikipedia:", "Template:", "Edit ")):
                self.cell["links"].append(title)

    def handle_data(self, data):
        if self.depth == 1 and self.cell is not None:
            self.cell["text"] += data

    def handle_endtag(self, tag):
        if self.depth == 1:
            if tag in ("th", "td") and self.cell is not None:
                self.cell["text"] = " ".join(self.cell["text"].split())
                self.row.append(self.cell)
                self.cell = None
            elif tag == "tr" and self.row:
                self.table.append(self.row)
            elif tag == "table":
                self.tables.append(self.table)
        if tag == "table":
            self.depth -= 1


def annual_titles(year):
    title = f"{year} in video games"
    data = request({"action": "parse", "page": title, "prop": "text|revid"}, f"annual-{year}")
    parsed = data["parse"]
    table = Tables()
    table.feed(parsed["text"])
    names = []
    for rows in table.tables:
        title_columns = []
        for row in rows:
            cols = [i for i, c in enumerate(row) if c["header"] and c["text"].strip().lower() in ("title", "game", "game title", "name")]
            if cols:
                title_columns = cols
                continue
            for col in title_columns:
                if col < len(row) and row[col]["links"]:
                    names.append(row[col]["links"][0])
    return list(dict.fromkeys(names)), {"title": title, "revision_id": parsed["revid"], "url": "https://en.wikipedia.org/w/index.php?oldid=" + str(parsed["revid"])}


def eras(year):
    if year < 1970: return "origins"
    if year < 1980: return "public-play"
    if year < 1990: return "personal"
    if year < 2000: return "dimensions"
    if year < 2010: return "connected"
    if year < 2020: return "everywhere"
    return "living-history"


def build():
    exclusions = set()
    for path in [ROOT.parent / "catalog.json", ROOT / "playhub-museum-candidates.json"]:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            exclusions.update(normalized(e["title"]) for e in data["entries"])
    discoveries = {}
    annuals = {}
    for year in YEARS:
        try:
            titles, source = annual_titles(year)
            annuals[year] = source
            for title in titles:
                if normalized(title) not in exclusions:
                    discoveries.setdefault(title, set()).add(year)
            print(f"Annual {year}: {len(titles)} linked titles; unique new candidates {len(discoveries)}", flush=True)
        except Exception as error:
            print(f"Annual {year}: FAILED {error}", flush=True)
    # Early annual articles list few releases. Their year categories supply
    # additional named games, still checked against each article's own categories.
    for year in list(range(1970, 1980)) + list(range(2020, 2026)):
        category = f"Category:{year} video games"
        data = request({"action": "query", "list": "categorymembers", "cmtitle": category,
                        "cmtype": "page", "cmnamespace": 0, "cmlimit": "max"}, f"year-category-{year}")
        members = data.get("query", {}).get("categorymembers", [])
        for page in members:
            if normalized(page["title"]) not in exclusions:
                discoveries.setdefault(page["title"], set()).add(year)
        print(f"Year category {year}: {len(members)} named article candidates", flush=True)
    save(ROOT / "wikipedia-discovery.json", {"annuals": annuals, "titles": {k: sorted(v) for k, v in discoveries.items()}})
    # Round-robin across years prevents the beginning of each decade dominating.
    per_year = {y: [t for t, ys in discoveries.items() if y in ys] for y in YEARS}
    queue = []
    seen = set()
    for i in range(max(map(len, per_year.values()), default=0)):
        for year in YEARS:
            if i < len(per_year[year]):
                title = per_year[year][i]
                if title not in seen:
                    queue.append(title)
                    seen.add(title)
    counts = {d: 0 for d in range(1970, 2030, 10)}
    records = []
    rejected = []
    for start in range(0, len(queue), 20):
        titles = [t for t in queue[start:start + 20]
                  if any(counts.get(y // 10 * 10, TARGET_PER_DECADE) < TARGET_PER_DECADE for y in discoveries[t])]
        if not titles:
            continue
        data = request({"action": "query", "titles": "|".join(titles), "redirects": 1,
                        "prop": "extracts|info|revisions|categories|pageimages", "exintro": 1, "explaintext": 1, "exlimit": "max",
                        "inprop": "url", "rvprop": "ids|timestamp",
                        "cllimit": "max", "piprop": "name"}, f"articles-{start:05}")
        # Continuation may carry filtered categories from remaining pages; never silently drop them.
        pages = {p["pageid"]: p for p in data.get("query", {}).get("pages", []) if "pageid" in p}
        continuation = data.get("continue")
        while continuation:
            more = request({"action": "query", "titles": "|".join(titles), "redirects": 1,
                            "prop": "categories", "cllimit": "max", **continuation}, f"categories-{start:05}")
            for page in more.get("query", {}).get("pages", []):
                if page.get("pageid") in pages:
                    pages[page["pageid"]].setdefault("categories", []).extend(page.get("categories", []))
            continuation = more.get("continue")
        for page in pages.values():
            title = page["title"]
            ident = "wikipedia-" + str(page["pageid"])
            if normalized(title) in exclusions or any(e["id"] == ident for e in records):
                continue
            text = page.get("extract", "").strip()
            years = [int(m.group(1)) for c in page.get("categories", []) if (m := re.fullmatch(r"Category:(\d{4}) video games", c["title"]))]
            if not years or len(text.split()) < 120 or "may refer to:" in text:
                rejected.append({"title": title, "reason": "no release-year category or insufficient introduction"})
                continue
            year = min(years)
            decade = year // 10 * 10
            if decade not in counts or counts[decade] >= TARGET_PER_DECADE:
                continue
            revision = page["revisions"][0]
            source_url = "https://en.wikipedia.org/w/index.php?oldid=" + str(revision["revid"])
            body = [p.strip() for p in text.split("\n") if p.strip()]
            # Literal extracts are not silently condensed or rewritten. Pronunciation/parentheses remain source text.
            summary = first_sentence(text)
            article_url = page.get("canonicalurl", "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")))
            display_title = re.sub(r" \((?:\d{4} )?(?:video game|arcade game|computer game)\)$", "", title)
            record = {"id": ident, "title": display_title, "year": year,
                      "date": {"month": 0, "day": 0, "precision": "year", "region": "Original release year category; regional dates may differ"},
                      "kind": "game", "subtitle": "From the reference collection", "summary": summary, "body": body,
                      "era_id": eras(year), "tags": ["reference", "Wikipedia"], "related_ids": [], "layout": "editorial",
                      "images": [], "videos": [], "models": [], "featured": False,
                      "sources": [{"title": title + " — article revision", "url": source_url, "publisher": "English Wikipedia contributors"},
                                  {"title": "Contributors and article history", "url": article_url + "?action=history", "publisher": "English Wikipedia contributors"},
                                  {"title": "Text licence: Creative Commons Attribution-ShareAlike 4.0", "url": LICENCE, "publisher": "Creative Commons"}],
                      "attribution": {"text": "Text reproduced from '" + title + "', by Wikipedia contributors, under CC BY-SA 4.0. No substantive text changes; lead paragraphs selected and formatting removed.",
                                      "source_url": source_url, "article_url": article_url,
                                      "contributors_url": article_url + "?action=history", "license": "CC BY-SA 4.0", "license_url": LICENCE,
                                      "revision_id": revision["revid"], "revision_timestamp": revision["timestamp"], "changes": "Lead section selected; plain-text formatting. Text otherwise reproduced."},
                      "provenance": {"provider": "English Wikipedia", "page_id": page["pageid"], "article_title": title,
                                     "year_index_discovery_years": sorted(discoveries.get(title, set())),
                                     "discovery_method": "Annual release/awards tables; supplemented by release-year category members for1970s/2020s",
                                     "release_year_basis": "Earliest filtered YYYY video games category; no month/day inferred",
                                     "page_image_filename": page.get("pageimage"), "retrieved": "2026-10-20"},
                      "factual_note": "Reference article introduction reproduced under its stated licence. Year comes from the article's release-year category; regional/port dates may differ."}
            discovered_years = discoveries.get(title, set())
            for dy in sorted(discovered_years)[:1]:
                record["sources"].append({"title": annuals[dy]["title"] + " — annual context", "url": annuals[dy]["url"], "publisher": "English Wikipedia contributors"})
            records.append(record)
            exclusions.add(normalized(title))
            counts[decade] += 1
        print(f"Article batch {start // 20 + 1}: {len(records)} ready; decades {counts}", flush=True)
        save(ROOT / "wikipedia-ready.json", {"schema_version": 1, "license_notice": "Wikipedia text is CC BY-SA 4.0; individual record attribution and revision links must remain visible in the museum.", "entries": records})
        if all(n >= TARGET_PER_DECADE for n in counts.values()):
            break
    save(ROOT / "wikipedia-audit.json", {"status": "complete_fetch_pass", "ready_count": len(records), "by_decade": counts,
         "annual_pages": len(annuals), "discovered_titles": len(discoveries), "rejected": rejected,
         "quality": "All included records have >=120-word live article introductions, revision IDs, licence/history links and an explicit year-category basis. No exact release dates inferred; nonfree media not added automatically."})


if __name__ == "__main__":
    build()
