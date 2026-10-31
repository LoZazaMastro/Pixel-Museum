#!/usr/bin/env python3
"""Build source-bound reference translations beside untouched Playhub locales.

Only explicitly reviewed reference batches are admitted. Authoring/source files are never
written. Packaging must check the generated audit before using runtime-locales.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json

CONTENT = Path(__file__).resolve().parents[1]
LANGUAGES = ("en", "it", "es", "fr", "de", "pt", "ru", "uk")
TARGETS = ("it", "es", "fr", "de")
FIELDS = ("title", "subtitle", "summary", "body", "story_headings")
BATCH_IDS = {
    "wikipedia-locales-reference-12.json": {'wikipedia-72385563', 'wikipedia-292879'},
    "wikipedia-locales-reference-11.json": {'wikipedia-66654', 'wikipedia-1956221', 'wikipedia-52727', 'wikipedia-6150793'},
    "wikipedia-locales-reference-10.json": {'wikipedia-83969309', 'wikipedia-77070226', 'wikipedia-66659306', 'wikipedia-77739989'},
    "wikipedia-locales-reference-09.json": {"wikipedia-70555372", "wikipedia-68100842"},
    "wikipedia-locales-reference-07.json": {'wikipedia-28420914', 'wikipedia-39646535', 'wikipedia-785', 'wikipedia-39645077'},
    "wikipedia-locales-reference-08.json": {'wikipedia-848794', 'wikipedia-57651025', 'wikipedia-1682727', 'wikipedia-24361200'},
    "wikipedia-locales-reference-06.json": {'wikipedia-1055604', 'wikipedia-1159581', 'wikipedia-15448272', 'wikipedia-595917'},
    "wikipedia-locales-breakout-elite.json": {"wikipedia-453246", "wikipedia-286774"},
    "wikipedia-locales-rez-bastion.json": {"wikipedia-101230", "wikipedia-30602654"},
    "wikipedia-locales-metroid-castlevania.json": {"wikipedia-355914", "wikipedia-756296"},
    "wikipedia-locales-arcade-stealth-balatro.json": {"wikipedia-695473", "wikipedia-15915369", "wikipedia-36949806", "wikipedia-76141126"},
    "wikipedia-locales-reference-05.json": {"wikipedia-18711188", "wikipedia-43010284", "wikipedia-52924170", "wikipedia-54027590", "wikipedia-54280556", "wikipedia-72536576"},
}
REVIEW = "editorial/wikipedia-locale-review.json"
AUDIT = "wikipedia-locale-integration-audit.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def digest(value):
    # Source-field hashes deliberately exclude the output newline.
    return hashlib.sha256(encoded(value)[:-1]).hexdigest()


def file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def text(value, label, limit, nonempty=True):
    require(isinstance(value, str), f"{label}: expected text")
    require("\0" not in value and len(value.encode("utf-8")) <= limit,
            f"{label}: invalid or oversized UTF-8 text")
    require(not nonempty or bool(value.strip()), f"{label}: empty translation")


def build(catalog, base, batches):
    """Pure join. Inputs and original/attached English narrative stay unchanged."""
    require(set(base) == set(LANGUAGES), "Expected all eight Playhub source locales")
    require(set(batches) == set(BATCH_IDS), "Unexpected translation batch")
    output = copy.deepcopy(base)
    lookup = {e["id"]: e for e in catalog["entries"]}
    protected = set()
    for language, document in base.items():
        require(document.get("locale") == language and isinstance(document.get("entries"), dict),
                f"{language}: invalid original locale document")
        protected.update(document["entries"])
    rows = []
    seen = set()
    for filename, batch in batches.items():
        require(batch.get("schema_version") == 1 and batch.get("source_language") == "en",
                f"{filename}: unsupported source schema/language")
        records = batch.get("entries", [])
        ids = [row.get("entry_id", row.get("id")) for row in records]
        require(len(ids) == len(set(ids)) and set(ids) == BATCH_IDS[filename],
                f"{filename}: missing, repeated or unreviewed reference ID")
        for record, entry_id in zip(records, ids):
            require(entry_id not in protected, f"{entry_id}: cannot overwrite a Playhub locale")
            source = lookup.get(entry_id)
            require(source is not None and source.get("editorial_mode") == "reference"
                    and not source.get("calendar_only"), f"{entry_id}: not an English reference")
            fields = {key: source.get(key, [] if key in ("body", "story_headings") else "") for key in FIELDS}
            body_hash, fields_hash = digest(fields["body"]), digest(fields)
            attr = source.get("attribution", {})
            snapshot = record.get("source")
            if snapshot is not None:
                require(all(snapshot.get(key) == value for key, value in fields.items()),
                        f"{entry_id}: stale English field snapshot")
                require(snapshot.get("body_sha256") == body_hash and snapshot.get("source_fields_sha256") == fields_hash,
                        f"{entry_id}: stale English source hash")
                require(snapshot.get("attribution") == attr and snapshot.get("sources") == source.get("sources"),
                        f"{entry_id}: stale source attribution/references")
                revision_url, revision_id = snapshot.get("revision_url"), snapshot.get("revision_id")
            else:
                require(record.get("source_body_sha256") == body_hash and record.get("source_fields_sha256") == fields_hash,
                        f"{entry_id}: stale English source hash")
                require(record.get("source_attribution") == attr and record.get("sources") == source.get("sources"),
                        f"{entry_id}: stale source attribution/references")
                require(record.get("source_paragraph_count") == len(fields["body"])
                        and record.get("source_heading_count") == len(fields["story_headings"]),
                        f"{entry_id}: stale English paragraph/heading count")
                revision_url, revision_id = record.get("source_revision_url"), record.get("source_revision_id")
            require(revision_url == attr.get("source_url") and revision_id == attr.get("revision_id")
                    and revision_url == f"https://en.wikipedia.org/w/index.php?oldid={revision_id}",
                    f"{entry_id}: source revision mismatch")
            translations = record.get("translations", record.get("locales", {}))
            require(set(translations) == set(TARGETS), f"{entry_id}: expected precisely four target languages")
            for language, translated in translations.items():
                pair = (entry_id, language)
                require(pair not in seen, f"{pair}: repeated overlay")
                seen.add(pair)
                for key, limit in (("title", 4096), ("subtitle", 8192), ("summary", 16384), ("editorial_credit", 16384)):
                    text(translated.get(key), f"{pair}/{key}", limit)
                for key in ("body", "story_headings"):
                    values = translated.get(key)
                    require(isinstance(values, list) and len(values) == len(fields[key]) and len(values) <= 1000,
                            f"{pair}/{key}: paragraph positions/count must match English")
                    for index, value in enumerate(values):
                        text(value, f"{pair}/{key}/{index}", 65536)
                require(translated.get("source_body_sha256", body_hash) == body_hash
                        and translated.get("source_fields_sha256", fields_hash) == fields_hash,
                        f"{pair}: stale per-locale source hash")
                translated_attr = translated.get("attribution", {})
                for key in ("source_url", "article_url", "contributors_url", "license", "license_url", "revision_id", "revision_timestamp"):
                    require(translated_attr.get(key) == attr.get(key), f"{pair}: {key} attribution mismatch")
                require(translated_attr.get("license") == "CC BY-SA 4.0"
                        and bool(translated_attr.get("changes"))
                        and translated.get("editorial_credit") == translated_attr.get("text"),
                        f"{pair}: translation credit/licence missing")
                row = {key: copy.deepcopy(translated[key]) for key in FIELDS}
                row.update(editorial_credit=translated["editorial_credit"],
                           attribution=copy.deepcopy(translated_attr), source_locale="en",
                           provenance={"mode": "direct_reference_translation", "source_file": f"expansion/{filename}",
                           "source_body_sha256": body_hash, "source_fields_sha256": fields_hash,
                           "source_revision_url": revision_url, "source_revision_id": revision_id,
                           "content_review": "independent_agent_source_and_semantic_review_passed",
                           "native_language_and_layout_signoff": False})
                output[language]["entries"][entry_id] = row
                rows.append({"exhibit_id": entry_id, "locale": language, "batch": filename,
                             "paragraphs": len(row["body"]), "headings": len(row["story_headings"]),
                             "source_body_sha256": body_hash, "source_fields_sha256": fields_hash,
                             "translated_fields_sha256": digest({key: row[key] for key in FIELDS}),
                             "editorial_credit": row["editorial_credit"], "attribution": copy.deepcopy(translated_attr)})
    for language, document in output.items():
        require(len(document["entries"]) <= 5000 and len(encoded(document)) <= 16 << 20,
                f"{language}: runtime locale exceeds parser limits")
    return output, {"schema_version": 1, "reference_entries": len({r["exhibit_id"] for r in rows}),
                    "translation_pairs": len(rows), "translated_paragraphs": sum(r["paragraphs"] for r in rows),
                    "translated_existing_headings": sum(r["headings"] for r in rows),
                    "original_playhub_locales_written": False, "master_catalog_written": False,
                    "native_language_and_layout_signoff": False, "translations": rows}


def source_paths(content):
    return ["catalog.json", *(f"locales/{language}.json" for language in LANGUAGES),
            *(f"expansion/{name}" for name in BATCH_IDS), REVIEW,
            "expansion/integrate_wikipedia_locales.py"]


def generate(content=CONTENT, destination=None):
    content = Path(content)
    destination = Path(destination) if destination is not None else content / "runtime-locales"
    require(destination.resolve() != (content / "locales").resolve(), "Never write original Playhub locales")
    before = {path: file_digest(content / path) for path in source_paths(content)}
    review = read(content / REVIEW)
    require(review.get("integration_decision") == "admit_source_checked_reference_overlays",
            "Translation content review has not admitted integration")
    require(review.get("reviewed_batch_sha256") == {name: before[f"expansion/{name}"] for name in BATCH_IDS},
            "Translation batch changed since independent content review")
    documents, audit = build(read(content / "catalog.json"),
        {language: read(content / "locales" / f"{language}.json") for language in LANGUAGES},
        {name: read(content / "expansion" / name) for name in BATCH_IDS})
    # Complete all source validation before writing a derived output.
    require(before == {path: file_digest(content / path) for path in before}, "Inputs changed during locale generation")
    destination.mkdir(parents=True, exist_ok=True)
    for language, document in documents.items():
        (destination / f"{language}.json").write_bytes(encoded(document))
    audit["input_sha256"] = before
    audit["output_sha256"] = {f"{language}.json": file_digest(destination / f"{language}.json") for language in LANGUAGES}
    (content / AUDIT).write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return audit


def verified_runtime_directory(content=CONTENT):
    """Fail packaging if assembly/generated locales are stale or modified."""
    content = Path(content)
    audit = read(content / AUDIT)
    require(audit.get("input_sha256") == {path: file_digest(content / path) for path in source_paths(content)},
            "Runtime reference locales are stale; run the catalogue assembler")
    destination = content / "runtime-locales"
    require(audit.get("output_sha256") == {f"{language}.json": file_digest(destination / f"{language}.json") for language in LANGUAGES},
            "Generated runtime locale hash mismatch")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content", type=Path, default=CONTENT)
    parser.add_argument("--generate", action="store_true", help="Write derived runtime locales/audit; never assemble or edit master")
    args = parser.parse_args()
    if args.generate:
        result = generate(args.content)
    else:
        verified_runtime_directory(args.content)
        result = read(args.content / AUDIT)
    print(json.dumps({key: result[key] for key in ("reference_entries", "translation_pairs", "translated_paragraphs", "translated_existing_headings", "native_language_and_layout_signoff")}, indent=2))
