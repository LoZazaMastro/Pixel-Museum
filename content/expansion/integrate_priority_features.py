"""Join reviewed writing without replacing the source collection.

The authoring documents retain cards, research notes and media briefs.  Runtime
blocks contain one narrative plus source-to-paragraph provenance.  This module
is pure during assembly: only the caller writes the resulting catalogue/audit.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

CONTENT = Path(__file__).resolve().parents[1]
BATCH_FILES = ("editorial-priority-music-design.json", "editorial-priority-people.json",
               "editorial-computing-networks-02.json", "editorial-people-regions-03.json", "editorial-cultures-production-04.json", "editorial-authorship-design-05.json", "editorial-composer-methods-06.json", "editorial-systems-authors-06.json", "editorial-music-craft-07.json", "editorial-design-communities-08.json", "editorial-preservation-worlds-09.json", "editorial-hardware-choices-11.json", "editorial-art-direction-12.json", "editorial-people-practices-10.json", "editorial-tools-audio-13.json", "editorial-production-design-16.json", "editorial-markets-machines-14.json", "editorial-networks-history-15.json")
HELD_DRAFT_IDS = frozenset(("feature-education-timesharing", "feature-plato-community",
                            "feature-joyce-weisbecker-work", "feature-muriel-tramis-history",
                            "feature-rebecca-heineman-ports", "feature-jarra-steel-commission",
                            "feature-india-production-credit", "feature-african-development-networks",
                            "feature-middle-east-independent-scenes", "feature-latin-american-making",
                            "feature-finnish-demos-to-games", "feature-russia-eastern-europe-development",
                            "feature-brenda-romero-systems", "feature-bob-bates-adventure",
                            "feature-jane-jensen-mystery", "feature-fukio-mitsuji-families",
                            "feature-winifred-phillips-adaptive", 
                             "feature-server-dependent-worlds", "feature-yoshitaka-amano-images", "feature-french-graphic-adventures", "feature-mobile-before-appstores", "feature-twine-personal-stories", "feature-indigenous-self-representation", "feature-accessibility-player-knowledge", "feature-shareware-distribution", "feature-game-audio-adaptive", "feature-engine-licensing", "feature-indie-tools-web", "feature-musicians-fm-pcm", "feature-survival-horror-sound", "feature-souls-learning-communities", "feature-north-american-crash", "feature-digital-indie-console", "feature-app-store-change", "feature-streamers-and-play", "feature-labour-and-credit", "feature-living-history-method"))
STANDALONE_LINK_ORDER = (
    "feature-mabel-addis-classroom", "feature-ed-smith-apf",
    "feature-umurangi-looking", "feature-riven-performance-audio",
    "feature-kondo-functional-music", "feature-kazuko-shibuya-pixel-art",
    "feature-maestro-nobuo-uematsu", "feature-akira-yamaoka-noise", "feature-jessica-curry-worlds",
    "feature-games-in-museums",
    "feature-berlin-game-museum",
)
STANDALONE_IDS = frozenset(STANDALONE_LINK_ORDER)
ATTACHED_PARENTS = {
    "feature-journey-music-companionship": "journey",
    "feature-monument-valley-art": "workbook-04-03-monument-valley",
    "feature-celeste-assistance": "celeste",
    "feature-paperwork-ethical-systems": "papers-please",
    "feature-tetsuya-mizuguchi-synesthesia": "wikipedia-101230",
    "feature-darren-korb-ashley-barrett": "wikipedia-30602654",
    "feature-bertie-fair": "bertie-the-brain",
    "feature-nimrod-demonstration": "nimrod",
    "feature-oxo-research": "oxo",
    "feature-tennis-open-house": "tennis-for-two",
    "feature-spacewar-sharing": "spacewar",
    "feature-brown-box-team": "brown-box",
    "feature-lawson-cartridge-team": "channel-f",
    "feature-carol-shaw-river": "carol-shaw",
    "feature-colossal-cave-language": "wikipedia-261798",
    "feature-mud-online-identity": "mud",
    "feature-activision-credit": "wikipedia-445630",
    "feature-coin-op-location-test": "pong",
    "feature-programmable-living-room": "atari-vcs",
    "feature-dona-bailey-arcade": "dona-bailey",
    "feature-dani-bunten-social": "mule",
    "feature-tectoy-localization": "tectoy",
    "feature-gunpei-yokoi-engineering": "game-boy",
    "feature-satoru-iwata-listening": "daily-12-06",
    "feature-latin-american-art-voices": "dandara",
    "feature-korean-pc-bang": "starcraft",
    "feature-amy-hennig-storycraft": "workbook-11-01-uncharted-3-drake-s-deception",
    "feature-nasir-gebelli-and-teams": "wikipedia-52753",
    "feature-keita-takahashi-play": "katamari-damacy",
    "feature-disco-elysium-authorship": "workbook-10-15-disco-elysium",
    "feature-hirokazu-tanaka-sound": "game-boy",
    "feature-shigeru-miyamoto-team": "super-mario-bros",
    "feature-shinji-mikami-team": "wikipedia-1789064",
    "feature-hironobu-sakaguchi-production": "daily-11-25",
    "feature-hideo-kojima-interface": "workbook-09-03-metal-gear-solid",
    "feature-sid-meier-systems": "workbook-02-24-sid-meier",
    "feature-will-wright-simulation": "simcity",
    "feature-john-carmack-engineering": "workbook-08-20-john-carmack",
    "feature-john-romero-levels": "doom",
    "feature-yoko-shimomura-craft": "street-fighter-ii",
    "feature-rob-hubbard-c64": "commodore-64",
    "feature-yuzo-koshiro-fm": "daily-12-12",
    "feature-david-wise-dkc": "wikipedia-153399",
    "feature-yasunori-mitsuda-rpg": "workbook-03-11-chrono-trigger",
    "feature-kim-swift-spatial-puzzles": "workbook-10-10-portal",
    "feature-localization-authorship": "workbook-04-02-final-fantasy-vi",
    "feature-fighting-game-communities": "street-fighter-ii",
    "feature-rating-hearings": "workbook-10-08-mortal-kombat",
    "feature-tetris-travel": "tetris",
    "feature-myst-handcrafted-world": "myst",
    "feature-polygon-camera-language": "super-mario-64",
    "feature-demoscene-tools": "preserving-play",
    "feature-odyssey-overlays": "odyssey",
    "feature-spectrum-bedroom-networks": "zx-spectrum",
    "feature-loading-screen-culture": "commodore-64",
    "feature-commercial-availability-study": "preserving-play",
    "feature-repair-sustainability": "preserving-play",
    "feature-playstation-industrial-design": "playstation",
    "feature-switch-hybrid-routine": "switch",
    "feature-handheld-two-screens": "daily-12-02",
    "feature-accessibility-hardware": "daily-12-03",
    "feature-sprites-readable-art": "wikipedia-66495",
    "feature-sonic-team-art": "sonic",
    "feature-yoji-shinkawa-design": "wikipedia-595618",
    "feature-wii-social-design": "wii",
    "feature-halo-accessible-fps": "xbox-halo",
    "feature-online-console-ritual": "workbook-12-21-phantasy-star-online",
    "feature-portable-pc-return": "steam-deck",
    "feature-roberta-williams-authorship": "roberta-williams",
    "feature-video-soft-business": "channel-f",
    "feature-credits-as-historical-record": "adventure",
    "feature-lena-raine-movement": "celeste",
    "feature-doom-mod-authorship": "doom",
    "feature-c64-sid-instrument": "commodore-64",
    "feature-3d-art-labour": "workbook-11-11-the-elder-scrolls-v-skyrim",
    "feature-japanese-rpg-writing": "wikipedia-760191",
    "feature-animal-crossing-time": "wikipedia-540952",
    "feature-minecraft-making-together": "minecraft",
    "feature-vr-presence-comfort": "workbook-03-23-half-life-alyx",
    "feature-valve-team-tools": "wikipedia-575509",
    "feature-china-game-networks": "wikipedia-33952595",
    "feature-steam-library-ownership": "steam",
    "feature-mmo-community-work": "workbook-05-06-eve-online",
    "feature-pandemic-shared-spaces": "animal-crossing",
    "feature-pong-operators": "wikipedia-453246",
    "feature-space-invaders-space": "space-invaders",
    "feature-pac-man-audience": "pac-man",
    "feature-nintendo-license-network": "nes",
    "feature-portable-engineering": "game-boy",
    "feature-sega-saturn-multiple-markets": "sega-saturn",
    "feature-playstation2-production": "playstation-2",
}
ALL_IDS = STANDALONE_IDS | ATTACHED_PARENTS.keys()
SOURCE_FIELDS = ("id", "title", "url", "publisher", "source_type", "locator",
                 "checked", "access_note", "rights", "license", "license_url",
                 "attribution", "chapter_urls", "publication_date")
RUNTIME_MARKER = "reviewed_priority_features_2026_10"
MEDIA_FILE = "priority-feature-media-additions.json"
MEDIA_FILES = (MEDIA_FILE, "priority-feature-media-next.json", "media-collection-batch-03.json", "priority-feature-context-media-01.json", "priority-feature-context-media-02.json", "priority-feature-context-media-04.json", "priority-feature-context-media-05.json", "priority-feature-context-media-06.json", "priority-feature-context-media-07.json", "priority-feature-context-media-08.json", "priority-feature-context-media-09.json", "priority-feature-context-media-10.json", "priority-feature-context-media-11.json", "priority-feature-context-media-12.json", "priority-feature-context-media-13.json")


def load_documents(directory):
    review = json.loads((directory.parent / "editorial/computing-networks-review-02.json").read_text(encoding="utf-8"))
    source = directory / "editorial-computing-networks-02.json"
    if hashlib.sha256(source.read_bytes()).hexdigest() != review["batch_sha256"]:
        raise ValueError("Computing feature source changed since independent review")
    decisions = {row["feature_id"]: row for row in review["entries"]}
    for identifier in ("feature-colossal-cave-language", "feature-mud-online-identity",
                       "feature-activision-credit", "feature-coin-op-location-test",
                       "feature-programmable-living-room"):
        if decisions[identifier].get("parent_id") != ATTACHED_PARENTS[identifier]:
            raise ValueError("Computing feature placement changed since review: " + identifier)
    people_review = json.loads((directory.parent / "editorial/people-regions-review-03.json").read_text(encoding="utf-8"))
    people_source = directory / "editorial-people-regions-03.json"
    if hashlib.sha256(people_source.read_bytes()).hexdigest() != people_review["batch_sha256"]:
        raise ValueError("People/regions feature source changed since independent review")
    people_decisions = {row["feature_id"]: row for row in people_review["entries"]}
    for identifier in ("feature-dona-bailey-arcade", "feature-dani-bunten-social",
                       "feature-tectoy-localization", "feature-gunpei-yokoi-engineering",
                       "feature-satoru-iwata-listening"):
        decision = people_decisions[identifier]
        if (decision.get("parent_id") != ATTACHED_PARENTS[identifier]
                or decision.get("placement_decision") != "attach_one_parent"
                or decision.get("content_decision") != "independent_source_review_passed"):
            raise ValueError("People/regions placement changed since review: " + identifier)
    cultures_review = json.loads((directory.parent / "editorial/cultures-production-review-04.json").read_text(encoding="utf-8"))
    cultures_source = directory / "editorial-cultures-production-04.json"
    if hashlib.sha256(cultures_source.read_bytes()).hexdigest() != cultures_review["batch_sha256"]:
        raise ValueError("Cultures/production feature source changed since independent review")
    cultures_decisions = {row["feature_id"]: row for row in cultures_review["entries"]}
    for identifier in ("feature-latin-american-art-voices", "feature-korean-pc-bang"):
        decision = cultures_decisions[identifier]
        if (decision.get("parent_id") != ATTACHED_PARENTS[identifier]
                or decision.get("placement_decision") != "attach_one_parent"
                or decision.get("content_decision") != "independent_source_review_passed"):
            raise ValueError("Cultures/production placement changed since review: " + identifier)
    authorship_review = json.loads((directory.parent / "editorial/authorship-design-review-05.json").read_text(encoding="utf-8"))
    authorship_source = directory / "editorial-authorship-design-05.json"
    if hashlib.sha256(authorship_source.read_bytes()).hexdigest() != authorship_review["batch_sha256"]:
        raise ValueError("Authorship/design feature source changed since independent review")
    authorship_decisions = {row["feature_id"]: row for row in authorship_review["entries"]}
    for identifier in ("feature-amy-hennig-storycraft", "feature-nasir-gebelli-and-teams",
                       "feature-keita-takahashi-play", "feature-disco-elysium-authorship"):
        decision = authorship_decisions[identifier]
        if (decision.get("parent_id") != ATTACHED_PARENTS[identifier]
                or decision.get("placement_decision") != "attach_one_parent"
                or decision.get("content_decision") != "independent_specific_source_review_passed"):
            raise ValueError("Authorship/design placement changed since review: " + identifier)
    composer_review = json.loads((directory.parent / "editorial/composer-methods-review-06.json").read_text(encoding="utf-8"))
    composer_source = directory / "editorial-composer-methods-06.json"
    if hashlib.sha256(composer_source.read_bytes()).hexdigest() != composer_review["batch_sha256"]:
        raise ValueError("Composer methods source changed since independent review")
    composer_decision = next(row for row in composer_review["entries"]
                             if row["feature_id"] == "feature-hirokazu-tanaka-sound")
    if (composer_decision.get("parent_id") != ATTACHED_PARENTS[composer_decision["feature_id"]]
            or composer_decision.get("placement_decision") != "attach_one_parent"
            or composer_decision.get("content_decision") != "independent_specific_source_review_passed"):
        raise ValueError("Composer methods placement changed since review")
    systems_review = json.loads((directory.parent / "editorial/systems-authors-review-06.json").read_text(encoding="utf-8"))
    systems_source = directory / "editorial-systems-authors-06.json"
    if hashlib.sha256(systems_source.read_bytes()).hexdigest() != systems_review["draft_sha256"]:
        raise ValueError("Systems/authors feature source changed since independent review")
    if systems_review.get("status") != "independent_source_schema_budget_and_placement_review_complete_no_factual_blocker":
        raise ValueError("Systems/authors source review is incomplete")
    systems_decisions = {row["feature_id"]: row for row in systems_review["features"]}
    for identifier in ("feature-shigeru-miyamoto-team", "feature-shinji-mikami-team",
                       "feature-hironobu-sakaguchi-production", "feature-hideo-kojima-interface",
                       "feature-sid-meier-systems", "feature-will-wright-simulation",
                       "feature-john-carmack-engineering", "feature-john-romero-levels"):
        decision = systems_decisions[identifier]
        if (decision["placement"].get("parent_id") != ATTACHED_PARENTS[identifier]
                or decision["placement"].get("mode") != "attach_once"
                or decision.get("factual_review") != "pass_with_named_primary_account_limits"):
            raise ValueError("Systems/authors placement changed since review: " + identifier)
    music_review = json.loads((directory.parent / "editorial/music-craft-review-07.json").read_text(encoding="utf-8"))
    if hashlib.sha256((directory / "editorial-music-craft-07.json").read_bytes()).hexdigest() != music_review["batch_sha256"]:
        raise ValueError("Music craft source changed since independent review")
    for row in music_review["entries"]:
        identifier = row["feature_id"]
        if identifier in STANDALONE_IDS and (row.get("placement_decision") != "admit_illustrated_distinct_subject"
                or row.get("content_decision") != "independent_source_review_passed"):
            raise ValueError("Music standalone placement changed since review: " + identifier)
        if identifier in ATTACHED_PARENTS and (row.get("parent_id") != ATTACHED_PARENTS[identifier]
                or row.get("placement_decision") != "attach_one_parent"
                or row.get("content_decision") != "independent_source_review_passed"):
            raise ValueError("Music craft placement changed since review: " + identifier)
    design_review = json.loads((directory.parent / "editorial/design-communities-review-08.json").read_text(encoding="utf-8"))
    if hashlib.sha256((directory / "editorial-design-communities-08.json").read_bytes()).hexdigest() != design_review["batch_sha256"]:
        raise ValueError("Design/community source changed since independent review")
    for row in design_review["entries"]:
        identifier = row["feature_id"]
        if (row.get("parent_id") != ATTACHED_PARENTS[identifier]
                or row.get("placement_decision") != "attach_one_parent"
                or row.get("content_decision") != "independent_source_review_passed"):
            raise ValueError("Design/community placement changed since review: " + identifier)
    preservation_review = json.loads((directory.parent / "editorial/preservation-worlds-review-09.json").read_text(encoding="utf-8"))
    if hashlib.sha256((directory / "editorial-preservation-worlds-09.json").read_bytes()).hexdigest() != preservation_review["batch_sha256"]:
        raise ValueError("Preservation source changed since independent review")
    for row in preservation_review["entries"]:
        identifier = row["feature_id"]
        if identifier in ATTACHED_PARENTS and (row.get("parent_id") != ATTACHED_PARENTS[identifier]
                or row.get("placement_decision") != "attach_one_parent"
                or row.get("content_decision") != "independent_source_review_passed"):
            raise ValueError("Preservation placement changed since review: " + identifier)
    hardware_review = json.loads((directory.parent / "editorial/hardware-choices-review-11.json").read_text(encoding="utf-8"))
    hardware_path = directory / "editorial-hardware-choices-11.json"
    if (hashlib.sha256(hardware_path.read_bytes()).hexdigest() != hardware_review["draft_sha256"]
            or hardware_review.get("status") != "source_schema_budget_and_placement_pass_with_two_wording_fixes_resolved"):
        raise ValueError("Hardware choices source changed or review incomplete")
    hardware_drafts = {row["id"]: row for row in json.loads(hardware_path.read_text(encoding="utf-8"))["entries"]}
    for decision in hardware_review["placement"]:
        identifier=decision["feature_id"]
        if decision["parent_id"] != ATTACHED_PARENTS[identifier]:
            raise ValueError("Hardware feature placement changed: " + identifier)
    for checked in hardware_review["checks"]:
        actual=hashlib.sha256(json.dumps(hardware_drafts[checked["id"]]["body"],ensure_ascii=False,separators=(",", ":")).encode()).hexdigest()
        if actual != checked["body_sha256"]:
            raise ValueError("Hardware reviewed body changed: " + checked["id"])
    art_review=json.loads((directory.parent / "editorial/art-direction-review-12.json").read_text(encoding="utf-8"))
    if hashlib.sha256((directory / "editorial-art-direction-12.json").read_bytes()).hexdigest()!=art_review["batch_sha256"]:
        raise ValueError("Art-direction source changed since independent review")
    for decision in art_review["entries"]:
        identifier=decision["feature_id"]
        if identifier in ATTACHED_PARENTS and (decision.get("parent_id")!=ATTACHED_PARENTS[identifier] or decision.get("content_decision")!="independent_source_review_passed" or decision.get("placement_decision")!="attach_one_parent"):
            raise ValueError("Art-direction placement changed: " + identifier)
    practices_review=json.loads((directory.parent / "editorial/people-practices-review-10-native.json").read_text(encoding="utf-8"))
    if (hashlib.sha256((directory / "editorial-people-practices-10.json").read_bytes()).hexdigest()!=practices_review["batch_sha256"] or practices_review["blocking_findings"] or practices_review["result"]!="pass_content_three_attachment_recommendations_five_distinct_media_holds"):
        raise ValueError("People/practices review incomplete or changed")
    for decision in practices_review["entries"]:
        identifier=decision["id"]
        if identifier in ATTACHED_PARENTS and (decision["placement"]["parent_id"]!=ATTACHED_PARENTS[identifier] or decision["placement"]["recommendation"]!="attach_preserve_body"):
            raise ValueError("People/practices placement changed: " + identifier)
    tools_review=json.loads((directory.parent / "editorial/tools-audio-review-13-native.json").read_text(encoding="utf-8"))
    if (hashlib.sha256((directory / "editorial-tools-audio-13.json").read_bytes()).hexdigest()!=tools_review["batch_sha256"] or tools_review["blocking_findings"] or tools_review["copyedits_required"] or tools_review["result"]!="content_pass_four_attachments_four_distinct_media_holds"):
        raise ValueError("Tools/audio review incomplete or changed")
    for decision in tools_review["entries"]:
        identifier=decision["id"]
        if identifier in ATTACHED_PARENTS and (decision["placement"]["parent_id"]!=ATTACHED_PARENTS[identifier] or decision["placement"]["recommendation"]!="additive_attachment_preserve_body"):
            raise ValueError("Tools/audio placement changed: " + identifier)
    production_review=json.loads((directory.parent / "editorial/production-design-review-16.json").read_text(encoding="utf-8"))
    if (hashlib.sha256((directory / "editorial-production-design-16.json").read_bytes()).hexdigest()!=production_review["draft_sha256"] or production_review["status"]!="source_schema_budget_pass_with_Souls_distinct_placement_hold_and_FM_year_recommendation"):
        raise ValueError("Production/design source changed or review incomplete")
    for identifier,decision in production_review["placement"].items():
        if identifier in ATTACHED_PARENTS and (decision["parent_id"]!=ATTACHED_PARENTS[identifier] or decision["recommendation"] not in ("attach", "attach_historical_context")):
            raise ValueError("Production/design placement changed: " + identifier)
    if "feature-souls-learning-communities" not in HELD_DRAFT_IDS:
        raise ValueError("Souls semantic duplicate requires an explicit new review")
    markets_review=json.loads((directory.parent / "editorial/markets-machines-review-14.json").read_text(encoding="utf-8"))
    if (hashlib.sha256((directory / "editorial-markets-machines-14.json").read_bytes()).hexdigest()!=markets_review["batch_sha256"] or markets_review["blocking_findings"] or markets_review["result"]!="seven_additive_attachments_two_distinct_media_holds"):
        raise ValueError("Markets/machines review incomplete or source changed")
    for decision in markets_review["entries"]:
        identifier=decision["feature_id"]
        if identifier in ATTACHED_PARENTS and (decision["parent_id"]!=ATTACHED_PARENTS[identifier] or decision["placement_decision"]!="attach_one_parent"):
            raise ValueError("Markets/machines placement changed: " + identifier)
    networks_review=json.loads((directory.parent / "editorial/networks-history-review-15.json").read_text(encoding="utf-8"))
    if (hashlib.sha256((directory / "editorial-networks-history-15.json").read_bytes()).hexdigest()!=networks_review["draft_sha256"] or networks_review["source_reuse_collisions"] or networks_review["status"]!="source_schema_budgets_and_placement_pass_media_pending"):
        raise ValueError("Networks/history source review incomplete or changed")
    for identifier,decision in networks_review["placement"].items():
        if identifier in ATTACHED_PARENTS and (decision["parent_id"]!=ATTACHED_PARENTS[identifier] or decision["recommendation"]!="attach"):
            raise ValueError("Networks/history placement changed: " + identifier)
    berlin_review=json.loads((directory.parent / "editorial/berlin-institution-admission-09.json").read_text(encoding="utf-8"))
    if (berlin_review["decision"]!="admit_distinct_illustrated_institutional_story_with_partial_card_media" or "feature-berlin-game-museum" not in STANDALONE_IDS or hashlib.sha256((directory / "editorial-preservation-worlds-09.json").read_bytes()).hexdigest()!=berlin_review["draft_sha256"] or hashlib.sha256((directory / "priority-feature-context-media-09.json").read_bytes()).hexdigest()!=berlin_review["media_sha256"]):
        raise ValueError("Berlin distinct subject admission source changed")
    museum_review=json.loads((directory.parent / "editorial/museum-preservation-admission-10.json").read_text(encoding="utf-8"))
    if (museum_review["decision"]!="admit_distinct_illustrated_preservation_practice_story" or "feature-games-in-museums" not in STANDALONE_IDS or hashlib.sha256((directory / "editorial-preservation-worlds-09.json").read_bytes()).hexdigest()!=museum_review["draft_sha256"] or hashlib.sha256((directory / "priority-feature-context-media-10.json").read_bytes()).hexdigest()!=museum_review["media_sha256"]):
        raise ValueError("Museum preservation distinct subject admission source changed")
    return [json.loads((directory / filename).read_text(encoding="utf-8"))
            for filename in BATCH_FILES]


def load_media(directory):
    """Join explicit, frozen curation batches; never admit candidates or holds.

    A feature may receive additional images in a later batch. Duplicate URLs,
    mismatched ownership and stale source-body receipts fail before assembly.
    """
    combined = {}
    drafts = _drafts(load_documents(directory))
    admissions = json.loads((directory / "feature-media-admissions.json").read_text(encoding="utf-8"))
    for filename in MEDIA_FILES:
        path = directory / filename
        if not path.exists():
            raise ValueError("Missing admitted feature media batch: " + filename)
        admission = admissions["batches"][filename]
        if hashlib.sha256(path.read_bytes()).hexdigest() != admission["sha256"]:
            raise ValueError("Frozen feature image batch changed: " + filename)
        document = json.loads(path.read_text(encoding="utf-8"))
        feature_document = document
        if filename.startswith("media-collection-"):
            feature_document = {"entries": [row for row in document.get("entries", [])
                                             if row.get("feature_id")]}
        selected = _approved_images(feature_document)
        if set(selected) != set(admission["body_sha256"]):
            raise ValueError("Feature image owner set differs from review: " + filename)
        for identifier in selected:
            actual = hashlib.sha256(json.dumps(drafts[identifier]["body"], ensure_ascii=False).encode("utf-8")).hexdigest()
            if actual != admission["body_sha256"][identifier]:
                raise ValueError("Feature image paragraph source changed: " + identifier)
        receipt = document.get("provenance", {})
        source_hash = receipt.get("source_feature_body_sha256")
        if source_hash:
            if len(selected) != 1:
                raise ValueError("Single-feature media receipt has ambiguous ownership")
            identifier = next(iter(selected))
            actual = hashlib.sha256(json.dumps(drafts[identifier]["body"],
                ensure_ascii=False).encode("utf-8")).hexdigest()
            if actual != source_hash:
                raise ValueError("Feature media source body changed: " + identifier)
        for identifier, images in selected.items():
            existing = combined.setdefault(identifier, [])
            if {i["url"] for i in images} & {i["url"] for i in existing}:
                raise ValueError("Duplicate image across admitted batches: " + identifier)
            existing.extend(images)
    return {"entries": [{"feature_id": identifier, "entry_id": identifier,
                          "images": images} for identifier, images in combined.items()]}


def _signature(entry):
    return copy.deepcopy((entry.get("body", []), entry.get("story_headings", [])))


def _drafts(documents):
    result = {}
    for document in documents:
        for draft in document.get("entries", []):
            identifier = draft["id"]
            if identifier in result:
                raise ValueError("Duplicate priority feature: " + identifier)
            result[identifier] = draft
    if set(result) != ALL_IDS | HELD_DRAFT_IDS:
        raise ValueError("Priority feature set changed; review placement explicitly: "
                         + repr(sorted(set(result) ^ (ALL_IDS | HELD_DRAFT_IDS))))
    return {identifier: draft for identifier, draft in result.items() if identifier in ALL_IDS}


def _approved_images(document):
    """Only the curation lane's admitted entries are runtime selections."""
    selected = {}
    for row in (document or {}).get("entries", []):
        identifier = row.get("feature_id", row.get("entry_id"))
        if (identifier not in ALL_IDS or identifier in selected
                or row.get("entry_id", identifier) != identifier):
            raise ValueError("Unknown/duplicate feature media owner: " + str(identifier))
        images = row.get("images", [])
        urls = set()
        for image in images:
            url = image.get("url", "")
            paragraph = image.get("story_paragraph")
            if (urlsplit(url).scheme != "https" or not urlsplit(url).netloc
                    or any(c.isspace() for c in url) or url in urls
                    or type(paragraph) is not int or not 0 <= paragraph < 4
                    or not image.get("source_page") or not image.get("credit")
                    or not image.get("license")):
                raise ValueError("Feature image lacks identity/credit/mapping: " + str(identifier))
            urls.add(url)
        selected[identifier] = copy.deepcopy(images)
    # Candidates, holds and authoring media briefs intentionally are not read.
    return selected


