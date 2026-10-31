"""Record independent review of three source-qualified original narrative images."""
from pathlib import Path
from PIL import Image
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];BASE='build/research/atari-1972-original-narrative-illustrations/'
PATH=BASE+'two-atari-one-advance-wars-quality-selected-candidate.json';EXPECTED='b3b3201bcf6a660a1273c8dc20ad18dfc78c8866db3420a227b5bc1e9a1d91fa'
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
assert sha(PATH)==EXPECTED
d=load(PATH);catalog={e['id']:e for e in load('content/catalog.json')['entries']}
for r in d['source_receipts']:assert sha(r['path'])==r['sha256']
rows=[];seen=set()
for entry_id,images in d['entries'].items():
    owner=catalog[entry_id];guard=d['article_guards'][entry_id]
    assert owner['body']==guard['original_body'] and owner.get('story_headings',[])==guard['original_headings']
    assert hashlib.sha256(json.dumps(owner['body'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==guard['body_sha256']
    for m in images:
        p=m['recovery_local_source'];v=m['verification'];assert sha(p)==v['source_sha256']
        with Image.open(ROOT/p) as im:
            rgb=im.convert('RGB');dims=list(im.size)
            pixel=hashlib.sha256(str(rgb.size).encode()+rgb.tobytes()).hexdigest()
        assert dims==v['native_dimensions']==[m['width'],m['height']] and pixel==v['decoded_rgb_identity_sha256']
        assert pixel not in seen;seen.add(pixel)
        assert 0<=m['story_paragraph']<len(owner['body'])
        assert m['url'] not in [i['url'] for i in owner['images']]
        rows.append(dict(entry_id=entry_id,url=m['url'],paragraph=m['story_paragraph'],dimensions=dims,sha256=sha(p)))
assert len(rows)==3 and {x['paragraph'] for x in rows if x['entry_id']=='workbook-06-27-atari'}=={0,1}
receipt=dict(status='PASS',candidate_path=PATH,candidate_sha256=EXPECTED,images=rows,source_hashes_verified=len(d['source_receipts']),observations=['All three originals individually viewed in full. The incorporation filing visibly identifies Atari and27June1972; the source HTML credits Ethan Johnson for the published scan. The early-team image shows Pong and four people, with1973/AlAlcorn archival credit explicitly stated in the source. It is not claimed to depict incorporation day or to have an independently identified photographer.','Nintendo screenshot shows actual2023ReBootCamp helicopter-versus-warship combat with commanding officers and unit status. Exact publisher gallery URL and native1280x720 retained; appropriate for the paragraph about air/sea units and not the unillustrated release-delay paragraph.','All six current article paragraphs read for association. Their complete text, headings and compact hashes remain unchanged. The apparent ANSI rendering of the existing en dash is not a UTF8 corruption and has not been edited.','CHM800x600prototype and768x1012cartridge catalogue remain held for quality under parent review; neither is admitted in this three-image variant. No CreativeCommons rights invented for reserved-rights documents/photos/game imagery.'],master_modified=False)
out=BASE+'independent-three-quality-selected-originals-review.json';(ROOT/out).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(out,sha(out))

