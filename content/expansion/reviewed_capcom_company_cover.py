"""Replace an unrelated player portrait with the reviewed corporate mark."""
from pathlib import Path
import copy, hashlib, json

def apply(entries, root):
    root = Path(root)
    def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = root/'content/expansion/museum-capcom-company-cover-reviewed.json'
    if not manifest.is_file(): return {'status':'not_available'}
    plan = json.loads(manifest.read_text(encoding='utf8'))
    candidate_path = root/plan['candidate_path']
    peer_path = root/plan['independent_review_receipt']
    if sha(candidate_path)!=plan['candidate_sha256'] or sha(peer_path)!=plan['independent_review_sha256']:
        raise ValueError('Capcom reviewed bytes changed')
    peer=json.loads(peer_path.read_text(encoding='utf8'))
    if peer.get('status')!='PASS' or peer.get('candidate_sha256')!=plan['candidate_sha256']:
        raise ValueError('Capcom peer is not exact')
    candidate=json.loads(candidate_path.read_text(encoding='utf8'))
    for source in candidate['source_receipts']:
        if sha(root/source['path'])!=source['sha256']: raise ValueError('Capcom source changed')
    owner=next(e for e in entries if e['id']==candidate['entry_id'])
    if owner['body']!=candidate['old_body']: raise ValueError('Capcom body changed')
    if owner['images']==candidate['new_images']: return {'status':'PASS','replaced_cover':0}
    if owner['images']!=candidate['old_images']: raise ValueError('Capcom image array changed')
    image=candidate['new_images'][0]
    if sha(root/image['recovery_local_source'])!=image['verification']['source_sha256']:
        raise ValueError('Capcom transparent vector rendering changed')
    owner['images']=copy.deepcopy(candidate['new_images']); owner['preferred_image']=0
    owner.setdefault('provenance',{})['reviewed_company_cover']={
        'candidate_path':plan['candidate_path'], 'candidate_sha256':plan['candidate_sha256'],
        'independent_review_receipt':plan['independent_review_receipt'],
        'scope':'Prior unrelated portrait archived externally in the exact reviewed candidate.'}
    return {'status':'PASS','replaced_cover':1}
