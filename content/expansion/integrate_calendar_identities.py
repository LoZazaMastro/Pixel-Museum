"""Apply two reviewed subject corrections before normal calendar enrichment.

Published paragraphs/headings are immutable. Scheduling and game release dates
remain separate. The declaration archives the inherited mismatch in full.
"""
import copy
import hashlib
import json

CASES = {"daily-05-21": ("workbook-05-21-senua-s-saga-hellblade-ii", "never-alone", 2014),
         "daily-08-30": ("workbook-08-30-astral-chain", "wikipedia-2829113", 1987)}
REVIEW_FILE = "calendar-identity-corrections-02.json"


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def integrate(entries, document):
    """Validate the entire migration before mutating the caller's entry list."""
    require(document.get("schema_version") == 1, "Unsupported identity correction schema")
    cases = document.get("cases", [])
    require(len(cases) == len(CASES) and {c["edition_id"] for c in cases} == set(CASES),
            "Identity correction must contain exactly the reviewed two editions")
    lookup = {e["id"]: e for e in entries}
    require(len(lookup) == len(entries), "Repeated catalogue ID before identity correction")
    changes, originals = [], []
    for case in cases:
        edition_id = case["edition_id"]
        old_id, target_id, year = CASES[edition_id]
        require((case["original_canonical_id"], case["corrected_canonical_id"], case["corrected_year"]) == (old_id, target_id, year),
                f"{edition_id}: unreviewed identity target")
        daily, old = lookup.get(edition_id), lookup.get(old_id)
        require(daily is not None and old is not None and daily.get("calendar_only"),
                f"{edition_id}: required inherited records missing")
        require(daily["title"] == case["original_title"] and daily["year"] == case["original_year"]
                and daily.get("linked_exhibit_id") == old_id, f"{edition_id}: inherited metadata changed")
        require(digest(daily["body"]) == case["expected_source_body_sha256"]
                and digest(daily["story_headings"]) == case["expected_source_heading_sha256"],
                f"{edition_id}: published narrative changed")
        require(digest(case["archived_published_edition"]["body"]) == case["expected_source_body_sha256"]
                and digest(case["archived_published_edition"]["story_headings"]) == case["expected_source_heading_sha256"],
                f"{edition_id}: archived published narrative differs from review")
        require(old["title"] == case["original_title"] and old["year"] == case["original_year"]
                and digest(old["body"]) == case["expected_source_body_sha256"],
                f"{old_id}: inherited canonical narrative changed")
        restored = case["restored_original_destination"]
        source = case["wikipedia_source_snapshot"]
        paragraphs = [p.strip() for p in source["extract"].split("\n") if p.strip()]
        selected = restored["provenance"]["selected_intro_paragraph_indices"]
        require(restored["id"] == old_id and restored["body"] == [paragraphs[i] for i in selected]
                and len(restored["story_headings"]) == len(selected), f"{old_id}: reference selection/hash mismatch")
        revision = source["revisions"][0]
        require(restored["attribution"]["revision_id"] == revision["revid"]
                and restored["attribution"]["source_url"] == f"https://en.wikipedia.org/w/index.php?oldid={revision['revid']}"
                and restored["attribution"]["license"] == "CC BY-SA 4.0", f"{old_id}: reference attribution mismatch")
        require(restored["year"] == case["original_year"] and restored["title"] == case["original_title"],
                f"{old_id}: opaque ID must retain its real original game")
        if target_id == "never-alone":
            require(target_id not in lookup, "Never Alone already has a canonical destination; resolve duplicate first")
        else:
            target = lookup.get(target_id)
            archived = document["archived_street_fighter_reference"]
            require(target is not None and target["year"] == year and target["title"] == case["corrected_title"]
                    and digest(target["body"]) == digest(archived["body"]), "Street Fighter reference changed before reviewed merge")
        originals.extend(copy.deepcopy([daily, old]))
        changes.append((case, daily, old))
    for case, daily, old in changes:
        target_id = case["corrected_canonical_id"]
        review = {"review_file": f"content/expansion/{REVIEW_FILE}", "source_edition_id": daily["id"],
                  "original_title": case["original_title"], "original_year": case["original_year"],
                  "original_canonical_id": old["id"], "corrected_canonical_id": target_id,
                  "published_body_sha256": case["expected_source_body_sha256"],
                  "published_heading_sha256": case["expected_source_heading_sha256"],
                  "reason": "Published metadata describes a different game from the complete original narrative."}
        # Images are not transferred across subjects. Normal calendar enrichment
        # later copies only the corrected canonical destination's own media.
        daily.update(title=case["corrected_title"], year=case["corrected_year"],
                     era_id="everywhere" if case["corrected_year"] == 2014 else "personal",
                     linked_exhibit_id=target_id, images=[], videos=[], models=[],
                     date={"month": 0, "day": 0, "precision": "year", "region": "Calendar slot is editorial scheduling; exact game release date is separate"},
                     source_identity_correction=copy.deepcopy(review))
        daily["sources"] = [copy.deepcopy(s) for s in daily["sources"] if s.get("publisher") == "Playhub / LoZazaMastro"]
        subject_sources = case["publisher_evidence"] if target_id == "never-alone" else lookup[target_id]["sources"]
        daily["sources"].extend(copy.deepcopy(subject_sources))
        daily["event_semantics"] = ("May 21 schedules World Day for Cultural Diversity discussion of Never Alone; the game year is 2014 and its publisher-listed PC release is November 18. This slot is not the game's launch anniversary."
            if daily["id"] == "daily-05-21" else "August 30 is the original editorial slot for the Street Fighter narrative. The game year is 1987; no independently verified exact regional launch day is asserted by metadata.")
        daily["factual_note"] = case["historical_date_review"]
        daily.pop("date_provenance", None)
        old.update(copy.deepcopy(case["restored_original_destination"]))
        old["source_identity_correction"] = copy.deepcopy(review)
        old.pop("calendar_editorial", None)
        old.pop("source_edition_restoration", None)
        old.pop("publication_readiness", None)
        if target_id == "never-alone":
            canonical = copy.deepcopy(daily)
            canonical.update(id=target_id, kind="game", calendar_only=False,
                             date=copy.deepcopy(case["canonical_date"]), era_id="everywhere",
                             layout="story", editorial_mode="playhub_published_story",
                             date_provenance=copy.deepcopy(case["canonical_date_provenance"]),
                             event_semantics="Never Alone PC release listed by its publisher as 18 November 2014. The published May 21 edition is commemorative scheduling.")
            for field in ("calendar", "linked_exhibit_id", "publication_readiness"):
                canonical.pop(field, None)
            canonical["related_ids"] = []
            entries.append(canonical)
        else:
            lookup[target_id]["source_identity_correction"] = copy.deepcopy(review)
            # The old Wikipedia introduction remains in the declaration and
            # normal calendar archive; its unmodified-text notice must not
            # describe the Playhub article that replaces it.
            lookup[target_id].pop("attribution", None)
            lookup[target_id]["provenance"] = copy.deepcopy(daily.get("provenance", {}))
        daily["related_ids"] = [r for r in daily.get("related_ids", []) if r != old["id"]]
    return {"schema_version": 1, "review_file": f"content/expansion/{REVIEW_FILE}",
            "corrected_editions": [c["edition_id"] for c in cases], "new_canonical_ids": ["never-alone"],
            "restored_opaque_destination_ids": [c["original_canonical_id"] for c in cases],
            "original_published_sections_preserved": sum(len(c["archived_published_edition"]["body"]) for c in cases),
            "calendar_slots_unchanged": True, "original_records_before_migration": originals}


