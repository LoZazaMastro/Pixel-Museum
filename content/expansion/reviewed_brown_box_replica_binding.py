"""Move one reviewed replica photograph from gallery to its matching feature."""
from pathlib import Path
import copy,hashlib,json
def digest(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return digest(json.dumps(v,ensure_ascii=False,separators=(',',':')).encode())
def apply(entries,root):
    root=Path(root);p=root/'content/expansion/museum-brown-box-replica-binding-reviewed.json'
    if not p.is_file():return dict(status='not_available')
    plan=json.loads(p.read_text(encoding='utf8'));path=root/plan['candidate_path'];review=json.loads((root/plan['independent_review_receipt']).read_text(encoding='utf8'))
    if plan.get('publication_status')!='independently_reviewed':return dict(status='not_admitted')
    if digest((root/plan['independent_review_receipt']).read_bytes())!=plan['independent_review_sha256']:raise ValueError('Brown Box exact peer bytes changed')
    if digest(path.read_bytes())!=plan['candidate_sha256'] or review.get('status')!='PASS' or review.get('candidate_sha256')!=plan['candidate_sha256']:raise ValueError('Brown Box replica candidate/peer changed')
    change=json.loads(path.read_text(encoding='utf8'))
    for s in change['source_receipts']:
        if digest((root/s['path']).read_bytes())!=s['sha256']:raise ValueError('Brown Box replica source changed')
    owner=next(e for e in entries if e['id']==change['entry_id']);feature=next(f for f in owner.get('editorial_features',[]) if f['id']==change['feature_id'])
    if canonical(owner['body'])!=change['old_main_body_sha256'] or canonical(feature['body'])!=change['old_feature_body_sha256']:raise ValueError('Brown Box main/feature body changed')
    if owner['images']==change['new_main_images'] and feature.get('images',[])==change['new_feature_images']:return dict(status='PASS',moved_images=0)
    if owner['images']!=change['old_main_images'] or canonical(owner['images'])!=change['old_main_images_sha256']:raise ValueError('Brown Box exact main image array changed')
    if feature.get('images',[])!=change['old_feature_images'] or canonical(feature.get('images',[]))!=change['old_feature_images_sha256']:raise ValueError('Brown Box exact feature image array changed')
    for image in change['new_feature_images']:
        v=image['verification']
        if digest((root/v['current_local_file']).read_bytes())!=v['current_bundled_sha256']:raise ValueError('Brown Box existing photograph bytes changed')
    oldurls=[i['url'] for i in owner['images']+feature.get('images',[])];newurls=[i['url'] for i in change['new_main_images']+change['new_feature_images']]
    if sorted(oldurls)!=sorted(newurls) or len(newurls)!=len(set(newurls)):raise ValueError('Replica move duplicates or loses an image')
    owner['images']=copy.deepcopy(change['new_main_images']);feature['images']=copy.deepcopy(change['new_feature_images'])
    feature.setdefault('provenance',{})['reviewed_replica_context_binding']=dict(candidate_path=plan['candidate_path'],candidate_sha256=plan['candidate_sha256'],independent_review_receipt=plan['independent_review_receipt'],scope='One existing photograph moved, no new image; later replica explicitly identified.')
    return dict(status='PASS',moved_images=1,new_assets=0,feature_paragraph=3)
