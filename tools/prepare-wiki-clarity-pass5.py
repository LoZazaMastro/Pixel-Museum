"""Replace specific repeated generic cards with source-complete Wikipedia prose."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "build/research/playhub-semantic-coverage/wiki-clarity/pass4"
entries = {e["id"]: e for e in json.loads((ROOT / "content/catalog.json").read_text(encoding="utf8"))["entries"]}

# Body positions remain stable. Each tuple selects whole source paragraphs,
# rather than applying a broad automated rewrite to unrelated clear material.
specs = [
    ("wikipedia-147941", 4, "wiki-147941.json", [13], "New levels for experienced Mario players"),
    ("wikipedia-147941", 5, "wiki-147941.json", [7], "Mario and Luigi move differently"),
    ("wikipedia-147941", 6, "wiki-147941.json", [8], "Poison Mushrooms, wind and deceptive routes"),
    ("workbook-06-06-the-legend-of-zelda-link-s-awakening", 4, "wiki-356690.json", [1], "A Game Boy experiment becomes an original adventure"),
    ("workbook-06-06-the-legend-of-zelda-link-s-awakening", 5, "wiki-356690.json", [8, 9], "Assigning items to the two buttons"),
    ("workbook-06-06-the-legend-of-zelda-link-s-awakening", 6, "wiki-356690.json", [10], "Trading, seashells and side quests"),
    ("workbook-06-22-quake", 4, "wiki-25266.json", [7], "Finding the exit through a three-dimensional level"),
    ("workbook-06-22-quake", 5, "wiki-25266.json", [11], "Strafe-jumping and rocket-jumping"),
    ("workbook-06-22-quake", 6, "wiki-25266.json", [37], "Trent Reznor and the sound of Quake"),
    ("workbook-06-24-commandos-behind-enemy-lines", 1, "wiki-10792367.json", [6], "Six specialists with different equipment"),
    ("workbook-06-24-commandos-behind-enemy-lines", 2, "wiki-10792367.json", [7], "Watching patrols and enemy sightlines"),
    ("workbook-06-24-commandos-behind-enemy-lines", 3, "wiki-10792367.json", [5], "A briefing defines the mission and escape"),
    ("workbook-06-26-viewtiful-joe", 4, "viewtiful-original-full.json", [5], "Punching, dodging and platforming"),
    ("workbook-06-26-viewtiful-joe", 5, "viewtiful-original-full.json", [7], "Slow, Mach Speed and Zoom In"),
    ("workbook-06-26-viewtiful-joe", 6, "viewtiful-original-full.json", [8], "Combos earn upgrades between stages"),
    ("workbook-06-21-driv3r", 1, "wiki-846968.json", [6], "Driving through three cities"),
    ("workbook-06-21-driv3r", 2, "wiki-846968.json", [7], "Leaving the car and entering combat"),
    ("workbook-06-21-driv3r", 3, "wiki-846968.json", [8], "Missions, free roaming and replay editing"),
    ("workbook-06-09-killer7", 4, "wiki-1151672.json", [7], "Paths, puzzles and changing personalities"),
    ("workbook-06-09-killer7", 5, "wiki-1151672.json", [9], "Blood supplies abilities and upgrades"),
    ("workbook-06-09-killer7", 6, "wiki-1151672.json", [51], "A high-contrast style divides reviewers"),
    ("workbook-06-20-time-crisis-4", 1, "wiki-3821602.json", [9], "GunCon 3 and the PlayStation 3 version"),
    ("workbook-06-20-time-crisis-4", 2, "wiki-3821602.json", [17], "Defending several screens with an infrared light gun"),
    ("workbook-06-20-time-crisis-4", 3, "wiki-3821602.json", [4], "Different weapons and defensive encounters"),
    ("workbook-06-01-tomb-raider-anniversary", 1, "wiki-6003023.json", [8], "Ledges, grappling hooks and traversal"),
    ("workbook-06-01-tomb-raider-anniversary", 2, "wiki-6003023.json", [9], "Switches, keys and timed puzzles"),
    ("workbook-06-01-tomb-raider-anniversary", 3, "wiki-6003023.json", [10], "Dodging a charge and counterattacking"),
    ("workbook-06-08-green-day-rock-band", 1, "wiki-23160352.json", [8], "Career challenges and the drum trainer"),
    ("workbook-06-08-green-day-rock-band", 2, "wiki-23160352.json", [6], "Four players perform different parts"),
    ("workbook-06-08-green-day-rock-band", 3, "wiki-23160352.json", [32], "Venues from different stages of Green Day's history"),
    ("workbook-06-07-mirror-s-edge-catalyst", 1, "wiki-43573181.json", [8], "Movement becomes a means of defence"),
    ("workbook-06-07-mirror-s-edge-catalyst", 2, "wiki-43573181.json", [7], "Runner Vision and routes through Glass"),
    ("workbook-06-07-mirror-s-edge-catalyst", 3, "wiki-43573181.json", [17], "Runners outside the city's network"),
    ("daily-06-05", 1, "wiki-59020828.json", [8], "Researching a response to the meteor"),
    ("daily-06-05", 2, "wiki-59020828.json", [4], "Resources, pollution and collective rules"),
    ("daily-06-05", 3, "wiki-59020828.json", [12], "The educational origins of Eco"),
    ("sonic", 4, "sonic-original-full.json", [1], "Designing Sega's new mascot"),
]

changes = []
for owner_id, index, basename, indices, heading in specs:
    source_path = FOLDER / basename
    source = json.loads(source_path.read_text(encoding="utf8"))
    page = next(iter(source["query"]["pages"].values()))
    lines = page["extract"].splitlines()
    paragraphs = [lines[n] for n in indices]
    if not all(len(paragraph.split()) >= 25 for paragraph in paragraphs):
        raise ValueError("Selection is not a substantive complete paragraph")
    body = "\n\n".join(paragraphs)
    owner = entries[owner_id]
    old = owner["body"][index]
    if body in owner["body"]:
        raise ValueError("Replacement would duplicate existing prose")
    revision = page["revisions"][0]["revid"]
    changes.append(dict(
        entry_id=owner_id, source_chapter_index=index,
        old_heading=owner["story_headings"][index], old_body=old,
        old_body_sha256=hashlib.sha256(old.encode()).hexdigest(),
        heading=heading, body=body, body_sha256=hashlib.sha256(body.encode()).hexdigest(),
        source=dict(title=page["title"], url="https://en.wikipedia.org/w/index.php?oldid=" + str(revision),
                    publisher="English Wikipedia contributors", license="Creative Commons Attribution-ShareAlike 4.0",
                    license_url="https://creativecommons.org/licenses/by-sa/4.0/",
                    attribution="Complete source paragraphs reproduced verbatim; card headings supplied editorially."),
        provenance=dict(source_file=source_path.relative_to(ROOT).as_posix(),
                        source_file_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
                        page_id=page["pageid"], revision_id=revision,
                        extract_line_indices=indices, source_paragraphs=paragraphs),
        reason="Replace a specifically identified generic template with a concrete account of the same game's mechanics, creation or setting. Archive all old prose; retain every media record and date."))

out = ROOT / "content/expansion/museum-playhub-clarity-pass5-candidate.json"
out.write_text(json.dumps(dict(schema_version=1, publication_status="awaiting_independent_review",
    replacements=changes, scope="37 bounded narrative replacements across13 actual game entries. All selected passages are complete original-game Wikipedia paragraphs. Existing good primary-reporting cards and all media/date fields remain unchanged."),
    ensure_ascii=True, indent=2) + "\n", encoding="utf8")
review_text = "\n\n".join(c["entry_id"] + " [" + str(c["source_chapter_index"]) + "] " + c["heading"] + "\n" + c["body"] for c in changes)
(FOLDER / "pass5-selected-paragraphs.txt").write_text(review_text, encoding="utf8")
print(json.dumps(dict(sha256=hashlib.sha256(out.read_bytes()).hexdigest(), replacements=len(changes),
                     source_paragraphs=sum(len(c["provenance"]["source_paragraphs"]) for c in changes),
                     words=sum(len(c["body"].split()) for c in changes))))
