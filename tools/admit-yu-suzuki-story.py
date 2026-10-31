"""Admit the exact peer-reviewed creator revision and verify an isolated join."""
from pathlib import Path
import copy,hashlib,json,runpy
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'build/research/yu-suzuki-complete-story'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
path=folder/'candidate.json';candidate=read(path)
peer=read(folder/'independent-six-chapter-review.json')
expected='b7b43ade512bb4f4a189dc5356b3ccfb218006b46b94c82adba077bb53d79482'
assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
assert expected in json.dumps(peer)
assert 'Ren' not in candidate['images'][5].get('caption','')
candidate['status']='text_and_images_reviewed'
candidate['videos'][1]['caption']='A rapid-fire interview with the Shenmue creator, published by Game Informer during its Shenmue III coverage.'
candidate['review']=dict(source_candidate_sha256=expected,independent_receipt='build/research/yu-suzuki-complete-story/independent-six-chapter-review.json',
    text_scope='New source-based editorial synthesis replacing a repetitive template draft, not a verbatim archival import.',
    post_peer_copyedit='Game Informer caption describes the published rapid-fire format, removing an unnecessary comparison with trailers; media identity and placement unchanged.',
    visual_scope='Nine original-size images viewed. Person-first hero not reused in the story. Saturn1994/PC2018 illustration editions retained; contextual film posters are not asserted to be video frames.',
    limitations='Physical PS5 film playback and final console performance pending.')
target=ROOT/'content/expansion/yu-suzuki-complete-story-reviewed.json'
target.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
join=runpy.run_path(str(ROOT/'content/expansion/reviewed_creator_stories.py'))['apply']
old=read(folder/'original-story.json');entries=[copy.deepcopy(old),dict(id='unrelated',body=['Keep this.'])]
unrelated=copy.deepcopy(entries[1]);report=join(entries,ROOT);once=copy.deepcopy(entries);join(entries,ROOT)
assert entries==once and entries[1]==unrelated
assert entries[0]['provenance']['creator_previous_template_draft']['body']==old['body']
assert len(entries[0]['body'])==6 and len(entries[0]['images'])==9
assert [v['story_paragraph'] for v in entries[0]['videos']]==[3,5]
receipt=dict(status='PASS',report=report,module_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    checks=['Exact peer candidate SHA','Previous template frozen in provenance','Six specific chapters with distinct associated images','Two contextual films retain placement','Idempotent join','Unrelated entry unchanged'])
(folder/'admission-review.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt))
