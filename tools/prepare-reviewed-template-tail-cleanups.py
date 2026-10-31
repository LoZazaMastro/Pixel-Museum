"""Retain concrete accounts while dropping their repeated non-factual tails."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'build/research/playhub-semantic-coverage/style-followup/concrete-prefix-candidate-research.json'
rows=json.loads(source.read_text(encoding='utf8'))['rows']
changes=[]
for row in rows:
    if row['owner_id']=='workbook-05-30-capcom':continue
    assert row['body'].startswith(row['proposed_body'])
    assert len(row['proposed_body'].split())>=45
    assert any(row['removed_template'].startswith(marker)for marker in ['The consequence extends beyond one feature.','This is where a design detail becomes language.','This passage explains why'])
    changes.append(dict(entry_id=row['owner_id'],paragraph_index=row['paragraph_index'],old_body=row['body'],
        old_body_sha256=hashlib.sha256(row['body'].encode()).hexdigest(),body=row['proposed_body'],
        body_sha256=hashlib.sha256(row['proposed_body'].encode()).hexdigest(),removed_template=row['removed_template']))
out=ROOT/'content/expansion/museum-reviewed-template-tail-cleanups.json'
out.write_text(json.dumps(dict(status='root_and_editorial_read_reviewed',
    review_scope='Root independently read the30 follow-up flagged passages and explicitly approved removal of their empty repeated tails while preserving the concrete account. Editorial agent read all remaining prefixes. Two date-word matches were false positives and retained; abstract Capcom history is reserved for a complete Wikipedia replacement.',
    source_audit=source.relative_to(ROOT).as_posix(),source_audit_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),changes=changes),indent=2,ensure_ascii=True)+'\n',encoding='utf8')
print(json.dumps(dict(file=out.relative_to(ROOT).as_posix(),paragraphs=len(changes),sha256=hashlib.sha256(out.read_bytes()).hexdigest())))
