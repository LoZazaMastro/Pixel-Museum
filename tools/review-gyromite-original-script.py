"""Inspect the original R.O.B. demonstration document and its public archival chain."""
from pathlib import Path
from PIL import Image
from html.parser import HTMLParser
import hashlib,json,re,html
ROOT=Path(__file__).resolve().parents[1];BASE='build/research/gyromite-rob-original-narrative-image/'
PATH=BASE+'one-original-rob-demonstration-script-candidate.json'
EXPECTED='5c65ea62aa230f03dea5d8007039702bfe477a91c5581902b6b0e398c0dfe4db'
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
assert sha(PATH)==EXPECTED
d=load(PATH)
for r in d['source_receipts']:assert sha(r['path'])==r['sha256']
e=next(x for x in load('content/catalog.json')['entries'] if x['id']=='workbook-08-13-gyromite')
g=d['article_guards'][e['id']];assert e['body']==g['original_body'] and e['story_headings']==g['original_headings']
assert hashlib.sha256(json.dumps(e['body'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==g['body_sha256']
m=d['entries'][e['id']][0];assert len(d['entries'][e['id']])==1 and m['story_paragraph']==2
assert sha(m['recovery_local_source'])==m['verification']['source_sha256']
with Image.open(ROOT/m['recovery_local_source']) as im:assert list(im.size)==[3352,4416]==m['verification']['native_dimensions'];mode=im.mode
page=(ROOT/(BASE+'vghf-nes-launch-source.html')).read_text(encoding='utf8')
plain=html.unescape(re.sub('<[^>]+>',' ',page));plain=re.sub(r'\s+',' ',plain)
assert 'The actual script that Nintendo’s Howard Phillips wrote and memorized' in plain
assert 'with his handwritten notes' in plain
urls=re.findall(r'https://drive\.google\.com[^\s"<>]+',page)
folders={n:(ROOT/(BASE+n)).read_text(encoding='utf8') for n in ['vghf-public-collection-folder.html','vghf-1985-test-market-folder.html','demo-script-folder.html']}
assert '0By3fjn1rWdp3VWhuQk13dWF3ekk' in folders['demo-script-folder.html']
assert '2/10/86' in m['caption'] and m['license_url']==''
assert m['url'] not in [i['url'] for i in e['images']]
receipt=dict(status='PASS',candidate_path=PATH,candidate_sha256=EXPECTED,original_asset_sha256=sha(m['recovery_local_source']),original_dimensions=[3352,4416],original_mode=mode,source_files_verified=len(d['source_receipts']),paragraph=2,observations=['The complete document was read through the existing inspection-only JPEG, including all margins and the handwritten HP2/10/86 mark. The original77MBPNG remains unchanged and its3352x4416native dimensions/hash were independently checked. Inspection derivative is not a replacement publication asset.','The VGHF collection page explicitly identifies HowardPhillips as writer of the memorized R.O.B. demonstration script and credits handwritten notes. The public Google folder listing contains the exact selected original download ID. Original Nintendo/author rights remain reserved; no CreativeCommons licence inferred.','The script explicitly sequences optical Test, Direct and GameA demonstration with both controllers, red/blue buttons and spinning gyros, and handwritten demonstrator cues. It is relevant to the existing paragraph about demonstrating the slow hardware and planning ahead. It is not used as an image of a1985unboxing or a measured performance test.','HP2/10/86 is retained literally without assuming day/month ordering. The archival sheet calls the professor Vector; no silent replacement with Hector in the image or caption. Entire current4paragraph body and headings remain exact.','The two960x717mall photographs remain held for resolution and are absent from this one-image candidate.'],master_modified=False)
out=BASE+'independent-one-original-demonstration-script-review.json';(ROOT/out).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(out,sha(out))
print('PUBLIC FOLDER LINKS',urls[:5]);print('FOLDER TITLES',[(n,re.findall(r'<title>(.*?)</title>',s)[:1]) for n,s in folders.items()])
