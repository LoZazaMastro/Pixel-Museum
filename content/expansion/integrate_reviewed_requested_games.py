"""Admit complete illustrated game candidates after source-bound peer review."""
from pathlib import Path
import copy,hashlib,json

BATCHES=(
    ('build/research/pyre-illustrated-story/candidate.json','build/research/pyre-illustrated-story/independent-review.json'),
    ('build/research/requested-switch-two/candidate.json','build/research/requested-switch-two/root-independent-review.json'),
    ('build/research/requested-xenoblade-tropical/candidate.json','build/research/requested-xenoblade-tropical/root-independent-review.json'),
)

def integrate(entries,root):
    root=Path(root);by_id={e['id']:e for e in entries};audit=[]
    for candidate_path,review_path in BATCHES:
        candidate=root/candidate_path;receipt=root/review_path
        if not candidate.is_file()or not receipt.is_file():
            audit.append(dict(candidate=candidate_path,status='awaiting_candidate_or_independent_review'));continue
        review=json.loads(receipt.read_text(encoding='utf8'))
        digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
        if review.get('status')!='PASS':
            audit.append(dict(candidate=candidate_path,status='not_admitted'));continue
        if review.get('candidate_sha256')!=digest:raise ValueError('Requested game changed after review: '+candidate_path)
        doc=json.loads(candidate.read_text(encoding='utf8'));added=[]
        for original in doc['entries']:
            assert len(original['body'])==len(original['story_headings'])>=2
            assert sorted(image['story_paragraph']for image in original['images']if image.get('story_paragraph',-1)>=0)==list(range(len(original['body'])))
            for image in original['images']:
                source=root/image['recovery_local_source']
                if hashlib.sha256(source.read_bytes()).hexdigest()!=image['verification']['sha256']:
                    raise ValueError('Requested game illustration changed: '+str(source))
            provenance=original['provenance']
            wiki_path=provenance.get('wikipedia_source_file')
            if not wiki_path and provenance.get('wikipedia_source_sha256'):
                wiki_path=(candidate.parent/'wikipedia.json').relative_to(root).as_posix()
            if wiki_path and hashlib.sha256((root/wiki_path).read_bytes()).hexdigest()!=provenance['wikipedia_source_sha256']:
                raise ValueError('Requested game Wikipedia source changed: '+original['id'])
            if original['id']in by_id:
                if by_id[original['id']]['body']!=original['body']:raise ValueError('Requested game identity collides: '+original['id'])
                continue
            entry=copy.deepcopy(original)
            entry['provenance']['independent_admission']=dict(candidate=candidate_path,candidate_sha256=digest,receipt=review_path)
            entries.append(entry);by_id[entry['id']]=entry;added.append(entry['id'])
        audit.append(dict(candidate=candidate_path,candidate_sha256=digest,status='PASS',added=added))
    return dict(batches=audit,added=[entry_id for batch in audit for entry_id in batch.get('added',[])])
