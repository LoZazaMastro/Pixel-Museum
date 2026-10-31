"""Reconcile the DS Lite text and photographed hardware against frozen sources."""
from pathlib import Path
from html.parser import HTMLParser
from PIL import Image
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
path=ROOT/'content/expansion/ds-lite-specific-story-candidate.json';candidate=read(path)
assert hashlib.sha256(path.read_bytes()).hexdigest()=='a2849730043b9b69a00a2ac9e90ecb3ad1475d4c08b8c065d0b42566b0119079'
class Paragraphs(HTMLParser):
    def __init__(self):super().__init__();self.active=False;self.skip=0;self.parts=[];self.rows=[]
    def handle_starttag(self,tag,attrs):
        if tag=='p':self.active=True;self.parts=[]
        if self.skip:self.skip+=1
        elif tag=='sup' and 'reference' in dict(attrs).get('class',''):self.skip=1
    def handle_endtag(self,tag):
        if self.skip:self.skip-=1;return
        if tag=='p' and self.active:self.rows.append(''.join(self.parts));self.active=False
    def handle_data(self,data):
        if self.active and not self.skip:self.parts.append(data)
parser=Paragraphs();parser.feed((ROOT/candidate['provenance']['source_html']).read_text(encoding='utf-8'))
normal=lambda s:re.sub(r'\s+',' ',s.replace('²','2')).strip()
actual={normal(s) for s in parser.rows}
assert len(candidate['body'])==len(candidate['story_headings'])==3
for paragraph in candidate['body']:assert normal(paragraph) in actual,paragraph[:80]
assert 'March 2, 2006' in candidate['body'][0]
assert len({i['url'] for i in candidate['images']})==4
assert sorted(i['story_paragraph'] for i in candidate['images'] if i['story_paragraph']>=0)==[0,1,2]
photos=[]
for image in candidate['images']:
    file=ROOT/image['recovery_local_source']
    with Image.open(file) as im:
        im.load();assert im.size==(image['width'],image['height'])
    assert image['credit'] and image['license'] and image['source_page']
    photos.append(dict(url=image['url'],size=[image['width'],image['height']],sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
receipt=dict(status='PASS',candidate_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    paragraph_source='Frozen Nintendo DS Wikipedia revision1376058033, including the actual DS Lite subsections. HTML superscript squared unit retained as ASCII2.',
    complete_source_paragraphs=3,photos=photos,
    visual_review='All four photographs viewed together: real black DS Lite hero, white DS Lite hardware photographed2006, distinct DS styluses, GBA-SP/DS-Lite cartridge-slot comparison. No original-DS/DSi substitution and no hero repeated in cards.',
    limitations='Published reference prose retained; not a new independent battery-life measurement or console layout signoff.')
(ROOT/'build/research/ds-lite-complete-story/root-independent-review.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print('PASS: three complete source paragraphs; four distinct correctly identified photographs at their real dimensions.')
