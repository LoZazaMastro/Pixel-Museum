"""Freeze thirteen visually inspected, explicitly mapped contextual images."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'content/expansion'
name='priority-feature-context-media-05.json'
path=folder/name
document=json.loads(path.read_text(encoding='utf-8'))
assert hashlib.sha256(path.read_bytes()).hexdigest()=='4fab101bd0ede5208535c4f3e6f95d68148ab7a63ef452b11a27e00a96289525'
drafts={entry['id']:entry for p in folder.glob('editorial-*.json') for entry in json.loads(p.read_text(encoding='utf-8')).get('entries',[])}
assert sum(len(row['images']) for row in document['entries'])==13
body_hashes={row['feature_id']:hashlib.sha256(json.dumps(drafts[row['feature_id']]['body'],ensure_ascii=False).encode()).hexdigest() for row in document['entries']}
admissions=folder/'feature-media-admissions.json'
registry=json.loads(admissions.read_text(encoding='utf-8'))
registry['batches'][name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'body_sha256':body_hashes,'review':'Root read all13 associated paragraphs and inspected the real-image contact sheet. Later venue, edition and date captions retained; symphonic box unrelated to specific WAR discussion held. NC-ND full unchanged photo display only. No blanket media-rights clearance or final signoff.'}
admissions.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
helper=folder/'integrate_priority_features.py'
text=helper.read_text(encoding='utf-8')
if '"'+name+'"' not in text:text=text.replace('"priority-feature-context-media-04.json")','"priority-feature-context-media-04.json", "'+name+'")')
helper.write_text(text,encoding='utf-8')
print('Context05:13 visual/mapping decisions frozen; unrelated later record held.')
