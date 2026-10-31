from html.parser import HTMLParser
from pathlib import Path
import re
class N:
 def __init__(self,t,a=None):self.tag=t;self.attrs=dict(a or []);self.children=[]
 def text(self):return ' '.join(c.text() if isinstance(c,N) else c for c in self.children).strip()
 def nodes(self,tag):
  for c in self.children:
   if isinstance(c,N):
    if c.tag==tag:yield c
    yield from c.nodes(tag)
class P(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.root=N('root');self.stack=[self.root]
 def handle_starttag(self,t,a):
  n=N(t,a);self.stack[-1].children.append(n)
  if t not in {'br','img','input','meta','link','hr','wbr','source','area','base','col','embed','param','track'}:self.stack.append(n)
 def handle_endtag(self,t):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==t:self.stack=self.stack[:i];break
 def handle_data(self,d):self.stack[-1].children.append(d)
if __name__=='__main__':
 p=P();p.feed(Path(__file__).with_name('annual-1995.html').read_text(encoding='utf-8'))
 for t in p.root.nodes('table'):
  rows=list(t.nodes('tr'))
  if rows:
   print('HEAD',re.sub(r'\s+',' ',rows[0].text())[:180]);print('ROW',re.sub(r'\s+',' ',rows[1].text())[:180] if len(rows)>1 else '')
