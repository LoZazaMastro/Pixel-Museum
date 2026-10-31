"""Record the independent reading of the preservation commission batch."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'content/expansion/editorial-preservation-worlds-09.json'
document = json.loads(path.read_text(encoding='utf-8'))
parents = {
    'feature-odyssey-overlays': 'odyssey',
    'feature-spectrum-bedroom-networks': 'zx-spectrum',
    'feature-loading-screen-culture': 'commodore-64',
    'feature-commercial-availability-study': 'preserving-play',
    'feature-repair-sustainability': 'preserving-play',
}
records = []
for entry in document['entries']:
    charges = [row['charged_words'] for row in entry['source_budget_audit']]
    assert len(charges) == 2 and max(charges) <= 195
    for source in entry['sources']:
        snapshot = source['snapshot']
        assert hashlib.sha256((ROOT / snapshot['path']).read_bytes()).hexdigest() == snapshot['sha256']
    parent = parents.get(entry['id'])
    records.append({
        'feature_id': entry['id'], 'parent_id': parent,
        'body_sha256': hashlib.sha256(json.dumps(entry['body'], ensure_ascii=False).encode()).hexdigest(),
        'content_decision': 'independent_source_review_passed',
        'placement_decision': 'attach_one_parent' if parent else 'hold_distinct_subject_pending_contextual_media',
        'source_word_charges': charges,
    })
review = {
    'schema_version': 1,
    'batch_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'independent_reviewer': 'root',
    'all32cards_read': True,
    'all4distinct_complete_parent_bodies_read': True,
    'source_review': 'Original archival raster pages of Odyssey rules pp9/34 and service parts p4 inspected; service description read. Participant Spectrum and loader passages read, including Hylands driver attribution. Original institutional Berlin collection and dated programme, ACMI practice, DiGRA report, VGHF methodology, Ryan April2021 announcement, CHM Core restoration pages22-25, TNMOC Q3p7, Habitat architecture and commit-pinned NeoHabitat documentation read. Failed exploratory HTML is excluded; scanned Odyssey PDF is the evidence.',
    'boundaries': ['2022 Berlin inventory and 2014 programme are dated records, not current totals or attendance evidence.', '2023 US commercial availability does not mean worldwide survival; April2021 Sony reversal is historical.', 'Participant memories retain attribution. No invented repair benefits or exact disputed PDP-1 day.', 'Three distinct institutional/server stories remain held for appropriate media; writing is saved.'],
    'entries': records,
    'editorial_signoffs': 0,
    'media_rights_signoffs': 0,
}
output = ROOT / 'content/editorial/preservation-worlds-review-09.json'
output.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for name in ('editorial-plan.py', 'refresh-media-backlog.py'):
    target = ROOT / 'tools' / name
    text = target.read_text(encoding='utf-8')
    if 'editorial-preservation-worlds-09.json' not in text:
        text = text.replace('"editorial-design-communities-08.json"', '"editorial-design-communities-08.json", "editorial-preservation-worlds-09.json"')
        text = text.replace("'editorial-design-communities-08.json'", "'editorial-design-communities-08.json', 'editorial-preservation-worlds-09.json'")
        target.write_text(text, encoding='utf-8')
print('Preservation review saved: five attachments, three distinct subjects held for media.')
