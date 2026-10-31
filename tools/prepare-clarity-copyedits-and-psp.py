"""Preserve concrete passages, remove repeated tails, and fix PSP's release anchor."""
from pathlib import Path
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "build/research/playhub-semantic-coverage/wiki-clarity/pass4"
catalog = json.loads((ROOT / "content/catalog.json").read_text(encoding="utf8"))
owners = {entry["id"]: entry for entry in catalog["entries"]}
frozen = FOLDER / "copyedit-frozen-source-entries.json"
ids = {row["entry_id"] for row in json.loads((FOLDER / "remaining-concrete-prefixes-research.json").read_text(encoding="utf8"))}
ids.add("workbook-06-25-phantom-covert-ops")
frozen.write_text(json.dumps([owners[identifier] for identifier in sorted(ids)], ensure_ascii=True, indent=2) + "\n", encoding="utf8")
changes = []


def replacement(identifier, index, body, heading, source, source_file=frozen, **provenance):
    entry = owners[identifier]
    old = entry["body"][index]
    changes.append(dict(entry_id=identifier, source_chapter_index=index,
        old_heading=entry["story_headings"][index], old_body=old,
        old_body_sha256=hashlib.sha256(old.encode()).hexdigest(), heading=heading,
        body=body, body_sha256=hashlib.sha256(body.encode()).hexdigest(), source=source,
        provenance=dict(source_file=source_file.relative_to(ROOT).as_posix(),
                        source_file_sha256=hashlib.sha256(source_file.read_bytes()).hexdigest(), **provenance),
        reason="Retain concrete facts and actions, remove repeated editorial boilerplate or artificial calendar framing. Preserve old wording in provenance."))


rows = json.loads((FOLDER / "remaining-concrete-prefixes-research.json").read_text(encoding="utf8"))
for row in rows:
    identifier, index = row["entry_id"], row["paragraph"]
    if identifier == "workbook-05-13-playstation-portable-psp" and index == 1:
        continue  # The whole announcement card receives a concrete hardware account below.
    entry = owners[identifier]
    old = entry["body"][index]
    assert old == row["old"]
    body = row["prefix"]
    removed_calendar_sentence = None
    if identifier == "daily-05-20" and index == 2:
        removed_calendar_sentence = "World Bee Day therefore gains a concrete playable counterpart linked to the daily work of a pollinator."
        assert body.endswith(removed_calendar_sentence)
        body = body[:-len(removed_calendar_sentence)].rstrip()
    assert len(body.split()) >= 45 and "World Bee Day" not in body
    existing_source = next((source for source in entry.get("sources", []) if source.get("url")), None)
    assert existing_source
    source = copy.deepcopy(existing_source)
    source["attribution"] = "Existing museum prose retained; repeated editorial tail removed. No source publication is quoted or newly licensed by this copyedit."
    replacement(identifier, index, body, entry["story_headings"][index], source,
                copyedit_only=True, retained_prefix_characters=[0, len(body)],
                removed_tail_marker=row["marker"], removed_calendar_sentence=removed_calendar_sentence)

psp_id = "workbook-05-13-playstation-portable-psp"
psp_path = FOLDER / "psp-full.json"
page = next(iter(json.loads(psp_path.read_text(encoding="utf8"))["query"]["pages"].values()))
revision = page["revisions"][0]["revid"]
primary_url = "https://sonyinteractive.com/en/press-releases/2004/psp-enters-the-market-on-december-12-2004-at-19800-yen-in-japan/"
primary_path = FOLDER / "psp-original-launch-primary.html"
primary = dict(title="PSP enters the market on December12,2004 in Japan", url=primary_url,
               publisher="Sony Computer Entertainment / Sony Interactive Entertainment,27October2004",
               attribution="Primary manufacturer release-date record. Bibliographic reference; original rights retained.")
