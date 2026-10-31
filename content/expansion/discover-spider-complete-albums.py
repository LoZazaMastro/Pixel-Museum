"""Resume metadata-only exact original album track discovery, retaining all holds."""
import concurrent.futures,importlib.util,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'build/research/soundtrack-broad/spider-complete'
s=importlib.util.spec_from_file_location('p',ROOT/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
albums=json.loads((OUT/'original-three-albums-inventory.json').read_text())['albums']
def norm(t):return re.sub('[^a-z0-9]','',t.lower())
def cue(t):
 t=re.sub(r'^(?:John Paesano|Jaden|Lecrae|EARTHGANG(?:, Benji\.)?)\s*[-–—]\s*','',t,flags=re.I)
 t=re.split(r'\s*\(?From\s+["“]',t,flags=re.I)[0].strip()
 t=re.sub(r'\s*\((?:Official (?:Video|Audio)|Audio Only)\)\s*$','',t,flags=re.I)
 return norm(t)
targets=[{**track,'entry_id':a['entry_id'],'game_title':a['title'],'year':a['year'],'composer_source':a['url']}for a in albums for track in a['tracks']]
def find(r):
 checkpoint=OUT/(str(r['year'])+'-'+str(r['album_number'])+'-discovery.json')
 if checkpoint.exists():return json.loads(checkpoint.read_text())
 query='"'+r['item_name']+'" "'+r['game_title']+'" soundtrack'
 try:
  results=p.search(query)
  for hit in results:
   if cue(hit.get('title',''))!=cue(r['item_name']):continue
   w=p.watch(hit['id']);text=w['shortDescription'];head=text[:900]
   # Label-delivered exact album and rights owner, not a generic title/channel match.
   if 'Provided to YouTube by'not in head or not any(x in head for x in ['Marvel Music','Hollywood Records','UMG','Universal']):continue
   if norm(r['game_title'])not in norm(text):continue
   if 'Original Video Game Soundtrack' not in text and 'Score'not in text and 'Marvel Music'not in text:continue
   length=[int(x)for x in r['duration'].split(':')];seconds=sum(x*60**i for i,x in enumerate(reversed(length)))
   if abs(float(w['lengthSeconds'])-seconds)>6:continue
   out={**r,'candidate_id':hit['id'],'publication':w,'status':'publication_identity_verified'};p.write(checkpoint,out);return out
  out={**r,'status':'unresolved','query':query,'search_candidates':[{'id':h['id'],'title':h.get('title'),'channel':h.get('channel')}for h in results]}
 except Exception as exc:out={**r,'status':'unresolved','error':str(exc)}
 p.write(checkpoint,out);return out
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
 for r in pool.map(find,targets):
  rows.append(r);p.write(OUT/'three-albums-discovery.json',{'records':rows,'expected_tracks':len(targets)});print(r['year'],r['album_number'],r['item_name'],r['status'],r.get('candidate_id',''),flush=True)
