"""Assemble authored stories and attributed reference entries without losing provenance.

Images and films stay at their publisher URLs. Licensed 3D models are bundled
separately; the runtime catalogue records their paths and individual provenance.
"""
from __future__ import annotations
import collections
import copy
import hashlib
import json
import re
import runpy
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent

def read(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def key(value):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower())

def overview(value):
    """Use a whole introductory sentence, with the original retained in the story."""
    abbreviations={"bros.","dr.","mr.","mrs.","ms.","jr.","sr.","st.","prof.","inc.","ltd.","no.","vol."}
    result=value
    for boundary in re.finditer(r"(?<=[.!?])\s+(?=[A-Z0-9])",value):
        candidate=value[:boundary.start()]
        token=candidate.rsplit(None,1)[-1].rstrip('\"\')]}')
        if token.lower() in abbreviations or re.fullmatch(r"(?:[A-Za-z]\.)+",token):continue
        result=candidate;break
    # Source copy with exceptionally long sentences uses its existing subtitle
    # instead; no mid-word clipping or artificial ellipsis is introduced.
    return result

def assemble():
    authored = runpy.run_path(str(ROOT / "compile_catalog.py"), run_name="museum_authoring")
    catalog = copy.deepcopy(authored["catalog"])
    entries = catalog["entries"]
    media = read(ROOT / "media.json", {})
    revisions = read(ROOT / "narrative-revisions.json", {})
    sources = read(ROOT / "narrative-revision-sources.json", {}).get("entries", {})
    for entry in entries:
        for field in ("images", "videos", "models"):
            entry[field] = copy.deepcopy(media.get(entry["id"], {}).get(field, []))
        entry.update(copy.deepcopy(revisions.get(entry["id"], {})))
        known = {s["url"] for s in entry["sources"]}
        entry["sources"].extend(copy.deepcopy(s) for s in sources.get(entry["id"], []) if s["url"] not in known)
        entry["editorial_credit"] = "Original exhibition text for Pixel Museum."
        entry["editorial_mode"] = "curated_story"
    duplicates = []
    ids = {e["id"] for e in entries}
    titles = {(key(e["title"]), e["year"]) for e in entries}
    for filename, mode in (("origins-additions.json", "curated_story"),
                           ("study-exhibit-additions.json", "curated_story"),
                           ("playhub-museum-candidates.json", "playhub_story"),
                           ("wikipedia-ready.json", "reference"),
                           ("wikipedia-early-ready.json", "reference")):
        incoming = read(ROOT / "expansion" / filename, {})
        for original in incoming.get("entries", []):
            title_key = (key(original["title"]), original["year"])
            if original["id"] in ids or title_key in titles:
                duplicates.append({"id": original["id"], "title": original["title"], "source": filename})
                continue
            entry = copy.deepcopy(original)
            entry["editorial_mode"] = mode
            if mode == "playhub_story":
                entry["editorial_credit"] = "Adapted from the Playhub historical collection. External historical references are listed below."
            elif mode == "curated_story":
                entry["editorial_credit"] = "Original exhibition text for Pixel Museum."
            full = entry.get("summary", "")
            if len(full) > 240:
                lead = overview(full)
                entry["summary"] = lead if len(lead) <= 320 else entry.get("subtitle", "") or entry["title"]
                if full not in entry.get("body", []):
                    entry["body"].insert(0, full)
            for field in ("images", "videos", "models", "tags", "related_ids", "sources", "body"):
                entry.setdefault(field, [])
            entries.append(entry); ids.add(entry["id"]); titles.add(title_key)
    # Verified source meshes replace earlier prototype objects. Keep assembly
    # selections explicit: invisible PCB and accessories are not silhouette detail.
    models = {}
    for row in read(ROOT / "model-candidates-curation.json", {}).get("candidates", []):
        if row.get("status") != "verified_downloadable_candidate": continue
        english_titles={"atari-vcs":"Atari 2600 / Heavy Sixer", "famicom":"Nintendo Family Computer", "playstation":"Sony PlayStation / SCPH-1000", "playstation-2":"Sony PlayStation 2", "wii":"Nintendo Wii"}
        models[row["exhibit_id"]] = dict(url=row["url"], title=english_titles.get(row["exhibit_id"],row["title"]),
            source_page=row["source_page"], creator=row["creator"], license=row["license"],
            license_url=row["license_url"], credit=f'{row["creator"]} / Open Console CAD / {row["license"]}',
            include_groups=row.get("runtime_recommendation", {}).get("keep_assembly_groups", []), initial_tilt=.4, initial_angle=0, source_z_up=True)
    for row in read(PROJECT / "docs/research/model-candidates-renderer.json", {}).get("candidates", []):
        if not row.get("actual_render_verified") or not row.get("direct_url"): continue
        exhibit_id = {"xbox": "xbox-halo"}.get(row["entry_id"], row["entry_id"])
        models[exhibit_id] = dict(url=row["direct_url"], title=row["title"],
            source_page=row["source_page"], creator=row["creator"], license=row["license"],
            license_url=row["license_url"], credit=f'{row["creator"]} / {row["license"]}',
            modifications_note=row.get("modifications_note", ""), include_groups=row.get("include_groups", []),
            initial_tilt=row.get("initial_tilt", .8 if exhibit_id == "zx-spectrum" else .13 if exhibit_id == "game-boy" else .38),
            initial_angle=row.get("initial_angle", row.get("initial_yaw", 0)), source_z_up=row.get("source_z_up", False))
    console_png_policy = runpy.run_path(str(ROOT / 'expansion/user_console_png_policy.py'))
    bundled = console_png_policy['authoring_models'](PROJECT)
    approved_bundled = {model["exhibit_id"]: {k:v for k,v in model.items() if k != "exhibit_id"} for model in bundled}
    # The user selected this exact original photograph instead of a 3D N64.
    # Validate it before admitting the otherwise model-gated hardware owner.
    n64_user_png = PROJECT / 'assets/images/user-nintendo-64-console-transparent.png'
    if hashlib.sha256(n64_user_png.read_bytes()).hexdigest() != '62c581ce8206acee885cee7b6821ef694dd699dc1eb9837b24bbc58026e83e64':
        raise ValueError('Nintendo 64 user-selected original photograph changed')
    for model in bundled:
        models[model["exhibit_id"]] = {k:v for k,v in model.items() if k != "exhibit_id"}
    # A reviewed complete new hardware article supersedes its old unillustrated
    # model-gated placeholder. Its guarded late admission validates all sources.
    complete_plan = read(ROOT / "expansion/museum-complete-new-entries-reviewed.json", {})
    complete_hardware_ids = {identifier for batch in complete_plan.get("batches", [])
        for identifier in batch.get("approved_entry_ids", [])} if complete_plan.get("publication_status") == "independently_reviewed" else set()
    for entry in read(ROOT / "expansion/hardware-additions.json", {}).get("entries", []):
        if (entry["id"] not in models and entry["id"] != 'nintendo-64') or entry["id"] in ids or entry["id"] in complete_hardware_ids:
            continue
        entry = copy.deepcopy(entry)
        entry["editorial_credit"] = "Original exhibition text for Pixel Museum."
        entry["editorial_mode"] = "curated_story"
        entries.append(entry); ids.add(entry["id"])
    for original in read(ROOT / "expansion/calendar-features.json", {}).get("entries", []):
        if original["id"] in ids:continue
        entry=copy.deepcopy(original);entry["editorial_mode"]="calendar_feature"
        if entry.get("body"):entry["summary"]=overview(entry["body"][0])
        for field in ("images","videos","models","tags","related_ids","sources","body"):entry.setdefault(field,[])
        entries.append(entry);ids.add(entry["id"])
    archive_records = read(ROOT / "expansion/archive-bibliography-curation.json", {}).get("records", [])
    story_headings = read(ROOT / "story-headings.json", {})
    illustrations = {row["entry_id"]:row.get("images", []) for row in read(ROOT / "expansion/illustration-additions.json", {}).get("entries", [])}
    quality = read(ROOT / "expansion/image-quality-upgrades.json", {})
    image_overrides = {(row["entry_id"],row["match_url"]):row for row in quality.get("overrides", [])}
    quality_additions = {row["entry_id"]:row.get("images", []) for row in quality.get("additions", [])}
    recovered_media = collections.defaultdict(list)
    for filename in ("playhub-illustration-additions.json", "publisher-media-additions.json", "steam-media-additions.json", "media-wikidata-steam-additions.json"):
        for row in read(ROOT / "expansion" / filename, {}).get("entries", []):
            recovered_media[row["entry_id"]].extend(copy.deepcopy(row.get("images", [])))
    image_identity_reviews = {row["entry_id"]: row for row in read(ROOT / "expansion/image-identity-corrections.json", {}).get("entries", [])}
    hardware_corrections = {row["id"]: row for row in read(ROOT / "expansion/hardware-identity-corrections.json", {}).get("overrides", [])}
    for entry in entries:
        added_images=illustrations.get(entry["id"], [])
        if added_images:
            images=[];seen_urls=set()
            for image in added_images+entry.get("images", []):
                if image.get("url") and image["url"] not in seen_urls:
                    images.append(copy.deepcopy(image));seen_urls.add(image["url"])
            entry["images"]=images
        reviewed_images=[]
        for image in entry.get("images", []):
            review=image_overrides.get((entry["id"],image.get("url")))
            if review and review["action"]=="remove":continue
            reviewed_images.append(copy.deepcopy(review["image"] if review and review["action"]=="replace" else image))
        reviewed_images=copy.deepcopy(quality_additions.get(entry["id"], []))+reviewed_images
        entry["images"]=[];reviewed_urls=set()
        for image in reviewed_images:
            # Originals remain in the research files. Only sources with a
            # measured, genuinely useful pixel size enter the display catalogue.
            if max(image.get("width",0),image.get("height",0))<1600:continue
            if image.get("url") and image["url"] not in reviewed_urls:
                entry["images"].append(image);reviewed_urls.add(image["url"])
        identity_review=image_identity_reviews.get(entry["id"], {})
        rejected_urls=set(identity_review.get("remove_urls", []))
        entry["images"]=[image for image in entry["images"] if image.get("url") not in rejected_urls]
        enriched=[];enriched_urls=set()
        for image in recovered_media.get(entry["id"], [])+entry["images"]:
            if image.get("url") and image["url"] not in enriched_urls:
                enriched.append(image);enriched_urls.add(image["url"])
        entry["images"]=enriched
        if identity_review:entry["image_identity_review"]=copy.deepcopy(identity_review)
        entry["story_headings"] = story_headings.get(entry["id"], entry.get("story_headings", []))
        if entry["id"] in models and models[entry["id"]].get("asset_file"):
            entry["models"] = [models[entry["id"]]]
        else:
            entry["models"] = []
        hardware_review = hardware_corrections.get(entry["id"])
        if hardware_review:
            entry["kind"] = hardware_review["kind"]
            model_id = hardware_review.get("approved_model_id")
            if model_id:
                if model_id not in approved_bundled:
                    raise ValueError("Hardware alias requires an approved bundled model: " + entry["id"])
                entry["models"] = [copy.deepcopy(approved_bundled[model_id])]
                entry["models"][0]["title"] = hardware_review.get("model_caption", entry["models"][0]["title"])
                entry["models"][0]["representation_note"] = hardware_review["representation_note"]
            else:
                entry["models"] = []
            entry["hardware_identity_review"] = copy.deepcopy(hardware_review)
            entry["factual_note"] = (entry.get("factual_note", "") + " " + hardware_review["representation_note"]).strip()
        attribution = entry.get("attribution", {})
        if isinstance(attribution, dict) and attribution.get("text"):
            entry["editorial_credit"] = attribution["text"]
        known = {s["url"] for s in entry["sources"]}
        for record in archive_records:
            if not any(key(subject)==key(entry["title"]) for subject in record.get("related_subjects", [])):
                continue
            if record["url"] in known: continue
            entry["sources"].append(dict(title=record["title"], url=record["url"],
                publisher=record["institution"], attribution=record.get("rights", "")))
            known.add(record["url"])
    # One chronology carries the full reviewed writing. Distinct historical
    # events retain their own stops, even when they share the same hardware.
    calendar_join = runpy.run_path(str(ROOT / "expansion/integrate_calendar.py"))
    template_revisions, template_originals = calendar_join["apply_revisions"](entries,
        [read(ROOT / ("expansion/calendar-template-revisions-" + agent + ".json"), {})
         for agent in ("soundtrack", "curation", "native")],
        read(ROOT / "expansion/calendar-template-review.json", {}))
    write(ROOT / "calendar-template-originals.json", {"schema_version": 1,
        "note": "Complete scheduled records before researched replacement of inherited template prose. Original writing, source selection, dates, attribution and media remain preserved here.",
        "entries": template_originals})
    identity_join = runpy.run_path(str(ROOT / "expansion/integrate_calendar_identities.py"))
    identity_audit = identity_join["integrate"](entries,
        read(ROOT / "expansion/calendar-identity-corrections-02.json", {}))
    write(ROOT / "calendar-identity-integration-audit.json", identity_audit)
    calendar_audit, original_editorial = calendar_join["integrate"](
        entries, read(ROOT / "expansion/date-corrections.json", {}))
    calendar_audit["researched_template_revisions"] = template_revisions
    write(ROOT / "calendar-editorial-originals.json", {"schema_version": 1,
        "note": "Canonical records before calendar-story enrichment. Original prose, attribution, dates and media are retained for authoring provenance.",
        "entries": original_editorial})
    write(ROOT / "calendar-integration-audit.json", calendar_audit)
    locale_join=runpy.run_path(str(ROOT / "expansion/reuse_playhub_locales.py"))
    locale_audit=locale_join["integrate"](entries,ROOT)
    calendar_audit["source_english_editions_restored"]=locale_audit["restored_source_english_editions"]
    calendar_audit["published_source_sections"]=locale_audit["original_english_sections"]
    write(ROOT / "calendar-integration-audit.json", calendar_audit)
    identity03_join = runpy.run_path(str(ROOT / "expansion/integrate_calendar_identities_03.py"))
    identity03_document = read(ROOT / "expansion/calendar-identity-corrections-03.json", {})
    identity03_audit = identity03_join["integrate"](entries, identity03_document)
    write(ROOT / "calendar-identity-integration-audit-03.json", identity03_audit)
    original_locale_documents = {path.stem: read(path, {}) for path in (ROOT / "locales").glob("*.json")}
    identity03_locale_audit = identity03_join["migrate_locale_overlays"](original_locale_documents, identity03_document)
    for language, document in original_locale_documents.items():
        write(ROOT / "locales" / (language + ".json"), document)
    write(ROOT / "calendar-identity-locale-audit-03.json", identity03_locale_audit)
    prose05_join = runpy.run_path(str(ROOT / "expansion/integrate_calendar_prose_05.py"))
    prose05_document = prose05_join["checked_document"](ROOT / "expansion/calendar-prose-restorations-05.json")
    prose05_audit = prose05_join["integrate"](entries, original_locale_documents, prose05_document)
    for language, document in original_locale_documents.items():
        write(ROOT / "locales" / (language + ".json"), document)
    write(ROOT / "calendar-prose-restoration-audit-05.json", prose05_audit)
    event_join = runpy.run_path(str(ROOT / "expansion/integrate_calendar_events.py"))
    event_audit = event_join["integrate"](entries, ROOT / "expansion")
    write(ROOT / "calendar-event-integration-audit.json", event_audit)
    prose_join=runpy.run_path(str(ROOT / "expansion/apply_reference_prose.py"))
    prose_audit=prose_join["apply"](entries,read(ROOT / "expansion/reference-prose-fixes.json", {}))
    write(ROOT / "reference-prose-integration-audit.json",prose_audit)
    headings_join=runpy.run_path(str(ROOT / "expansion/apply_reference_headings.py"))
    heading_batches = [read(ROOT / "expansion" / filename, {}) for filename in
        ("reference-heading-additions.json", "reference-heading-additions-02.json", "reference-heading-additions-03.json", "reference-heading-additions-04.json", "reference-heading-additions-05.json")]
    headings_audit=headings_join["apply"](entries,{"entries": [row for batch in heading_batches
        for row in batch.get("entries", [])]})
    write(ROOT / "reference-heading-integration-audit.json",headings_audit)
    soundtrack_join = runpy.run_path(str(ROOT / "expansion/integrate_soundtracks.py"))
    soundtrack_audit = soundtrack_join["integrate"](entries,
        read(ROOT / "expansion/soundtrack-selections.json", {}))
    write(ROOT / "soundtrack-integration-audit.json", soundtrack_audit)
    # New authored features never replace original Playhub bodies or locale
    # sidecars. Existing subjects receive compact connected narrative blocks;
    # only the six explicitly reviewed distinct subjects become new stops.
    priority_join = runpy.run_path(str(ROOT / "expansion/integrate_priority_features.py"))
    priority_audit = priority_join["integrate"](entries,
        priority_join["load_documents"](ROOT / "expansion"),
        catalog["eras"], priority_join["load_media"](ROOT / "expansion"))
    write(ROOT / "priority-feature-integration-audit.json", priority_audit)
    collection_media_join = runpy.run_path(str(ROOT / "expansion/integrate_collection_media.py"))
    collection_media_audit = collection_media_join["integrate"](entries, ROOT / "expansion")
    write(ROOT / "collection-media-integration-audit.json", collection_media_audit)
    # Validate old paragraph-bound acquisition batches before replacing their
    # parent prose. Archive exact originals and remove only stale parent links;
    # independently attached features retain their own bodies and media.
    narrative06_join = runpy.run_path(str(ROOT / "expansion/integrate_calendar_narratives_06.py"))
    narrative06_document = narrative06_join["checked_document"](ROOT.parent)
    narrative06_audit = narrative06_join["integrate"](entries, original_locale_documents,
                                                    narrative06_document)
    for language, document in original_locale_documents.items():
        write(ROOT / "locales" / (language + ".json"), document)
    write(ROOT / "calendar-canonical-narratives-audit-06.json", narrative06_audit)
    narrative07_join = runpy.run_path(str(ROOT / "expansion/integrate_calendar_narratives_07.py"))
    narrative07_document = narrative07_join["checked_document"](ROOT.parent)
    narrative07_audit = narrative07_join["integrate"](entries, original_locale_documents,
                                                    narrative07_document)
    for language, document in original_locale_documents.items():
        write(ROOT / "locales" / (language + ".json"), document)
    write(ROOT / "calendar-canonical-narratives-audit-07.json", narrative07_audit)
    legacy_join = runpy.run_path(str(ROOT / "expansion/integrate_legacy_media_review.py"))
    legacy_audit = legacy_join["integrate"](entries, ROOT.parent)
    write(ROOT / "legacy-image-visual-integration-audit.json", legacy_audit)
    replacements_join = runpy.run_path(str(ROOT / "expansion/integrate_legacy_media_replacements.py"))
    replacements_audit = replacements_join["integrate"](entries, ROOT.parent, legacy_audit)
    write(ROOT / "legacy-media-replacement-integration-audit.json", replacements_audit)
    recent_six_join = runpy.run_path(str(ROOT / "expansion/integrate_recent_six_reviewed.py"))
    recent_six_audit = recent_six_join["integrate"](entries, ROOT.parent)
    write(ROOT / "recent-six-reviewed-integration-audit.json", recent_six_audit)
    requested_games_join = runpy.run_path(str(ROOT / "expansion/integrate_reviewed_requested_games.py"))
    requested_games_audit = requested_games_join["integrate"](entries, ROOT.parent)
    write(ROOT / "requested-reviewed-games-integration-audit.json", requested_games_audit)
    switch_games_join = runpy.run_path(str(ROOT / "expansion/reviewed_switch_game_additions.py"))
    switch_games_audit = switch_games_join["apply"](entries, ROOT.parent)
    write(ROOT / "switch-reviewed-games-integration-audit.json", switch_games_audit)
    museum_join = runpy.run_path(str(ROOT / "expansion/apply_museum_revision.py"))
    museum_audit = museum_join["apply"](entries)
    write(ROOT / "museum-revision-audit.json", museum_audit)
    complete_themes_join = runpy.run_path(str(ROOT / "expansion/integrate_playhub_theme_complete.py"))
    complete_themes_audit = complete_themes_join["integrate"](entries, ROOT.parent)
    write(ROOT / "playhub-complete-theme-integration-audit.json", complete_themes_audit)
    semantic_themes_join = runpy.run_path(str(ROOT / "expansion/integrate_playhub_semantic_restorations.py"))
    semantic_themes_audit = semantic_themes_join["integrate"](entries, ROOT.parent)
    write(ROOT / "playhub-semantic-theme-integration-audit.json", semantic_themes_audit)
    reviewed_hardware_join = runpy.run_path(str(ROOT / "expansion/integrate_reviewed_hardware_stories.py"))
    reviewed_hardware_audit = reviewed_hardware_join["integrate"](entries, ROOT.parent)
    write(ROOT / "reviewed-hardware-story-integration-audit.json", reviewed_hardware_audit)
    ps5_hardware_join = runpy.run_path(str(ROOT / "expansion/ps5_illustrated_hardware.py"))
    ps5_hardware_audit = ps5_hardware_join["apply"](entries, ROOT.parent)
    write(ROOT / "ps5-illustrated-hardware-integration-audit.json", ps5_hardware_audit)
    story_illustrations_join = runpy.run_path(str(ROOT / "expansion/reviewed_story_illustrations.py"))
    story_illustrations_join["apply"](entries, ROOT.parent)
    c64_media_join = runpy.run_path(str(ROOT / "expansion/c64_reviewed_media.py"))
    c64_media_audit = c64_media_join["apply"](entries, ROOT.parent)
    write(ROOT / "c64-reviewed-media-integration-audit.json", c64_media_audit)
    clarity_join = runpy.run_path(str(ROOT / "expansion/clarify_playhub_narrative.py"))
    clarity_audit = clarity_join["apply"](entries, ROOT.parent)
    write(ROOT / "playhub-clarity-integration-audit.json", clarity_audit)
    clarity_pass2_audit = clarity_join["apply"](entries, ROOT.parent,
        "content/expansion/museum-playhub-clarity-pass2-candidate.json",
        "build/research/playhub-semantic-coverage/wiki-clarity/pass2-independent-review.json")
    write(ROOT / "playhub-clarity-pass2-integration-audit.json", clarity_pass2_audit)
    clarity_pass3_audit = clarity_join["apply"](entries, ROOT.parent,
        "content/expansion/museum-playhub-clarity-pass3-candidate.json",
        "build/research/playhub-semantic-coverage/wiki-clarity/pass3-independent-review.json")
    write(ROOT / "playhub-clarity-pass3-integration-audit.json", clarity_pass3_audit)
    clarity_pass4_audit = clarity_join["apply"](entries, ROOT.parent,
        "content/expansion/museum-playhub-clarity-pass4-candidate.json",
        "build/research/playhub-semantic-coverage/wiki-clarity/pass4-independent-review.json")
    write(ROOT / "playhub-clarity-pass4-integration-audit.json", clarity_pass4_audit)
    clarity_pass5_audit = clarity_join["apply"](entries, ROOT.parent,
        "content/expansion/museum-playhub-clarity-pass5-candidate.json",
        "build/research/playhub-semantic-coverage/wiki-clarity/pass5-root-independent-review.json")
    write(ROOT / "playhub-clarity-pass5-integration-audit.json", clarity_pass5_audit)
    classic_clarity_audit = clarity_join["apply"](entries, ROOT.parent,
        "build/research/playhub-semantic-coverage/wiki-clarity/model-agent-five/candidate.json",
        "build/research/playhub-semantic-coverage/wiki-clarity/model-agent-five/root-independent-review.json")
    write(ROOT / "playhub-classic-five-clarity-integration-audit.json", classic_clarity_audit)
    calendar_introductions_audit = clarity_join["apply"](entries, ROOT.parent,
        "content/expansion/museum-clear-calendar-introductions-candidate.json",
        "build/research/playhub-semantic-coverage/wiki-clarity/clear-calendar-introductions-independent-review.json")
    write(ROOT / "clear-calendar-introductions-integration-audit.json", calendar_introductions_audit)
    calendar_events_audit = clarity_join["apply"](entries, ROOT.parent,
        "content/expansion/museum-calendar-event-removal-candidate.json",
        "build/research/playhub-semantic-coverage/calendar-event-removal/independent-review.json")
    write(ROOT / "calendar-event-removal-integration-audit.json", calendar_events_audit)
    region_caveats_audit = clarity_join["apply"](entries, ROOT.parent,
        "content/expansion/museum-region-caveat-copyedits-candidate.json",
        "build/research/playhub-semantic-coverage/region-caveat-cleanup/root-independent-review.json")
    write(ROOT / "region-caveat-copyedits-integration-audit.json", region_caveats_audit)
    final_copyedits_audit = clarity_join["apply"](entries, ROOT.parent,
        "content/expansion/museum-clarity-copyedits-psp-phantom-candidate.json",
        "build/research/playhub-semantic-coverage/wiki-clarity/final-copyedits-root-independent-review.json")
    write(ROOT / "playhub-final-copyedits-integration-audit.json", final_copyedits_audit)
    template_tails_join = runpy.run_path(str(ROOT / "expansion/remove_reviewed_template_tails.py"))
    template_tails_audit = template_tails_join["apply"](entries, ROOT.parent)
    write(ROOT / "reviewed-template-tails-integration-audit.json", template_tails_audit)
    clear_hardware_audit = clarity_join["apply"](entries, ROOT.parent,
        "build/research/hardware-release-consolidation/clear-hardware-introductions-candidate.json",
        "build/research/hardware-release-consolidation/clear-introductions-root-review.json")
    write(ROOT / "clear-hardware-introductions-integration-audit.json", clear_hardware_audit)
    hardware_family_join = runpy.run_path(str(ROOT / "expansion/hardware_family_consolidation.py"))
    hardware_family_audit = hardware_family_join["apply"](entries, ROOT.parent)
    write(ROOT / "hardware-family-consolidation-integration-audit.json", hardware_family_audit)
    catalog["entry_aliases"] = hardware_family_join["navigation_aliases"](entries,
        catalog.get("entry_aliases", {}), museum_audit.get("aliases", {}), hardware_family_audit.get("aliases", {}))
    hardware_family_join["redirect_references"](entries, catalog["entry_aliases"])
    hardware_subject_media_join = runpy.run_path(str(ROOT / "expansion/hardware_subject_media.py"))
    hardware_subject_media_audit = hardware_subject_media_join["apply"](entries, ROOT.parent)
    write(ROOT / "hardware-subject-media-integration-audit.json", hardware_subject_media_audit)
    getaway_production_join = runpy.run_path(str(ROOT / "expansion/getaway_reviewed_production_story.py"))
    getaway_production_audit = getaway_production_join["apply"](entries, ROOT.parent)
    write(ROOT / "getaway-reviewed-production-integration-audit.json", getaway_production_audit)
    fh6_narrative_media_join = runpy.run_path(str(ROOT / "expansion/fh6_reviewed_narrative_media.py"))
    fh6_narrative_media_audit = fh6_narrative_media_join["apply"](entries, ROOT.parent)
    write(ROOT / "fh6-reviewed-narrative-media-integration-audit.json", fh6_narrative_media_audit)
    automodellista_media_join = runpy.run_path(str(ROOT / "expansion/automodellista_reviewed_narrative_media.py"))
    automodellista_media_audit = automodellista_media_join["apply"](entries, ROOT.parent)
    write(ROOT / "automodellista-reviewed-narrative-media-integration-audit.json", automodellista_media_audit)
    preservation_media_join = runpy.run_path(str(ROOT / "expansion/preservation_reviewed_feature_media.py"))
    preservation_media_audit = preservation_media_join["apply"](entries, ROOT.parent)
    write(ROOT / "preservation-reviewed-feature-media-integration-audit.json", preservation_media_audit)
    preservation_store_join = runpy.run_path(str(ROOT / "expansion/preservation_store_reviewed_feature_media.py"))
    preservation_store_audit = preservation_store_join["apply"](entries, ROOT.parent)
    write(ROOT / "preservation-reviewed-storefront-media-integration-audit.json", preservation_store_audit)
    yoshi_release_join = runpy.run_path(str(ROOT / "expansion/yoshi_island_release_consolidation.py"))
    yoshi_release_audit = yoshi_release_join["apply"](entries, ROOT.parent)
    catalog["entry_aliases"].update(yoshi_release_audit.get("aliases", {}))
    write(ROOT / "yoshi-island-release-consolidation-audit.json", yoshi_release_audit)
    maze_media_join = runpy.run_path(str(ROOT / "expansion/maze_reviewed_narrative_media.py"))
    maze_media_audit = maze_media_join["apply"](entries, ROOT.parent)
    write(ROOT / "maze-reviewed-narrative-media-integration-audit.json", maze_media_audit)
    kinect_media_join = runpy.run_path(str(ROOT / "expansion/kinect_reviewed_narrative_media.py"))
    kinect_media_audit = kinect_media_join["apply"](entries, ROOT.parent)
    write(ROOT / "kinect-reviewed-narrative-media-integration-audit.json", kinect_media_audit)
    stanley_media_join = runpy.run_path(str(ROOT / "expansion/stanley2013_reviewed_narrative_media.py"))
    stanley_media_audit = stanley_media_join["apply"](entries, ROOT.parent)
    write(ROOT / "stanley2013-reviewed-narrative-media-integration-audit.json", stanley_media_audit)
    reviewed_story_gaps_join = runpy.run_path(str(ROOT / "expansion/reviewed_story_gap_images.py"))
    reviewed_story_gaps_audit = reviewed_story_gaps_join["apply"](entries, ROOT.parent)
    write(ROOT / "reviewed-story-gap-images-integration-audit.json", reviewed_story_gaps_audit)
    additional_clarity_join = runpy.run_path(str(ROOT / "expansion/reviewed_clarity_next.py"))
    additional_clarity_audit = additional_clarity_join["apply"](entries, ROOT.parent)
    write(ROOT / "additional-reviewed-clarity-integration-audit.json", additional_clarity_audit)
    fourteen_clarity_join = runpy.run_path(str(ROOT / "expansion/reviewed_article_clarity.py"))
    fourteen_clarity_audit = fourteen_clarity_join["apply"](entries, ROOT.parent)
    write(ROOT / "fourteen-article-reviewed-clarity-integration-audit.json", fourteen_clarity_audit)
    final_body_media_audit = reviewed_story_gaps_join["apply"](entries, ROOT.parent, stage='after_clarity')
    write(ROOT / "reviewed-final-body-story-gap-images-integration-audit.json", final_body_media_audit)
    post_media_clarity_audit = additional_clarity_join["apply"](entries, ROOT.parent, stage='after_media')
    write(ROOT / "reviewed-post-media-clarity-integration-audit.json", post_media_clarity_audit)
    # Lua's identity review binds its final, already clarified article body.
    lua_cover_join = runpy.run_path(str(ROOT / "expansion/reviewed_lua_language_cover.py"))
    lua_cover_audit = lua_cover_join["apply"](entries, ROOT.parent)
    write(ROOT / "reviewed-lua-language-cover-integration-audit.json", lua_cover_audit)
    # This media review binds the final Wikipedia design paragraph, so it must
    # follow the earlier reviewed clarity join that restores that paragraph.
    gba_media_join = runpy.run_path(str(ROOT / "expansion/gba_original_reviewed_narrative_media.py"))
    gba_media_audit = gba_media_join["apply"](entries, ROOT.parent)
    write(ROOT / "gba-original-reviewed-narrative-media-integration-audit.json", gba_media_audit)
    gba_sp_media_join = runpy.run_path(str(ROOT / "expansion/gba_sp_reviewed_narrative_media.py"))
    gba_sp_media_audit = gba_sp_media_join["apply"](entries, ROOT.parent)
    write(ROOT / "gba-sp-reviewed-narrative-media-integration-audit.json", gba_sp_media_audit)
    public_credits_join = runpy.run_path(str(ROOT / "expansion/normalize_public_archive_credits.py"))
    public_credits_audit = public_credits_join["integrate"](entries)
    write(ROOT / "public-archive-credit-normalization-audit.json", public_credits_audit)
    # This exact image-array review must follow every generic media join.
    i_am_alive_join = runpy.run_path(str(ROOT / "expansion/reviewed_i_am_alive_bindings.py"))
    i_am_alive_audit = i_am_alive_join["apply"](entries, ROOT.parent)
    write(ROOT / "i-am-alive-reviewed-final-bindings-audit.json", i_am_alive_audit)
    episode2_join = runpy.run_path(str(ROOT / "expansion/reviewed_episode2_bindings.py"))
    write(ROOT / "episode2-reviewed-existing-bindings-audit.json", episode2_join["apply"](entries, ROOT.parent))
    dishonored_cleanup_join = runpy.run_path(str(ROOT / "expansion/reviewed_dishonored_release_prose.py"))
    write(ROOT / "dishonored-reviewed-release-prose-audit.json", dishonored_cleanup_join["apply"](entries, ROOT.parent))
    brown_replica_join = runpy.run_path(str(ROOT / "expansion/reviewed_brown_box_replica_binding.py"))
    write(ROOT / "brown-box-reviewed-replica-binding-audit.json", brown_replica_join["apply"](entries, ROOT.parent))
    context13_join = runpy.run_path(str(ROOT / "expansion/reviewed_thirteenth_context_images.py"))
    write(ROOT / "thirteenth-reviewed-context-images-audit.json", context13_join["apply"](entries, ROOT.parent))
    capcom_cover_join = runpy.run_path(str(ROOT / "expansion/reviewed_capcom_company_cover.py"))
    write(ROOT / "capcom-reviewed-company-cover-audit.json", capcom_cover_join["apply"](entries, ROOT.parent))
    requested_music_join = runpy.run_path(str(ROOT / "expansion/reviewed_requested_catalog_music.py"))
    write(ROOT / "requested-catalog-music-corrections-audit.json", requested_music_join["apply"](catalog, ROOT.parent))
    localized_titles_join = runpy.run_path(str(ROOT / "expansion/reviewed_localized_soundtrack_titles.py"))
    write(ROOT / "localized-soundtrack-titles-audit.json", localized_titles_join["apply"](entries, ROOT.parent))
    ready_three_join = runpy.run_path(str(ROOT / "expansion/reviewed_ready_three_editorial.py"))
    write(ROOT / "ready-three-reviewed-editorial-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent))
    write(ROOT / "dq-mh-reviewed-editorial-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-dq-mh-editorial-reviewed.json"))
    write(ROOT / "mh-clear-prose-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-mh-clear-prose-reviewed.json"))
    write(ROOT / "live-a-live-clear-prose-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-live-a-live-clear-prose-reviewed.json"))
    write(ROOT / "dq-combat-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-dq-combat-reviewed.json"))
    write(ROOT / "gba-mhfu-illustrations-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-gba-mhfu-illustrations-reviewed.json"))
    write(ROOT / "yu-capcom-media-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-yu-capcom-media-reviewed.json"))
    write(ROOT / "gamecube-transparent-cover-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-gamecube-transparent-cover-reviewed.json"))
    write(ROOT / "three-console-mhfu-final-media-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-three-console-mhfu-final-media-reviewed.json"))
    write(ROOT / "nintendo-super-famicom-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-nintendo-super-famicom-reviewed.json"))
    write(ROOT / "kates-existing-anchors-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-kates-existing-anchors-reviewed.json"))
    write(ROOT / "kojima-remove-hamilton-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-kojima-remove-hamilton-reviewed.json"))
    write(ROOT / "nintendo-eleven-alpha-slots-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-nintendo-eleven-alpha-slots-reviewed.json"))
    write(ROOT / "kitano-existing-prose-images-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-kitano-existing-prose-images-reviewed.json"))
    write(ROOT / "kojima-requested-bbc-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-kojima-requested-bbc-reviewed.json"))
    write(ROOT / "bertie-two-chapters-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-bertie-two-chapters-reviewed.json"))
    write(ROOT / "first-creators-existing-prose-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-first-creators-existing-prose-reviewed.json"))
    write(ROOT / "et1982-existing-story-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-et1982-existing-story-reviewed.json"))
    write(ROOT / "nimrod-existing-story-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-nimrod-existing-story-reviewed.json"))
    write(ROOT / "oxo-existing-story-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-oxo-existing-story-reviewed.json"))
    generic_labels_join = runpy.run_path(str(ROOT / "expansion/remove_generic_display_labels.py"))
    write(ROOT / "generic-display-labels-removal-audit.json", generic_labels_join["apply"](entries))
    write(ROOT / "gt7-clean-cover-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-gt7-clean-cover-reviewed.json"))
    write(ROOT / "six-exact-covers-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-six-exact-covers-reviewed.json"))
    among_us_3d_removed = [entry for entry in entries if entry["id"] == "wikipedia-69475509"]
    if any(entry["title"] != "Among Us 3D" for entry in among_us_3d_removed):
        raise ValueError("Among Us 3D exclusion identity drift")
    entries[:] = [entry for entry in entries if entry["id"] != "wikipedia-69475509"]
    write(ROOT / "among-us-3d-user-exclusion-audit.json", {"status": "PASS", "removed": [{key: entry[key] for key in ("id", "title", "year", "date")} for entry in among_us_3d_removed], "original_among_us_retained": any(entry["id"] == "wikipedia-65260678" and entry["title"] == "Among Us" for entry in entries)})
    butterfly_soup_2_removed = [entry for entry in entries if entry["id"] == "wikipedia-72151918"]
    if any(entry["title"] != "Butterfly Soup 2" for entry in butterfly_soup_2_removed):
        raise ValueError("Butterfly Soup 2 exclusion identity drift")
    entries[:] = [entry for entry in entries if entry["id"] != "wikipedia-72151918"]
    write(ROOT / "butterfly-soup-2-user-exclusion-audit.json", {"status": "PASS", "removed": [{key: entry[key] for key in ("id", "title", "year", "date")} for entry in butterfly_soup_2_removed], "original_butterfly_soup_present": any(entry["title"] == "Butterfly Soup" for entry in entries), "scope": "Exact sequel ID only; no original, soundtrack source, or local asset deletion"})
    gunvolt_3_removed = [entry for entry in entries if entry["id"] == "wikipedia-64398557"]
    if any(entry["title"] != "Azure Striker Gunvolt 3" for entry in gunvolt_3_removed):
        raise ValueError("Azure Striker Gunvolt 3 exclusion identity drift")
    entries[:] = [entry for entry in entries if entry["id"] != "wikipedia-64398557"]
    write(ROOT / "gunvolt-3-user-exclusion-audit.json", {"status": "PASS", "removed": [{key: entry[key] for key in ("id", "title", "year", "date")} for entry in gunvolt_3_removed], "scope": "Exact third-game ID only; franchise/company articles and original assets retained"})
    additional_user_exclusions = {"wikipedia-66659306": "BROK the InvestiGator", "wikipedia-80652032": "Arena Breakout", "nintendo-ultra-hand": "Ultra Hand"}
    additional_removed = [entry for entry in entries if entry["id"] in additional_user_exclusions]
    if any(entry["title"] != additional_user_exclusions[entry["id"]] for entry in additional_removed):
        raise ValueError("Exact requested game exclusion identity drift")
    entries[:] = [entry for entry in entries if entry["id"] not in additional_user_exclusions]
    write(ROOT / "brok-arena-user-exclusion-audit.json", {"status": "PASS", "removed": [{key: entry[key] for key in ("id", "title", "year", "date")} for entry in additional_removed], "scope": "Exact requested titles only; no shared media or source deletion"})
    selected_exclusions_join = runpy.run_path(str(ROOT / "expansion/apply_user_selected_game_exclusions.py"))
    write(ROOT / "selected-user-game-exclusions-audit.json", selected_exclusions_join["apply"](entries, ROOT.parent))
    sports_exclusions_join = runpy.run_path(str(ROOT / "expansion/user_sports_policy.py"))
    write(ROOT / "annual-sports-user-exclusions-audit.json", sports_exclusions_join["apply"](entries, ROOT.parent))
    original_film_posters_join = runpy.run_path(str(ROOT / "expansion/reviewed_original_video_posters.py"))
    write(ROOT / "original-film-posters-reviewed-integration-audit.json", original_film_posters_join["apply"](entries, ROOT.parent))
    write(ROOT / "sid-seven-paragraphs-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-sid-seven-paragraphs-reviewed.json"))
    write(ROOT / "exact-cyberpunk-film-preview-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-exact-cyberpunk-film-preview-reviewed.json"))
    write(ROOT / "sakaguchi-context-stage1-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-sakaguchi-context-stage1-reviewed.json"))
    write(ROOT / "sakaguchi-context-stage2-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-sakaguchi-context-stage2-reviewed.json"))
    write(ROOT / "sakaguchi-context-stage3-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-sakaguchi-context-stage3-reviewed.json"))
    write(ROOT / "tecmo-mabel-lost-odyssey-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-tecmo-mabel-lost-odyssey-reviewed.json"))
    write(ROOT / "odyssey-doctor-pong-startrader-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-odyssey-doctor-pong-startrader-reviewed.json"))
    write(ROOT / "mabel-readable-recognition-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-mabel-readable-recognition-reviewed.json"))
    write(ROOT / "pong-colossal-illustrations-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-pong-colossal-original-illustrations-reviewed.json"))
    write(ROOT / "videosoft-illustrations-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-videosoft-original-magazine-illustrations-reviewed.json"))
    write(ROOT / "breakout-illustrations-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-breakout-original-manual-illustrations-reviewed.json"))
    write(ROOT / "tanktics-illustrations-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-tanktics-primary-original-illustrations-reviewed.json"))
    write(ROOT / "vcs-manual-illustrations-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-vcs-original-manual-illustrations-reviewed.json"))
    write(ROOT / "target-koshiro-illustrations-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-target-koshiro-existing-prose-illustrations-reviewed.json"))
    write(ROOT / "iwata-apf-trek80-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-iwata-apf-trek80-source-bound-illustrations-reviewed.json"))
    write(ROOT / "mud-oregon-pong-vcs-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-mud-oregon-pong-vcs-original-illustrations-reviewed.json"))
    write(ROOT / "starfleet-decwar-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-starfleet-decwar-original-documents-reviewed.json"))
    write(ROOT / "atc-adventure-koei-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-atc-adventure-koei-context-images-reviewed.json"))
    write(ROOT / "pitfall-phaser-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-pitfall-phaser-original-artifacts-reviewed.json"))
    write(ROOT / "shaw-fonz-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-shaw-fonz-context-images-reviewed.json"))
    write(ROOT / "heavyweight-triple-hunt-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-heavyweight-triple-hunt-source-context-reviewed.json"))
    write(ROOT / "spectrum-feature-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-spectrum-feature-real-publishing-artifacts-reviewed.json"))
    write(ROOT / "spectrum-main-ys-arc-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-spectrum-main-ys-arc-reviewed.json"))
    write(ROOT / "shootaway-indy-nakamoto-wumpus-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-shootaway-indy-nakamoto-wumpus-reviewed.json"))
    write(ROOT / "galaxy-empire-primary-context-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-galaxy-empire-primary-context-reviewed.json"))
    write(ROOT / "space-race-rebound-grantrak-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-space-race-rebound-grantrak-reviewed.json"))
    write(ROOT / "spasim-author-artifacts-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-spasim-author-artifacts-reviewed.json"))
    write(ROOT / "wander-dnd-pedit-original-context-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-wander-dnd-pedit-original-context-reviewed.json"))
    write(ROOT / "f1-machine-and-legacy-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-f1-machine-and-legacy-reviewed.json"))
    write(ROOT / "deathrace-autorace-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-deathrace-autorace-reviewed.json"))
    write(ROOT / "neil-druckmann-context-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-neil-druckmann-context-reviewed.json"))
    write(ROOT / "avalanche-controls-hardware-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-avalanche-controls-hardware-reviewed.json"))
    write(ROOT / "heiankyo-official-context-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-heiankyo-official-context-reviewed.json"))
    write(ROOT / "starhawk-mystery-original-context-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-starhawk-mystery-original-context-reviewed.json"))
    write(ROOT / "deep-scan-original-arcade-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-deep-scan-original-arcade-reviewed.json"))
    write(ROOT / "avatar-plato-preservation-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-avatar-plato-preservation-reviewed.json"))
    write(ROOT / "cutieq-iwatani-context-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-cutieq-iwatani-context-reviewed.json"))
    write(ROOT / "warrior-real-vector-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-warrior-real-vector-reviewed.json"))
    write(ROOT / "taipan-related-story-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-taipan-related-story-reviewed.json"))
    write(ROOT / "haunt-recovery-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-haunt-recovery-reviewed.json"))
    write(ROOT / "space-eduware-identity-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-space-eduware-identity-reviewed.json"))
    write(ROOT / "galaxian-namco-leaflet-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-galaxian-namco-leaflet-reviewed.json"))
    write(ROOT / "computer-golf-period-review-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-computer-golf-period-review-reviewed.json"))
    write(ROOT / "head-on-gremlin-identity-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-head-on-gremlin-identity-reviewed.json"))
    write(ROOT / "akalabeth-original-artifacts-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-akalabeth-original-artifacts-reviewed.json"))
    write(ROOT / "home-run-period-chapters-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-home-run-period-chapters-reviewed.json"))
    miyamoto_shared_join = runpy.run_path(str(ROOT / "expansion/reviewed_miyamoto_shared_story.py"))
    write(ROOT / "miyamoto-shared-story-integration-audit.json", miyamoto_shared_join["apply"](entries, ROOT.parent))
    complete_new_entries_join = runpy.run_path(str(ROOT / "expansion/reviewed_complete_new_entries.py"))
    write(ROOT / "complete-new-entries-reviewed-integration-audit.json", complete_new_entries_join["apply"](entries, ROOT.parent))
    new_entry_music_join = runpy.run_path(str(ROOT / "expansion/reviewed_new_entry_soundtracks.py"))
    write(ROOT / "five-primary-provider-label-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-five-primary-provider-label-corrections-reviewed.json"))
    write(ROOT / "new-entry-soundtrack-integration-audit.json", new_entry_music_join["apply"](entries, ROOT.parent))
    gallery_bindings_join = runpy.run_path(str(ROOT / "expansion/reviewed_existing_gallery_bindings.py"))
    write(ROOT / "existing-gallery-bindings-integration-audit.json", gallery_bindings_join["apply"](entries, ROOT.parent))
    write(ROOT / "ten-existing-local-story-mappings-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-ten-existing-local-story-mappings-reviewed.json"))
    write(ROOT / "horizon-warzone-original-context-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-horizon-warzone-original-context-reviewed.json"))
    write(ROOT / "centipede-original-console-port-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-centipede-original-console-port-reviewed.json"))
    native_hq_posters_join = runpy.run_path(str(ROOT / "expansion/reviewed_native_hq_video_posters.py"))
    write(ROOT / "native-hq-film-posters-integration-audit.json", native_hq_posters_join["apply"](entries, ROOT.parent))
    additive_publisher_join = runpy.run_path(str(ROOT / "expansion/reviewed_additive_publisher_images.py"))
    write(ROOT / "additive-publisher-images-integration-audit.json", additive_publisher_join["apply"](entries, ROOT.parent))
    specific_headings_join = runpy.run_path(str(ROOT / "expansion/reviewed_specific_story_headings.py"))
    write(ROOT / "specific-story-headings-integration-audit.json", specific_headings_join["apply"](entries, ROOT.parent))
    ids = {entry["id"] for entry in entries}
    # Pending exhibits have no runtime destination yet. Keep their references
    # in authoring sources, but expose only links that can actually be opened.
    for entry in entries:
        entry["related_ids"] = [related for related in entry.get("related_ids", []) if related in ids]
    write(ROOT / "atari-lynx-original-manual-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-atari-lynx-original-manual-reviewed.json"))
    write(ROOT / "game-boy-tanaka-collected-artifacts-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-game-boy-tanaka-collected-artifacts-reviewed.json"))
    write(ROOT / "tengai-ziria-original-artifacts-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-tengai-ziria-original-artifacts-reviewed.json"))
    write(ROOT / "dk-oil-ffiii-dqiv-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-dk-oil-ffiii-dqiv-reviewed.json"))
    write(ROOT / "papers-please-feature-images-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-papers-please-feature-images-reviewed.json"))
    write(ROOT / "ffii-wrong-film-identity-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-ffii-wrong-film-identity-reviewed.json"))
    write(ROOT / "blizzard-explicit-partial-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-blizzard-explicit-partial-reviewed.json"))
    write(ROOT / "blizzard-opening-gap-policy-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-blizzard-opening-gap-policy-reviewed.json"))
    write(ROOT / "tectoy-localisation-context-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-tectoy-localisation-context-reviewed.json"))
    write(ROOT / "tectoy-original-console-redistribution-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-tectoy-original-console-redistribution-reviewed.json"))
    write(ROOT / "dkc-wise-context-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-dkc-wise-context-reviewed.json"))
    write(ROOT / "chrono-re-eidos-context-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chrono-re-eidos-context-reviewed.json"))
    write(ROOT / "chronological-1962-1983-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-1962-1983-reviewed.json"))
    write(ROOT / "chronological-1984-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-1984-reviewed.json"))
    write(ROOT / "chronological-1985-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-1985-reviewed.json"))
    write(ROOT / "chronological-1986-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-1986-reviewed.json"))
    write(ROOT / "chronological-1987-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-1987-reviewed.json"))
    write(ROOT / "chronological-1988-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-1988-reviewed.json"))
    write(ROOT / "chronological-1989-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-1989-reviewed.json"))
    write(ROOT / "chronological-1990-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-1990-reviewed.json"))
    write(ROOT / "chronological-1991-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-1991-reviewed.json"))
    write(ROOT / "chronological-1992-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-1992-reviewed.json"))
    write(ROOT / "chronological-1993-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-1993-reviewed.json"))
    write(ROOT / "chronological-1994-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-1994-reviewed.json"))
    write(ROOT / "chronological-1995-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-1995-reviewed.json"))
    write(ROOT / "chronological-1996-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-1996-reviewed.json"))
    write(ROOT / "chronological-1997-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-1997-reviewed.json"))
    write(ROOT / "chronological-1998-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-1998-reviewed.json"))
    write(ROOT / "chronological-1999-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-1999-reviewed.json"))
    write(ROOT / "requested-wii-fit-media-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-chronological-2007-reviewed.json"))
    new_game_articles = runpy.run_path(str(ROOT / "expansion/reviewed_new_game_articles.py"))
    write(ROOT / "new-game-articles-reviewed-integration-audit.json", new_game_articles["apply"](entries, ROOT.parent))
    paragraph_boundaries_join = runpy.run_path(str(ROOT / "expansion/reviewed_paragraph_boundaries.py"))
    write(ROOT / "paragraph-boundaries-reviewed-integration-audit.json", paragraph_boundaries_join["apply"](entries, ROOT.parent))
    write(ROOT / "annual-sports-final-no-resurrection-audit.json", sports_exclusions_join["apply"](entries, ROOT.parent))
    write(ROOT / "selected-user-final-no-resurrection-audit.json", selected_exclusions_join["apply"](entries, ROOT.parent))
    write(ROOT / "annual-sports-reference-pruning-audit.json", sports_exclusions_join["prune_references"](entries, ROOT.parent))
    # Editorial full-owner proposals cannot restore superseded model selectors
    # or material variants. The separately reviewed bundled index owns these.
    for entry in entries:
        if entry['id'] in approved_bundled:
            entry['models'] = [copy.deepcopy(approved_bundled[entry['id']])]
    series_s_user = runpy.run_path(str(ROOT / 'expansion/user_series_s_cover.py'))
    write(ROOT / 'user-series-s-cover-integration-audit.json', series_s_user['apply'](entries, ROOT.parent))
    hardware_image_user = runpy.run_path(str(ROOT / 'expansion/user_hardware_image_only.py'))
    write(ROOT / 'user-hardware-image-only-integration-audit.json', hardware_image_user['apply'](entries, ROOT.parent))
    write(ROOT / 'user-all-console-png-integration-audit.json', console_png_policy['apply'](entries, ROOT.parent))
    write(ROOT / "pre1995-after-console-png-reviewed-integration-audit.json", ready_three_join["apply"](entries, ROOT.parent, "museum-pre1995-after-console-png-reviewed.json"))
    ps1_final_cover = runpy.run_path(str(ROOT / 'expansion/user_ps1_final_cover.py'))
    write(ROOT / 'user-ps1-final-cover-integration-audit.json', ps1_final_cover['apply'](entries, ROOT.parent))
    alex_summary = runpy.run_path(str(ROOT / 'expansion/alex_kidd_summary_clarity.py'))
    write(ROOT / 'alex-kidd-summary-clarity-audit.json', alex_summary['apply'](entries))
    smb2_headings = runpy.run_path(str(ROOT / 'expansion/smb2_story_heading_clarity.py'))
    write(ROOT / 'smb2-story-heading-clarity-audit.json', smb2_headings['apply'](entries))
    original_butoden_back = runpy.run_path(str(ROOT / 'expansion/super_butoden_original_back.py'))
    write(ROOT / 'super-butoden-original-back-integration-audit.json', original_butoden_back['apply'](entries, ROOT.parent))
    reviewed_early_media = runpy.run_path(str(ROOT / 'expansion/reviewed_early_media_boundary.py'))
    write(ROOT / 'reviewed-early-media-boundary-integration-audit.json', reviewed_early_media['apply'](entries, ROOT.parent))
    def chronology_order(entry):
        date = entry.get("date", {})
        dated = date.get("precision") in ("month", "day") and 1 <= date.get("month", 0) <= 12
        return (entry["year"], date["month"] if dated else 0,
                date.get("day", 0) if dated and date.get("precision") == "day" else 0)
    entries.sort(key=chronology_order)
    readiness_module=runpy.run_path(str(ROOT / "expansion/publication_readiness.py"))
    readiness=readiness_module["evaluate"](entries)
    readiness_by_id={row["entry_id"]:row for row in readiness["entries"]}
    for entry in entries:
        review=readiness_by_id.get(entry["id"])
        if review:entry["publication_readiness"]={key:copy.deepcopy(review[key]) for key in ("status","editorial_signoff","blockers","hd_images","contextual_sections")}
    append_only = runpy.run_path(str(ROOT / 'expansion/reviewed_append_only_backfills.py'))
    write(ROOT / 'reviewed-append-only-backfill-integration-audit.json', append_only['apply'](entries, ROOT.parent))
    reviewed_music = runpy.run_path(str(ROOT / 'expansion/reviewed_nine_music_layer.py'))
    write(ROOT / 'reviewed-nine-2010-public-music-integration-audit.json', reviewed_music['apply'](entries, ROOT.parent))
    earlier_music = runpy.run_path(str(ROOT / 'expansion/reviewed_earliest_two_music_layer.py'))
    write(ROOT / 'reviewed-earliest-two-public-music-integration-audit.json', earlier_music['apply'](entries, ROOT.parent))
    existing_owner_replacements = runpy.run_path(str(ROOT / 'expansion/reviewed_2011_existing_owner_replacements.py'))
    write(ROOT / 'reviewed-2011-existing-owner-replacement-integration-audit.json', existing_owner_replacements['apply'](entries, ROOT.parent))
    reviewed_films = runpy.run_path(str(ROOT / 'expansion/reviewed_five_2010_film_layer.py'))
    write(ROOT / 'reviewed-five-2010-film-integration-audit.json', reviewed_films['apply'](entries, ROOT.parent))
    five_music = runpy.run_path(str(ROOT / 'expansion/reviewed_five_2010_music_layer.py'))
    write(ROOT / 'reviewed-five-2010-217-public-music-integration-audit.json', five_music['apply'](entries, ROOT.parent))
    five_2011_music = runpy.run_path(str(ROOT / 'expansion/reviewed_five_2011_music_layer.py'))
    write(ROOT / 'reviewed-five-2011-382-public-music-integration-audit.json', five_2011_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_combined_168_classic_music_layer.py'))
    write(ROOT / 'reviewed-combined-168-46-49-music-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    postmusic_owner_replacements = runpy.run_path(str(ROOT / 'expansion/reviewed_2011_postmusic_owner_replacements.py'))
    write(ROOT / 'reviewed-2011-postmusic-owner-replacement-integration-audit.json', postmusic_owner_replacements['apply'](entries, ROOT.parent))
    global_labels = runpy.run_path(str(ROOT / 'expansion/reviewed_global_205_display_layer.py'))
    write(ROOT / 'reviewed-global-205-display-cleanups-integration-audit.json', global_labels['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_nine_classic_185_music_layer.py'))
    write(ROOT / 'reviewed-nine-classic-185-music-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_sonic2_alttp51_music_layer.py'))
    write(ROOT / 'reviewed-sonic2-alttp51-music-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_tekken3_opening_display_layer.py'))
    write(ROOT / 'reviewed-tekken3-opening-display-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_classic_fiftyfive_cues_layer.py'))
    write(ROOT / 'reviewed-classic-fiftyfive-cues-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_xevious_dr_mario_nine_cues_layer.py'))
    write(ROOT / 'reviewed-xevious-dr-mario-nine-cues-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    reviewed_2012 = runpy.run_path(str(ROOT / 'expansion/reviewed_2012_mixed_owner_layer.py'))
    write(ROOT / 'reviewed-2012-mixed-owner-integration-audit.json', reviewed_2012['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_precutoff_fiftythree_display_layer.py'))
    write(ROOT / 'reviewed-precutoff-fiftythree-display-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_pacman_commando17_layer.py'))
    write(ROOT / 'reviewed-pacman-commando17-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_five_original88_layer.py'))
    write(ROOT / 'reviewed-five-original88-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_three_original42_layer.py'))
    write(ROOT / 'reviewed-three-original42-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_three_original25_layer.py'))
    write(ROOT / 'reviewed-three-original25-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_three_original48_layer.py'))
    write(ROOT / 'reviewed-three-original48-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_eleven_original131_layer.py'))
    write(ROOT / 'reviewed-eleven-original131-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_four_original53_layer.py'))
    write(ROOT / 'reviewed-four-original53-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_seven_original45_layer.py'))
    write(ROOT / 'reviewed-seven-original45-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_six_original36_layer.py'))
    write(ROOT / 'reviewed-six-original36-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_four_available16_layer.py'))
    write(ROOT / 'reviewed-four-available16-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_five_available39_layer.py'))
    write(ROOT / 'reviewed-five-available39-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_two_famous26_layer.py'))
    write(ROOT / 'reviewed-two-famous26-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_seven_famous134_layer.py'))
    write(ROOT / 'reviewed-seven-famous134-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_seven_famous313_layer.py'))
    write(ROOT / 'reviewed-seven-famous313-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_six_requested131_layer.py'))
    write(ROOT / 'reviewed-six-requested131-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_four_requested140_layer.py'))
    write(ROOT / 'reviewed-four-requested140-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_eleven_mandatory396_layer.py'))
    write(ROOT / 'reviewed-eleven-mandatory396-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_nine_mandatory311_layer.py'))
    write(ROOT / 'reviewed-nine-mandatory311-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_three_mandatory72_layer.py'))
    write(ROOT / 'reviewed-three-mandatory72-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_fantavision_regional30_layer.py'))
    write(ROOT / 'reviewed-fantavision-regional30-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    required_owner = runpy.run_path(str(ROOT / 'expansion/reviewed_streets_rage2_new_owner_layer.py'))
    write(ROOT / 'reviewed-streets-rage2-new-owner-integration-audit.json', required_owner['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_four_mandatory189_layer.py'))
    write(ROOT / 'reviewed-four-mandatory189-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    required_owner = runpy.run_path(str(ROOT / 'expansion/reviewed_mickey_wild_adventure_new_owner_layer.py'))
    write(ROOT / 'reviewed-mickey-wild-adventure-new-owner-integration-audit.json', required_owner['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_four_mandatory81_layer.py'))
    write(ROOT / 'reviewed-four-mandatory81-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_three_mandatory336_layer.py'))
    write(ROOT / 'reviewed-three-mandatory336-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    required_owner = runpy.run_path(str(ROOT / 'expansion/reviewed_red_alert_new_owner_layer.py'))
    write(ROOT / 'reviewed-red-alert-new-owner-integration-audit.json', required_owner['apply'](entries, ROOT.parent))
    required_owner = runpy.run_path(str(ROOT / 'expansion/reviewed_heroes3_new_owner_layer.py'))
    write(ROOT / 'reviewed-heroes3-new-owner-integration-audit.json', required_owner['apply'](entries, ROOT.parent))
    required_owner = runpy.run_path(str(ROOT / 'expansion/reviewed_ape_two_new_owner_layer.py'))
    write(ROOT / 'reviewed-ape-two-new-owner-integration-audit.json', required_owner['apply'](entries, ROOT.parent))
    required_owner = runpy.run_path(str(ROOT / 'expansion/reviewed_battlefield_v_new_owner_layer.py'))
    write(ROOT / 'reviewed-battlefield-v-new-owner-integration-audit.json', required_owner['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_four_available184_layer.py'))
    write(ROOT / 'reviewed-four-available184-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    resumed_2012 = runpy.run_path(str(ROOT / 'expansion/reviewed_2012_mixed_owner_layer.py'))
    write(ROOT / 'reviewed-resumed-2012-owner-integration-audit.json', resumed_2012['apply'](entries, ROOT.parent, ROOT / 'expansion/museum-reviewed-2012-resumed-owner-layer.json'))
    required_owner = runpy.run_path(str(ROOT / 'expansion/reviewed_isaac2011_new_owner_layer.py'))
    write(ROOT / 'reviewed-isaac2011-new-owner-integration-audit.json', required_owner['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_six_available160_layer.py'))
    write(ROOT / 'reviewed-six-available160-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_four_available104_layer.py'))
    write(ROOT / 'reviewed-four-available104-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_four_cod107_layer.py'))
    write(ROOT / 'reviewed-four-cod107-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_two_available24_layer.py'))
    write(ROOT / 'reviewed-two-available24-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_three_available76_layer.py'))
    write(ROOT / 'reviewed-three-available76-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_three_new2012_55_layer.py'))
    write(ROOT / 'reviewed-three-new2012-55-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_seven_late2012_187_layer.py'))
    write(ROOT / 'reviewed-seven-late2012-187-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    final2012 = runpy.run_path(str(ROOT / 'expansion/reviewed_2012_mixed_owner_layer.py'))
    write(ROOT / 'reviewed-final2012-post187-owner-integration-audit.json', final2012['apply'](entries, ROOT.parent, ROOT / 'expansion/museum-reviewed-final2012-post187-owner-layer.json'))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_six_existing2013_165_layer.py'))
    write(ROOT / 'reviewed-six-existing2013-165-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    midyear2013 = runpy.run_path(str(ROOT / 'expansion/reviewed_2012_mixed_owner_layer.py'))
    write(ROOT / 'reviewed-midyear2013-post165-owner-integration-audit.json', midyear2013['apply'](entries, ROOT.parent, ROOT / 'expansion/museum-reviewed-midyear2013-post165-owner-layer.json'))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_pikmin_dragon_sly_layer.py'))
    write(ROOT / 'reviewed-pikmin-dragon-sly-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_publisher_six84_original2013_layer.py'))
    write(ROOT / 'reviewed-publisher-six84-original2013-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_required2014_six_music_layer.py'))
    write(ROOT / 'reviewed-required2014-six-music-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    combined_music = runpy.run_path(str(ROOT / 'expansion/reviewed_requested_three159_music_layer.py'))
    write(ROOT / 'reviewed-requested-three159-music-integration-audit.json', combined_music['apply'](entries, ROOT.parent))
    user_card_media = runpy.run_path(str(ROOT / 'expansion/user_portal_halo3_card_media.py'))
    write(ROOT / 'user-portal-halo3-card-media-audit.json', user_card_media['apply'](entries, ROOT.parent))
    required_music_series = runpy.run_path(str(ROOT / 'expansion/guitar_hero_rock_band_required_series.py'))
    write(ROOT / 'guitar-hero-rock-band-required-series-audit.json', required_music_series['apply'](entries, ROOT.parent))
    legacy_music = runpy.run_path(str(ROOT / 'expansion/reviewed_legacy_three_soundtracks.py'))
    write(ROOT / 'reviewed-legacy-three-soundtracks-audit.json', legacy_music['apply'](entries, ROOT.parent))
    required_peripherals = runpy.run_path(str(ROOT / 'expansion/required_peripheral_hardware.py'))
    write(ROOT / 'required-peripheral-hardware-audit.json', required_peripherals['apply'](entries, ROOT.parent))
    user_media = runpy.run_path(str(ROOT / 'expansion/reviewed_user_media.py'))
    write(ROOT / 'reviewed-user-media-audit.json', user_media['apply'](entries, ROOT.parent))
    person_labels = runpy.run_path(str(ROOT / 'expansion/reviewed_catalog_person_labels.py'))
    write(ROOT / 'reviewed-person-event-labels-audit.json', person_labels['apply'](entries, ROOT.parent))
    # Final explicit user exclusions also guard append-only reviewed owners.
    # Exact-preimage soundtrack-only corrections, after prior broad music layers.
    audio_only_join = runpy.run_path(str(ROOT / 'expansion/reviewed_audio_only_owner_layer.py'))
    write(ROOT / 'reviewed-audio-only-owner-integration-audit.json', audio_only_join['apply'](entries, ROOT.parent))
    write(ROOT / 'selected-user-post-reviewed-no-resurrection-audit.json', selected_exclusions_join['apply'](entries, ROOT.parent))
    final_english = runpy.run_path(str(ROOT / 'expansion/final_english_layer.py'))
    final_policy = read(ROOT / 'expansion/final-english-publication-policy.json', {})
    write(ROOT / 'final-english-integration-audit.json', final_english['apply'](entries, ROOT.parent, 'catalog', final_policy['manifest'], final_policy['review']))
    write(ROOT / 'final-english-exclusion-audit.json', selected_exclusions_join['apply'](entries, ROOT.parent))
    # Append reviewed gaps from the console-by-console comparison.
    console_gaps = runpy.run_path(str(ROOT / 'expansion/reviewed_console_additions.py'))
    write(ROOT / 'console-additions-integration-audit.json', console_gaps['apply'](entries, ROOT.parent))
    entries.sort(key=chronology_order)
    readiness = readiness_module['evaluate'](entries)
    catalog["edition"] = "Museum collection and reference library"
    write(ROOT / "catalog.json", catalog)
    # Derived reference overlays live beside the exact published Playhub files.
    # Source/revision drift rejects assembly instead of applying stale prose.
    locale_join = runpy.run_path(str(ROOT / "expansion/integrate_wikipedia_locales.py"))
    locale_audit = {"translations": [], "policy": "English editorial development build; original translated authoring sidecars retained unchanged."}
    readiness["catalog_sha256"] = hashlib.sha256((ROOT / "catalog.json").read_bytes()).hexdigest()
    write(ROOT / "publication-readiness.json", readiness)
    # The credits inventory follows the exact assembled records, including
    # unmodified Wikipedia introductions and their immutable revision links.
    credits = read(ROOT / "credits.json", {})
    credits["editorial"] = "Pixel Museum combines original exhibition writing, adapted Playhub stories and attributed Wikipedia reference introductions. Each entry preserves its own sources, editorial provenance and applicable text licence."
    credits["sources"] = [{"exhibit_id": e["id"], "editorial_credit": e.get("editorial_credit", ""),
        "attribution": e.get("attribution", {}), "references": e["sources"]} for e in entries]
    credits["sources"].extend({"exhibit_id": e["id"], "feature_id": feature["id"],
        "editorial_credit": feature.get("editorial_credit", ""),
        "references": copy.deepcopy(feature["sources"])}
        for e in entries for feature in e.get("editorial_features", []))
    credits["translations"] = [{key: copy.deepcopy(row[key]) for key in
        ("exhibit_id", "locale", "editorial_credit", "attribution", "source_body_sha256", "source_fields_sha256")}
        for row in locale_audit["translations"]]
    credits["media"] = [{"exhibit_id": e["id"], "media_kind": kind[:-1], **item}
        for e in entries for kind in ("images", "videos", "models") for item in e[kind]]
    credits["media"].extend({"exhibit_id": e["id"], "feature_id": feature["id"],
        "media_kind": "image", **copy.deepcopy(image)}
        for e in entries for feature in e.get("editorial_features", [])
        for image in feature.get("images", []))
    credits["soundtracks"] = [{"exhibit_id": e["id"], "room_index": room_index, **copy.deepcopy(room)}
        for e in entries if not e.get("calendar_only", False)
        for room_index, room in enumerate(e.get("soundtrack_rooms") or ([e["soundtrack"]] if e.get("soundtrack") else []))]
    write(ROOT / "credits.json", credits)
    # Publish only exact-source reuse or independently reviewed translations.
    # Separate sidecars preserve the original Playhub authoring files.
    runpy.run_path(str(ROOT.parent / "tools/publish-editorial-locales.py"))
    audit = dict(entries=len(entries), chronology_entries=sum(not e.get("calendar_only",False) for e in entries),
        runtime_chronology_entries=readiness["distinct_runtime_articles"],
        verified_hd_illustrated_articles=readiness["articles_with_verified_hd_cover"],
        automated_checks_clear_articles=readiness["automated_checks_clear_articles"],
        editorially_ready_articles=readiness["editorially_ready_articles"],
        chronology_console_models_held=[{"id": e["id"], "title": e["title"]} for e in entries
            if (not e.get("calendar_only",False) or not e.get("linked_exhibit_id")) and e["kind"] == "console" and not e["models"]],
        independent_calendar_stops=sum(e.get("calendar_only",False) and not e.get("linked_exhibit_id") for e in entries),
        inherited_calendar_merges_before_identity_review=len(calendar_audit["merged"]),
        enriched_canonical_stories=sum(not e.get("calendar_only",False) and bool(e.get("calendar_editorial")) for e in entries),
        calendar_features=sum(e.get("calendar_only",False) for e in entries), decades=dict(sorted(collections.Counter(str(e["year"]//10*10) for e in entries if not e.get("calendar_only",False)).items())),
        editorial_modes=dict(collections.Counter(e.get("editorial_mode") for e in entries)),
        images=sum(len(e["images"]) for e in entries), videos=sum(len(e["videos"]) for e in entries),
        models=sum(bool(e["models"]) for e in entries), duplicate_records_excluded=duplicates,
        soundtrack_playlists=len(soundtrack_audit["canonical_exhibits"]), soundtrack_tracks=soundtrack_audit["unique_tracks"],
        priority_features=priority_audit["feature_drafts_integrated"],
        priority_feature_cards=priority_audit["narrative_cards_preserved"],
        priority_feature_standalone_destinations=priority_audit["net_new_timeline_destinations"],
        attached_editorial_features=sum(len(e.get("editorial_features", [])) for e in entries),
        hardware_without_models=[{"id": e["id"], "title": e["title"]} for e in entries if e["kind"] in ("console", "computer", "hardware") and not e["models"]],
        catalog_bytes=(ROOT / "catalog.json").stat().st_size)
    write(ROOT / "assembly-audit.json", audit)
    print(json.dumps({k:v for k,v in audit.items() if k != "duplicate_records_excluded"}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    assemble()
    # Apply the user's returned prose after the original source-bound overlays.
    # Stable card IDs preserve every existing media association.
    external_importer = PROJECT / 'tools/import-external-editorial.py'
    if (ROOT / 'external-editorial/sol-pro-20261030').is_dir():
        runpy.run_path(str(external_importer))['apply']()
