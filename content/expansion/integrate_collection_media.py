"""Admit frozen media batches after narrative/calendar transformations.

Paragraph anchors in these batches refer to the canonical assembled article,
not to the earlier calendar source. A separate receipt binds every body array.
Feature images are handled by integrate_priority_features, never duplicated.
"""
from __future__ import annotations

import copy
import hashlib
import json
from urllib.parse import urlsplit

MEDIA_FILES = ("media-collection-batch-03.json", "media-collection-batch-04.json", "media-collection-batch-05.json", "media-collection-batch-06.json", "daily-identity-media-03.json", "daily-identity-media-04.json", "media-collection-batch-07.json")


def body_hash(body):
    return hashlib.sha256(json.dumps(body, ensure_ascii=False).encode("utf-8")).hexdigest()


def integrate(entries, directory):
    by_id = {entry["id"]: entry for entry in entries}
    if len(by_id) != len(entries):
        raise ValueError("Duplicate article ID before media admission")
    receipts = json.loads((directory / "collection-media-admissions.json").read_text(encoding="utf-8"))
    report = {"schema_version": 1, "added_images": 0, "canonical_articles": [],
              "input_sha256": {}, "source_prose_changes": 0, "editorial_signoffs": 0}
    for filename in MEDIA_FILES:
        path = directory / filename
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        receipt = receipts["batches"][filename]
        if digest != receipt["sha256"]:
            raise ValueError("Frozen media source changed: " + filename)
        document = json.loads(path.read_text(encoding="utf-8"))
        report["input_sha256"][filename] = digest
        rows = [row for row in document["entries"] if not row.get("feature_id")]
        if {row["entry_id"] for row in rows} != set(receipt["body_sha256"]):
            raise ValueError("Media owner set differs from reviewed receipt")
        for row in rows:
            identifier = row["entry_id"]
            entry = by_id.get(identifier)
            reviewed_daily = (filename in {"daily-identity-media-03.json", "daily-identity-media-04.json"} and entry is not None
                and entry.get("source_identity_correction", {}).get("review_file") == "content/expansion/calendar-identity-corrections-03.json"
                and not entry.get("linked_exhibit_id"))
            if not entry or (entry.get("calendar_only") and not reviewed_daily):
                raise ValueError("Media owner is not a canonical article: " + identifier)
            if body_hash(entry.get("body", [])) != receipt["body_sha256"][identifier]:
                raise ValueError("Media paragraph source changed: " + identifier)
            known = {image["url"] for image in entry.get("images", [])}
            additions = []
            for original in row["images"]:
                image = copy.deepcopy(original)
                url = image.get("url", "")
                paragraph = image.get("story_paragraph")
                if (urlsplit(url).scheme != "https" or not urlsplit(url).netloc or any(char.isspace() for char in url)
                        or not image.get("source_page") or not image.get("credit")
                        or not image.get("license") or not image.get("quality_verified")
                        or max(image.get("width", 0), image.get("height", 0)) < 1600
                        or not image.get("verification", {}).get("sha256")):
                    raise ValueError("Media lacks decoded identity/rights evidence: " + identifier)
                if paragraph is not None and (type(paragraph) is not int or
                        not 0 <= paragraph < len(entry.get("body", []))):
                    raise ValueError("Media has invalid canonical paragraph: " + identifier)
                # The source's full edition and verification record is retained.
                # Use a concrete caption rather than a generic console disclaimer
                # on articles whose original game was itself released for PC.
                if image.get("title", "").endswith(": library artwork"):
                    edition = image["title"][:-len(": library artwork")]
                    image["caption"] = "Official publisher library artwork for " + edition + "."
                if url not in known:
                    additions.append(image)
                    known.add(url)
            entry["images"] = additions + entry.get("images", [])
            if reviewed_daily:
                entry['identity_media_admission'] = {'review_file': 'content/expansion/' + filename,
                    'reviewed_batch_sha256': digest, 'source_body_sha256': receipt['body_sha256'][identifier]}
            report["added_images"] += len(additions)
            report["canonical_articles"].append(identifier)
    report["canonical_article_count"] = len(set(report["canonical_articles"]))
    return report