def _runtime_block(draft, destination, images=None):
    identifier = draft["id"]
    body, headings, cards = (draft.get(key, []) for key in ("body", "story_headings", "cards"))
    if not (len(body) == len(headings) == len(cards) == 4):
        raise ValueError("Priority feature requires four complete cards: " + identifier)
    if not all(isinstance(text, str) and text.strip() for text in body + headings):
        raise ValueError("Empty priority narrative or heading: " + identifier)
    sources = {}
    for original in draft.get("sources", []):
        source_id = original["id"]
        if source_id in sources or not original.get("url", "").startswith("https://"):
            raise ValueError("Invalid priority source: " + identifier + "/" + source_id)
        sources[source_id] = {key: copy.deepcopy(original[key]) for key in SOURCE_FIELDS if key in original}
    paragraph_sources = [[] for _ in body]
    for index, card in enumerate(cards):
        if (card.get("body_index", card.get("index")) != index
                or card.get("body", body[index]) != body[index]
                or card.get("heading") != headings[index]):
            raise ValueError("Priority body/card mapping changed: " + identifier)
        citations = card.get("citations", [])
        if not citations or set(card.get("source_ids", [])) != {c["source_id"] for c in citations}:
            raise ValueError("Priority card citations missing: " + identifier)
        for citation in citations:
            source_id = citation["source_id"]
            source = sources.get(source_id)
            citation_url = citation.get("url")
            if (source is None or citation_url not in [source["url"], *source.get("chapter_urls", [])]
                    or not citation.get("locator")):
                raise ValueError("Priority citation does not resolve: " + identifier)
            paragraph_sources[index].append(source_id)
            source.setdefault("story_paragraphs", []).append(index)
            if citation["locator"] != source.get("locator"):
                source.setdefault("paragraph_locators", {})[str(index)] = citation["locator"]
            if citation_url != source["url"]:
                source.setdefault("paragraph_urls", {})[str(index)] = citation_url
    for source in sources.values():
        if "story_paragraphs" in source:
            source["story_paragraphs"] = sorted(set(source["story_paragraphs"]))
    runtime_sources = list(sources.values())
    for source in sources.values():
        for chapter in source.get("chapter_urls", []):
            if not chapter.startswith("https://"):
                raise ValueError("Invalid reviewed chapter URL: " + identifier)
            runtime_sources.append({"id": source['id'] + '-chapter-' + str(len(runtime_sources)),
                'title': source['title'] + ' / cited chapter', 'url': chapter,
                'publisher': source.get('publisher', ''), 'rights': source.get('rights', ''),
                'publication_group': source['id']})
    # A parent's cover and an authoring brief are not contextual images. Only
    # admitted records from the dedicated curation file can enter these blocks.
    if draft.get("images"):
        raise ValueError("New priority images require a reviewed integration decision: " + identifier)
    summary = draft.get("summary") or draft.get("article_question") or draft["title"]
    return {
        "id": identifier, "title": draft["title"], "summary": summary,
        "body": copy.deepcopy(body), "story_headings": copy.deepcopy(headings),
        "images": copy.deepcopy(images or []), "sources": runtime_sources,
        "editorial_credit": draft.get("editorial_credit", "Pixel Museum editorial"),
        "language": "en", "year": draft["year"],
        "date": copy.deepcopy(draft["date"]),
        "event_semantics": draft["event_semantics"],
        "canonical_entry_id": destination,
        "related_ids": copy.deepcopy(draft.get("related_ids", [])),
        "source_batch": RUNTIME_MARKER,
        "editorial_status": "authored_draft_media_localization_and_native_review_pending",
    }


