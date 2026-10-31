#!/usr/bin/env python3
"""Refresh media evidence without discarding authored paragraph briefs or tasks."""
from pathlib import Path
import collections
import copy
import datetime
import hashlib
import json
import re
import runpy

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate(image):
    return (max(image.get("width", 0), image.get("height", 0)) >= 1600
            and image.get("quality_verified") and image.get("source_page")
            and image.get("credit"))


def migrate_reading_flow(row, entry, repairs):
    """Only migrate explicitly authored repairs; retain every previous brief."""
    body = entry.get("body", [])
    current_hashes = [hashlib.sha256(text.encode()).hexdigest() for text in body]
    previous_hashes = [section["body_sha256"] for section in row["sections"]]
    if previous_hashes == current_hashes:
        return
    repair = repairs.get(entry["id"])
    assert repair and previous_hashes == repair["expected_body_sha256"], (
        entry["id"], "Changed prose has no matching reviewed migration")
    assert body == repair["body"], (entry["id"], "Replacement differs from reviewed repair")
    old_sections = copy.deepcopy(row["sections"])
    row.setdefault("reading_flow_migrations", []).append({
        "source": "content/expansion/reference-prose-fixes.json",
        "reason": repair["reason"], "paragraph_mapping": repair["paragraph_mapping"],
        "previous_sections": old_sections, "replacement_body_sha256": current_hashes})
    minimum = len(body) // 2 + 1
    required = {n * len(body) // minimum for n in range(minimum)}
    row["sections"] = []
    for index, text in enumerate(body):
        inherited = [section for section in old_sections
                     if int(repair["paragraph_mapping"][str(section["paragraph_index"])]) == index]
        heading = entry.get("story_headings", [])[index]
        row["sections"].append({
            "paragraph_index": index, "heading": heading, "body_anchor": text[:260],
            "body_sha256": current_hashes[index], "required_for_majority": index in required,
            "existing_explicit_image_indices": [],
            "brief": "Find dated, identifiable evidence for this repaired section: " + heading +
                     ". Review the inherited source briefs below; no repeated generic cover.",
            "inherited_briefs": [{"original_paragraph_index": section["paragraph_index"],
                                  "brief": section["brief"]} for section in inherited],
            "status": "research_required" if index in required else "optional_if_relevant"})
    row["body_sections"] = len(body)
    row["minimum_distinct_contextual_sections"] = minimum


def priority_drafts():
    return {row["id"]: row for name in ("editorial-priority-music-design.json",
                                       "editorial-priority-people.json", "editorial-computing-networks-02.json", "editorial-people-regions-03.json", "editorial-cultures-production-04.json", "editorial-authorship-design-05.json", "editorial-composer-methods-06.json", "editorial-systems-authors-06.json", "editorial-music-craft-07.json", "editorial-design-communities-08.json", "editorial-preservation-worlds-09.json", "editorial-hardware-choices-11.json", "editorial-art-direction-12.json", "editorial-people-practices-10.json", "editorial-tools-audio-13.json", "editorial-production-design-16.json", "editorial-markets-machines-14.json", "editorial-networks-history-15.json")
            for row in read("content/expansion/" + name)["entries"]}


def migrate_reviewed_identity_jobs(backlog, lookup):
    """Preserve old briefs while separating reviewed subjects and references."""
    rows = {row['entry_id']: row for row in backlog['entries']}
    identity = read('content/expansion/calendar-identity-corrections-03.json')
    prose = read('content/expansion/calendar-prose-restorations-05.json')
    changes, additions = [], []

    def rebuild(row, entry, source, original_body):
        hashes = [hashlib.sha256(text.encode()).hexdigest() for text in entry['body']]
        previous = [section['body_sha256'] for section in row['sections']]
        if previous == hashes:
            return
        assert previous == [hashlib.sha256(text.encode()).hexdigest() for text in original_body], (entry['id'], 'Unreviewed media brief drift')
        row.setdefault('source_identity_migrations', []).append({
            'source': source, 'previous_sections': copy.deepcopy(row['sections']),
            'previous_article_source_urls': copy.deepcopy(row.get('existing_article_source_urls', [])),
            'replacement_body_sha256': hashes,
            'reason': 'Reviewed canonical prose/identity repair. Prior briefs are archived, never re-labelled as evidence for the new paragraphs.'})
        minimum = len(hashes) // 2 + 1
        required = {n * len(hashes) // minimum for n in range(minimum)}
        row['sections'] = [{'paragraph_index': index, 'heading': entry['story_headings'][index],
            'body_anchor': text[:260], 'body_sha256': hashes[index],
            'required_for_majority': index in required, 'existing_explicit_image_indices': [],
            'brief': 'Find specific, identifiable evidence for ' + entry['title'] + ': ' + entry['story_headings'][index] + '. Preserve edition, creator, licence and contextual uncertainty; no repeated filler cover.',
            'status': 'research_required'} for index, text in enumerate(entry['body'])]
        row.update(body_sections=len(hashes), minimum_distinct_contextual_sections=minimum)
        changes.append(entry['id'])

    for case in identity['cases']:
        if case['correction_kind'] != 'whole_subject_mapping':
            continue
        daily_id, owner_id = case['edition_id'], case['wrong_canonical_id']
        owner = rows[owner_id]
        if daily_id not in rows:
            daily = copy.deepcopy(owner)
            entry = lookup[daily_id]
            # These are the actual unchanged source sections, so their briefs
            # travel with their narrative rather than being discarded.
            assert [section['body_sha256'] for section in daily['sections']] == [hashlib.sha256(text.encode()).hexdigest() for text in entry['body']]
            daily.update(entry_id=daily_id, title=entry['title'], year=entry['year'], kind=entry['kind'],
                calendar_only=True, runtime_distinct=True, reuse_media_review_from=None,
                body_identical_to_linked=None, priority_batch='P7-reviewed-identity-stories',
                existing_media=[], metadata_hd_image_indices=[], current_explicit_contextual_sections=[],
                editorial_features=[], installed_trial_ids=[], tested_trial=False, trial_priority=None)
            daily['source_identity_origin'] = {'previous_job_id': owner_id, 'review_file': 'content/expansion/calendar-identity-corrections-03.json'}
            for section in daily['sections']:
                section['inherited_from_job'] = owner_id
            rows[daily_id] = daily
            backlog['entries'].append(daily)
            additions.append(daily_id)
        rebuild(owner, lookup[owner_id], 'content/expansion/calendar-identity-corrections-03.json', case['archived_published_edition']['body'])
    baer = next(case for case in prose['biography_cases'] if case['edition_id'] == 'daily-03-08')
    if baer['edition_id'] in rows:
        row = rows.pop(baer['edition_id'])
        row.setdefault('previous_identity_jobs', []).append(copy.deepcopy(row))
        row['entry_id'] = baer['target_canonical_id']
        rows[row['entry_id']] = row
        for batch in backlog['batches']:
            for unit in batch['work_units']:
                unit['entry_ids'] = [row['entry_id'] if key == baer['edition_id'] else key for key in unit['entry_ids']]
    for case in prose['biography_cases'] + prose['english_correction_cases']:
        rebuild(rows[case['target_canonical_id']], lookup[case['target_canonical_id']],
            'content/expansion/calendar-prose-restorations-05.json', case['archived_published_edition']['body'])
    if additions:
        backlog['batches'].append({'id': 'P7-reviewed-identity-stories', 'work_units': [{
            'id': 'P7-reviewed-identity-stories-001', 'entry_ids': sorted(additions),
            'definition_of_done': 'Review actual subject images and every inherited brief; old wrong-game media is never transferred.'}]})
    # Aliases remain discovery records, not extra article work units. Changed
    # canonical prose is explicitly distinguished from exact-source duplication.
    backlog['calendar_aliases'] = [{'entry_id': entry['id'], 'reuse_media_review_from': entry['linked_exhibit_id'],
        'body_identical_to_linked': entry['body'] == lookup[entry['linked_exhibit_id']]['body'], 'tested_trial': False}
        for entry in lookup.values() if entry.get('calendar_only') and entry.get('linked_exhibit_id')
        and lookup[entry['linked_exhibit_id']]['year'] == entry['year']]
    if changes or additions:
        backlog.setdefault('schema_migrations', []).append({'kind': 'reviewed_identity03_and_prose05_jobs',
            'changed_job_ids': changes, 'added_distinct_daily_jobs': additions,
            'baer_existing_subject_job_rekeyed_to': baer['target_canonical_id'],
            'previous_sections_and_sources_archived': True})


def migrate_reviewed_narrative_jobs(backlog, lookup, batch="06"):
    """Move only explicitly reviewed parent jobs to new prose; archive all old briefs.

    Old paragraph numbers convey no authority over a newly researched body.
    Attached feature jobs and their own source-bound assignments are untouched.
    """
    assert batch in ('06','07')
    expected_count = 45 if batch=='06' else 12
    module = runpy.run_path(str(ROOT / f'content/expansion/integrate_calendar_narratives_{batch}.py'))
    document = module['checked_document'](ROOT)
    receipt_path = ROOT / f'content/calendar-canonical-narratives-audit-{batch}.json'
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    assert receipt['reviewed_declaration_sha256'] == module['DECLARATION_SHA256']
    originals = {row['original_canonical']['id']: row['original_canonical']
                 for row in receipt['original_records']}
    cases = {row['target_canonical_id']: row for row in document['cases']}
    assert len(originals) == len(cases) == expected_count and set(originals) == set(cases)
    working = copy.deepcopy(backlog)
    jobs = {row['entry_id']: row for row in working['entries']}
    changes = []
    for identifier, case in cases.items():
        entry, row, original = lookup[identifier], jobs[identifier], originals[identifier]
        assert entry['body'] == case['proposed_canonical']['body'], (identifier, 'Unreviewed narrative'+batch+' body')
        assert entry['canonical_narrative_enrichment']['reviewed_declaration_sha256'] == module['DECLARATION_SHA256']
        hashes = [hashlib.sha256(text.encode()).hexdigest() for text in entry['body']]
        previous = [section['body_sha256'] for section in row['sections']]
        if previous == hashes:
            continue
        assert previous == [hashlib.sha256(text.encode()).hexdigest() for text in original['body']], (
            identifier, 'Unreviewed pre-narrative'+batch+' media brief drift')
        archived = copy.deepcopy(row['sections'])
        row.setdefault('source_identity_migrations', []).append({
            'source': f'content/expansion/calendar-canonical-narratives-{batch}.json',
            'integration_receipt': f'content/calendar-canonical-narratives-audit-{batch}.json',
            'receipt_sha256': sha(receipt_path),
            'reviewed_declaration_sha256': module['DECLARATION_SHA256'],
            'previous_sections': archived,
            'previous_article_source_urls': copy.deepcopy(row.get('existing_article_source_urls', [])),
            'previous_hero_task': copy.deepcopy(row.get('hero_task', {})),
            'previous_existing_media': copy.deepcopy(row.get('existing_media', [])),
            'replacement_body_sha256': hashes,
            'reason': f'Independently reviewed canonical narrative{batch} replaces the parent template; original daily prose/locales and every old acquisition brief remain archived. No old paragraph mapping is asserted for the new body.'})
        minimum = len(hashes) // 2 + 1
        required = {n * len(hashes) // minimum for n in range(minimum)}
        source_urls = [source['url'] for source in case['proposed_canonical']['sources']]
        row['sections'] = [{
            'paragraph_index': index, 'heading': entry['story_headings'][index],
            'body_anchor': text[:260], 'body_sha256': hashes[index],
            'required_for_majority': index in required, 'existing_explicit_image_indices': [],
            'brief': 'Find precise, identifiable evidence for ' + entry['title'] + ': ' +
                     entry['story_headings'][index] + '. Read the reviewed narrative and its primary sources. Historical template briefs are archived separately; neither their images nor their paragraph numbers prove a fit here.',
            'source_urls': source_urls,
            'status': 'research_required' if index in required else 'optional_if_relevant'}
            for index, text in enumerate(entry['body'])]
        row.update(body_sections=len(hashes), minimum_distinct_contextual_sections=minimum,
                   current_explicit_contextual_sections=[])
        changes.append(identifier)
    if changes:
        working.setdefault('schema_migrations', []).append({
            'kind': f'reviewed_canonical_narratives{batch}_jobs',
            'source': f'content/calendar-canonical-narratives-audit-{batch}.json',
            'receipt_sha256': sha(receipt_path),
            'reviewed_declaration_sha256': module['DECLARATION_SHA256'],
            'changed_job_ids': sorted(changes), 'new_destinations': 0,
            'previous_sections_sources_and_media_archived': True,
            'attached_feature_jobs_unchanged_by_migration': True})
    backlog.clear()
    backlog.update(working)
    return changes


def feature_job(entry, draft, parent_id=None):
    """Exact authored brief and hash per card; never another parent's job."""
    assert entry["body"] == draft["body"] and entry["story_headings"] == draft["story_headings"]
    minimum = len(entry["body"]) // 2 + 1
    required = {n * len(entry["body"]) // minimum for n in range(minimum)}
    sections = []
    for index, text in enumerate(entry["body"]):
        card = draft["cards"][index]
        brief = card["media_brief"]
        sections.append({
            "paragraph_index": index, "heading": entry["story_headings"][index],
            "body_anchor": text[:260], "body_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "required_for_majority": index in required, "existing_explicit_image_indices": [],
            "brief": brief["description"], "authored_media_brief": copy.deepcopy(brief),
            "source_citations": copy.deepcopy(card["citations"]),
            "status": "research_required"})
    job = {
        "entry_id": entry["id"], "title": entry["title"], "year": entry["year"],
        "kind": "feature", "calendar_only": False, "runtime_distinct": parent_id is None,
        "reuse_media_review_from": None, "body_identical_to_linked": None,
        "priority_batch": "P5-reviewed-priority-features" if parent_id is None else "parent_work_unit",
        "body_sections": len(sections), "minimum_distinct_contextual_sections": minimum,
        "current_explicit_contextual_sections": [], "metadata_hd_image_indices": [],
        "readiness_blockers": ["editorial_review_pending", "localization_pending", "native_layout_review_pending"],
        "hero_task": {"status": "find_first_legitimate_image", "existing_candidate_indices": [],
                      "brief": "Acquire exact feature evidence; do not substitute the parent article cover."},
        "source_lane_order": list(dict.fromkeys(
            "vghf" if "gamehistory.org" in source["url"] else
            "chm" if "computerhistory.org" in source["url"] else
            "strong" if "museumofplay.org" in source["url"] else
            "smithsonian" if "si.edu" in source["url"] else
            "brookhaven" if "bnl.gov" in source["url"] else
            "official-music" if "bandcamp.com" in source["url"] else
            "publisher-media" for source in entry["sources"])) + ["commons"],
        "existing_article_source_urls": list(dict.fromkeys(source["url"] for source in entry["sources"])),
        "existing_media": [], "sections": sections,
        "documentary_video": {"existing_count": 0, "next_action": "Use the exact authored briefs; no filler quota."},
        "soundtrack": {"existing_tracks": 0, "next_action": "Official source and article-specific argument required."},
        "published_experience_ids": [], "media_family": "authored_historical_feature",
        "tasks": ["Complete the exact authored media briefs and retain absent assets as pending.",
                  "Review image identity, rights, decoded size and contextual mapping.",
                  "Keep the feature's English fallback and own credit explicit."],
        "approval_state": "not_editorially_signed_off_by_this_plan",
        "installed_trial_ids": [], "tested_trial": False, "trial_priority": None,
    }
    if parent_id is not None:
        job["feature_id"] = entry["id"]
        job["canonical_entry_id"] = parent_id
    return job


def nested_jobs(parent_row, parent_entry, drafts):
    """Nested assignments do not repeat the parent in acquisition work units."""
    previous = {row["feature_id"]: row for row in parent_row.get("editorial_features", [])}
    result = []
    for feature in parent_entry.get("editorial_features", []):
        expected = feature_job(feature, drafts[feature["id"]], parent_entry["id"])
        job = previous.pop(feature["id"], expected)
        assert [section["body_sha256"] for section in job["sections"]] == [
            section["body_sha256"] for section in expected["sections"]], (
                feature["id"], "Attached prose changed without reviewed brief migration")
        for section, authored in zip(job["sections"], expected["sections"]):
            assert section["authored_media_brief"] == authored["authored_media_brief"], (
                feature["id"], "Authored media brief changed without migration")
        images = feature.get("images", [])
        mapped = {}
        for index, image in enumerate(images):
            paragraph = image.get("story_paragraph")
            if type(paragraph) is int and 0 <= paragraph < len(feature["body"]):
                mapped.setdefault(paragraph, []).append(index)
        job["existing_media"] = [{"index": index, "title": image.get("title", ""),
            "url": image["url"], "source_page": image.get("source_page", ""),
            "declared_dimensions": [image.get("width"), image.get("height")],
            "chapter_index": image.get("story_paragraph"), "licence": image.get("license", ""),
            "rights_state": ("declared_open_licence_still_verify_exact_file"
                if re.search(r"\bCC(?:\s|[-0-9])|public domain", image.get("license", ""), re.I)
                else "copyrighted_editorial_use_requires_item_review"),
            "rights_basis": image.get("rights_basis", ""),
            "rights_review": image.get("rights_review", ""),
            "current_quality_note": image.get("quality_verified", "")}
            for index, image in enumerate(images)]
        job["metadata_hd_image_indices"] = [index for index, image in enumerate(images) if candidate(image)]
        job["current_explicit_contextual_sections"] = sorted(mapped)
        job["hero_task"]["existing_candidate_indices"] = list(range(len(images)))
        job["hero_task"]["status"] = ("identity_rights_crop_and_live_decode_review" if images
                                      else "find_first_legitimate_image")
        for section in job["sections"]:
            index = section["paragraph_index"]
            section["existing_explicit_image_indices"] = mapped.get(index, [])
            section["status"] = "mapping_and_context_review" if index in mapped else "research_required"
        result.append(job)
    assert not previous, (parent_entry["id"], "Existing attached jobs disappeared")
    parent_row["editorial_features"] = result


def main():
    catalog_path = ROOT / "content/catalog.json"
    catalog_hash = sha(catalog_path)
    catalog = read("content/catalog.json")
    lookup = {entry["id"]: entry for entry in catalog["entries"]}
    backlog = read("content/editorial/media-backlog.json")
    production = read("content/editorial/production-plan.json")
    readiness = read("content/publication-readiness.json")
    assert production["catalog_sha256"] == catalog_hash, "Refresh production register first"
    assert readiness["catalog_sha256"] == catalog_hash, "Refresh readiness snapshot first"
    ready = {entry["entry_id"]: entry for entry in readiness["entries"]}
    distinct = {entry["entry_id"] for entry in production["articles"]}
    drafts = priority_drafts()
    priority_module = runpy.run_path(str(ROOT / "content/expansion/integrate_priority_features.py"))
    identity_module = runpy.run_path(str(ROOT / "content/expansion/integrate_calendar_identities.py"))
    identity_module["migrate_media_backlog"](backlog, lookup,
        read("content/expansion/calendar-identity-corrections-02.json"))
    migrate_reviewed_identity_jobs(backlog, lookup)
    migrate_reviewed_narrative_jobs(backlog, lookup)
    migrate_reviewed_narrative_jobs(backlog, lookup,"07")
    previous_ids = {entry["entry_id"] for entry in backlog["entries"]}
    added_ids = distinct - previous_ids
    assert previous_ids <= distinct, "Existing media jobs must not disappear"
    assert added_ids <= priority_module["STANDALONE_IDS"], "Unreviewed new media destinations"
    for identifier in sorted(added_ids):
        backlog["entries"].append(feature_job(lookup[identifier], drafts[identifier]))
    if added_ids:
        batch_id = "P5-reviewed-priority-features"
        # A later reviewed batch can add distinct subjects to this existing
        # lane. Give the new work unit its own stable ID; preserve prior jobs.
        batch_id += "-" + hashlib.sha256("\n".join(sorted(added_ids)).encode()).hexdigest()[:12]
        assert all(batch["id"] != batch_id for batch in backlog["batches"]), "Duplicate priority work unit"
        backlog["batches"].append({
            "id": batch_id, "distinct_articles": len(added_ids),
            "minimum_contextual_sections": sum(len(lookup[key]["body"]) // 2 + 1 for key in added_ids),
            "missing_hero_candidates": 0,
            "work_units": [{"id": batch_id + "-001", "entry_ids": sorted(added_ids),
                "definition_of_done": "Complete exact authored card briefs, image identity/rights/quality, localization and native review. No editorial sign-off inferred."}]})
        backlog.setdefault("schema_migrations", []).append({
            "kind": "reviewed_priority_standalone_jobs", "source": "content/priority-feature-integration-audit.json",
            "preserved_existing_job_count": len(previous_ids), "added_entry_ids": sorted(added_ids),
            "attached_jobs_are_nested_not_duplicate_work_units": True})
    assert {entry["entry_id"] for entry in backlog["entries"]} == distinct
    units = [key for batch in backlog["batches"] for unit in batch["work_units"]
             for key in unit["entry_ids"]]
    assert len(units) == len(set(units)) == len(distinct)
    assert set(units) == distinct
    trial_path = ROOT / "dist/vertical-slice-ready-04/PPSA70421/content/catalog.json"
    trial = json.loads(trial_path.read_text(encoding="utf-8"))
    trial_ids = [entry["id"] for entry in trial["entries"]]
    assert len(trial_ids) == len(set(trial_ids)) == 35
    assert set(trial_ids) <= lookup.keys()
    trial_owner = {}
    for key in trial_ids:
        owner = key if key in distinct else lookup[key].get("linked_exhibit_id", "")
        assert owner in distinct, (key, "Trial article has no distinct acquisition owner")
        trial_owner[key] = owner
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    review = read("content/editorial/plan-review.json")
    repairs = {row["entry_id"]: row for row in read("content/expansion/reference-prose-fixes.json")["entries"]}
    r03 = next(finding for finding in review["findings"] if finding["id"] == "R03")
    for row in backlog["entries"]:
        entry = lookup[row["entry_id"]]
        migrate_reading_flow(row, entry, repairs)
        body = entry.get("body", [])
        assert len(body) == len(row["sections"]), "Narrative changed; review its briefs"
        for section, text in zip(row["sections"], body):
            assert section["body_sha256"] == hashlib.sha256(text.encode()).hexdigest(), (
                entry["id"], section["paragraph_index"], "Narrative changed")
        images = entry.get("images", [])
        valid, mapped, current_media = [], {}, []
        for index, image in enumerate(images):
            if candidate(image):
                valid.append(index)
            paragraph = image.get("story_paragraph")
            explicit = isinstance(paragraph, int) and 0 <= paragraph < len(body)
            if explicit:
                mapped.setdefault(paragraph, []).append(index)
            licence = image.get("license", "")
            open_licence = bool(re.search(r"\bCC(?:\s|[-0-9])|public domain", licence, re.I))
            current_media.append({
                "index": index, "title": image.get("title", ""),
                "source_page": image.get("source_page", ""), "url": image.get("url", ""),
                "declared_dimensions": [image.get("width"), image.get("height")],
                "current_quality_note": image.get("quality_verified", ""),
                "chapter_index": paragraph if explicit else None,
                "rights_state": "declared_open_licence_still_verify_exact_file" if open_licence
                else "copyrighted_editorial_use_requires_item_review", "licence": licence})
        row["existing_media"] = current_media
        row["metadata_hd_image_indices"] = valid
        row["current_explicit_contextual_sections"] = sorted(mapped)
        row["readiness_blockers"] = ready[row["entry_id"]].get("blockers", [])
        row["hero_task"]["existing_candidate_indices"] = list(range(len(images)))
        row["hero_task"]["status"] = ("identity_rights_crop_and_live_decode_review" if images
                                         else "find_first_legitimate_image")
        for section in row["sections"]:
            index = section["paragraph_index"]
            headings = entry.get("story_headings", [])
            section["heading"] = headings[index] if index < len(headings) else None
            section["existing_explicit_image_indices"] = mapped.get(index, [])
            section["status"] = ("mapping_and_context_review" if index in mapped else
                                 "research_required" if section["required_for_majority"] else
                                 "optional_if_relevant")
        row["documentary_video"]["existing_count"] = len(entry.get("videos", []))
        row["soundtrack"]["existing_tracks"] = len(entry.get("soundtrack", {}).get("tracks", []))
        row["existing_article_source_urls"] = list(dict.fromkeys(
            source["url"] for source in entry.get("sources", []) if source.get("url")))
        row["installed_trial_ids"] = [key for key, owner in trial_owner.items() if owner == row["entry_id"]]
        row["tested_trial"] = bool(row["installed_trial_ids"])
        row["trial_priority"] = ("Review first within its existing work unit; included in the installed PS5 trial. "
                                 "This does not establish per-article media or editorial sign-off."
                                 if row["tested_trial"] else None)
        nested_jobs(row, entry, drafts)
    by_id = {entry["entry_id"]: entry for entry in backlog["entries"]}
    for alias in backlog["calendar_aliases"]:
        alias["tested_trial"] = alias["entry_id"] in trial_ids
        if alias["tested_trial"]:
            alias["priority_owner"] = trial_owner[alias["entry_id"]]
    for batch in backlog["batches"]:
        chosen = [by_id[key] for unit in batch["work_units"] for key in unit["entry_ids"]]
        batch["distinct_articles"] = len(chosen)
        batch["minimum_contextual_sections"] = sum(row["minimum_distinct_contextual_sections"] for row in chosen)
        batch["missing_hero_candidates"] = sum(not row["existing_media"] for row in chosen)
        batch["installed_trial_articles"] = sum(row["tested_trial"] for row in chosen)
    counts = backlog["counts"]
    counts.update({
        "raw_catalog_records": len(catalog["entries"]),
        "raw_noncalendar_records": sum(not entry.get("calendar_only", False) for entry in catalog["entries"]),
        "preserved_daily_editions": sum(bool(entry.get("calendar_only")) for entry in catalog["entries"]),
        "distinct_runtime_articles": len(distinct),
        "raw_records_with_any_image": sum(bool(entry.get("images")) for entry in catalog["entries"]),
        "raw_image_records": sum(len(entry.get("images", [])) for entry in catalog["entries"]),
        "distinct_articles_with_any_image": sum(bool(lookup[key].get("images")) for key in distinct),
        "distinct_articles_with_metadata_hd_cover": sum(bool(ready[key].get("hd_images")) for key in distinct),
        "distinct_articles_with_majority_mapped_images": sum(
            len(by_id[key]["current_explicit_contextual_sections"]) > len(lookup[key].get("body", [])) // 2
            for key in distinct),
        "distinct_articles_with_majority_metadata_hd_mappings": sum(
            len(ready[key].get("contextual_sections", [])) > len(lookup[key].get("body", [])) // 2
            for key in distinct),
        "distinct_articles_with_documentary_video": sum(bool(lookup[key].get("videos")) for key in distinct),
        "distinct_articles_with_soundtrack": sum(bool(lookup[key].get("soundtrack")) for key in distinct),
        "distinct_articles_with_3d": sum(bool(lookup[key].get("models")) for key in distinct),
        "installed_trial_articles": len(trial_ids),
        "editorially_signed_off_by_this_register": 0})
    counts["narrative_sections"] = sum(len(row["sections"]) for row in backlog["entries"])
    counts["strict_majority_contextual_target"] = sum(row["minimum_distinct_contextual_sections"] for row in backlog["entries"])
    attached = [feature for row in backlog["entries"] for feature in row.get("editorial_features", [])]
    standalone = [row for row in backlog["entries"] if row["entry_id"] in priority_module["STANDALONE_IDS"]]
    counts.update(attached_editorial_features=len(attached),
        attached_editorial_sections=sum(len(feature["sections"]) for feature in attached),
        attached_strict_majority_contextual_target=sum(feature["minimum_distinct_contextual_sections"] for feature in attached),
        standalone_priority_features=len(standalone),
        standalone_priority_sections=sum(len(row["sections"]) for row in standalone),
        priority_feature_cards=sum(len(feature["sections"]) for feature in attached)+sum(len(row["sections"]) for row in standalone),
        total_narrative_sections_including_attached=counts["narrative_sections"]+sum(len(feature["sections"]) for feature in attached),
        total_contextual_target_including_attached=counts["strict_majority_contextual_target"]+sum(feature["minimum_distinct_contextual_sections"] for feature in attached))
    counts.pop("minimum_contextual_section_slots", None)
    previous = {"catalog_sha256": backlog["catalog_sha256"], "generated_utc": backlog["generated_utc"],
                "note": "Previous snapshot retained as history; current image evidence is refreshed separately."}
    history = backlog.setdefault("snapshot_history", [])
    if previous["catalog_sha256"] != catalog_hash and (
            not history or history[-1]["catalog_sha256"] != previous["catalog_sha256"]):
        history.append(previous)
    backlog.update({"catalog_sha256": catalog_hash, "generated_utc": now,
                    "priority_overlay": {"id": "installed-trial-ready-04", "entry_ids": trial_ids,
                                         "canonical_entry_ids": list(dict.fromkeys(trial_owner.values())),
                                         "alias_to_owner": {key: owner for key, owner in trial_owner.items() if key != owner},
                                         "source": str(trial_path.relative_to(ROOT)).replace("\\", "/"),
                                         "source_sha256": sha(trial_path), "duplicates_work_units": False},
                    "review_followup": {"source": "docs/editorial/independent-review.md",
                                        "recorded_utc": now,
                                        "R03": {"status": r03["status"], "resolution": r03.get("resolution", ""),
                                                "review_source": "content/editorial/plan-review.json",
                                                "note": "Current follow-up only; this tool does not edit the historical review."},
                                        "R07": "Media snapshot refreshed here; this is not retrospective editorial sign-off."}})
    path = ROOT / "content/editorial/media-backlog.json"
    path.write_text(json.dumps(backlog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"catalog_sha256": catalog_hash, "counts": counts,
                      "sections": sum(len(row["sections"]) for row in backlog["entries"]),
                      "media_families": dict(collections.Counter(row["media_family"] for row in backlog["entries"]))}, indent=2))


if __name__ == "__main__":
    main()
