"""Independent bounded SP launch/prose/accessory review before a grouped join."""
from pathlib import Path
from PIL import Image
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];BASE='build/research/gba-sp-launch-and-concrete-article/'
CP=BASE+'four-wikipedia-cards-launch-without-regional-prose-candidate.json';CH='ebf7c3006cfd12b0111a7ff52a261b27c5d2e43b9cadc3a21cf6664a87a2bccf'
IP=BASE+'two-original-sp-accessory-illustrations-readable-candidate.json';IH='f8ac4816a6a0c305776b8b27531964c7b6ce8862d4e5fd17695e039b3be38734'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert sha(CP)==CH and sha(IP)==IH
c,im=load(CP),load(IP);owner=next(e for e in load('content/catalog.json')['entries'] if e['id']=='workbook-01-07-game-boy-advance-sp')
source=load(BASE+'wikipedia-original-api.json')['query']['pages']['292722']
assert source['revisions'][0]['revid']==1380880449
lines=source['extract'].splitlines();bodies=[];records=[]
for row in c['changes']:
    if 'body' in row:
        n=row['source_chapter_index'];assert owner['body'][n]==row['old_body'] and owner['story_headings'][n]==row['old_heading']
        assert hashlib.sha256(row['old_body'].encode()).hexdigest()==row['old_body_sha256']
        assert hashlib.sha256(row['body'].encode()).hexdigest()==row['body_sha256']
        p=row['provenance'];assert sha(p['source_file'])==p['source_file_sha256']
        actual=[lines[n] for n in p['paragraph_indices']];assert actual==p['source_paragraphs']
        if p['adaptations']:
            assert n==0 and p['full_paragraph'] is False
            spans=p['adaptations'][0]['retained_character_spans'];actual[0]=' '.join(actual[0][a:b].strip() for a,b in spans)
            assert all(actual[0].endswith('.') for _ in [0])
        else:assert p['full_paragraph'] is True
        assert '\n\n'.join(actual)==row['body']
        bodies.append(row['body']);records.append(dict(index=n,body_sha256=row['body_sha256'],source_indices=p['paragraph_indices']))
    elif 'old_date' in row:
        assert owner['date']==row['old_date'] and row['date']==dict(month=2,day=14,precision='day',region='')
        assert row['year']==2003 and 'released in Japan on February 14, 2003' in source['extract']
    else:
        assert owner.get(row['field'],'')==row['old_value']
        assert hashlib.sha256(row['old_value'].encode()).hexdigest()==row['old_value_sha256']
assert len(records)==4
rp=BASE+'independent-four-concrete-cards-real-launch-review.json'
receipt=dict(status='PASS',candidate_path=CP,candidate_sha256=CH,records=records,observations=['All4 old/new cards read and reconstructed from actual Wikipedia revision1380880449 raw extract lines. Card0 selects complete first/third sentences with exact spans and retains the complete second source paragraph; regional dates no longer occupy the prose. Other cards reproduce whole paragraphs.','The first release14February2003 is explicitly supported by actual source prose; stable historicalID is retained, announcement7January is removed from active date/event semantics. Summary/subtitle are clear and factually supported.','SatoruOkada design history, original front lighting versus later backlit revision, and the headphone/charging shared port are concrete and edition-correct. Existing artwork and model records remain outside this text correction.'],master_modified=False)
(ROOT/rp).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert im['requires_clarity_candidate_sha256']==CH
guard=im['article_guards'][owner['id']];assert guard['original_body']==bodies
assert hashlib.sha256(json.dumps(bodies,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==guard['body_sha256']
infos=[]
for s in im['source_receipts']:
    assert sha(s['path'])==s['sha256']
    infos.extend(p['imageinfo'][0] for p in load(s['path'])['query']['pages'].values() if p.get('imageinfo'))
images=[]
for i in im['entries'][owner['id']]:
    assert sha(i['recovery_local_source'])==i['verification']['source_sha256']
    with Image.open(ROOT/i['recovery_local_source']) as pic:pic.load();assert pic.size==(i['width'],i['height'])
    raw=next(r for r in infos if r['descriptionurl']==i['source_page']);m=raw['extmetadata']
    assert m['LicenseShortName']['value']=='Public domain' and 'Evan-Amos' in m['Artist']['value']
    assert (raw['width'],raw['height'])==(i['width'],i['height'])
    assert not any(old['url']==i['url'] for old in owner['images'])
    images.append(dict(path=i['recovery_local_source'],paragraph=i['story_paragraph'],sha256=sha(i['recovery_local_source']),dimensions=[i['width'],i['height']],full_native_individually_viewed=True))
assert len(images)==2
irp=BASE+'independent-two-original-sp-accessory-images-review.json'
ireceipt=dict(status='PASS',candidate_path=IP,candidate_sha256=IH,requires_clarity_candidate_sha256=CH,images=images,observations=['Both full native photographs individually opened. AGS003 rechargeable originalSP battery hardware and originalSP headphone adapter are correctly identified; captions use the actual later photo date where supplied and do not mislabel a launch image.','Original Commons metadata verifies EvanAmos publicdomain dedication, native3700x2000battery and4200x1890adapter. Byte hashes and new post-claritybody guard match. Battery maps to overview/batteryparagraph0, adapter to shared-portparagraph3.','Two other narrative scenes remain without new illustrations. No duplicatehero, upscaling, generated image, new3Dmodel or complete-article claim.'],master_modified=False)
(ROOT/irp).write_text(json.dumps(ireceipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(rp,sha(rp));print(irp,sha(irp))
