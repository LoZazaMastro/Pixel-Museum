"""Bind partial translations to the exact English owner shipped in a package."""
import hashlib
import json

TEXT_FIELDS = ("title", "subtitle", "summary", "body", "story_headings")


def source_fields(owner):
    return {key: owner.get(key, [] if key in ("body", "story_headings") else "")
            for key in TEXT_FIELDS}


def source_hash(owner):
    value = json.dumps(source_fields(owner), ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def project(document, catalogs, language):
    assert document.get("locale") == language
    owners = {}
    for catalog in catalogs:
        for entry in catalog.get("entries", []):
            for owner in (entry, *entry.get("editorial_features", [])):
                assert owner["id"] not in owners, "Duplicate translation owner"
                owners[owner["id"]] = owner
    result = {"locale": language, "entries": {}}
    audit = {"locale": language, "included": [], "stale": [], "not_in_package": []}
    for identity, translation in document.get("entries", {}).items():
        owner = owners.get(identity)
        if owner is None:
            audit["not_in_package"].append(identity)
            continue
        provenance = translation.get("provenance", {})
        if provenance.get("source_fields_sha256") != source_hash(owner):
            audit["stale"].append(identity)
            continue
        localized = {}
        for field in (*TEXT_FIELDS, "editorial_credit"):
            if field not in translation:
                continue
            value = translation[field]
            if field in ("body", "story_headings"):
                assert isinstance(value, list) and len(value) == len(owner.get(field, [])), (identity, field)
                assert all(isinstance(item, str) and "\0" not in item and len(item.encode("utf-8")) <= 65536 for item in value)
            else:
                assert isinstance(value, str) and "\0" not in value and len(value.encode("utf-8")) <= 16384
            localized[field] = value
        if localized:
            result["entries"][identity] = localized
            audit["included"].append(identity)
    return result, audit