def _era(year, eras):
    matching = [era["id"] for era in eras
                if era.get("start_year", year) <= year <= era.get("end_year", year)]
    if not matching:
        raise ValueError("No era for priority feature year: " + str(year))
    return matching[0]


def integrate(entries, documents, eras, media_document=None):
    """Append explicit distinct stories and attach reviewed existing topics.

    Incoming original bodies/headings are checked before returning.  Locales are
    not arguments and are never read or written here.  Repeated calls refresh
    only this lane's own marked blocks, rather than adding duplicate features.
    """
    drafts = _drafts(documents)
    approved_images = _approved_images(media_document)
    by_id = {entry["id"]: entry for entry in entries}
    if len(by_id) != len(entries):
        raise ValueError("Duplicate catalogue ID before priority integration")
    protected = {identifier: _signature(entry) for identifier, entry in by_id.items()
                 if identifier not in STANDALONE_IDS}
    for identifier in STANDALONE_IDS & by_id.keys():
        if by_id[identifier].get("source_batch") != RUNTIME_MARKER:
            raise ValueError("Priority standalone collides with another article: " + identifier)
    for identifier, parent in ATTACHED_PARENTS.items():
        entry = by_id.get(parent)
        # One reviewed Iwata biography is an independent calendar destination.
        # An alias would hide its attachments behind the canonical target.
        independent_biography = ((identifier, parent) in {
            ("feature-satoru-iwata-listening", "daily-12-06"),
            ("feature-hironobu-sakaguchi-production", "daily-11-25"),
            ("feature-yuzo-koshiro-fm", "daily-12-12"),
            ("feature-handheld-two-screens", "daily-12-02"),
            ("feature-accessibility-hardware", "daily-12-03")}
            and entry and not entry.get("linked_exhibit_id"))
        if not entry or (entry.get("calendar_only") and not independent_biography):
            raise ValueError("Missing/noncanonical priority feature parent: " + identifier)
    destinations = {identifier: identifier for identifier in STANDALONE_IDS}
    destinations.update(ATTACHED_PARENTS)
    # Preserve authored batch order, independent of set/dict ordering.
    for identifier, draft in drafts.items():
        destination = destinations[identifier]
        block = _runtime_block(draft, destination, approved_images.get(identifier))
        if identifier in STANDALONE_IDS:
            block.update(kind="feature", layout="story", era_id=_era(draft["year"], eras),
                         editorial_mode="original_additive_feature", videos=[], models=[], tags=[])
            if identifier in by_id:
                entries[entries.index(by_id[identifier])] = block
            else:
                entries.append(block)
            by_id[identifier] = block
        else:
            parent = by_id[destination]
            features = parent.setdefault("editorial_features", [])
            matches = [i for i, feature in enumerate(features) if feature.get("id") == identifier]
            if len(matches) > 1:
                raise ValueError("Duplicate attached feature: " + identifier)
            if matches:
                if features[matches[0]].get("source_batch") != RUNTIME_MARKER:
                    raise ValueError("Attached feature belongs to another lane: " + identifier)
                features[matches[0]] = block
            else:
                features.append(block)
            for related in block["related_ids"]:
                if related not in by_id:
                    raise ValueError("Unknown related attached exhibit: " + related)
                if related != destination and related not in parent.setdefault("related_ids", []):
                    parent["related_ids"].append(related)
    # Distinct creator features link to their works, and the works link back.
    for identifier in STANDALONE_LINK_ORDER:
        entry = by_id[identifier]
        for related in entry["related_ids"]:
            if related not in by_id:
                raise ValueError("Unknown related priority exhibit: " + related)
            backlinks = by_id[related].setdefault("related_ids", [])
            if identifier not in backlinks:
                backlinks.append(identifier)
    for identifier, signature in protected.items():
        if _signature(by_id[identifier]) != signature:
            raise AssertionError("Original narrative changed: " + identifier)
    audit = validate(entries, documents, media_document)
    audit.update(protected_original_body_heading_records=len(protected),
                 original_body_headings_modified=0, locale_files_modified=0,
                 net_new_timeline_destinations=len(STANDALONE_IDS),
                 runtime_payload_bytes=len(json.dumps(
                     [by_id[id] if id in STANDALONE_IDS else
                      next(f for f in by_id[destinations[id]]["editorial_features"] if f["id"] == id)
                      for id in drafts], ensure_ascii=False, separators=(",", ":")).encode("utf-8")))
    return audit


