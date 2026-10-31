"""Publish the exact independently reviewed six-game source and media batch."""
from pathlib import Path
import copy, hashlib, json
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'build/research/recent-game-six'
def load(path):return json.loads(path.read_text(encoding='utf8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
review=load(WORK/'independent-six-articles-media-review.json')
assert review['status']=='PASS'
assert sha(WORK/'review-ready-candidate.json')==review['candidate_sha256']
assert sha(WORK/'developer-films-review-checkpoint.json')==review['film_checkpoint_sha256']
candidate=load(WORK/'review-ready-candidate.json');films=load(WORK/'developer-films-review-checkpoint.json')
entries=copy.deepcopy(candidate['entries']);by_id={e['id']:e for e in entries}
for row in films['entries']:
    target=by_id[row['entry_id']]
    target['videos'].append(copy.deepcopy(row['video']))
    if row.get('poster'):target['images'].append(copy.deepcopy(row['poster']))
for entry in entries:
    entry.setdefault('provenance',{})['independent_recent_six_review']={
        'receipt':'build/research/recent-game-six/independent-six-articles-media-review.json',
        'receipt_sha256':sha(WORK/'independent-six-articles-media-review.json'),
        'candidate_sha256':review['candidate_sha256'],
        'film_checkpoint_sha256':review['film_checkpoint_sha256'],
        'scope':review['scope']}
doc={'schema_version':1,'publication_status':'validated','scope':review['scope'],
     'review_receipt':'build/research/recent-game-six/independent-six-articles-media-review.json',
     'review_receipt_sha256':sha(WORK/'independent-six-articles-media-review.json'),'entries':entries}
path=ROOT/'content/expansion/recent-six-reviewed-additions.json'
path.write_text(json.dumps(doc,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':'PASS','entries':len(entries),'paragraphs':sum(len(e['body'])for e in entries),
                 'images':sum(len(e['images'])for e in entries),'videos':sum(len(e['videos'])for e in entries)}))
