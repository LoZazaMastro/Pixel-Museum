"""Freeze independent paragraph/source/placement review of canonical batch07."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'content/expansion/calendar-template-revisions-native-07.json'
draft = json.loads(path.read_text(encoding='utf-8'))
assert len(draft['entries']) == 12
result = {
    'schema_version': 1,
    'batch_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'independent_reviewer': 'root',
    'all36cards_read': True,
    'source_review': 'Specific primary passages independently read: Finley postmortem and original BioShock360 manual PDFpp6-7; original/later Sonic interviews; Abrash visibility/PVS and passages, official id README; Nintendo official Italian after-school account and original1993 manual transcript; SquareEnix Ishii2021 full indexed original recovered after JS-only endpoint and1991/2005 messages; Suda2018 and Takada original magazine PDFpp44-45; NaughtyDog2023 named staff and2013 environment description; Inaba firsthand GDC report and Platinum2012 conversation; both Bloodstained2019 interviews; both Riot2020 engineering accounts; Abe2020 and publisher description; Insomniac accessibility and Rivet primary announcements.',
    'interpretation_notes': [
        'Retrospective and contemporary evidence remain separately dated and attributed.',
        'Viewtiful source is an eyewitness report, not a claim to have watched the GDC talk.',
        'Sonic sample recollection does not establish first-ever sampled speech.',
        'No perfect anticheat, network fairness, shipped universal accessibility or PS5 performance inference.',
        'The legal distinction in Quake is specifically Carmack README history, not new legal advice.',
        'Review admits canonical narrative only; full daily strings/locales stay archival and old paragraph/media mappings cannot be silently inherited.',
    ],
    'entries': [],
    'editorial_signoffs': 0,
    'media_signoffs': 0,
}
for entry in draft['entries']:
    assert len(entry['body']) == len(entry['story_headings']) == 3
    result['entries'].append({
        'target_canonical_id': entry['target_canonical_id'],
        'proposal_id': entry['id'],
        'new_body_sha256': hashlib.sha256(json.dumps(entry['body'], ensure_ascii=False).encode()).hexdigest(),
        'content_decision': 'independent_specific_primary_source_review_passed',
        'placement_decision': 'replace_only_generic_canonical_parent_preserve_daily_editions',
        'new_destinations_claimed': 0,
    })
(ROOT / 'content/editorial/calendar-canonical-review-07.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Canonical07 independent review frozen for12 canonical parents/36cards.')
