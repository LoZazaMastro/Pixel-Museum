"""Seven original illustrations, retaining readable Wikipedia body text."""
from pathlib import Path
import json, hashlib
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/automodellista-original-press'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
art=json.loads((BASE/'selected-master-inventory.json').read_text(encoding='utf8'))
manual=json.loads((BASE/'manual-selected-native-pages.json').read_text(encoding='utf8'))
press='https://archive.org/details/Capcom_E3_2002_Press_CD'
manual_page='https://archive.org/details/ps2_Auto_Modellista_USA'
images=[]
art_plans=[
 (0,'22.psd','A line-up of cel-shaded cars','Original promotional car artwork from Capcom\'s E3 2002 press CD. The original artwork is shown intact; it is not a gameplay screenshot.'),
 (1,'13.psd','Outlines and flat colours','Original E3 2002 car artwork demonstrates the game\'s cel-shaded visual treatment. No fan repaint or modern remaster is substituted.'),
 (5,'21.psd','Nine different liveries','A nine-panel livery illustration from the original E3 2002 press CD. This is the publisher\'s original composition, not a montage assembled for the museum.'),
]
for paragraph,name,title,caption in art_plans:
 r=next(r for r in art if r['group']=='art'and r['name']==name)
 f=ROOT/r['file'];p=ROOT/r['png'];assert sha(f)==r['sha256']and sha(p)==r['png_sha256']
 a=Image.open(f);a.load();z=Image.open(p);z.load();assert a.size==z.size and a.tobytes()==z.tobytes()
 images.append(dict(url=r['url'],source_page=press,title=title,caption=caption,
     story_paragraph=paragraph,width=r['width'],height=r['height'],
     creator='Capcom / original promotional artwork contributors',credit='Capcom / original E3 2002 press artwork',
     license='Original publisher and artwork rights retained. Archival press material; no open licence claimed.',
     recovery_local_source=r['png'],verification=dict(sha256=r['png_sha256'],original_source_sha256=r['sha256'],
         no_upscale=True,no_crop=True,pixels_identical=True,visually_reviewed=True),
     quality_scope='Native original press-master dimensions, not a new 4K render. Smaller preview JPGs and lower-resolution game captures are excluded.'))
manual_plans=[
 (2,10,'Courses in the North American manual','Printed page 9 of the original North American manual, including U.S. Speedway and U.S. Dirt Track. The regional edition is explicit because the accompanying card explains its changes.'),
 (3,13,'Garage Life in the original manual','Printed page 12 explains the main Garage Life mode and the relationship between racing and customising a car.'),
 (4,14,'Tyres, brakes and tuning','Printed page 13 shows Tune Car and its tyre, brake, suspension, turbine and other settings. An original manual page rather than a recreated interface.'),
 (6,23,'Connecting the PlayStation 2','Printed page 22 explains the original North American PlayStation 2 network setup. It documents that original service, not the later Xbox Insignia revival mentioned in the text.'),
]
for paragraph,pdf_page,title,caption in manual_plans:
 r=next(r for r in manual if r['pdf_page']==pdf_page);p=ROOT/r['file'];assert sha(p)==r['sha256']
 im=Image.open(p);im.load();assert im.size==(1364,2160)and hashlib.sha256(im.tobytes()).hexdigest()==r['pixel_sha256']
 images.append(dict(url='https://archive.org/download/ps2_Auto_Modellista_USA/Auto_Modellista_USA.pdf#page='+str(pdf_page+1),
     source_page=manual_page,title=title,caption=caption,story_paragraph=paragraph,
     width=r['width'],height=r['height'],creator='Capcom / original manual contributors',
     credit='Capcom / original North American instruction manual',
     license='Original publisher, manual and depicted game artwork rights retained. Archival scan; no open licence claimed.',
     recovery_local_source=r['file'],verification=dict(sha256=r['sha256'],no_upscale=True,no_crop=True,
         embedded_jp2_sha256=r['source_image_sha256'],embedded_pixels_sha256=r['pixel_sha256'],
         pdf_zero_based_page=pdf_page,printed_page=r['printed_page'],visually_reviewed=True),
     quality_scope='Original embedded 1364x2160 scan extracted directly to PNG without re-rasterisation or enlargement.'))
images.sort(key=lambda r:r['story_paragraph'])
assert len(images)==7 and [r['story_paragraph']for r in images]==list(range(7))
assert len({r['verification']['sha256']for r in images})==7
candidate=dict(schema_version=1,publication_status='independent_review_pending',entry_id='wikipedia-2364191',
    preserve_body=True,preserve_hero=True,images=images,
    story_headings=['Capcom\'s cel-shaded racing game','A hand-drawn appearance','The revised North American edition',
                    'Garage Life and car setup','Tuning the mechanical parts','Paint, stickers and bodywork','Racing online'],
    additional_sources=[dict(title='Capcom E3 2002 press CD',url=press,publisher='Capcom; archived publisher press materials'),
                        dict(title='Auto Modellista original North American instruction manual',url=manual_page,publisher='Capcom')],
    source_receipts=[dict(file=str(p.relative_to(ROOT)).replace('\\','/'),sha256=sha(p))for p in [
        BASE/'capcom-2002-disc-directory.html',BASE/'art-psd-directory.html',BASE/'selected-master-inventory.json',
        BASE/'Auto_Modellista_USA-original-manual.pdf',BASE/'manual-selected-native-pages.json']],
    scope='Seven distinct primary press/manual artifacts paired to seven existing clear Wikipedia paragraphs. No text, date, music or original cover change. Original PSD composite pixels preserved, no invented transparency, no generic unrelated game images, no complete press disc or full manual shipped.')
p=BASE/'seven-original-illustrations-candidate.json'
p.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(p.relative_to(ROOT),sha(p))