def validate(entries, documents, media_document=None):
    """Check every admitted runtime paragraph and its per-card source mapping."""
    drafts = _drafts(documents)
    approved_images = _approved_images(media_document)
    by_id = {entry["id"]: entry for entry in entries}
    if len(by_id) != len(entries):
        raise AssertionError("Duplicate runtime catalogue ID")
    for identifier, draft in drafts.items():
        destination = ATTACHED_PARENTS.get(identifier, identifier)
        expected = _runtime_block(draft, destination, approved_images.get(identifier))
        if identifier in STANDALONE_IDS:
            actual = by_id[identifier]
        else:
            matches = [feature for feature in by_id[destination].get("editorial_features", [])
                       if feature.get("id") == identifier]
            if len(matches) != 1 or identifier in by_id:
                raise AssertionError("Missing or duplicated attached narrative: " + identifier)
            actual = matches[0]
        for field, value in expected.items():
            if actual.get(field) != value:
                raise AssertionError("Runtime feature differs from draft: " + identifier + "/" + field)
        if any(field in actual for field in ("cards", "source_registry", "media_briefs")):
            raise AssertionError("Authoring metadata leaked into runtime feature")
    return {"schema_version": 1, "feature_drafts_integrated": len(drafts),
            "narrative_cards_preserved": sum(len(draft["body"]) for draft in drafts.values()),
            "standalone_ids": sorted(STANDALONE_IDS),
            "attached_features": copy.deepcopy(ATTACHED_PARENTS),
            "source_paragraph_provenance": "all admitted card citation sets preserved on sources",
            "written_proposals_held_from_runtime": sorted(HELD_DRAFT_IDS),
            "media_images_supplied": sum(len(images) for images in approved_images.values()),
            "media_candidates_or_holds_admitted": 0, "new_translations_created": 0,
            "editorial_signoff": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate an already assembled catalogue")
    parser.add_argument("--catalog", type=Path, default=CONTENT / "catalog.json")
    args = parser.parse_args()
    document = json.loads(args.catalog.read_text(encoding="utf-8"))
    documents = load_documents(CONTENT / "expansion")
    media_document = load_media(CONTENT / "expansion")
    if args.check:
        result = validate(document["entries"], documents, media_document)
    else:
        before = copy.deepcopy(document["entries"])
        result = integrate(document["entries"], documents, document["eras"], media_document)
        first = copy.deepcopy(document["entries"])
        integrate(document["entries"], documents, document["eras"], media_document)
        assert document["entries"] == first, "Priority integration is not idempotent"
        result["dry_run_only"] = True
        result["input_catalog_records"] = len(before)
        result["output_catalog_records"] = len(document["entries"])
    result["input_sha256"] = {name: hashlib.sha256(
        (CONTENT / "expansion" / name).read_bytes()).hexdigest() for name in BATCH_FILES}
    for name in MEDIA_FILES:
        result["input_sha256"][name] = hashlib.sha256(
            (CONTENT / "expansion" / name).read_bytes()).hexdigest()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
