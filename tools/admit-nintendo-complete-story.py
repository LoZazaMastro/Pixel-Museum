"""Freeze the visually reviewed Nintendo source and check its isolated join."""
from pathlib import Path
import copy,hashlib,json,runpy
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'build/research/nintendo-complete-story'
source=json.loads((folder/'nintendo-complete-candidate.json').read_text(encoding='utf-8'))
original=json.loads((folder/'original-story.json').read_text(encoding='utf-8'))
retained=[c for c in source['chapter_sources'] if c['original_index'] is not None]
assert sorted(c['original_index'] for c in retained)==list(range(7))
assert all(c['body']==original['body'][c['original_index']] for c in retained)
source['status']='text_and_images_reviewed'
source['review']={
    'date':'2026-10-21','original_chapters_retained_verbatim':7,'narrative_chapters':19,
    'image_review':'Every artefact visually inspected; Nintendo cards, Color TV-Game, Game & Watch, DS and Iwata originals recovered with actual per-file authors/licences. Main-block artwork is not reused inside cards.',
    'native_film':'-CSWjjbWm30, Nintendo UK, public AVC/AAC metadata verified against the official Nintendo Museum Direct page.',
    'limitations':'Physical PS5 video playback and final on-console layout remain to be tested.'}
target=ROOT/'content/expansion/nintendo-complete-story-reviewed.json'
target.write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
join=runpy.run_path(str(ROOT/'content/expansion/nintendo_complete_story.py'))['apply']
entries=[copy.deepcopy(original),dict(id='unrelated',body=['Preserve this.'])]
untouched=copy.deepcopy(entries[1]);report=join(entries,ROOT);once=copy.deepcopy(entries)
join(entries,ROOT)
assert entries==once and entries[1]==untouched
assert entries[0]['videos'][0]['story_paragraph']==17
assert len(entries[0]['body'])==19 and entries[0]['preferred_image']==0
assert sorted(i['story_paragraph'] for i in entries[0]['images'] if i.get('story_paragraph',-1)>=0)==list(range(19))
receipt=dict(status='PASS',report=report,module_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    checks=['Seven original prose chapters retained exactly','19 unique illustrated paragraph associations','Film placed after museum chapter, not introduction','Idempotent isolated join','Unrelated entry unchanged'])
(folder/'admission-review.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt))
