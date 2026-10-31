"""Reuse a collected Playhub game image for the exact Mistwalker paragraph."""
from pathlib import Path
import copy
import hashlib
import json
import shutil
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/sakaguchi-existing-prose-contextual-illustrations'
PLAYHUB = Path('F:/Playhub/Plugin/Playhub/Source/GamingModeDeckyPlugin')
name = 'jul-dec-review-work-lost-odyssey-4.jpg'
original = PLAYHUB / 'src/assets/history' / name
local = BASE / 'existing-playhub-lost-odyssey-original.jpg'
shutil.copy2(original, local)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(original) == sha(local)
with Image.open(local) as image:
    image.load()
    assert image.size == (1280, 720)
metadata = json.loads((PLAYHUB / 'quick_settings/history_images.json').read_text(encoding='utf8'))
def find(value):
    if isinstance(value, dict):
        if value.get('file') == name:
            yield value
        for child in value.values():
            yield from find(child)
    elif isinstance(value, list):
        for child in value:
            yield from find(child)
source, = list(find(metadata))
catalog = json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf8'))
old = next(e for e in catalog['entries'] if e['id'] == 'daily-11-25')
new = copy.deepcopy(old)
assert 'Blue Dragon and Lost Odyssey' in old['body'][4]
assert all(image.get('story_paragraph') != 4 for image in old['images'])
new['images'].append(dict(
    url=source['url'], source_page=source['sourceUrl'],
    title='Lost Odyssey: selecting an attack in battle',
    caption='The original Xbox 360 Lost Odyssey battle interface, with attack targets and turn-based commands visible.',
    creator='Mistwalker / feelplus / Microsoft Game Studios',
    credit='Lost Odyssey game imagery: Mistwalker / feelplus / Microsoft Game Studios; respective rights retained',
    license='Original game imagery; respective game and publisher rights retained. No open licence claimed.',
    width=1280, height=720, story_paragraph=4,
    recovery_local_source=local.relative_to(ROOT).as_posix(),
    verification=dict(sha256=sha(local), native_dimensions=[1280,720],
        processing='Existing collected image copied byte-for-byte; no enlargement, crop, regeneration or frame added.',
        original_collected_file=str(original), original_provider=source['provider'],
        visually_reviewed=True,
        context='Original Lost Odyssey battle screen accompanies the existing paragraph explicitly discussing Lost Odyssey and Blue Dragon at Mistwalker. No claim of showing a developer or specific named production event.')))
assert new['body'] == old['body'] and new['editorial_features'] == old['editorial_features']
out = BASE / 'one-existing-lost-odyssey-main4-image-candidate.json'
doc = dict(schema_version=1,status='CANDIDATE_PENDING_INDEPENDENT_PEER',
    rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
    source_files={local.relative_to(ROOT).as_posix():sha(local)},
    scope='Only one pertinent image added to the existing Mistwalker main paragraph4; all seven main and four feature paragraphs, cover, films, music and dates unchanged.',
    quality_limits=['Original game capture is1280x720, not a new4K rendering.',
                    'Takahashi production-team feature paragraph remains unillustrated; no whole-article completion claim.'])
out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
