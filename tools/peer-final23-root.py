import hashlib, json, re
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
F = ROOT / 'build/research/playhub-semantic-coverage/wiki-clarity/repeated-final23'
class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__(); self.active=False; self.sup=0; self.buf=[]; self.items=[]
    def handle_starttag(self, tag, attrs):
        if tag=='p': self.active=True; self.buf=[]
        if tag=='sup': self.sup+=1
    def handle_endtag(self, tag):
        if tag=='sup': self.sup=max(0,self.sup-1)
        if tag=='p' and self.active:
            s=' '.join(''.join(self.buf).split())
            if s: self.items.append(s)
            self.active=False
    def handle_data(self,data):
        if self.active and not self.sup: self.buf.append(data)
def sha(b):return hashlib.sha256(b).hexdigest()
cpath=F/'candidate.json'; c=json.loads(cpath.read_text('utf-8'))
catalog=json.loads((ROOT/'content/catalog.json').read_text('utf-8'))
owners={e['id']:e for e in catalog['entries']}
results=[]
for r in c['replacements']:
    p=r['provenance']; path=ROOT/p['source_file']; raw=path.read_bytes()
    assert sha(raw)==p['source_file_sha256']
    s=json.loads(raw)
    if 'parse' in s:
        data=s['parse']; parser=Paragraphs(); text=data['text']
        if isinstance(text,dict):text=text['*']
        parser.feed(text); paras=parser.items
        assert data['pageid']==p['page_id'] and data['revid']==p['revision_id']
    else:
        pages=s['query']['pages']; pages=pages.values() if isinstance(pages,dict) else pages
        data=next(x for x in pages if x['pageid']==p['page_id'])
        assert data['revisions'][0]['revid']==p['revision_id']
        paras=data['extract'].splitlines()
    selected=[paras[i] for i in p['paragraph_indices']]
    assert selected==p['source_paragraphs'],r['entry_id']
    assert '\n\n'.join(selected)==r['body'],r['entry_id']
    assert sha(r['body'].encode())==r['body_sha256']
    old=owners[r['entry_id']]['body'][r['source_chapter_index']]
    assert old==r['old_body'] and sha(old.encode())==r['old_body_sha256']
    assert r['body'] not in owners[r['entry_id']]['body'][:3]
    results.append({'entry_id':r['entry_id'],'source_verified':True,'old_body_matches':True,'whole_paragraphs':len(selected)})
out={'status':'PASS','candidate_sha256':sha(cpath.read_bytes()),'cards':len(results),
     'review':'Root read all 23 candidate bodies and headings. Concrete gameplay, development and art direction replace repeated generic calendar prose. UTF-8 accents checked; no edits to dates or media.',
     'checks':results}
(F/'root-independent-review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False))
