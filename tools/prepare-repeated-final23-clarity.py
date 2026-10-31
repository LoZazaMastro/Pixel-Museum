"""Freeze concrete Wikipedia replacements for the final repeated calendar templates."""
from pathlib import Path
import hashlib
import json
import runpy
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "build/research/playhub-semantic-coverage/wiki-clarity/repeated-final23"
SELECTIONS = (
    ("workbook-04-02-final-fantasy-vi", 52755, [8], "Equipping weapons, armor and Relics"),
    ("workbook-03-11-chrono-trigger", 6614, [1], "The designers behind the Dream Team"),
    ("workbook-03-09-super-mario-rpg", 88522, [11], "Nintendo and Square design an action-focused RPG"),
    ("workbook-03-21-game-boy-advance", 12430, [9], "The landscape design and its designers"),
    ("workbook-03-28-kingdom-hearts", 210873, [7], "Traveling between worlds in the Gummi Ship"),
    ("workbook-03-22-god-of-war", 1620297, [7], "The Challenge of the Gods and unlockable rewards"),
    ("workbook-03-27-monster-hunter-freedom-2g", 14354925, [1], "New quests, equipment and hunting companions"),
    ("workbook-03-19-gears-of-war-judgment", 33108510, [11], "People Can Fly takes the lead"),
    ("workbook-03-25-diablo-iii-reaper-of-souls", 40314020, [19], "The Mystic changes equipment and appearance"),
    ("workbook-04-01-goat-simulator", 41938088, [5], "A joke prototype from an internal game jam"),
    ("workbook-04-03-monument-valley", 41521554, [4], "From a concept drawing to a tablet game"),
    ("workbook-04-04-the-elder-scrolls-online", 35708711, [13], "Seven years of development at ZeniMax Online"),
    ("workbook-03-12-yakuza-0", 44916461, [4], "Arcades, side quests and Completion Points"),
    ("workbook-03-13-code-name-s-t-e-a-m", 43030597, [12], "Comic-book art and Lovecraftian aliens"),
    ("workbook-03-24-bloodborne", 43013126, [], "Cooperative play and Chalice Dungeons"),
    ("workbook-03-26-pillars-of-eternity", 37020286, [4], "Creating a character and choosing skills"),
    ("workbook-03-31-hyper-light-drifter", 40792578, [5, 6], "Alx Preston's personal inspiration"),
    ("workbook-03-30-thimbleweed-park", 44445175, [3], "Verb commands and puzzles across five characters"),
    ("workbook-03-16-kirby-star-allies", 55229262, [4], "Dream Friends from earlier Kirby adventures"),
    ("workbook-03-29-yoshi-s-crafted-world", 54331152, [6], "Finding crafted souvenirs for the Blockafellers"),
    ("workbook-03-10-call-of-duty-warzone", 63331650, [8], "Plunder: collecting Cash against the clock"),
    ("workbook-03-23-half-life-alyx", 62378822, [14], "Why Valve returned to Half-Life through VR"),
    ("workbook-04-05-lego-star-wars-the-skywalker-saga", 61002930, [4], "Voice acting and the optional Mumble Mode"),
)


def digest(value):
    if not isinstance(value, bytes):
        value = value.encode("utf8")
    return hashlib.sha256(value).hexdigest()


