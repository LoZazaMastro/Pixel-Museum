"""Admit the two SP accessory photographs only after their reviewed text join."""
from pathlib import Path
import copy,hashlib,json

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def apply(entries,root):
    root=Path(root);base=root/'build/research/gba-sp-launch-and-concrete-article'
    path=base/'two-original-sp-accessory-illustrations-readable-candidate.json'
    receipt=base/'independent-two-original-sp-accessory-images-review.json'
    peer=json.loads(receipt.read_text(encoding='utf8'));candidate_sha=digest(path)
    if peer.get('status')!='PASS' or peer.get('candidate_sha256')!=candidate_sha:
        raise ValueError('Original SP accessory review mismatch')
    doc=json.loads(path.read_text(encoding='utf8'))
    for source in doc['source_receipts']:
        if digest(root/source['path'])!=source['sha256']:raise ValueError('Original SP image source changed')
    added=0
    for identifier,images in doc['entries'].items():
        owner=next(e for e in entries if e['id']==identifier);guard=doc['article_guards'][identifier]
        body_sha=hashlib.sha256(json.dumps(owner['body'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        if body_sha!=guard['body_sha256'] or owner['story_headings']!=guard['original_headings']:
            raise ValueError('SP images require the reviewed final SP narrative')
        hero=owner['images'][owner.get('preferred_image',0)]['url'];known={i['url'] for i in owner['images']}
        for image in images:
            if image['url']==hero or digest(root/image['recovery_local_source'])!=image['verification']['source_sha256']:
                raise ValueError('SP accessory image changed or repeats hero')
            if image['url'] not in known:
                owner['images'].append(copy.deepcopy(image));known.add(image['url']);added+=1
        owner.setdefault('provenance',{})['gba_sp_reviewed_narrative_media']=dict(candidate_sha256=candidate_sha,independent_review=receipt.relative_to(root).as_posix(),requires_clarity_candidate_sha256=doc['requires_clarity_candidate_sha256'])
    return dict(status='PASS',new_images=added,narrative_paragraphs=4,new_illustrated_paragraphs=[0,3],other_two_not_claimed_complete=True)
