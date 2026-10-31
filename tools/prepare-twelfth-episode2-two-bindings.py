"""Prepare only two semantic image bindings; no new media or displayed text."""
from pathlib import Path
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[1];FOLDER=ROOT/'build/research/twelfth-episode2-existing-bindings';FOLDER.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return sha(json.dumps(v,ensure_ascii=False,separators=(',',':')).encode())
source=(ROOT/'content/catalog.json').read_bytes();assert sha(source)=='50e3d1f91119a6aa7dd62032ef8f7c7f7a42a053d67a7b05ea3e9b51bdca70ba'
owner=next(e for e in json.loads(source)['entries'] if e['id']=='9-nine-episode-2');images=copy.deepcopy(owner['images'])
assert owner['preferred_image']==0 and images[1]['story_paragraph']==images[2]['story_paragraph']==-1
images[1]['story_paragraph']=0;images[2]['story_paragraph']=2
originals=[]
for i in owner['images'][1:]:
    p=ROOT/'build/research/image-quality'/(sha(i['url'].encode())[:16]+'.jpg');assert sha(p.read_bytes())==i['verification']['sha256']
    originals.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p.read_bytes()),native_dimensions=[1280,720]))
candidate=dict(schema_version=1,status='candidate_pending_independent_review',entry_id=owner['id'],source_catalog_sha256=sha(source),scope='Only images[1].story_paragraph=-1→0 and images[2].story_paragraph=-1→2. No new asset, title, caption, body, heading, date, cover, film, music or model changes.',old_body=owner['body'],body_sha256=canonical(owner['body']),old_images=owner['images'],old_images_sha256=canonical(owner['images']),new_images=images,new_images_sha256=canonical(images),preferred_image=0,bindings=[dict(image_index=1,paragraph=0,reason='The screenshot names Sora in its dialogue UI, directly matching the introductory paragraph naming this episode heroine.',confidence='strong'),dict(image_index=2,paragraph=2,reason='The screenshot names Noa and shows illustrated dialogue and visual-novel UI; it illustrates paragraph2 opening presentation sentence. It does not illustrate the paragraph remaining release-history statements.',confidence='qualified')],source_receipts=originals,review_basis=dict(path='build/research/post-eleventh-readonly-existing-still-audit/current-main-article-associations.json',sha256='9477f3613b4f53b634673ead35d7b45c8daa5db8660179f2dfd8d1c83188c583'),limits=['Paragraph1 town/shrine/earthquake events are not directly illustrated by these character close-ups. No binding to paragraph1 is made.','No whole-article completion, new image count or global gap reduction is claimed. The actual compositor may group prose differently; only the two explicit bindings are admitted.','Only pre-existing English Steam publisher stills are used, explicitly later translated-edition illustrations. No original Japanese UI claim.'])
p=FOLDER/'two-existing-publisher-still-bindings-candidate.json';assert not p.exists();p.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(p.relative_to(ROOT),sha(p.read_bytes()))
