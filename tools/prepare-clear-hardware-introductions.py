"""Freeze concrete hardware introductions and the DS first-release date."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "build/research/hardware-release-consolidation"
source_file = FOLDER / "wikipedia-hardware-introductions.json"
pages = {page["title"]: page for page in json.loads(source_file.read_text(encoding="utf8"))["query"]["pages"].values()}
owners = {entry["id"]: entry for entry in json.loads((ROOT / "content/catalog.json").read_text(encoding="utf8"))["entries"]}
changes = []


def add(identifier, title, heading, body, **notes):
    page = pages[title]
    old = owners[identifier]["body"][0]
    changes.append(dict(entry_id=identifier, source_chapter_index=0, old_body=old,
        old_body_sha256=hashlib.sha256(old.encode()).hexdigest(), body=body,
        body_sha256=hashlib.sha256(body.encode()).hexdigest(), heading=heading,
        reason="Replace a regional-launch warning with a clear introduction to the hardware; preserve the existing technical and game-history paragraphs.",
        source=dict(title=title, url="https://en.wikipedia.org/w/index.php?oldid=" + str(page["revisions"][0]["revid"]),
            publisher="English Wikipedia contributors", license="Creative Commons Attribution-ShareAlike4.0",
            license_url="https://creativecommons.org/licenses/by-sa/4.0/",
            attribution=notes.pop("attribution", "Complete Wikipedia sentences selected from the introduction; editorial heading supplied separately.")),
        provenance=dict(source_file=source_file.relative_to(ROOT).as_posix(),
            source_file_sha256=hashlib.sha256(source_file.read_bytes()).hexdigest(),
            page_id=page["pageid"], revision_id=page["revisions"][0]["revid"],
            **notes)))


ps3 = pages["PlayStation 3"]["extract"].splitlines()[0]
parts = re.split(r"(?<=\.) ", ps3)
assert len(parts) == 4, parts
spans = []
for index in (0, 1, 3):
    start = ps3.index(parts[index])
    spans.append([start, start + len(parts[index])])
add("playstation-3", "PlayStation 3", "Sony's seventh-generation home console",
    " ".join(parts[index] for index in (0, 1, 3)),
    extract_line_indices=[0], source_paragraphs=[ps3], selected_character_spans=spans)

ds = pages["Nintendo DS"]["extract"].splitlines()[0]
add("daily-12-02", "Nintendo DS", "Two screens and a touch interface", ds,
    extract_line_indices=[0], source_paragraphs=[ds], full_paragraph=True,
    attribution="Complete English Wikipedia introduction paragraph reproduced verbatim; heading supplied editorially.")

intell = pages["Intellivision"]["extract"].splitlines()[0]
phrase = " in 1979"
assert intell.count(phrase) == 1
body = intell.replace(phrase, "", 1)
add("intellivision", "Intellivision", "Mattel's home console", body,
    extract_line_indices=[0], source_paragraphs=[intell],
    editorial_omission=dict(text=phrase, source_start=intell.index(phrase),
        reason="Omit the local-test year from prose; preserve the existing1980 national-release chronology, supported by the cited Blue Sky Rangers primary history."),
    attribution="Wikipedia introduction adapted by omitting only the phrase 'in1979', which refers to the local test-market release. Remaining source wording retained; the existing national-release date stays1980.")

ds_html = FOLDER / "nintendo-ds-original-wikipedia.html"
html = ds_html.read_text(encoding="utf8")
assert "November 21, 2004" in re.sub("<[^>]*>", " ", html)
document = dict(schema_version=1, publication_status="candidate_requires_independent_review",
    replacements=changes,
    date_corrections=[dict(entry_id="daily-12-02", old_date=owners["daily-12-02"]["date"], year=2004,
        date=dict(month=11, day=21, precision="day", region=""),
        reason="One first commercial release stop, as given by the original Nintendo DS article infobox, instead of the inheritedDecember2 Japanese editorial slot.",
        date_provenance=dict(source_file=ds_html.relative_to(ROOT).as_posix(),
            source_file_sha256=hashlib.sha256(ds_html.read_bytes()).hexdigest(),
            source_page="https://en.wikipedia.org/wiki/Nintendo_DS", revision_id=pages["Nintendo DS"]["revisions"][0]["revid"],
            evidence="Infobox: Released / November21,2004 / DS: NA November21,2004"),
        event_semantics="First commercial release of the original Nintendo DS hardware.")],
    field_corrections=[dict(entry_id="daily-12-02", field="summary", old_value=owners["daily-12-02"]["summary"],
        value="Nintendo's dual-screen handheld combined a touchscreen, microphone and wireless play with traditional buttons and Game Boy Advance compatibility.",
        reason="Replace a Japanese-launch-only teaser with a clear description of the same original hardware.")])
path = FOLDER / "clear-hardware-introductions-candidate.json"
path.write_text(json.dumps(document, ensure_ascii=True, indent=2) + "\n", encoding="utf8")
(FOLDER / "clear-hardware-introductions-readable.txt").write_text("\n\n".join(
    row["entry_id"] + "\nOLD: " + row["old_body"] + "\nNEW: " + row["body"] for row in changes), encoding="utf8")
print(json.dumps(dict(candidate_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), replacements=len(changes)), indent=2))
