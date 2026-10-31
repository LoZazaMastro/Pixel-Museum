"""Audit every actual native StoryCard against a frozen authoring collection."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('directory',type=Path)
args=parser.parse_args()
base=args.directory
load=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
master=load(base/'master.json')
native=load(base/'composition.json')
original={e['id']:e for e in master['entries']}
assert [e['entry_id'] for e in native['entries']]==list(original)
totals=Counter()
gaps=[]
film_gaps=[]
dense_illustrated=[]
short_articles=[]
for row in native['entries']:
    entry=original[row['entry_id']]
    bodies=[entry.get('body',[])]+[f.get('body',[]) for f in entry.get('editorial_features',[])]
    retained=[[] for _ in bodies]
    identities=[]
    article_scenes=0
    for index,card in enumerate(row['cards']):
        totals['cards']+=1
        assert card['kind']!=1, f"Empty photograph card: {entry['id']} card{index}"
        if card['image_identity']:
            identities.append(card['image_identity'])
        if card['kind'] not in (0,2) or card['paragraph']<0:
            if card['kind']==2 and not card['image_url']:
                film_gaps.append(dict(id=entry['id'],card=index,video=card['video']))
            continue
        paragraphs=[card['paragraph']]+card['continuation']
        group=card['feature']+1
        assert 0<=group<len(bodies)
        assert all(0<=p<len(bodies[group]) for p in paragraphs)
        retained[group]+=paragraphs
        totals['composed_prose_scenes']+=1
        article_scenes+=1
        if not card['image_url'] and card['kind']==0:
            gaps.append(dict(id=entry['id'],title=entry['title'],year=entry['year'],
                feature=card['feature'],paragraphs=paragraphs,card=index))
        prose_bytes=sum(len(bodies[group][p].encode('utf8')) for p in paragraphs)
        if card['image_url'] and prose_bytes>2400:
            dense_illustrated.append(dict(id=entry['id'],title=entry['title'],year=entry['year'],
                feature=card['feature'],paragraphs=paragraphs,card=index,
                source_utf8_bytes=prose_bytes,image_url=card['image_url'],
                review_reason='Long illustrated scene: review editorial rhythm and available distinct images; this is not a clipping failure.'))
        if card['kind']==2 and not card['image_url']:
            film_gaps.append(dict(id=entry['id'],card=index,video=card['video']))
    assert len(identities)==len(set(identities)), f"Repeated picture in {entry['id']}"
    for group,body in enumerate(bodies):
        assert retained[group]==list(range(len(body))), f"Paragraph omitted/repeated/reordered in {entry['id']} group{group}"
        totals['source_paragraphs_once_in_order']+=len(body)
    if article_scenes<2:
        short_articles.append(dict(id=entry['id'],title=entry['title'],year=entry['year'],
            narrative_scenes=article_scenes,source_paragraphs=sum(map(len,bodies)),
            review_reason='Fewer than two narrative cards: redistribute existing complete paragraphs with distinct relevant images first; seek additional sourced material only if the source itself is too short.'))
    totals['entries']+=1
gaps.sort(key=lambda e:(e['year'],e['id'],e['feature'],e['card']))
dense_illustrated.sort(key=lambda e:(e['year'],e['id'],e['feature'],e['card']))
short_articles.sort(key=lambda e:(e['year'],e['id']))
report=dict(status='PASS_ALL_ACTUAL_NATIVE_PARAGRAPH_ORDERS_AND_UNIQUE_IMAGES',
    frozen_master_sha256=sha(base/'master.json'),
    frozen_runtime_sha256=sha(base/'catalog.json'),
    actual_native_snapshot_sha256=sha(base/'composition.json'),counts=dict(totals),
    remaining_unillustrated_narrative_scenes=len(gaps),remaining_film_preview_gaps=len(film_gaps),
    long_illustrated_scenes_for_editorial_review=len(dense_illustrated),
    articles_with_fewer_than_two_narrative_cards=len(short_articles),
    source_text_omitted=False,repeated_story_images=False,empty_photograph_cards=False,
    limits=['Checks actual compiled compositor output, not a Python approximation.',
        'Paragraph indices and sequence are checked globally; actual rendered wording/scroll have separate scoped native receipts.',
        'Unillustrated scenes remain visible and are reported; this is not editorial completion or semantic-image approval.',
        'The 2400-byte density flag creates a review queue, not a text cap or automatic rewrite.',
        'Single-card articles are separately queued even when short and illustrated; paragraph/image integrity alone does not establish editorial completeness.',
        'No physical PS5 performance or loading-time claim.'])
(base/'all-source-paragraph-and-image-identity-receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
(base/'remaining-unillustrated-chronological-queue.json').write_text(json.dumps(gaps,indent=2)+'\n',encoding='utf8')
(base/'remaining-film-preview-gaps.json').write_text(json.dumps(film_gaps,indent=2)+'\n',encoding='utf8')
(base/'long-illustrated-scene-editorial-review-queue.json').write_text(json.dumps(dense_illustrated,indent=2)+'\n',encoding='utf8')
(base/'single-narrative-card-editorial-review-queue.json').write_text(json.dumps(short_articles,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,indent=2))
