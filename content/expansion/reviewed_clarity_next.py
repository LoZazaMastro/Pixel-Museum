"""Source-only admission for the independently read additional clarity batches."""
from pathlib import Path
import copy
import hashlib
import json

BASE = "build/research/playhub-semantic-coverage/wiki-clarity/"
PLANS = (
    ("strong-first17/candidate.json", "strong-first17/root-independent-review.json"),
    ("additional-three/candidate.json", "additional-three/root-independent-review.json"),
    ("repeated-final23/candidate.json", "repeated-final23/root-independent-review.json"),
    ("pass6-root/candidate.json", "pass6-root/independent-fifty-two-card-review.json"),
    ("pass6-root/two-real-game-release-dates-candidate.json", "pass6-root/independent-two-real-game-release-dates-review.json"),
    ("pass6-root/four-clear-game-summaries-candidate.json", "pass6-root/four-clear-game-summaries-root-review.json"),
    ("secret-world-final/candidate.json", "secret-world-final/independent-two-card-review.json"),
    ("army-final/candidate.json", "army-final/independent-two-card-review.json"),
    ("final-five-root/candidate.json", "final-five-root/independent-five-card-review.json"),
    ("final-seven-editorial/candidate.json", "final-seven-editorial/root-independent-review.json"),
    ("build/research/nobuyoshi-sano-primary-portrait/three-concrete-career-cards-candidate.json", "build/research/nobuyoshi-sano-primary-portrait/independent-three-concrete-career-cards-review.json"),
    ("remaining-semantic-three/five-additional-concrete-cards-candidate.json", "remaining-semantic-three/independent-five-additional-concrete-cards-review.json"),
    ("build/research/gba-sp-launch-and-concrete-article/four-wikipedia-cards-launch-without-regional-prose-candidate.json", "build/research/gba-sp-launch-and-concrete-article/independent-four-concrete-cards-real-launch-review.json"),
    ("new-bounded-current-audit/sayonara-three/three-concrete-sayonara-cards-clarity-edited-candidate.json", "new-bounded-current-audit/sayonara-three/independent-three-clarity-edited-sayonara-cards-review.json"),
    ("build/research/mega-drive-three-concrete-cards/three-concrete-wikipedia-mega-drive-cards-clear-identities-candidate.json", "build/research/mega-drive-three-concrete-cards/independent-three-concrete-mega-drive-cards-review.json"),
    ("sakaguchi-bounded-two/two-concrete-sakaguchi-cards-standalone-fantasian-candidate.json", "sakaguchi-bounded-two/root-independent-two-standalone-sakaguchi-cards-review.json"),
    ("build/research/gta2-three-concrete-cards/three-concrete-gta2-cards-multiplier-claim-omitted-candidate.json", "build/research/gta2-three-concrete-cards/independent-three-known-error-omitted-gta2-cards-review.json"),
    ("build/research/vanquish-concrete-gameplay-production-cards/three-concrete-vanquish-cards-unclear-qualifier-omitted-candidate.json", "build/research/vanquish-concrete-gameplay-production-cards/independent-three-clear-vanquish-cards-review.json"),
    ("build/research/yakuza-one-duplicate-card-production-fix/one-concrete-yakuza-production-card-clear-lead-candidate.json", "build/research/yakuza-one-duplicate-card-production-fix/root-independent-one-yakuza-production-card-review.json"),
    ("build/research/bg3-early-access-date-minimal-fix/one-bg3-early-access-date-correction-clean-attribution-candidate.json", "build/research/bg3-early-access-date-minimal-fix/root-independent-one-bg3-date-correction-review.json"),
)

POST_MEDIA_PLANS = (
    ("build/research/atlus-persona-concrete-calendar-card/one-concrete-persona-social-links-with-definition-candidate.json", "build/research/atlus-persona-concrete-calendar-card/independent-one-persona-definition-social-links-review.json"),
)


def check_file(root, file, sha):
    if hashlib.sha256((root / file).read_bytes()).hexdigest() != sha:
        raise ValueError("An independently reviewed clarity source changed: " + file)


