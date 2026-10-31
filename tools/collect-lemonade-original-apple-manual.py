"""Inspect the original Apple cassette booklet, keeping the publisher's pages intact."""
from pathlib import Path
import urllib.request,hashlib,json
from pypdf import PdfReader
import pypdfium2
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/lemonade-existing-prose-original-apple-manual';base.mkdir(parents=True,exist_ok=True)
url='https://www.brutaldeluxe.fr/projects/cassettes/apple/apple_theappletapes_appleiiplus_manual.pdf'
p=base/'apple-original-cassette-booklet.pdf'
if not p.exists():
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=35)as r:data=r.read()
    assert data.startswith(b'%PDF');p.write_bytes(data)
doc=PdfReader(p);rows=[]
for n,page in enumerate(doc.pages):
    text=page.extract_text()or''
    row=dict(pdf_page=n+1,text=text)
    rows.append(row)
report=dict(source_url=url,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),pages=rows)
(base/'manual-inspection.json').write_text(json.dumps(report,indent=2,ensure_ascii=True)+'\n',encoding='utf8')
print(json.dumps(report,ensure_ascii=True))
renderer=pypdfium2.PdfDocument(p)
for n in [4,5,6]:
    if n<len(doc.pages):renderer[n].render(scale=3).to_pil().save(base/f'original-full-pdf-page-{n+1}.png')
