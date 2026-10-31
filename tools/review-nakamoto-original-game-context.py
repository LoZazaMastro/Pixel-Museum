"""Independent exact-edition review after viewing both retained game images."""
from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/shinichi-nakamoto-existing-prose-original-game-captures'
path=base/'four-existing-nakamoto-paragraphs-three-original-game-chapters-candidate.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
doc=json.loads(path.read_text(encoding='utf8'));row,=doc['rows'];old=row['old_entry'];new=row['new_entry']
current=next(e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']if e['id']==row['entry_id'])
assert current==old and new['body']==old['body'] and len(old['body'])==4
assert old.get('story_headings')==new.get('story_headings')
assert new['images'][0]==old['images'][0]and new['images'][0].get('portrait')
assert doc['expected_main_paragraph_groups']==[[0,1],[2],[3]]
for name,digest in doc['source_files'].items():assert sha(ROOT/name)==digest,name
for item,dimensions,htmlfile in zip(new['images'][1:],[(256,224),(640,490)],['lode-runner-nes-source.html','bomberman-nes-source.html']):
    p=ROOT/item['recovery_local_source']
    assert sha(p)==item['verification']['sha256']
    with Image.open(p)as image:
        image.load();assert image.size==dimensions==(item['width'],item['height'])
    assert item['url'].split('/')[-1]in(base/htmlfile).read_text(encoding='utf8')
assert len({sha(ROOT/i['recovery_local_source'])for i in new['images']})==3
out=base/'root-independent-four-existing-paragraphs-two-original-game-images-peer-review.json'
report=dict(status='PASS_INDEPENDENT_EXACT_EDITION_IMAGE_AND_PROSE_REVIEW',candidate=path.relative_to(ROOT).as_posix(),candidate_sha256=sha(path),
    current_owner_unchanged=True,four_existing_paragraphs_and_headings_unchanged=True,portrait_cover_exclusive=True,all_source_hashes_checked=True,
    full_visual_review=['Original Hudson Famicom/NES Lode Runner shows characteristic ladders, gold and the robots discussed in its paragraph.',
        'Early Famicom/NES Bomberman shows the character, green maze, destructible bricks and cross-shaped explosion; not Super Bomberman or a 3D sequel.'],
    limits=['The 256 by 224 Lode Runner image is native game pixel art, not a low-resolution modern photograph.',
        'Bomberman retains the published 640 by 490 rendition; no HD or native-framebuffer claim.',
        'Previously gathered images reused; no extra prose, music or new YouTube request.',
        'Native three-scene text/scroll validation recorded separately by timeline agent.'])
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(receipt=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
