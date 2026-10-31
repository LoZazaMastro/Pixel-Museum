"""Admit reviewed hardware families without retaining regional chronology stops."""
from pathlib import Path
import copy
import hashlib
import json

FOLDER = "build/research/hardware-release-consolidation"
REFERENCE_FIELDS = frozenset(("canonical_entry_id", "linked_exhibit_id", "entry_id",
    "exhibit_id", "initial_id", "target_id", "related_ids", "entry_ids"))


def body_digest(entry):
    return hashlib.sha256(json.dumps(entry.get("body", []), ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def navigation_aliases(entries, *alias_maps):
    """Flatten reviewed retired hardware IDs; reject cycles and missing targets."""
    by_id = {entry["id"]: entry for entry in entries}
    combined = {}
    for mapping in alias_maps:
        combined.update(mapping)
    result = {}
    for old, value in combined.items():
        if old in by_id or not isinstance(old, str) or len(old.encode()) > 192:
            continue
        seen = {old}
        for _ in range(32):
            if value in by_id:
                owner = by_id[value]
                if owner.get("kind") in ("console", "computer", "hardware") or value == "minecraft":
                    result[old] = value
                break
            if value in seen or value not in combined:
                break
            seen.add(value)
            value = combined[value]
    if len(result) > 4096:
        raise ValueError("Hardware alias inventory exceeds the native bound")
    return result


def redirect_references(value, aliases, path="", changes=None):
    """Only navigation fields change; source identity and legal credits do not."""
    if changes is None:
        changes = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in ("provenance", "attribution", "source_verification"):
                continue
            location = path + "/" + key
            if key in REFERENCE_FIELDS:
                if isinstance(child, str) and child in aliases:
                    value[key] = aliases[child]
                    changes.append(dict(path=location, old=child, value=value[key]))
                elif isinstance(child, list):
                    updated = list(dict.fromkeys(aliases.get(item, item)
                                   if isinstance(item, str) else item for item in child))
                    if updated != child:
                        value[key] = updated
                        changes.append(dict(path=location, old=child, value=updated))
            else:
                redirect_references(child, aliases, location, changes)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            redirect_references(child, aliases, path + "/" + str(index), changes)
    return changes


def project(entries, document, candidate_sha256="research_projection"):
    by_id = {entry["id"]: entry for entry in entries}
    aliases = {}
    results = []
    for plan in document["merges"]:
        canonical = plan["canonical_id"]
        retired = plan["retired_id"]
        aliases[retired] = canonical
        target, source = by_id.get(canonical), by_id.get(retired)
        if source is None:
            if target is None:
                raise ValueError("Both reviewed hardware records are absent")
            continue
        if target is None:
            raise ValueError("Canonical hardware record is absent: " + canonical)
        for identifier, digest in plan["old_body_sha256"].items():
            if body_digest(by_id[identifier]) != digest:
                raise ValueError("Reviewed hardware body changed: " + identifier)
        old_target, old_source = copy.deepcopy(target), copy.deepcopy(source)
        maps = {canonical: {}, retired: {}}
        target["body"], target["story_headings"] = [], []
        for index, row in enumerate(plan["paragraphs"]):
            original = by_id[row["entry_id"]] if row["entry_id"] != canonical else old_target
            if original["body"][row["paragraph_index"]] != row["old_body"]:
                raise ValueError("Hardware paragraph locator changed")
            target["body"].append(row["body"])
            target["story_headings"].append(row["heading"])
            maps[row["entry_id"]][row["paragraph_index"]] = index
        target.update(copy.deepcopy(plan["fields"]))
        preferred = old_target["images"][old_target.get("preferred_image", 0)]["url"]
        excluded = set(plan.get("excluded_image_urls", []))
        target["images"] = []
        seen = set()
        for original in (old_target, old_source):
            for image in original.get("images", []):
                if image["url"] in excluded or image["url"] in seen:
                    continue
                image = copy.deepcopy(image)
                image.update(copy.deepcopy(plan.get("image_metadata_overrides", {}).get(image["url"], {})))
                position = image.get("story_paragraph")
                if isinstance(position, int) and position >= 0:
                    image["story_paragraph"] = maps[original["id"]].get(position, -1)
                # Preserve genuine standalone artefacts; never invent a paragraph
                # association from their old gallery position after a merge.
                else:
                    image["story_paragraph"] = -1
                if image["url"] in plan.get("image_associations", {}):
                    image["story_paragraph"] = plan["image_associations"][image["url"]]
                target["images"].append(image)
                seen.add(image["url"])
        for image in plan.get("replacement_images", []):
            if image["url"] not in seen:
                target["images"].append(copy.deepcopy(image))
                seen.add(image["url"])
        target["preferred_image"] = next(index for index, image in enumerate(target["images"])
                                         if image["url"] == preferred)
        for field, key in (("models", "asset_file"), ("sources", "url"),
                           ("videos", "youtube_id"), ("editorial_features", "id")):
            combined = []
            known = set()
            for original in (old_target, old_source):
                for item in original.get(field, []):
                    if item.get(key) in known:
                        continue
                    item = copy.deepcopy(item)
                    if field == "sources" and item.get("url") in plan.get("excluded_source_urls", []):
                        continue
                    if field == "videos" and isinstance(item.get("story_paragraph"), int) and item["story_paragraph"] >= 0:
                        item["story_paragraph"] = maps[original["id"]].get(item["story_paragraph"], -1)
                    combined.append(item)
                    known.add(item.get(key))
            target[field] = combined
        for model in target["models"]:
            caption = plan.get("model_captions", {}).get(model.get("asset_file"))
            if caption:
                model["display_caption"] = caption
        for source_record in plan.get("additional_sources", []):
            if not any(row.get("url") == source_record["url"] for row in target["sources"]):
                target["sources"].append(copy.deepcopy(source_record))
        # A merged owner must not lose optional soundtrack rooms or experiences.
        for field in ("soundtrack", "soundtrack_rooms", "experience", "experiences"):
            if source.get(field) and not target.get(field):
                target[field] = copy.deepcopy(source[field])
        target["related_ids"] = list(dict.fromkeys(old_target.get("related_ids", []) + old_source.get("related_ids", [])))
        target["tags"] = list(dict.fromkeys(old_target.get("tags", []) + old_source.get("tags", [])))
        target["editorial_credit"] = " ".join(dict.fromkeys(text for text in
            (old_target.get("editorial_credit", ""), old_source.get("editorial_credit", "")) if text))
        target["explicit_story_media_only"] = True
        provenance = target.setdefault("provenance", {})
        provenance["hardware_family_consolidation"] = dict(
            candidate_sha256=candidate_sha256, aliases=[canonical, retired],
            # Provenance is a JSON document. Keep its map keys identical in
            # memory and after saving so later exact-owner reviews compare
            # the same source record without weakening their guards.
            source_paragraph_maps={owner: {str(index): value for index, value in mapping.items()}
                                   for owner, mapping in maps.items()},
            prior_records=[old_target, old_source],
            paragraph_edits=copy.deepcopy(plan["paragraphs"]),
            excluded_image_urls=copy.deepcopy(plan.get("excluded_image_urls", [])),
            excluded_source_urls=copy.deepcopy(plan.get("excluded_source_urls", [])),
            policy="One chronology stop for one hardware family; original designs and later regional revisions remain in its story.")
        results.append(dict(canonical_id=canonical, retired_id=retired,
            paragraphs=len(target["body"]), feature_paragraphs=sum(len(feature.get("body", [])) for feature in target["editorial_features"]),
            images=len(target["images"]), models=[model["asset_file"] for model in target["models"]]))
    retired_ids = set(aliases)
    entries[:] = [entry for entry in entries if entry["id"] not in retired_ids]
    changes = redirect_references(entries, aliases)
    for entry in entries:
        entry["related_ids"] = [identifier for identifier in entry.get("related_ids", []) if identifier != entry["id"]]
    return dict(status="PASS", candidate_sha256=candidate_sha256, aliases=aliases,
                consolidations=results, rewritten_references=changes)


def apply(entries, root):
    root = Path(root)
    candidate = root / FOLDER / "family-consolidation-candidate.json"
    review = root / FOLDER / "family-consolidation-root-review.json"
    if not candidate.is_file() or not review.is_file():
        return dict(status="not_admitted", aliases={})
    receipt = json.loads(review.read_text(encoding="utf8"))
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if receipt.get("status") != "PASS":
        return dict(status="not_admitted", aliases={})
    if receipt.get("candidate_sha256") != digest:
        raise ValueError("Hardware consolidation changed after review")
    return project(entries, json.loads(candidate.read_text(encoding="utf8")), digest)
