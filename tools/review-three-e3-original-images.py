"""Independent full-image and original Commons metadata check, preserving dated context."""
from pathlib import Path
from PIL import Image
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[1];BASE='build/research/e3-2010-original-narrative-images/'
PATH=BASE+'three-paragraph-bound-e3-native-jpeg-readable-candidate.json'
EXPECTED='0e910ba255587a0b227544aac18ae416502add6641e521cf4b482962554aa747'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert sha(PATH)==EXPECTED
d=load(PATH)
for s in d['source_receipts']:assert sha(s['path'])==s['sha256']
owner=next(e for e in load('content/catalog.json')['entries'] if e['id']=='daily-06-15')
guard=d['article_guards']['daily-06-15']
assert owner['body']==guard['original_body'] and owner['story_headings']==guard['original_headings']
assert hashlib.sha256(json.dumps(owner['body'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==guard['body_sha256']
original=load(BASE+'three-paragraph-bound-e3-original-images-candidate.json')
for n,(a,b) in enumerate(zip(original['entries']['daily-06-15'],d['entries']['daily-06-15'])):
    c=copy.deepcopy(b)
    if n in (1,2):c['caption']=a['caption']
    if n==2:
        c['verification']=a['verification'];c['recovery_local_source']=a['recovery_local_source']
    assert c==a
query=load(BASE+'two-existing-image-original-source-query.json')['query']['pages']
infos=[p['imageinfo'][0] for p in query.values()]
seen=set();rows=[]
for n,i in enumerate(d['entries']['daily-06-15']):
    p=i['recovery_local_source'];assert sha(p)==i['verification']['source_sha256']
    with Image.open(ROOT/p) as im:
        im.load();assert im.size==(i['width'],i['height']);h=hashlib.sha256(str(im.size).encode()+im.convert('RGB').tobytes()).hexdigest()
    if n:assert h==i['verification']['decoded_rgb_identity_sha256']
    assert h not in seen;seen.add(h)
    assert i['story_paragraph']==n+1
    assert not any(old['url']==i['url'] for old in owner['images'])
    if n:
        raw=next(r for r in infos if r['descriptionurl']==i['source_page']);m=raw['extmetadata']
        assert (raw['width'],raw['height'])==(i['width'],i['height'])
        assert i['creator'] in m['Artist']['value']
        assert m['DateTimeOriginal']['value'].startswith('2010-06-15' if n==1 else '2011-11-22')
        assert m['LicenseShortName']['value']==('CC BY 2.0' if n==1 else 'Public domain')
    rows.append(dict(paragraph=n+1,path=p,sha256=sha(p),dimensions=[i['width'],i['height']],full_native_individually_viewed=True))
assert d['entries']['daily-06-15'][0]==load(BASE+'one-contemporaneous-kinect-demo-guard-corrected-candidate.json')['entries']['daily-06-15'][0]
receipt=dict(status='PASS',candidate_path=PATH,candidate_sha256=EXPECTED,images=rows,observations=['All4 actual article paragraphs read. All3 full native images individually opened: original projected Kinect scanning event, physical original AquaBlue3DS prototypes behind E3displaycase, originalMove controller held with buttons and strap. Correct paragraph associations1,2,3; hero not reused.','Original Commons imageinfo metadata verifies3DS15June2010 popculturegeekCCBY2, and Move22November2011 EvanAmospublicdomain. Later Move photograph explicitly illustrates the original control grip, not an E3event photograph.','All source-file hashes/native dimensions and body/headings guards match. Kinect image is identical to the already independently approved exact original; no new claim of direct framebuffer screenshot.','Two caption date-spacing repairs affect readability only. Final Move uses the current actual original CommonsJPEG directly; the earlier PlayhubPNG was not pixel-identical and is excluded from this final candidate. No unsupported lossless-conversion claim.','Photos remain unmodified; no app performance, virtual stereoscopy or physicalPS5 playback claim.'],master_modified=False)
out=BASE+'independent-three-original-e3-native-jpeg-context-images-review.json';(ROOT/out).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(out,sha(out))
