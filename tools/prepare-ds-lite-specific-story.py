"""Prepare a source-bound, illustrated DS Lite revision; do not admit before peer review."""
from pathlib import Path
from html.parser import HTMLParser
import copy,hashlib,json,re
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'build/research/ds-lite-complete-story'
source=ROOT/'build/research/cover-people/Nintendo_DS_Lite.html';html=source.read_text(encoding='utf8')
assert 'wgRevisionId":1376058033' in html
class Text(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag in['style','script'] or(tag=='sup'and'reference'in attrs.get('class','')):self.skip+=1
    def handle_endtag(self,tag):
        if tag in['sup','style','script']and self.skip:self.skip-=1
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)
def paragraphs(section):
    start=html.index('id="'+section+'"');end=html.find('<div class="mw-heading',start+30)
    result=[]
    for raw in re.findall(r'<p\b[^>]*>(.*?)</p>',html[start:end],re.S):
        parser=Text();parser.feed(raw);text=''.join(parser.parts).strip()
        if len(text.split())>25:result.append(text)
    return result
body=[paragraphs('DS_Lite')[0],paragraphs('Nintendo_DS_Lite')[0],paragraphs('Compatibility')[0]]
assert '200\xa0cd/m2' in body[1], 'Keep the actual square-metre exponent, not reference-only sup stripping'
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'));by={e['id']:e for e in catalog['entries']};original=by['workbook-03-02-nintendo-ds-lite']
manifest=json.loads((ROOT/'assets/images/manifest.json').read_text(encoding='utf8'))
def dimensions(path):
    with Image.open(ROOT/path)as im:im.load();return im.size
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
hero=copy.deepcopy(original['images'][0]);hero.update(url='https://upload.wikimedia.org/wikipedia/commons/5/56/Nintendo-DS-Lite-Black-Open.png',
 width=3200,height=2700,recovery_local_source='build/research/ds-lite-complete-story/black-open-original.png',
 story_paragraph=-1,cover_art=True,creator='Evan-Amos',credit='Evan-Amos / public domain',
 license='Released into the worldwide public domain by the photographer Evan-Amos.',
 caption='Original black DS Lite photographed later, in2011; the original unscaled3200x2700 master.',
 verification={'sha256':sha('build/research/ds-lite-complete-story/black-open-original.png'),'no_upscale':True})
side={'url':'https://upload.wikimedia.org/wikipedia/commons/8/81/Nintendo_DS_Lite_%28right_side%29.jpg',
 'source_page':'https://commons.wikimedia.org/wiki/File:Nintendo_DS_Lite_(right_side).jpg',
 'title':'Nintendo DS Lite: original2006 hardware, right side','caption':'The stylus holder, power switch and relocated Start/Select buttons, photographed in June2006.',
 'creator':'Havok','credit':'Havok / CC BY2.5','license':'Creative Commons Attribution2.5 Generic',
 'license_url':'https://creativecommons.org/licenses/by/2.5/','width':2306,'height':1481,
 'story_paragraph':0,'recovery_local_source':'build/research/ds-lite-complete-story/right_side.jpg',
 'verification':{'sha256':sha('build/research/ds-lite-complete-story/right_side.jpg'),'native_dimensions':[2306,1481],'no_upscale':True},
 'visual_review':'Actually viewed full original photograph: white original DS Lite and stylus, clear hardware details. Source dates the image to June2006, not a later DSi.'}
images=[hero,side]
for urlpart,index in [('Nintendo-DS-Styli.jpg',1),('Game-Boy-Nintendo-DS-Slots.jpg',2)]:
    image=copy.deepcopy(next(i for i in by['daily-12-02']['images']if urlpart in i['url']))
    image['story_paragraph']=index
    image['recovery_local_source']=manifest['images'][image['url']]
    images.append(image)
doc={'publication_status':'awaiting_independent_review','entry_id':original['id'],
 'body':body,'story_headings':['2006 / A redesign meets heavy demand','A slimmer case, brighter displays and a larger stylus','Keeping the Game Boy Advance cartridge slot'],
 'summary':'DS Lite refines the original dual-screen handheld with a slimmer body, brighter displays and a larger stylus, while retaining its DS and Game Boy Advance game libraries.',
 'images':images,'preferred_image':0,'videos':copy.deepcopy(original.get('videos',[])),
 'sources':[{'title':'Nintendo DS — DS Lite history, redesign and compatibility sections','url':'https://en.wikipedia.org/w/index.php?title=Nintendo_DS&oldid=1376058033','publisher':'Wikipedia contributors','revision_id':1376058033,'license':'CC BY-SA4.0','license_url':'https://creativecommons.org/licenses/by-sa/4.0/'}],
 'editorial_credit':'Wikipedia contributors / CC BY-SA4.0',
 'attribution':{'text':'Three complete English Wikipedia paragraphs reproduced from the frozen revision. Card headings and summary supplied editorially.','license':'CC BY-SA4.0','source_url':'https://en.wikipedia.org/w/index.php?title=Nintendo_DS&oldid=1376058033'},
 'provenance':{'source_html':source.relative_to(ROOT).as_posix(),'source_sha256':sha(source.relative_to(ROOT)),
 'source_sections':['History / DS Lite paragraph0','Hardware / Nintendo DS Lite paragraph0','Games / Compatibility paragraph0'],
 'previous_draft':{k:copy.deepcopy(original.get(k))for k in['body','story_headings','images','sources','editorial_credit']},
 'selection_note':'The current DS Lite Wikipedia URL redirects to the main DS article. Select only its explicit DS Lite sections plus the shared original DS/DS Lite GBA compatibility paragraph, never the DSi revision. The three generic template paragraphs are preserved only as research provenance, not historical claims.'}}
path=ROOT/'content/expansion/ds-lite-specific-story-candidate.json';path.write_text(json.dumps(doc,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
sheet=Image.new('RGB',(1600,570),'#ece9e1');draw=ImageDraw.Draw(sheet)
for n,image in enumerate(images):
    local=image['recovery_local_source']
    im=Image.open(ROOT/local).convert('RGBA');base=Image.new('RGBA',im.size,'white');base.alpha_composite(im)
    thumb=ImageOps.contain(base.convert('RGB'),(780,240));x=n%2*800;y=n//2*285;sheet.paste(thumb,(x+(780-thumb.width)//2,y));draw.text((x+8,y+245),f"{n}: {image['title']}"[:90],fill='black')
sheet.save(WORK/'four-original-images-contact.jpg',quality=94)
print(json.dumps({'status':'candidate_only','body_paragraphs':3,'words':sum(len(x.split())for x in body),'images':4,'candidate_sha256':sha(path.relative_to(ROOT))}))
