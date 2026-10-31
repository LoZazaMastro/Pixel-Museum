"""Freeze the remaining seven repeated design-template cards from local sources."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "build/research/playhub-semantic-coverage/wiki-clarity/final-seven-editorial"
SOURCE_FOLDER = ROOT / "build/research/playhub-semantic-coverage/wiki-clarity/pass6-root"
PLANS = (
    ("workbook-08-21-bioshock", 5, "BioShock", [25], "Weapons, EVE and Vita-Chambers"),
    ("workbook-08-21-bioshock", 6, "BioShock", [27], "Hacking security and researching enemies"),
    ("workbook-08-01-monster-hunter-tri", 2, "Monster Hunter Tri", [14, 15], "Four-player online quests"),
    ("workbook-08-01-monster-hunter-tri", 3, "Monster Hunter Tri", [8], "Forging equipment from monster materials"),
    ("workbook-08-14-hyrule-warriors", 3, "Hyrule Warriors", [26, 27], "Nintendo, Omega Force and Team Ninja collaborate"),
    ("never-alone", 5, "Never Alone (video game)", [19], "Awards for the debut and its cultural impact"),
    ("never-alone", 6, "Never Alone (video game)", [21, 22], "Praise for the art and divided views on platforming"),
)


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode("utf8")).hexdigest()


def main():
    FOLDER.mkdir(parents=True, exist_ok=True)
    master = ROOT / "content/catalog.json"
    entries = {entry["id"]: entry for entry in json.loads(master.read_text(encoding="utf8"))["entries"]}
    rows, readable = [], []
    for entry_id, index, title, indices, heading in PLANS:
        entry = entries[entry_id]
        old = entry["body"][index]
        assert "This coherence lets" in old or "A broader principle emerges" in old
        file = SOURCE_FOLDER / (title + ".json")
        document = json.loads(file.read_text(encoding="utf8"))
        pages = document["query"]["pages"]
        page = next(iter(pages.values())) if isinstance(pages, dict) else pages[0]
        paragraphs = page["extract"].splitlines()
        selected = [paragraphs[i] for i in indices]
        body = "\n\n".join(selected)
        adaptations = []
        if entry_id == "workbook-08-01-monster-hunter-tri" and index == 2:
            body = selected[0].replace(
                "Monster Hunter on the Wii and Wii U offer an online component", "Monster Hunter Tri on the Wii offered an online component").replace(
                "requiring players to individual completely all quests in a rank before moving to a new tier",
                "requiring players to complete all quests in a rank before moving to a new tier")
            body += " The Wii version's online service has since been shut down."
            adaptations = [
                "Restrict the mixed Wii/Wii U opening sentence to the original Wii subject, using past tense.",
                "Correct the source's ungrammatical 'individual completely' wording to 'complete'.",
                "Summarize source paragraph 15's closure statement for the Wii service, omitting the separate Ultimate/Wii U service history."]
        assert body not in entry["body"]
        revision = page["revisions"][0]["revid"]
        rows.append(dict(entry_id=entry_id, source_chapter_index=index,
            old_body=old, old_body_sha256=sha(old), old_heading=entry["story_headings"][index],
            heading=heading, body=body, body_sha256=sha(body),
            source=dict(title=page["title"], url=f"https://en.wikipedia.org/w/index.php?oldid={revision}",
                publisher="English Wikipedia contributors", license="Creative Commons Attribution-ShareAlike 4.0",
                license_url="https://creativecommons.org/licenses/by-sa/4.0/",
                attribution=("Adapted from the complete source paragraphs with minimal scope and grammar corrections recorded in provenance; card heading supplied editorially."
                    if adaptations else "Complete source paragraphs reproduced verbatim; card heading supplied editorially.")),
            provenance=dict(source_file=file.relative_to(ROOT).as_posix(), source_file_sha256=sha(file.read_bytes()),
                page_id=page["pageid"], revision_id=revision, paragraph_indices=indices,
                source_paragraphs=selected, locator="Zero-based raw splitlines index of the frozen English Wikipedia extract, including blank lines and headings.",
                full_paragraph=not adaptations, adaptations=adaptations,
                selection_scope="Minimal disclosed adaptation of the two complete source paragraphs" if adaptations else "Complete source paragraphs reproduced verbatim")))
        readable.append(f"{entry['title']} / paragraph {index}\n{heading}\n{body}\n")
    doc = dict(schema_version=1, publication_status="candidate_pending_independent_review",
        source_catalog_sha256=sha(master.read_bytes()), scope="Seven remaining repeated design-template bodies; keep all other current paragraphs, dates and media.",
        replacements=rows, notes=["BioShock's existing primary manual card retains the Little Sisters/ADAM decision; new paragraphs add ammunition, EVE, checkpoints, hacking and research instead of repeating that decision.",
            "Monster Hunter online source is explicitly adapted to the original Wii subject, with a grammar correction and an accurate service-closure note. The source's ten-weapon passage mixes Ultimate features and was not selected.",
            "Never Alone already explains collaboration and character switching in paragraphs 0-4; the two replacement cards add documented awards and critical reception instead of duplicating them."],
        new_word_count=sum(len(row["body"].split()) for row in rows), master_modified=False)
    output = FOLDER / "candidate.json"
    output.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    (FOLDER / "projected-card-text.txt").write_text("\n".join(readable), encoding="utf8")
    print(json.dumps(dict(candidate=output.relative_to(ROOT).as_posix(), candidate_sha256=sha(output.read_bytes()), cards=len(rows), words=doc["new_word_count"])))


if __name__ == "__main__":
    main()
