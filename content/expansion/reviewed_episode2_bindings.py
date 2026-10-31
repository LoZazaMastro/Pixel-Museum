"""Two reviewed numeric associations on a full-array guarded existing article."""
from pathlib import Path
import copy,hashlib,json
def digest(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return digest(json.dumps(v,ensure_ascii=False,separators=(',',':')).encode())
def apply(entries,root):
    root=Path(root);p=root/'content/expansion/museum-episode2-existing-bindings-reviewed.json'
    if not p.is_file():return dict(status='not_available')
    plan=json.loads(p.read_text(encoding='utf8'));candidate=root/plan['candidate_path'];peer=root/plan['independent_review_receipt']
    if plan.get('publication_status')!='independently_reviewed':return dict(status='not_admitted')
    if digest(candidate.read_bytes())!=plan['candidate_sha256']:raise ValueError('Episode2 reviewed binding candidate changed')
    review=json.loads(peer.read_text(encoding='utf8'))
    if review.get('status')!='PASS' or review.get('candidate_sha256')!=plan['candidate_sha256']:raise ValueError('Episode2 independent binding receipt mismatch')
    change=json.loads(candidate.read_text(encoding='utf8'))
    for source in change['source_receipts']:
        if digest((root/source['path']).read_bytes())!=source['sha256']:raise ValueError('Episode2 original publisher still changed')
    owner=next(e for e in entries if e['id']==change['entry_id'])
    if canonical(owner['body'])!=change['body_sha256'] or owner['preferred_image']!=0:raise ValueError('Episode2 body or cover guard changed')
    if owner['images']==change['new_images']:return dict(status='PASS',changed_bindings=0)
    if owner['images']!=change['old_images'] or canonical(owner['images'])!=change['old_images_sha256']:raise ValueError('Episode2 exact prior image array changed')
    for old,new in zip(change['old_images'],change['new_images']):
        a,b=copy.deepcopy(old),copy.deepcopy(new);a.pop('story_paragraph',None);b.pop('story_paragraph',None)
        if a!=b:raise ValueError('Episode2 binding includes an unapproved nonnumeric image edit')
    owner['images']=copy.deepcopy(change['new_images'])
    owner.setdefault('provenance',{})['reviewed_episode2_existing_bindings']=dict(candidate_path=plan['candidate_path'],candidate_sha256=plan['candidate_sha256'],independent_review_receipt=plan['independent_review_receipt'],scope='Two existing image associations only; no new media or text; no paragraph1 or article-completeness assertion.')
    return dict(status='PASS',changed_bindings=2,paragraphs=[0,2],new_assets=0)
