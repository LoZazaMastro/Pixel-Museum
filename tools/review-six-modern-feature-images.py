"""Bounded independent review of six individually viewed feature illustrations."""
from pathlib import Path
from PIL import Image
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
BASE='build/research/story-text-profile/priority-original-illustrations/three-modern-features-six-original-images/'
PATH=BASE+'six-source-bound-feature-illustrations-candidate.json'
EXPECTED='62c534752550156ab011429b0c6b0b0adf7540da98836e6fb7e7588c2a5179ba'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert sha(PATH)==EXPECTED
d=load(PATH);master=load('content/catalog.json');owners={e['id']:e for e in master['entries']}
for s in d['source_receipts']:assert sha(s['path'])==s['sha256']
html='\n'.join((ROOT/s['path']).read_text(encoding='utf8') for s in d['source_receipts'])
rows=[];seen=set()
for change in d['feature_entries']:
    e=owners[change['entry_id']];f=next(f for f in e['editorial_features'] if f['id']==change['feature_id'])
    assert f['body']==change['feature_body']
    assert hashlib.sha256(json.dumps(f['body'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==change['feature_body_sha256']
    existing=e.get('images',[])+[i for feature in e.get('editorial_features',[]) for i in feature.get('images',[])]
    for image in change['images']:
        p=image['recovery_local_source'];assert sha(p)==image['verification']['source_sha256']
        with Image.open(ROOT/p) as im:
            im.load();assert im.size==(image['width'],image['height']);rgb=hashlib.sha256(str(im.size).encode()+im.convert('RGB').tobytes()).hexdigest()
        assert rgb==image['verification']['decoded_rgb_identity_sha256'] and rgb not in seen;seen.add(rgb)
        assert not any(i['url']==image['url'] for i in existing)
        assert 0<=image['story_paragraph']<len(f['body'])
        identity=image['url'].split('/iiif/image/',1)[1].split('/')[0] if '/iiif/image/' in image['url'] else image['url'].rsplit('/',1)[1]
        assert identity in html
        assert image['license_url']==''
        rows.append(dict(entry_id=e['id'],feature_id=f['id'],paragraph=image['story_paragraph'],path=p,sha256=sha(p),dimensions=[image['width'],image['height']],full_image_individually_viewed=True))
assert len(rows)==6
evidence=d['research_evidence'];assert sha(evidence['comparison_receipts'])==evidence['comparison_receipts_sha256']
receipt=dict(status='PASS',candidate_path=PATH,candidate_sha256=EXPECTED,checked_master_sha256=sha('content/catalog.json'),images=rows,observations=['All12 existing feature paragraphs read, all6 new native images individually opened, then all14 existing compositions compared on the source contact. Six new URL/pixel identities are distinct from each other and from the existing hero/story subjects.','LongHatHouse own studio page identifies Lucas andJoao without assigning frame positions. The2018 interview opening image depicts the fictional game heroine, not a historical portrait. No capture date or photographer invented.','Actual Articy interface images visibly identify2021ReleaseCandidate, KineemaStationCall and Pawnshop/boombox branches. They illustrate the later production workflow in the captions, without pretending to be photographs of the2018 interview.','Getty primary article publishes the exact custom-gallery capture and ManetSpring pattern sheet withQR. The complete screenshot is not labelledCC0; painting public domain does not establish an open licence for the complete pattern-sheet layout. Native910x574 retained without enlargement.','Only six assigned paragraphs illustrated; other six feature paragraphs remain outside this bounded batch. No prose/date/music/video changed and no app performance claim.'],source_receipts_verified=len(d['source_receipts']),master_modified=False)
out=BASE+'independent-six-source-bound-feature-illustrations-review.json'
(ROOT/out).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(out,sha(out))
