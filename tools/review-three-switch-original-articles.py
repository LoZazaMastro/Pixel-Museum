"""Source reconstruction and native-asset verification after individual visual review."""
from pathlib import Path
from html.parser import HTMLParser
from PIL import Image
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
PATH='build/research/three-original-switch-articles-high-resolution-cover-candidate.json'
EXPECTED='ace9ee6d5ae62d16d2cea5196b95806d7ab45a8cf12ac11231621693d3a14696'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
class Paragraphs(HTMLParser):
    def __init__(self):super().__init__();self.p=False;self.sup=0;self.buf=[];self.ps=[];self.all=[]
    def handle_starttag(self,t,a):
        if t=='p':self.p=True;self.buf=[]
        if t=='sup':self.sup+=1
    def handle_endtag(self,t):
        if t=='p' and self.p:self.ps.append(''.join(self.buf).strip());self.p=False
        if t=='sup':self.sup=max(0,self.sup-1)
    def handle_data(self,x):
        self.all.append(x)
        if self.p and not self.sup:self.buf.append(x)
assert sha(PATH)==EXPECTED
doc=load(PATH)
previous=load('build/research/three-original-switch-articles-distinct-preview-candidate.json')
for a,b in zip(previous['entries'],doc['entries']):
    for field in ('body','story_headings','date','year','videos'):assert a[field]==b[field]
    assert a['images'][1:]==b['images'][1:]
for s in doc['source_receipts']:assert sha(s['path'])==s['sha256']
folders=['arms-original-2017','origami-king-original-2020','engage-original-2023']
dates=[(2017,6,16,'June 16, 2017'),(2020,7,17,'July 17, 2020'),(2023,1,20,'January 20, 2023')]
master=load('content/catalog.json');ids={e['id'] for e in master['entries']};report=[]
for e,folder,(year,month,day,date_text) in zip(doc['entries'],folders,dates):
    assert e['id'] not in ids
    assert e['year']==year and e['date']==dict(month=month,day=day,precision='day',region='Worldwide')
    base='build/research/'+folder+'/'
    source=load(base+'wikipedia-parse.json')['parse'];pid=source['pageid']
    assert e['id']==f'wikipedia-{pid}' and e['attribution']['revision_id']==source['revid']
    rev=load(base+'wikipedia-revision.json')['query']['pages'][str(pid)]['revisions'][0]
    assert rev['revid']==source['revid'] and rev['timestamp']==e['attribution']['revision_timestamp']
    p=Paragraphs();p.feed(source['text']['*'])
    assert date_text in re.sub(r'\s+',' ',' '.join(p.all))
    publisher=(ROOT/(base+'nintendo-original-page.html')).read_text(encoding='utf8')
    assert f'{day:02}/{month:02}/{year}' in publisher
    assert len(e['body'])==len(e['story_headings'])==5 and e['attribution']['license']=='CC BY-SA 4.0'
    texts=[]
    for row in [r for r in doc['source_passages'] if r['entry_id']==e['id']]:
        actual=p.ps[row['parse_p_index']]
        assert actual==row['source_paragraph'] and row['selected_text'] in actual
        assert e['body'][row['story_paragraph']]==row['selected_text']
        assert row['selected_text'].endswith('.')
        texts.append(dict(paragraph=row['story_paragraph'],raw_p_index=row['parse_p_index'],full_paragraph=actual==row['selected_text'],body_sha256=hashlib.sha256(row['selected_text'].encode()).hexdigest()))
    assert len(texts)==5
    allhtml='\n'.join((ROOT/s['path']).read_text(encoding='utf8') for s in doc['source_receipts'] if s['path'].startswith(base) and s['path'].endswith('.html'))
    def published(url):
        if url in allhtml:return True
        if url.startswith('https://assets.nintendo.com/image/upload/ncom/'):
            # The product page publishes the extensionless Cloudinary asset ID
            # with q_auto/f_auto delivery options. Check that exact asset ID.
            return url.split('/image/upload/',1)[1].rsplit('.',1)[0] in allhtml
        if url.startswith('https://www.nintendo.com/jp/switch/ayfna/'):
            return '../'+url.split('/ayfna/',1)[1] in allhtml
        return False
    pixels=set();images=[]
    for n,i in enumerate(e['images']):
        assert sha(i['recovery_local_source'])==i['verification']['source_sha256']
        with Image.open(ROOT/i['recovery_local_source']) as picture:
            picture.load();assert picture.size==(i['width'],i['height'])
            digest=hashlib.sha256(picture.convert('RGB').tobytes()).hexdigest()
        assert digest not in pixels;pixels.add(digest)
        if 1<=n<=5:
            assert i['story_paragraph']==n-1
            assert published(i['url']),(e['title'],n,i['url'])
        if n==6 and folder!='arms-original-2017':assert published(i['url'])
        if n==0 and folder=='origami-king-original-2020':
            assert i['width']==1920 and i['height']==1080
            assert i['url'].split('/image/upload/',1)[1] in allhtml
        assert 'no open image licence' in i['license'] or 'rights' in i['license'].lower()
        images.append(dict(index=n,paragraph=i.get('story_paragraph',-1),path=i['recovery_local_source'],sha256=sha(i['recovery_local_source']),dimensions=[i['width'],i['height']],full_image_individually_viewed=True))
    assert len(images)==7 and e['preferred_image']==0
    v=e['videos'][0];native=load(v['verification']['receipt'])
    assert native['id']==v['youtube_id'] and native['title']==v['title']
    assert native['channel'] in ['Nintendo UK','Nintendo of America']
    assert native['channel_id'] in ['UCGIY_O-8vW4rfX98KlMkvRg','UC8aH9G6LYF3NHP7L3M0dVEQ'] or native['channel']=='Nintendo UK'
    assert native['native_compatible_avc_aac'] and native['avc_format_count']>0 and native['aac_format_count']>0
    assert v['poster_url']==e['images'][-1]['url']
    report.append(dict(entry_id=e['id'],title=e['title'],revision=source['revid'],paragraphs=texts,images=images,video=dict(id=v['youtube_id'],channel=native['channel'],channel_id=native['channel_id'],seconds=native['duration'])))
