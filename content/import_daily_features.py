"""Import scheduled English Playhub features without inventing anniversaries.

The published365-workbook editions are the current Playhub calendar; legacy
days and occasion themes do not replace them. Publication slots are stored in
calendar, never in historical month/day fields. Unresolved years are audited.
"""
from __future__ import annotations
import argparse
import copy
import datetime
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
SOURCE_URL = "https://github.com/LoZazaMastro/Playhub/blob/main/catalog/on-this-day.json"


def english(value):
    return value.get("en", "") if isinstance(value, dict) else value if isinstance(value, str) else ""


def key(value):
    value = re.sub(r"\s*\([^)]*\)", "", value)
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower())


def source_record(url):
    host = urlparse(url).netloc.removeprefix("www.")
    return {"title": host, "url": url, "publisher": host}


def import_features(source_path, catalog_path, destination):
    raw = source_path.read_bytes()
    source = json.loads(raw)
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    entries = [e for e in catalog["entries"] if not e.get("calendar_only")]
    by_title = {}
    for entry in entries:
        by_title.setdefault(key(entry["title"]), []).append(entry)
    editions = source.get("editions", {}).get("entries", [])
    edition_by_date = {}
    for edition in editions:
        if edition.get("published"):
            edition_by_date.setdefault(edition.get("anniversary", {}).get("date", ""), []).append(edition)
    def match_subject(record):
        for subject in [record.get("subject", ""), record.get("topic", "")]:
            if not subject:
                continue
            normalized = key(subject)
            candidates = by_title.get(normalized, [])
            canonical = [e for e in candidates if not e["id"].startswith(("wikipedia-", "workbook-"))]
            if len(canonical) == 1:
                return canonical[0], "catalog_canonical_title"
            years = {e["year"] for e in candidates}
            if candidates and len(years) == 1:
                return candidates[0], "catalog_exact_title"
        return None, "unresolved_or_ambiguous_subject"

    imported, omitted = [], []
    by_id = {e["id"]: e for e in entries}
    schedule = {}
    for edition in editions:
        if not edition.get("published") or "en" not in edition.get("locales", []):
            continue
        record = copy.deepcopy(edition["theme"])
        anniversary = edition.get("anniversary", {})
        date = anniversary.get("date", "")
        try:
            month, day = map(int, date.split("-")); datetime.date(2025, month, day)
        except (ValueError, TypeError):
            omitted.append({"calendar_date": date, "reason": "invalid_nonleap_calendar_slot"}); continue
        title = record.get("subject") or record.get("topic") or ""
        feature_title, intro = english(record.get("title")), english(record.get("intro"))
        matched = by_id.get(record.get("id", ""))
        if matched:
            method = "exact_published_workbook_id"
        else:
            matched, method = match_subject(record)
        year = anniversary.get("year")
        year_method = "published_edition_historical_anchor"
        extra_year_source = None
        if not isinstance(year, int):
            if matched:
                year, year_method = matched["year"], "matching_catalog_subject"
            elif title == "Xbox Adaptive Controller" and "September 2018" in intro:
                year, year_method = 2018, "published_intro_and_primary_launch_report"
                extra_year_source = {"title": "Gaming Gets More Inclusive With The Launch Of The Xbox Adaptive Controller", "publisher": "Xbox Wire / Microsoft", "url": "https://news.xbox.com/en-us/2018/09/04/gaming-gets-more-inclusive-with-the-launch-of-the-xbox-adaptive-controller/"}
            elif title == "Christmas NiGHTS" and "published the promotional disc in 1996" in intro:
                year, year_method = 1996, "explicit_historical_year_in_published_intro"
            elif title == "The Sims 2: Holiday Party Pack" and "November 2005" in intro:
                year, year_method = 2005, "explicit_historical_year_in_published_intro"
        if not isinstance(year, int) or not title or not feature_title or not intro:
            omitted.append({"calendar_date": date, "subject": title, "source_theme_id": record.get("id"), "reason": "unresolved_year_or_missing_english_text"}); continue
        body, headings = [intro], [feature_title]
        for chapter in record.get("chapters", []):
            text = english(chapter.get("body"))
            if text:
                body.append(text); headings.append(english(chapter.get("title")))
        references = []
        for url in record.get("sources", []):
            if isinstance(url, str) and url.startswith(("https://", "http://")) and url not in {r["url"] for r in references}:
                references.append(source_record(url))
        if extra_year_source and extra_year_source["url"] not in {r["url"] for r in references}:
            references.append(extra_year_source)
        references.append({"title": "Playhub: original published daily edition", "url": SOURCE_URL, "publisher": "Playhub / LoZazaMastro", "attribution": "Original published Playhub English introduction and chapter text retained without rewriting."})
        era = next((era["id"] for era in catalog["eras"] if era["start_year"] <= year <= era["end_year"]), catalog["eras"][0]["id"])
        source_images = copy.deepcopy(source.get("images", {}).get(record.get("media_id", record.get("id", "")), []))
        kind = matched["kind"] if matched else "person" if anniversary.get("kind") == "birth" or record.get("kind") in ("birth", "nascita") else "console" if record.get("kind") in ("hardware", "lancio_hardware", "annuncio_hardware") else "hardware" if title == "Xbox Adaptive Controller" else "technology" if record.get("kind") in ("foundation", "fondazione_impresa", "acquisizione", "cambio_denominazione", "evento") else "game"
        feature = {
            "id": "daily-" + date, "title": title, "subtitle": feature_title,
            "year": year, "kind": kind, "era_id": era,
            "date": {"month": 0, "day": 0, "precision": "year", "region": ""},
            "calendar_only": True, "calendar": {"month": month, "day": day},
            "linked_exhibit_id": matched["id"] if matched else "",
            "event_semantics": "Scheduled published Playhub edition. The calendar slot is not asserted as a historical anniversary; the year is the source's historical anchor.",
            "summary": re.split(r"(?<=[.!?])\s+(?=[A-Z])", intro)[0],
            "body": body, "story_headings": headings, "layout": "essay", "featured": False,
            "tags": ["Daily feature", "Playhub collection"], "related_ids": [matched["id"]] if matched else [],
            "images": [], "videos": [], "models": [], "sources": references,
            "editorial_mode": "playhub_story", "editorial_credit": "Playhub historical collection / LoZazaMastro. Original published English text and chapter headings retained.",
            "source_subject": record.get("subject", ""), "source_topic": record.get("topic", ""), "source_feature_title": feature_title,
            "provenance": {"source_url": SOURCE_URL, "source_origin": "editions.entries", "source_record_id": record.get("id", ""), "source_revision": source.get("revision"), "source_updated_at": source.get("updatedAt"), "year_resolution": year_method, "subject_resolution": method, "source_anniversary_metadata": copy.deepcopy(anniversary), "source_theme_kind": record.get("kind", ""), "matched_entry_id": matched["id"] if matched else "", "matched_title": matched["title"] if matched else ""},
            "research_media_refs": {"media": copy.deepcopy(record.get("media", {})), "media_id": record.get("media_id", ""), "images": source_images, "intro_image_file": record.get("intro_image_file", ""), "cover_image_file": record.get("cover_image_file", ""), "chapters": [{k:copy.deepcopy(v) for k,v in c.items() if k not in ("body", "title", "kicker")} for c in record.get("chapters", [])]},
        }
        imported.append(feature)
        schedule[date] = feature["id"]

    audit = {
        "source_file": str(source_path), "source_url": SOURCE_URL, "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_days_count": len(source.get("days", {})), "source_published_editions_count": sum(bool(e.get("published")) for e in editions),
        "calendar_candidates": len(edition_by_date), "imported_count": len(imported), "omitted_count": len(omitted),
        "policy": "Published365-workbook editions take priority; legacy335 days are not imported. Full English introduction and every chapter retained. Edition historical anchor or explicit sourced year stays separate from the calendar publication slot. No fabricated anniversary. Primary assets remain a separate media review step.",
        "omitted": omitted,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({"schema_version": 1, "entries": imported, "schedule": dict(sorted(schedule.items())), "audit": audit}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    assert all(len(e["body"]) == len(e["story_headings"]) and e["date"]["month"] == e["date"]["day"] == 0 for e in imported)
    print(json.dumps({"output": str(destination), "imported": len(imported), "omitted": len(omitted), "october20": next(({"id":e["id"],"title":e["title"],"linked_exhibit_id":e["linked_exhibit_id"],"paragraphs":len(e["body"])} for e in imported if e["id"] == "daily-10-20"), None)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(r"F:\Playhub\Plugin\Playhub\catalog\on-this-day.json"))
    parser.add_argument("--catalog", type=Path, default=ROOT / "catalog.json")
    parser.add_argument("--output", type=Path, default=ROOT / "expansion/calendar-features.json")
    args = parser.parse_args()
    import_features(args.source, args.catalog, args.output)