def apply(entries, root, stage='before_media'):
    if stage not in ('before_media', 'after_media'):
        raise ValueError('Unknown reviewed clarity join stage')
    root = Path(root)
    owners = {entry["id"]: entry for entry in entries}
    for entry in entries:
        owners.update({feature["id"]: feature for feature in entry.get("editorial_features", [])})
    results = []
    for candidate_relative, receipt_relative in (POST_MEDIA_PLANS if stage == 'after_media' else PLANS):
        candidate = root / (candidate_relative if candidate_relative.startswith("build/") else BASE + candidate_relative)
        receipt = root / (receipt_relative if receipt_relative.startswith("build/") else BASE + receipt_relative)
        if not candidate.is_file() or not receipt.is_file():
            results.append(dict(candidate=candidate_relative, status="not_available"))
            continue
        peer = json.loads(receipt.read_text(encoding="utf8"))
        if peer.get("status") != "PASS":
            results.append(dict(candidate=candidate_relative, status="not_admitted"))
            continue
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if peer.get("candidate_sha256") != digest:
            raise ValueError("Additional clarity candidate changed after peer review: " + candidate_relative)
        doc = json.loads(candidate.read_text(encoding="utf8"))
        rows = doc.get("replacements", doc.get("changes", doc.get("field_corrections", [])))
        changed = 0
        for row in rows:
            owner = owners[row["entry_id"]]
            archive = owner.setdefault("provenance", {}).setdefault("additional_reviewed_clarity", [])
            attribution = dict(candidate_sha256=digest, independent_review=receipt.relative_to(root).as_posix(),
                original=copy.deepcopy(row))
            if "body" in row:
                index = row["source_chapter_index"]
                if owner["body"][index] == row["body"]:
                    continue
                if owner["body"][index] != row["old_body"] or hashlib.sha256(owner["body"][index].encode()).hexdigest() != row["old_body_sha256"]:
                    raise ValueError("Additional clarity old paragraph changed: " + owner["id"])
                if hashlib.sha256(row["body"].encode()).hexdigest() != row["body_sha256"]:
                    raise ValueError("Additional clarity replacement text hash changed")
                provenance = row["provenance"]
                if row.get("source"):
                    check_file(root, provenance["source_file"], provenance["source_file_sha256"])
                else:
                    check_file(root, provenance["original_record_file"], provenance["original_record_sha256"])
                    start, end = provenance["selected_character_span"]
                    if row["old_body"][start:end] != row["body"]:
                        raise ValueError("Retained concrete prefix changed")
                headings = owner.setdefault("story_headings", [])
                while len(headings) < len(owner["body"]):
                    headings.append("")
                owner["body"][index], headings[index] = row["body"], row["heading"]
                if row.get("source"):
                    source = copy.deepcopy(row["source"])
                    if not any(item.get("url") == source["url"] for item in owner.get("sources", [])):
                        owner.setdefault("sources", []).append(source)
                    credit = "Includes English Wikipedia passages credited by article revision under CC BY-SA 4.0; card headings supplied editorially."
                    if credit not in owner.get("editorial_credit", ""):
                        owner["editorial_credit"] = (owner.get("editorial_credit", "").rstrip() + " " + credit).strip()
            elif "old_date" in row:
                if owner.get("year") == row["year"] and owner.get("date") == row["date"]:
                    continue
                if owner.get("date") != row["old_date"]:
                    raise ValueError("Reviewed artificial calendar date changed: " + owner["id"])
                check_file(root, row["source_file"], row["source_file_sha256"])
                owner["year"], owner["date"] = row["year"], copy.deepcopy(row["date"])
                owner["date_provenance"] = dict(source=copy.deepcopy(row["source"]),
                    source_file_sha256=row["source_file_sha256"], verified_visible_infobox_date=row["verified_visible_infobox_date"])
                if not any(item.get("url") == row["source"]["url"] for item in owner.get("sources", [])):
                    owner.setdefault("sources", []).append(copy.deepcopy(row["source"]))
            elif "field" in row:
                field = row["field"]
                if field not in ("summary", "subtitle", "event_semantics"):
                    raise ValueError("Unsupported clarity field: " + field)
                if owner.get(field, "") == row["value"]:
                    continue
                old = owner.get(field, "")
                if old != row["old_value"] or hashlib.sha256(old.encode()).hexdigest() != row["old_value_sha256"]:
                    raise ValueError("Reviewed old clarity field changed: " + owner["id"])
                provenance = row.get("provenance")
                if provenance:
                    check_file(root, provenance["source_file"], provenance["source_file_sha256"])
                if field == "event_semantics" and not row["value"]:
                    owner.pop(field, None)
                else:
                    owner[field] = row["value"]
            else:
                raise ValueError("Unknown additional clarity correction")
            archive.append(attribution)
            changed += 1
        results.append(dict(candidate=candidate_relative, status="PASS", candidate_sha256=digest,
            changed_records=changed, reviewed_records=len(rows)))
    return dict(status="PASS", batches=results)
