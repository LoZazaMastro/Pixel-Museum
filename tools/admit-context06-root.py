"""Freeze five visually inspected, explicitly mapped contextual images."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'content/expansion'
name='priority-feature-context-media-06.json'
path=folder/name
document=json.loads(path.read_text(encoding='utf-8'))
assert hashlib.sha256(path.read_bytes()).hexdigest()=='1c22c26d54153e6dd5bfffc02ae0d7849d7db33696257900e312f310c3db03fd'
drafts={entry['id']:entry for p in folder.glob('editorial-*.json') for entry in json.loads(p.read_text(encoding='utf-8')).get('entries',[])}
assert sum(len(row['images']) for row in document['entries'])==5
body_hashes={row['feature_id']:hashlib.sha256(json.dumps(drafts[row['feature_id']]['body'],ensure_ascii=False).encode()).hexdigest() for row in document['entries']}
admissions=folder/'feature-media-admissions.json'
registry=json.loads(admissions.read_text(encoding='utf-8'))
registry['batches'][name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'body_sha256':body_hashes,'review':'Root read all five exact associated paragraphs and visually inspected the five actual image contact sheet. Later2014 public collaboration,2012 museum exhibition, actual controller details, Dutch publishing material and2015 game environment are accurately distinguished from development evidence. No generic studio photo or unrelated hardware substituted. No blanket rights or final signoff.'}
admissions.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
helper=folder/'integrate_priority_features.py'
text=helper.read_text(encoding='utf-8')
if '"'+name+'"' not in text:text=text.replace('"priority-feature-context-media-05.json")','"priority-feature-context-media-05.json", "'+name+'")')
helper.write_text(text,encoding='utf-8')
print('Context06: five exact-card visual decisions frozen; unverified studio/low-detail material held.')