receipt=dict(status='PASS',candidate_path=PATH,candidate_sha256=EXPECTED,checked_master_sha256=sha('content/catalog.json'),entries=report,source_receipts_verified=len(doc['source_receipts']),observations=['All15 new bodies read in full and reconstructed independently from raw API HTML paragraph indices; selected complete-sentence excerpts are identified rather than falsely called full paragraphs. Three original dates match both infobox and actual Nintendo product HTML.','All21 final images individually opened and21 native image hashes/dimensions checked. Original game identity and all15 paragraph subjects are visually coherent. ARMS control diagram and multiplayer image are950px native assets; no enlargement.','The original two keyart-derived film thumbnails were rejected as visual cover repetition. Final Origami theater/ShyGuy screenshot and Engage Marth screenshot are distinct publisher illustrations accompanying the film, explicitly not extracted video frames.','Origami hero is now the actual original1920x1080 NintendoUS store artwork, whose exact asset identifier occurs in the publisher HTML. It replaces the smaller797x729 delivery without cropping, editing or enlargement. Other covers retain native delivery dimensions or explicitly documented proportional reduction.','Three actual Nintendo public international publications have positiveAVC/AAC metadata. Native language fields are empty; this review establishes title/channel/publication provenance, not decoded-audio review or physicalPS5 playback.','Original publisher rights reserved; WikipediaCCBYSA textual attribution and exact revisions preserved. No prior master records modified.'],master_modified=False)
out='build/research/three-original-switch-articles-high-resolution-independent-review.json'
(ROOT/out).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(out,sha(out))
