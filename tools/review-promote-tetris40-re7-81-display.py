"""Review the bounded name correction and promote two already reconciled rooms."""
from pathlib import Path
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
BASE='build/research/soundtrack-broad/modern-next-four/'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
original=BASE+'tetris40-resident-evil-seven81-public-collections-candidate.json'
path=BASE+'tetris40-resident-evil-seven81-display-corrected-candidate.json'
expected='07fdba91cbba19e4cbb41324c5ba6fc55f042f5811f5dbd6a5a0720650b64f39'
assert sha(path)==expected
old,new=load(original),load(path)
prior=load(BASE+'independent-one-hundred-twenty-one-collection-review.json')
assert prior['status']=='PASS' and prior['candidate_sha256']==sha(original)
changes=[]
for a,b in zip(old['entries'],new['entries']):
    for n,(x,y) in enumerate(zip(a['tracks'],b['tracks'])):
        clean=copy.deepcopy(y)
        if x!=y:
            assert x['label_artist_credit']==y['label_artist_credit']
            assert (x['creator'],y['creator']) in [('Michael A. Levin feat. Jordan Reyne','Michael A. Levine feat. Jordan Reyne'),('Cris Velaco','Cris Velasco')]
            clean['creator']=x['creator']
            assert y['artist_name_spelling_source'] in ['https://www.michaellevinemusic.com/resident-evil','https://www.crisvelasco.com/']
            assert y['artist_credit_scope']=="Recording artist credit from the label metadata, with name spelling corrected against the credited musician's official website; raw label_artist_credit preserved. No new composer/performer role allocation."
            clean.pop('artist_name_spelling_source')
            clean['artist_credit_scope']=x['artist_credit_scope']
            changes.append(dict(ordinal=n+1,title=y['title'],raw=x['creator'],display=y['creator']))
        assert clean==x
    clean=copy.deepcopy(b);clean['tracks']=a['tracks'];assert clean==a
assert len(changes)==5
for s in new['source_receipts']:assert sha(s['path'])==s['sha256']
cris=(ROOT/(BASE+'cris-velasco-official.html')).read_text(encoding='utf8')
levine=(ROOT/(BASE+'michael-levine-resident-evil-official.html')).read_text(encoding='utf8')
assert 'Cris Velasco' in cris
for title in ['Apprehension','So Close Yet So Far','The Beast','Not Over Yet']:assert title in cris
assert 'MICHAEL A. LEVINE' in levine and 'Jordan Reyne' in levine
receipt_path=BASE+'independent-display-corrected-121-review.json'
receipt=dict(status='PASS',candidate_path=path,candidate_sha256=expected,previous_full_review=BASE+'independent-one-hundred-twenty-one-collection-review.json',previous_full_review_sha256=sha(BASE+'independent-one-hundred-twenty-one-collection-review.json'),changes=changes,all121_track_fields_other_than_five_creators_and_their_explicit_spelling_provenance_exactly_preserved=True,raw_label_artist_credits_preserved=True,official_artist_pages_checked=True,no_new_role_allocation=True,master_modified=False)
(ROOT/receipt_path).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
music='content/expansion/soundtrack-multitrack-priority-overrides.json'
old_sha='045304c848c9547555f3f392afd2fd6045aa17126acf28160b8e49ed6db93906'
assert sha(music)==old_sha
doc=load(music);before=copy.deepcopy(doc['entries']);assert len(before)==73
for e in new['entries']:
    assert not any(x['entry_id']==e['entry_id'] for x in before)
    e=copy.deepcopy(e);e['independent_review_receipt']=receipt_path
    doc['entries'].append(e)
assert len(doc['entries'])==75 and doc['entries'][:73]==before
temp=ROOT/(music+'.tmp');temp.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8');temp.replace(ROOT/music)
report=dict(status='PASS_SOURCE_ONLY_PROMOTION',previous_source_sha256=old_sha,source_sha256=sha(music),source_entries=75,added_recordings=121,prior73_exactly_preserved=True,independent_review=receipt_path,independent_review_sha256=sha(receipt_path),master_modified=False,runtime_modified=False)
(ROOT/(BASE+'source75-promotion.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,indent=2))
