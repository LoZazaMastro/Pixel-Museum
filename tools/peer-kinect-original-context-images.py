"""Read-only independent source/pixel audit of four original Kinect illustrations."""
from pathlib import Path
import hashlib
import html
import json
import re
from PIL import Image
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/kinect-original-story'
candidate=BASE/'four-original-context-images-candidate.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(candidate)=='d6a493d0fa105149556592b7bf0659bc2bb8c7215fb263a5b539c7b58f874312'
c=json.loads(candidate.read_text(encoding='utf8'))
catalog=ROOT/'content/catalog.json'
e=next(e for e in json.loads(catalog.read_text(encoding='utf8'))['entries'] if e['id']==c['entry_id'])
assert hashlib.sha256(json.dumps(e['body'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==c['body_sha256']
assert len(e['body'])==len(c['story_headings'])==len(c['images'])==4
assert [i['story_paragraph'] for i in c['images']]==list(range(4))
hero=e['images'][e.get('preferred_image',0)]
assert hero['url']=='https://upload.wikimedia.org/wikipedia/commons/6/67/Xbox-360-Kinect-Standalone.png'
assert sha(ROOT/hero['recovery_local_source'])==hero['verification']['sha256']

def visible(path):
    text=path.read_text(encoding='utf8')
    text=re.sub(r'<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>',' ',text,flags=re.S|re.I)
    return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',text)))

commons=[
 (0,'e3-primary-page.html','James Pfaff','litheon','14 June 2010','Attribution 2.0 Generic'),
 (1,'people0-primary-page.html','Atomic Taco','Seattle','18 November 2010','Attribution-Share Alike 2.0 Generic'),
 (3,'people1-primary-page.html','Sergey Galyonkin','Sergiy Galyonkin','21 August 2010','Attribution-Share Alike 2.0 Generic')]
sources=[]
for index,file,author,alias,date,licence in commons:
    p=BASE/file
    text=visible(p)
    for token in [author,alias,date,licence]:assert token in text,(file,token)
    assert c['images'][index]['url'] in p.read_text(encoding='utf8')
    start=text.index('Author ')
    sources.append({'paragraph':index,'source_file':p.relative_to(ROOT).as_posix(),'source_sha256':sha(p),
                    'author':author,'source_name_alias':alias,'date':date,'file_licence':licence,
                    'author_context':text[max(0,start-120):start+180],
                    'source_page':c['images'][index]['source_page']})

images=[]
for im in c['images']:
    p=ROOT/im['recovery_local_source']
    assert sha(p)==im['verification']['sha256']
    with Image.open(p) as decoded:
        decoded.load()
        assert list(decoded.size)==im['verification']['native_dimensions']==[im['width'],im['height']]
    images.append({'story_paragraph':im['story_paragraph'],'path':im['recovery_local_source'],
                   'sha256':sha(p),'dimensions':[im['width'],im['height']],
                   'full_native_image_visually_reviewed':True})
assert len({i['sha256'] for i in images} | {hero['verification']['sha256']})==5

d=c['images'][2]['derivation']
pdf_path=ROOT/d['source_pdf']
assert sha(pdf_path)==d['source_pdf_sha256']
document=pdfium.PdfDocument(pdf_path)
page=document[d['zero_based_page']]
assert list(page.get_size())==d['pdf_page_size_points']==[612,792]
render=page.render(scale=d['render_scale_pixels_per_point'],crop=tuple(d['pdfium_crop_points_left_bottom_right_top']))
reproduced=render.to_pil()
with Image.open(ROOT/c['images'][2]['recovery_local_source']) as supplied:
    assert reproduced.size==supplied.size==(1428,960)
    assert reproduced.convert('RGB').tobytes()==supplied.convert('RGB').tobytes()
textpage=page.get_textpage()
paper_text=textpage.get_text_range()
for token in ['Jamie Shotton','Microsoft Research Cambridge','Xbox Incubation','Figure 1. Overview','body part','joint']:
    assert token in paper_text,token
textpage.close();render.close();page.close();document.close()
primary=BASE/'research-primary-page.html'
primary_text=visible(primary)
for token in ['Jamie Shotton','CVPR','June 2011','Published by IEEE']:
    assert token in primary_text,token
sources.append({'paragraph':2,'source_file':primary.relative_to(ROOT).as_posix(),
                'source_sha256':sha(primary),'source_page':c['images'][2]['source_page'],
                'publication':'CVPR, June 2011; Microsoft Research publication page identifies IEEE',
                'actual_pdf_sha256':sha(pdf_path),'actual_pdf_first_page_visually_reviewed':True,
                'figure_render_reproduced_exact_RGB_pixels':True,'render_dimensions':[1428,960]})

associations=[
 {'paragraph':0,'status':'PASS','basis':'Visible original Xbox360 Kinect sensor, Xbox360S and controller at E3 June2010; accurately labelled pre-launch, not a later KinectOne sensor.'},
 {'paragraph':1,'status':'PASS','basis':'Two customers visibly move their bodies while the TV displays KinectSports football. The 18November2010 original photograph illustrates gesture input and physical play distance, not a controller-based game.'},
 {'paragraph':2,'status':'PASS','basis':'Figure1 visibly maps a depth image to body-part labels and 3D joint proposals, matching the computer-vision paragraph. Source is a mixed vector/raster research illustration and is identified as such, with no colour-camera/4K photograph claim.'},
 {'paragraph':3,'status':'PASS','basis':'Original2010 Gamescom/Rudolphplatz demonstration booth visibly provides displays, open floor and public access. Caption describes arrangement, not an unsupported claim that this particular photograph shows every named launch game.'}]
out={'schema_version':1,'publication_status':'PASS','candidate_path':candidate.relative_to(ROOT).as_posix(),
     'candidate_sha256':sha(candidate),'source_catalog_sha256':sha(catalog),'entry_id':e['id'],
     'body_unchanged_sha256':c['body_sha256'],'body_hash_encoding':'UTF8 JSON, ensure_ascii=False, separators=(comma,colon)',
     'hero_unchanged':{'url':hero['url'],'sha256':hero['verification']['sha256']},
     'images':images,'source_receipts':sources,'paragraph_associations':associations,
     'headings_review':'All four new headings directly identify the sensor, body input, part/joint recognition and physical play space described in the unchanged paragraphs.',
     'rights_review':'Commons file licences checked in actual visible author/licensing sections, not generic page-footer CC terms. James Pfaff: CC BY2.0; Atomic Taco: CC BY-SA2.0; Galyonkin: CC BY-SA2.0. The name variants Sergey/Sergiy identify the same photographer in the author line/Flickr category. Research figure retains author/publication rights and claims no open licence.',
     'limits':['2010 photos are genuine original camera dimensions; no 4K restoration or upscaling.',
               'The1428x960 PDF-derived figure includes original low-resolution depth raster panels; exact PDF render parity does not turn those panels into high-resolution photographs.',
               'Body/date remain unchanged; media association QA does not newly verify every historical or technical sentence of the existing published article.',
               'No production/master modifications, deployment or physical console rendering performed.'],
     'master_modified':False}
target=BASE/'independent-four-context-images-review.json'
target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':target.relative_to(ROOT).as_posix(),'sha256':sha(target),'status':out['publication_status'],'images':len(images),'figure_pixels':'EXACT'}))