def migrate_media_backlog(backlog, lookup, document):
    """Move subject-specific briefs explicitly, retaining every previous job.

    This operates only after the corrected master exists. No acquisition job is
    removed, and the two restored game IDs keep their original work units.
    """
    rows = {row["entry_id"]: row for row in backlog["entries"]}
    cases = {case["edition_id"]: case for case in document["cases"]}
    never = cases["daily-05-21"]
    street = cases["daily-08-30"]
    old_never, old_street = never["original_canonical_id"], street["original_canonical_id"]
    target_street = street["corrected_canonical_id"]
    expected_bodies = {old_never: never["restored_original_destination"]["body"],
                       old_street: street["restored_original_destination"]["body"],
                       target_street: street["archived_published_edition"]["body"],
                       "never-alone": never["archived_published_edition"]["body"]}
    original_bodies = {old_never: never["archived_published_edition"]["body"],
                       old_street: street["archived_published_edition"]["body"],
                       target_street: document["archived_street_fighter_reference"]["body"]}
    hashes = lambda body: [hashlib.sha256(p.encode("utf-8")).hexdigest() for p in body]
    for identifier, body in expected_bodies.items():
        require(identifier in lookup and lookup[identifier]["body"] == body,
                f"{identifier}: corrected media migration target differs from review")
    # Capture the inherited prose briefs before restoring their old ID's job.
    def inherited(identifier):
        row = rows[identifier]
        if [s["body_sha256"] for s in row["sections"]] == hashes(original_bodies[identifier]):
            return copy.deepcopy(row["sections"])
        histories = row.get("source_identity_migrations", [])
        require(histories, f"{identifier}: missing archived source briefs")
        return copy.deepcopy(histories[0]["previous_sections"])
    inherited_never, inherited_street = inherited(old_never), inherited(old_street)
    new_briefs = {
        old_never: ["An official Hellblade II gameplay image matching combat or puzzles; identify edition, capture date and rights. A still cannot establish clinical accuracy.",
                    "Publisher release material for the 2024 PC/Xbox launch or separately labelled 2025 Enhanced/PS5 update. Keep platform and version distinct."],
        old_street: ["Official Astral Chain character/production material with Taura, Kamiya or Katsura provenance; distinguish artwork from release gameplay.",
                     "Official 2019 Astral Chain gameplay showing the player twin tethered to a Legion during combat or investigation.",
                     "A dated Nintendo/PlatinumGames announcement or identifiable 2019 gameplay record. Critical reception/sales require their textual sources, not an unrelated sequel image."]}
    migrated = []
    for identifier in (old_never, old_street, target_street):
        row, entry = rows[identifier], lookup[identifier]
        current = hashes(entry["body"])
        previous = [s["body_sha256"] for s in row["sections"]]
        if previous == current:
            continue
        require(previous == hashes(original_bodies[identifier]), f"{identifier}: unexpected old media brief hashes")
        row.setdefault("source_identity_migrations", []).append({
            "source": f"content/expansion/{REVIEW_FILE}", "previous_sections": copy.deepcopy(row["sections"]),
            "previous_article_source_urls": copy.deepcopy(row.get("existing_article_source_urls", [])),
            "previous_hero_task": copy.deepcopy(row.get("hero_task", {})),
            "replacement_body_sha256": current,
            "reason": "Explicit reviewed subject correction; published briefs move to their actual subject rather than disappearing."})
        minimum = len(current) // 2 + 1
        required = {n * len(current) // minimum for n in range(minimum)}
        if identifier == target_street:
            row["sections"] = copy.deepcopy(inherited_street)
            for section in row["sections"]:
                section["inherited_from_job"] = old_street
        else:
            row["sections"] = [{"paragraph_index": index, "heading": entry["story_headings"][index],
                "body_anchor": paragraph[:260], "body_sha256": current[index],
                "required_for_majority": index in required, "existing_explicit_image_indices": [],
                "brief": new_briefs[identifier][index], "status": "research_required"}
                for index, paragraph in enumerate(entry["body"])]
        row.update(title=entry["title"], year=entry["year"], body_sections=len(current),
                   minimum_distinct_contextual_sections=minimum)
        migrated.append(identifier)
    added = []
    if "never-alone" not in rows:
        entry = lookup["never-alone"]
        job = copy.deepcopy(rows[old_never])
        job.update(entry_id="never-alone", title=entry["title"], year=entry["year"],
                   priority_batch="P6-reviewed-source-identities", sections=inherited_never,
                   body_sections=len(entry["body"]), minimum_distinct_contextual_sections=len(entry["body"]) // 2 + 1,
                   existing_media=[], metadata_hd_image_indices=[], current_explicit_contextual_sections=[],
                   installed_trial_ids=[], tested_trial=False, trial_priority=None, editorial_features=[])
        job["existing_article_source_urls"] = list(dict.fromkeys(s["url"] for s in entry.get("sources", [])))
        job.pop("source_identity_migrations", None)
        for section in job["sections"]:
            section["inherited_from_job"] = old_never
        job["hero_task"] = {"status": "find_first_legitimate_image", "existing_candidate_indices": [],
            "brief": "An identifiable Never Alone (2014) publisher image of Nuna/Fox or documented community production. Review exact subject, version, rights and decoded dimensions; no Hellblade image."}
        job["source_identity_origin"] = {"previous_job_id": old_never, "source": f"content/expansion/{REVIEW_FILE}"}
        backlog["entries"].append(job)
        require(all(b["id"] != "P6-reviewed-source-identities" for b in backlog["batches"]), "Repeated identity media work unit")
        backlog["batches"].append({"id": "P6-reviewed-source-identities", "distinct_articles": 1,
            "minimum_contextual_sections": job["minimum_distinct_contextual_sections"], "missing_hero_candidates": 1,
            "work_units": [{"id": "P6-reviewed-source-identities-001", "entry_ids": ["never-alone"],
                "definition_of_done": "Complete inherited original-published-story briefs with correct subject/version, evidence, rights, decode/crop review and editorial signoff; missing media remains pending."}]})
        added.append("never-alone")
    else:
        require([s["body_sha256"] for s in rows["never-alone"]["sections"]] == hashes(expected_bodies["never-alone"]),
                "Never Alone existing job changed without review")
    for alias in backlog.get("calendar_aliases", []):
        if alias["entry_id"] in cases:
            alias["reuse_media_review_from"] = cases[alias["entry_id"]]["corrected_canonical_id"]
            alias["body_identical_to_linked"] = True
    if migrated or added:
        backlog.setdefault("schema_migrations", []).append({"kind": "reviewed_source_identity_jobs",
            "source": f"content/expansion/{REVIEW_FILE}", "preserved_existing_job_count": len(rows),
            "added_entry_ids": added, "migrated_existing_job_ids": migrated,
            "old_sections_and_briefs_archived": True, "newly_duplicated_work_units": False})
    return {"added_entry_ids": added, "migrated_existing_job_ids": migrated}
