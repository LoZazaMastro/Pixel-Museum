"""Project the authoring collection into the data consumed by the native app.

Research leads, audit receipts and duplicate provenance snapshots stay in the
authoring collection. Display text, media identity, source citations and rights
travel with the app; the complete media/source inventory also remains in credits.
This is a packaging transform, not an editorial filter or image downgrade.
"""
from __future__ import annotations

import copy
import hashlib
import json

ENTRY_FIELDS = frozenset((
    "id", "kind", "title", "subtitle", "summary", "year", "era_id", "layout", "culture_category",
    "event_semantics", "editorial_credit", "factual_note", "linked_exhibit_id", "story_entry_id",
    "body", "tags", "related_ids", "story_headings", "featured", "calendar_only", "preferred_image",
    "calendar", "date", "images", "videos", "soundtrack", "soundtrack_rooms", "models", "sources",
    "editorial_features", "editorial_mode", "language", "explicit_story_media_only", "preserve_unillustrated_opening",
    "source_identity_correction", "calendar_link_provenance", "date_provenance",
    "canonical_reference_restoration", "disclosed_english_correction",
    "canonical_narrative_enrichment",
    "identity_media_admission",
    "source_edition_restoration", "editorial_revision",
))
IMAGE_FIELDS = frozenset((
    "url", "dark_url", "source_page", "title", "caption", "creator", "license", "license_url",
    "credit", "story_paragraph", "width", "height", "native_long_edge",
    "rights_basis", "rights_review", "edition_note", "representation_note",
    "attribution", "modifications_note",
    "cover_art", "cover_role", "kind", "role",
))
VIDEO_FIELDS = frozenset((
    "youtube_id", "url", "title", "caption", "creator", "source_page",
    "license", "license_url", "credit", "edition_note", "representation_note",
    "official_uploader_verified", "channel_url", "poster_url", "start_seconds", "end_seconds", "story_paragraph",
))

# These fields are already ignored by Catalog::parse. Keep their full records
# in authoring/Credits inventories, while excluding duplicated runtime metadata.
# Do not remove media URLs, source citations, credits or cue bounds here.
UNUSED_ENTRY_METADATA = frozenset((
    "editorial_mode", "language", "source_identity_correction",
    "calendar_link_provenance", "date_provenance",
    "canonical_reference_restoration", "disclosed_english_correction",
    "identity_media_admission", "source_edition_restoration", "editorial_revision",
))
UNUSED_SOUNDTRACK_METADATA = frozenset((
    "album_completeness", "recording_collection_scope", "independent_review_receipt",
    "completeness", "coverage_status", "full_album_collection", "music_kind",
    "expected_album_tracks", "id",
))
SOUNDTRACK_TRACK_FIELDS = VIDEO_FIELDS - {"channel_url", "official_uploader_verified"}


def compact_ignored_metadata(document):
    """Compact an owned runtime projection, preserving every parsed value.

    Native C++ field snapshots and complete actual StoryCard compositions are
    the acceptance checks; this helper is not a replacement for those tests.
    """
    for entry in document["entries"]:
        for key in UNUSED_ENTRY_METADATA:
            entry.pop(key, None)
        if isinstance(entry.get("canonical_narrative_enrichment"), dict):
            # The native reader uses this object's presence only as an implicit
            # true media-policy flag. Its existing explicit flag is equivalent,
            # including legacy objects that contain explicitfalse alongside it.
            entry["explicit_story_media_only"] = True
            entry.pop("canonical_narrative_enrichment")
        rooms = ([entry["soundtrack"]] if entry.get("soundtrack") else [])
        rooms += entry.get("soundtrack_rooms", [])
        for room in rooms:
            for key in UNUSED_SOUNDTRACK_METADATA:
                room.pop(key, None)
            for track in room.get("tracks", []):
                track.pop("channel_url", None)
                track.pop("official_uploader_verified", None)
    return document


def select(row, fields):
    return {key: copy.deepcopy(value) for key, value in row.items() if key in fields}


def images(rows):
    return [select(row, IMAGE_FIELDS) for row in (rows or [])]


def videos(rows):
    return [select(row, VIDEO_FIELDS) for row in (rows or [])]


def project(catalog, source_sha256=None):
    result = {key: copy.deepcopy(catalog[key]) for key in
              ("title", "subtitle", "remote_catalog_url", "initial_id", "edition", "eras", "entry_aliases")
              if key in catalog}
    result["entries"] = []
    for original in catalog["entries"]:
        entry = select(original, ENTRY_FIELDS)
        entry["images"] = images(original.get("images", []))
        entry["videos"] = videos(original.get("videos", []))
        if original.get("soundtrack"):
            entry["soundtrack"] = copy.deepcopy(original["soundtrack"])
            entry["soundtrack"]["tracks"] = videos(original["soundtrack"].get("tracks", []))
        for room in entry.get("soundtrack_rooms", []):
            room["tracks"] = videos(room.get("tracks", []))
        for feature in entry.get("editorial_features", []):
            feature["images"] = images(feature.get("images", []))
        result["entries"].append(entry)
    if source_sha256:
        result["source_catalog_sha256"] = source_sha256
    return compact_ignored_metadata(result)


def encoded(document):
    return (json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def receipt(original, runtime, original_bytes):
    return {
        "schema_version": 1,
        "authoring_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "runtime_sha256": hashlib.sha256(encoded(runtime)).hexdigest(),
        "authoring_bytes": len(original_bytes),
        "compact_authoring_bytes": len(encoded(original)),
        "runtime_bytes": len(encoded(runtime)),
        "entries": len(runtime["entries"]),
        "narrative_paragraphs": sum(len(entry.get("body", [])) + sum(
            len(feature.get("body", [])) for feature in entry.get("editorial_features", []))
            for entry in runtime["entries"]),
        "remote_images": sum(len(entry.get("images", [])) + sum(
            len(feature.get("images", [])) for feature in entry.get("editorial_features", []))
            for entry in runtime["entries"]),
        "text_media_or_source_selections_changed": False,
        "research_and_verification_receipts_retained_in_authoring": True,
        "physical_ps5_parse_timing_verified": False,
    }
