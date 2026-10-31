"""Replace the remaining four calendar-observance teasers with source prose."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "build/research/playhub-semantic-coverage/wiki-clarity/pass6-root"


def main():
    catalog = json.loads((ROOT / "content/catalog.json").read_text(encoding="utf8"))
    by_id = {entry["id"]: entry for entry in catalog["entries"]}
    source = FOLDER / "candidate.json"
    rows = json.loads(source.read_text(encoding="utf8"))["changes"]
    changes = []
    for identifier in ("daily-03-17", "daily-03-14", "daily-03-18", "never-alone"):
        row = next(r for r in rows if r["entry_id"] == identifier and r["source_chapter_index"] == 0)
        paragraph = row["body"].split("\n\n")[0]
        sentence = re.split(r"(?<=[.!?])\s+(?=[A-Z])", paragraph)[0]
        assert sentence in paragraph and len(sentence) < 240
        old = by_id[identifier]
        changes.append(dict(entry_id=identifier, field="summary", old_value=old["summary"],
            old_value_sha256=hashlib.sha256(old["summary"].encode()).hexdigest(), value=sentence,
            source=row["source"], provenance=dict(source_file=row["provenance"]["source_file"],
                source_file_sha256=row["provenance"]["source_file_sha256"],
                revision_id=row["provenance"]["revision_id"], source_paragraph=paragraph,
                selected_character_span=[0, len(sentence)], full_source_sentence=True),
            reason="Use a complete concrete game-overview sentence instead of an unrelated observance introduction."))
        previous = old.get("event_semantics", "")
        retained = previous.split(". The published May 21 edition")[0] + "." if identifier == "never-alone" else ""
        changes.append(dict(entry_id=identifier, field="event_semantics", old_value=previous,
            old_value_sha256=hashlib.sha256(previous.encode()).hexdigest(), value=retained,
            reason="Remove only artificial calendar scheduling. The publisher-backed actual Never Alone release statement is retained; date fields and sources remain unchanged."))
    document = dict(schema_version=1, publication_status="independent_review_pending",
        field_corrections=changes, preserve_body_dates_media=True,
        text_source_candidate_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    out = FOLDER / "four-clear-game-summaries-candidate.json"
    out.write_text(json.dumps(document, ensure_ascii=True, indent=2) + "\n", encoding="utf8")
    print(json.dumps(dict(file=out.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
        summaries=[dict(id=r["entry_id"], length=len(r["value"]), text=r["value"]) for r in changes if r["field"] == "summary"])))


if __name__ == "__main__":
    main()
