"""Collect existing source prose and original artefacts for Nintendo's story."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/nintendo-complete-story'
OUT.mkdir(parents=True,exist_ok=True)
read=lambda path:json.loads(path.read_text(encoding='utf-8'))
save=lambda name,data:(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

class Chapters(HTMLParser):
    def __init__(self):
        super().__init__();self.title='';self.heading=None;self.paragraph=False;self.parts=[];self.skip=0;self.rows=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('h2','h3'):self.heading=tag;self.parts=[]
        elif tag=='p' and not self.heading:self.paragraph=True;self.parts=[]
        elif tag=='sup':self.skip+=1
        elif tag=='br' and self.paragraph:self.parts.append(' ')
    def handle_data(self,data):
        if (self.heading or self.paragraph) and not self.skip:self.parts.append(data)
    def handle_endtag(self,tag):
        if tag=='sup':self.skip=max(0,self.skip-1)
        if tag==self.heading:
            self.title=' '.join(''.join(self.parts).split());self.heading=None;self.parts=[]
        elif tag=='p' and self.paragraph:
            text=' '.join(''.join(self.parts).split())
            if text:self.rows.append(dict(section=self.title,text=text))
            self.paragraph=False;self.parts=[]

source=read(OUT/'history-wikipedia-full.json')['parse']
parser=Chapters();markup=source['text'];parser.feed(markup if isinstance(markup,str) else markup['*'])
save('history-sections-readable.json',dict(source='https://en.wikipedia.org/wiki/History_of_Nintendo',
    revision=source['revid'],license='CC BY-SA 4.0',paragraphs=parser.rows))
catalog=read(ROOT/'content/catalog.json')
ids=['daily-09-23','nes','game-boy','daily-11-21','nintendo-64','workbook-03-21-game-boy-advance',
     'workbook-09-14-nintendo-gamecube','daily-12-02','wii','nintendo-3ds','daily-11-18','switch','switch-2','daily-11-16','daily-12-06']
records=[]
for entry_id in ids:
    entry=next((e for e in catalog['entries'] if e['id']==entry_id),None)
    if entry:records.append(dict(id=entry_id,title=entry['title'],year=entry['year'],images=entry.get('images',[]),sources=entry.get('sources',[])))
save('existing-exhibit-artifacts.json',records)
nintendo=next(e for e in catalog['entries'] if e['id']=='daily-09-23')
original_path=OUT/'original-story.json'
if not original_path.exists():save('original-story.json',nintendo)
print('Collected',len(parser.rows),'source paragraphs and',sum(len(e['images']) for e in records),'existing artefacts.')