for index, line, heading in [(0, 0, "Sony's first PlayStation handheld"),
                             (1, 22, "The original PSP-1000 hardware")]:
    paragraph = page["extract"].splitlines()[line]
    body = paragraph
    spans = None
    if index == 0:
        first_end = paragraph.index(".") + 1
        final_start = paragraph.index("As a seventh generation console,")
        spans = [[0, first_end], [final_start, len(paragraph)]]
        body = "\n\n".join(paragraph[start:end] for start, end in spans)
    replacement(psp_id, index, body, heading,
        dict(title="PlayStation Portable", url="https://en.wikipedia.org/w/index.php?oldid=" + str(revision),
             publisher="English Wikipedia contributors", license="Creative Commons Attribution-ShareAlike4.0",
             license_url="https://creativecommons.org/licenses/by-sa/4.0/",
             attribution="Two complete source sentences selected from the same paragraph; regional release list omitted; card heading supplied editorially." if spans else "Complete source paragraph reproduced verbatim; card heading supplied editorially."),
        source_file=psp_path, page_id=page["pageid"], revision_id=revision,
        extract_line_indices=[line], source_paragraphs=[paragraph])
    if spans:
        changes[-1]["provenance"]["selected_character_spans"] = spans
    changes[-1]["additional_sources"] = [primary]

phantom_id = "workbook-06-25-phantom-covert-ops"
product = FOLDER / "phantom-publisher-product.html"
source = dict(title="Phantom: Covert Ops / developer game page", url="https://ndreams.com/games/phantom-covert-ops/",
              publisher="nDreams", license="Original museum prose based on the developer's public game description; no publisher text reproduced verbatim.",
              attribution="Factual gameplay description supplied editorially. Original developer publication and imagery retain their rights.")
phantom = [
    (1, "Moving through the wetlands by kayak",
     "The player travels through hostile wetlands in a military kayak. Water routes let the operative approach beneath enemy walkways or move past guarded positions while remaining seated in the craft. The kayak supplies the means of travel throughout the mission, so choosing a route also means deciding how close to move to the people guarding it."),
    (2, "Avoiding a patrol or attacking from cover",
     "Phantom offers both concealed approaches and armed encounters. The operative carries military weapons and equipment, but can also attempt to pass enemies without being noticed. A route below a walkway can therefore serve a different purpose from an exposed approach: it offers a way to infiltrate, while another position may be used to ambush a guard."),
    (3, "A campaign built around the same seated role",
     "The campaign gives the operative a single night to prevent a wider conflict. Its missions take place across the wetland setting and retain the same role of travelling by kayak. The developer describes multiple missions across an expansive location, with additional modes and unlockable content extending the game beyond completing that campaign.")]
for index, heading, body in phantom:
    replacement(phantom_id, index, body, heading, source, source_file=product,
                authored_from_primary=True, developer_subject="Phantom: Covert Ops (2020)",
                primary_evidence=["Dispatched into remote, hostile wetlands in your tactical kayak",
                                  "Engage your targets lethally or infiltrate unnoticed from within the shadows",
                                  "Sneak beneath enemy walkways, or ambush hostiles",
                                  "Cinematic campaign layered with multiple missions across a rich, expansive location"])

entry = owners[psp_id]
out = dict(schema_version=1, publication_status="awaiting_independent_review", replacements=changes,
    field_corrections=[dict(entry_id=psp_id, field="summary", old_value=entry["summary"],
        value="Sony's first PlayStation handheld combines a widescreen display, UMD optical media and wireless connectivity.",
        reason="Describe the hardware rather than using the2003 announcement as the public summary.")],
    date_corrections=[dict(entry_id=psp_id, old_date=entry["date"], year=2004,
        date=dict(month=12, day=12, precision="day", region=""), source=primary,
        source_file=primary_path.relative_to(ROOT).as_posix(),
        source_file_sha256=hashlib.sha256(primary_path.read_bytes()).hexdigest(),
        reason="One canonical PSP release stop,12December2004; remove the13May2003 announcement chronology stop.")],
    scope="33 concrete passages retained after removing repeated boilerplate; one complete PSP hardware paragraph and two complete overview sentences replace announcement framing and regional date lists, with primary Sony release-date correction; three clear original Phantom descriptions use primary developer facts because no English Wikipedia game article was found. No media deleted, reused or reassigned.")
p = ROOT / "content/expansion/museum-clarity-copyedits-psp-phantom-candidate.json"
p.write_text(json.dumps(out, ensure_ascii=True, indent=2) + "\n", encoding="utf8")
(FOLDER / "final-copyedits-selected.txt").write_text("\n\n".join(c["entry_id"] + " [" + str(c["source_chapter_index"]) + "]\n" + c["body"] for c in changes), encoding="utf8")
print(json.dumps(dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(), replacements=len(changes),
                     words=sum(len(c["body"].split()) for c in changes))))
