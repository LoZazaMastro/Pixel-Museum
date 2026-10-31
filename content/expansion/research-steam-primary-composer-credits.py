"""Discover missing composer credits from actual publisher Steam music pages.
Only explicit Composer fields; Artist/Developer/Producer are never substituted.
A soundtrack's exact parent game must resolve too. Research only until reviewed.
"""
import json,importlib.util,re,concurrent.futures,html,hashlib
from pathlib import Path
from urllib.parse import quote
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
cat=json.loads((R/'content/catalog.json').read_text());cat=cat if isinstance(cat,list) else cat['entries'];games={e['id']:e for e in cat if e.get('kind')=='game'};bytitle={}
for e in games.values():bytitle.setdefault(p.album_core(e['title']),set()).add(e['year'])
folder=p.RESEARCH/'steam-credits';folder.mkdir(exist_ok=True)
def core(name):
 name=re.sub(r'\b(?:original|official|game|complete|music|sound\s*track|OST)\b',' ',name,flags=re.I)
 return p.album_core(name)
def get(url,kind):
 path=folder/(hashlib.sha256(url.encode()).hexdigest()[:20]+'.'+kind)
 if path.exists():return path.read_text(encoding='utf8'),path
 value=p.fetch(url);path.write_text(value,encoding='utf8');return value,path

def process(e):
 receipt=folder/(e['id']+'.json')
 if receipt.exists():return json.loads(receipt.read_text())
 out={'entry_id':e['id'],'title':e['title'],'year':e['year'],'status':'research_pending','candidates':[]}
 try:
  raw,searchreceipt=get('https://store.steampowered.com/search/suggest?term='+quote(e['title']+' soundtrack')+'&f=games&cc=us&l=english','html')
  ids=list(dict.fromkeys(re.findall('data-ds-appid="(\d+)"',raw)))
  for appid in ids[:4]:
   raw,appreceipt=get('https://store.steampowered.com/api/appdetails?appids='+appid+'&l=english','json');api=json.loads(raw).get(appid,{}).get('data',{})
   if not api or core(api.get('name',''))!=p.album_core(e['title']):continue
   if not api.get('fullgame',{}).get('appid'):continue
   pid=str(api['fullgame']['appid']);raw,parentreceipt=get('https://store.steampowered.com/api/appdetails?appids='+pid+'&l=english','json');parent=json.loads(raw).get(pid,{}).get('data',{})
   if p.album_core(parent.get('name',''))!=p.album_core(e['title']):continue
   if len(bytitle.get(p.album_core(e['title']),[]))>1:
    out['candidates'].append({'appid':appid,'reason':'Same-title remake/original ambiguity; requires manual parent-edition identification.'});continue
   raw,htmlreceipt=get('https://store.steampowered.com/app/'+appid+'/?l=english','html');credits={}
   for row in re.findall(r'<tr class="album_metadata_row">(.*?)</tr>',raw,re.S):
    cells=re.findall(r'<td[^>]*>(.*?)</td>',row,re.S)
    if len(cells)==2:credits[p.text(cells[0]).rstrip(':')]=p.text(cells[1])
   if not credits.get('Composer'):
    out['candidates'].append({'appid':appid,'name':api['name'],'credits':credits,'reason':'No explicit Composer field; no artist/developer fallback.'});continue
   out.update(status='primary_composer_candidate',source_page='https://store.steampowered.com/app/'+appid,album_name=api['name'],parent_game={'appid':pid,'title':parent['name'],'release_date':parent.get('release_date')},credits=credits,source_receipt=htmlreceipt.relative_to(R).as_posix(),source_receipt_sha256=hashlib.sha256(htmlreceipt.read_bytes()).hexdigest(),parent_receipt=parentreceipt.relative_to(R).as_posix());break
 except Exception as ex:out['error']=str(ex)
 if out['status']=='research_pending':out['status']='research_hold'
 p.write(receipt,out);return out
rows=[]
for f in (p.RESEARCH/'games').glob('*.json'):
 d=json.loads(f.read_text());e=games.get(d['entry_id'])
 if not e or d.get('state')!='composer_research_required' or e['year']<1980:continue
 if p.cached_exact_composer(e):continue
 rows.append(e)
rows.sort(key=lambda x:-x['year']);results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for row in pool.map(process,rows):
  results.append(row);print(row['status'],row['title'],row.get('credits',{}).get('Composer',''),flush=True)
  p.write(p.RESEARCH/'steam-primary-composer-candidates.json',{'publication_status':'research_only','scope':'ExactSteamOST parentgame identity and explicitComposer field; candidates require editorial role/edition review, do not auto-admit music.','entries':results})
print('FINAL',len(results),'checked',sum(e['status']=='primary_composer_candidate' for e in results),'primary composer candidates',flush=True)
