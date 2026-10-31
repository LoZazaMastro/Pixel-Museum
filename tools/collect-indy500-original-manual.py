"""Collect the publisher manual without altering the historical document."""
from pathlib import Path
import hashlib,json,urllib.request
from pypdf import PdfReader
from PIL import Image,ImageDraw
import io
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/indy500-existing-prose-original-manual'
base.mkdir(parents=True,exist_ok=True)
url='https://www.ataricompendium.com/archives/manuals/vcs/indy_500.pdf'
pdf=base/'indy-500-original-manual.pdf'
if not pdf.exists():
    request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(request,timeout=45) as response:
        data=response.read()
    assert data.startswith(b'%PDF')
    pdf.write_bytes(data)
reader=PdfReader(pdf)
sheet=Image.new('RGB',(1640,1400),'#303030')
draw=ImageDraw.Draw(sheet)
for n in range(8):
    img=reader.pages[n].images[0]
    path=base/f'manual-pdf-page-{n+1}.jpg'
    path.write_bytes(img.data)
    view=Image.open(io.BytesIO(img.data)).convert('RGB')
    view.thumbnail((390,650))
    x=(n%4)*410;y=(n//4)*700
    sheet.paste(view,(x,y+25))
    draw.text((x+8,y+6),f'PDF page {n+1}',fill='white')
sheet.save(base/'first-eight-original-pages-contact.jpg',quality=92)
report={'source_url':url,'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
    'page_count':len(reader.pages),'pages':[]}
for n,page in enumerate(reader.pages):
    text=page.extract_text() or ''
    row={'pdf_page':n+1,'text':text,'images':[]}
    for i,img in enumerate(page.images):
        row['images'].append({'index':i,'size':list(img.image.size),'format':img.image.format})
    report['pages'].append(row)
(base/'manual-inspection.json').write_text(json.dumps(report,indent=2,ensure_ascii=True)+'\n',encoding='utf8')
print(json.dumps(report,ensure_ascii=True))
