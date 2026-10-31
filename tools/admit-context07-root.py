"""Freeze ten visually inspected, explicitly mapped contextual images."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'content/expansion'
name='priority-feature-context-media-07.json'
path=folder/name
document=json.loads(path.read_text(encoding='utf-8'))
assert hashlib.sha256(path.read_bytes()).hexdigest()=='99b578d9cb60285f46179bc96b14ab74de3ae47d1e8565a361bb355e344f4759'
drafts={entry['id']:entry for p in folder.glob('editorial-*.json') for entry in json.loads(p.read_text(encoding='utf-8')).get('entries',[])}
assert sum(len(row['images']) for row in document['entries'])==10
body_hashes={row['feature_id']:hashlib.sha256(json.dumps(drafts[row['feature_id']]['body'],ensure_ascii=False).encode()).hexdigest() for row in document['entries']}
admissions=folder/'feature-media-admissions.json'
registry=json.loads(admissions.read_text(encoding='utf-8'))
registry['batches'][name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'body_sha256':body_hashes,'review':'Root read all associated hardware11 paragraphs and visually inspected ten actual images. Original non-analogue PS1, explicitly2024 anniversary collection/accessories, actual2021 OLED Joy-Con/screen/hinged stand, AlvinDaniel and Access caps, physical2010 DSiXL kept in exact revision context. Manufacturer copyright retained; licensed DSiXL photographer credited. No prototype or development image invented and no blanket rights/native signoff.'}
admissions.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
helper=folder/'integrate_priority_features.py'
text=helper.read_text(encoding='utf-8')
if '"'+name+'"' not in text:text=text.replace('"priority-feature-context-media-06.json")','"priority-feature-context-media-06.json", "'+name+'")')
helper.write_text(text,encoding='utf-8')
print('Context07: ten exact-card hardware visual decisions frozen; missing prototype/950px images held.')
