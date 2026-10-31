"""Resolve game-specific composer credits when a base title names a franchise.
Only exact existing game articles with compatible release-year descriptions enter
this source override; missing music credits remain research holds.
"""
import concurrent.futures,html,importlib.util,json,re,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CACHE=ROOT/'build/research/soundtrack-broad/composer-recovery';CACHE.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('broad',Path(__file__).with_name('soundtrack-broad-pipeline.py'));broad=importlib.util.module_from_spec(spec);spec.loader.exec_module(broad)
def api(site,params):
 url=site+'?'+urllib.parse.urlencode({'format':'json','formatversion':2,**params})
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'PixelMuseumEditorial/1.0'}),timeout=25) as r:return json.load(r)
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
c=json.loads((ROOT/'content/catalog.json').read_text());entries=c if isinstance(c,list) else c['entries'];by={e['id']:e for e in entries};pending=[]
for p in (ROOT/'build/research/soundtrack-broad/games').glob('*.json'):
 d=json.loads(p.read_text())
 if d.get('state')=='composer_research_required' and d['entry_id'] in by:pending.append(by[d['entry_id']])
titles={}
for e in pending:
 title=e['title'];variants=list(dict.fromkeys([title,title.title()]));titles[e['id']]=[f'{t} ({e["year"]} video game)' for t in variants]+[t+' (video game)' for t in variants]+variants
alltitles=list(dict.fromkeys(t for ts in titles.values() for t in ts));pages={};redirects={}
def mergeprops(d):
 for p in d.get('query',{}).get('pages',[]):pages[p['title']]=p
 for k in ['normalized','redirects']:
  for r in d.get('query',{}).get(k,[]):redirects[r['from']]=r['to']
for cachefile in CACHE.glob('pageprops-*.json'):mergeprops(json.loads(cachefile.read_text()))
unknown=[t for t in alltitles if t not in pages and t not in redirects]
for n in range(0,len(unknown),40):
 try:
  d=api('https://en.wikipedia.org/w/api.php',{'action':'query','prop':'pageprops','titles':'|'.join(unknown[n:n+40]),'redirects':1});write(CACHE/f'pageprops-extra-{n}.json',d);mergeprops(d)
 except Exception as error:print('Cached page identities retained; API unavailable:',error,flush=True);break
def resolve(t):
 for _ in range(5):
  if t not in redirects:break
  t=redirects[t]
 return pages.get(t)
def recover(e):
 for title in titles[e['id']]:
  p=resolve(title)
  if not p or 'missing' in p:continue
  description=p.get('pageprops',{}).get('wikibase-shortdesc','');year=re.search(r'\b((?:19|20)\d{2})\b',description)
  if year and abs(int(year.group(1))-e['year'])>1:continue
  if re.search(r'^(?:video )?game series|^series |franchise|^genre |^character |^company |\bfilm\b',description,re.I):continue
  url='https://en.wikipedia.org/wiki/'+urllib.parse.quote(p['title'].replace(' ','_'))
  candidate=dict(e);candidate['sources']=[{'url':url}]
  names,source,evidence=broad.composer(candidate)
  if names:return e['id'],{'composers':names,'source_page':source,'evidence':evidence,'verification':'Actual game-specific article composer infobox; compatible game identity/year.','checked':'2026-10-21'}
  q=p.get('pageprops',{}).get('wikibase_item')
  if not q:continue
  try:
   d=api('https://www.wikidata.org/w/api.php',{'action':'wbgetentities','ids':q,'props':'claims'});write(CACHE/(q+'.json'),d)
   claims=d.get('entities',{}).get(q,{}).get('claims',{}).get('P86',[]);ids=[x.get('mainsnak',{}).get('datavalue',{}).get('value',{}).get('id') for x in claims];ids=[id for id in ids if id]
   if not ids:continue
   labels=api('https://www.wikidata.org/w/api.php',{'action':'wbgetentities','ids':'|'.join(ids),'props':'labels','languages':'en'});write(CACHE/(q+'-composer-labels.json'),labels);names=[labels['entities'][id].get('labels',{}).get('en',{}).get('value','') for id in ids];names=[n for n in names if n]
   if names:return e['id'],{'composers':names,'source_page':'https://www.wikidata.org/wiki/'+q,'evidence':'Composer property P86 on exact game entity, linked from '+url,'verification':'Structured composer credit on exact original game entity, independently matched to YouTube publishing credits later.','checked':'2026-10-21'}
  except Exception:pass
 return e['id'],None
outpath=ROOT/'content/expansion/soundtrack-composer-source-overrides.json';out=json.loads(outpath.read_text()) if outpath.exists() else {'schema_version':1,'entries':{}}
for id,recovery in concurrent.futures.ThreadPoolExecutor(max_workers=6).map(recover,pending):
 if recovery:out['entries'][id]=recovery;print('RECOVERED',id,', '.join(recovery['composers']),flush=True)
write(outpath,out);print('OVERRIDES',len(out['entries']),'from',len(pending),'pending games',flush=True)
