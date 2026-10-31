"""Retain the actual TI port manual as a distinct artifact of the game's adaptations."""
from pathlib import Path
import urllib.request,hashlib,json
from pypdf import PdfReader
import pypdfium2
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/wumpus-existing-prose-ti-adaptation'
base.mkdir(parents=True,exist_ok=True)
url='https://mocagh.org/ti994a/huntwumpus-manual.pdf'
path=base/'ti-original-hunt-wumpus-manual.pdf'
if not path.exists():
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=35)as r:data=r.read()
    assert data.startswith(b'%PDF');path.write_bytes(data)
doc=PdfReader(path);renderer=pypdfium2.PdfDocument(path)
sheet=Image.new('RGB',(1600,1200),'#303030');draw=ImageDraw.Draw(sheet)
rows=[]
for n,p in enumerate(doc.pages):
    text=p.extract_text()or''
    rows.append(dict(pdf_page=n+1,text=text))
    if n<8:
        pic=renderer[n].render(scale=1).to_pil().convert('RGB');pic.thumbnail((390,550))
        x=n%4*400;y=n//4*600;sheet.paste(pic,(x,y+25));draw.text((x+5,y+5),f'PDF page {n+1}',fill='white')
sheet.save(base/'manual-first-eight-pages-contact.jpg',quality=92)
report=dict(source_url=url,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),pages=rows)
(base/'manual-inspection.json').write_text(json.dumps(report,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(pages=len(doc.pages),source_pdf_sha256=report['sha256'])))
