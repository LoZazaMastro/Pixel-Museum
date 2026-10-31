"""Remove only the peer-reviewed regional rollout sentence, preserving its tail."""
from pathlib import Path
import copy,hashlib,json
def digest(b):return hashlib.sha256(b).hexdigest()
def apply(entries,root):
    root=Path(root);p=root/'content/expansion/museum-dishonored-release-prose-reviewed.json'
    if not p.is_file():return dict(status='not_available')
    plan=json.loads(p.read_text(encoding='utf8'));candidate=root/plan['candidate_path'];peer=root/plan['independent_review_receipt']
    if digest(candidate.read_bytes())!=plan['candidate_sha256']:raise ValueError('Dishonored cleanup candidate changed')
    review=json.loads(peer.read_text(encoding='utf8'))
    if review.get('status')!='PASS' or review.get('candidate_sha256')!=plan['candidate_sha256']:raise ValueError('Dishonored cleanup peer mismatch')
    change=json.loads(candidate.read_text(encoding='utf8'));owner=next(e for e in entries if e['id']==change['entry_id']);index=change['source_chapter_index']
    if owner['body'][index]==change['body']:return dict(status='PASS',changed_paragraphs=0)
    if owner['body'][index]!=change['old_body'] or digest(owner['body'][index].encode())!=change['old_body_sha256']:raise ValueError('Dishonored cleanup exact old prose changed')
    old,new=review['old_first_sentence'],review['new_first_sentence']
    if change['body']!=new+change['old_body'][len(old):] or not change['old_body'].startswith(old):raise ValueError('Dishonored cleanup exceeds reviewed sentence')
    owner['body'][index]=change['body']
    owner.setdefault('provenance',{})['reviewed_single_release_prose_cleanup']=dict(candidate_path=plan['candidate_path'],candidate_sha256=plan['candidate_sha256'],independent_review_receipt=plan['independent_review_receipt'],original_body=change['old_body'],counts_as_wikipedia_clarity_replacement=False)
    return dict(status='PASS',changed_paragraphs=1,regional_rollout_removed=True)
