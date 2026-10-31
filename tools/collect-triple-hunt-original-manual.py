"""Inspect genuine Atari operating instructions for the three original games."""
from pathlib import Path
import hashlib
import json
import urllib.request
from pypdf import PdfReader
from PIL import Image
import io
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/triple-hunt-existing-prose-original-manual'
BASE.mkdir(parents=True,exist_ok=True)
url='https://www.arcade-museum.com/manuals-videogames/T/TripleHunt.pdf'
pdf=BASE/'atari-triple-hunt-original-manual.pdf'
if not pdf.exists():
    request=urllib.request.Request(url,headers={'User-Agent':'PixelMuseumResearch/1.0 (historical source review)'})
    with urllib.request.urlopen(request,timeout=45)as response:
        pdf.write_bytes(response.read())
reader=PdfReader(pdf)
render_doc=pdfium.PdfDocument(pdf)
rows=[]
for n in [5,23,24,25,26]:
    page=reader.pages[n]
    for k,item in enumerate(page.images):
        path=BASE/f'original-manual-pdf{n+1}-image{k}{Path(item.name).suffix}'
        path.write_bytes(item.data)
        png=BASE/f'original-manual-pdf{n+1}-image{k}.png'
        # Render the page so its original indexed colour table is honoured.
        # The bare CCITT extraction does not carry the PDF palette semantics.
        render_doc[n].render(scale=300/72).to_pil().save(png)
        rows.append(dict(pdf_page=n+1,file=path.relative_to(ROOT).as_posix(),
                         size=Image.open(io.BytesIO(item.data)).size,
                         sha256=hashlib.sha256(item.data).hexdigest(),
                         lossless_png=png.relative_to(ROOT).as_posix(),
                         png_sha256=hashlib.sha256(png.read_bytes()).hexdigest()))
receipt=dict(source_url=url,pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),pages=len(reader.pages),images=rows)
(BASE/'original-manual-inspection.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
print(json.dumps(receipt))