def main():
    master_file = ROOT / "content/catalog.json"
    catalog = json.loads(master_file.read_text(encoding="utf8"))
    owners = {entry["id"]: entry for entry in catalog["entries"]}
    records = json.loads((FOLDER / "source-original-revisions-index.json").read_text(encoding="utf8"))
    sources = {row["page_id"]: row for row in records}
    parser_class = runpy.run_path(str(ROOT / "tools/prepare-yoshi-island-consolidation.py"))["Paragraphs"]
    batch_file = FOLDER / "source-full-batch.json"
    pages = json.loads(batch_file.read_text(encoding="utf8"))["query"]["pages"]
    pages = list(pages.values()) if isinstance(pages, dict) else pages
    replacements, invariants, readable = [], [], []
    for entry_id, page_id, indices, heading in SELECTIONS:
        entry = owners[entry_id]
        old = entry["body"][3]
        assert "enters this calendar" in old or "movement from intention" in old, entry_id
        if page_id == 43013126:
            source_file = batch_file
            page = next(row for row in pages if row["pageid"] == page_id)
            paragraphs = page["extract"].splitlines()
            indices = [next(i for i, text in enumerate(paragraphs) if text.startswith("The game includes online multiplayer features."))]
            title, revision = page["title"], page["revisions"][0]["revid"]
            locator = "Zero-based raw splitlines index in the actual Wikipedia API extract, including blank lines and headings."
        else:
            record = sources[page_id]
            source_file = ROOT / record["file"]
            assert digest(source_file.read_bytes()) == record["sha256"]
            source = json.loads(source_file.read_text(encoding="utf8"))["parse"]
            assert source["revid"] == record["revision_id"]
            parser = parser_class()
            parser.feed(source["text"])
            paragraphs = parser.paragraphs
            title, revision = record["title"], record["revision_id"]
            locator = "Zero-based non-empty HTML p elements in the original revision, reference superscripts omitted and layout whitespace normalized."
        selected = [paragraphs[index] for index in indices]
        body = "\n\n".join(selected)
        assert all(body != existing for existing in entry["body"][:3])
        source_ref = dict(title=title, url=f"https://en.wikipedia.org/w/index.php?oldid={revision}",
            publisher="English Wikipedia contributors", license="Creative Commons Attribution-ShareAlike 4.0",
            license_url="https://creativecommons.org/licenses/by-sa/4.0/",
            attribution="Complete source paragraphs reproduced verbatim; card heading supplied editorially.")
        row = dict(entry_id=entry_id, source_chapter_index=3,
            index_semantics="Absolute active body index; preserve every other paragraph, date and media association.",
            old_heading=entry.get("story_headings", [""] * len(entry["body"]))[3],
            old_body=old, old_body_sha256=digest(old), heading=heading, body=body,
            body_sha256=digest(body), source=source_ref,
            provenance=dict(source_kind="Frozen original Wikipedia article revision", source_file=source_file.relative_to(ROOT).as_posix(),
                source_file_sha256=digest(source_file.read_bytes()), page_id=page_id, revision_id=revision,
                actual_title=title, requested_title=title, paragraph_indices=indices,
                locator=locator, source_paragraphs=selected, full_paragraph=True,
                selection_scope="One or two complete source paragraphs; no abridgment, sentence rewriting or added claims."))
        replacements.append(row)
        unchanged = {key: value for key, value in entry.items() if key not in ("body", "story_headings")}
        invariants.append(dict(entry_id=entry_id, body_count=len(entry["body"]), changed_indices=[3],
            preserved_body={str(i): text for i, text in enumerate(entry["body"]) if i != 3},
            all_other_entry_fields_sha256=digest(json.dumps(unchanged, ensure_ascii=False, sort_keys=True, separators=(",", ":")))))
        readable.append(f"{entry['title']}\n{heading}\n{body}\n")
    result = dict(schema_version=1, publication_status="candidate_pending_independent_review",
        source_catalog_sha256=digest(master_file.read_bytes()),
        scope="Replace 23 repeated calendar/design template cards with concrete Wikipedia passages. Preserve the good first three chapters and all dates/images/video/music/models.",
        replacements=replacements, entry_invariants=invariants,
        research_notes=["All 23 sources identify the exact original game or hardware, including Warzone 2020 and God of War 2005.",
            "Bloodborne uses the frozen full API extract; other 22 sources use frozen full original-revision HTML.",
            "Source paragraphs selected after reading the preceding three active chapters to avoid repeating their primary topic.",
            "Game Boy Advance has a fifth technical paragraph, which is preserved."],
        new_word_count=sum(len(row["body"].split()) for row in replacements), master_modified=False)
    output = FOLDER / "candidate.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    (FOLDER / "projected-card-text.txt").write_text("\n".join(readable), encoding="utf8")
    print(json.dumps(dict(file=output.relative_to(ROOT).as_posix(), sha256=digest(output.read_bytes()),
        entries=len(replacements), words=result["new_word_count"], master_modified=False)))


if __name__ == "__main__":
    main()
