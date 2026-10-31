"""Acquire both exact DS2 artist albums, keeping title-level resumable metadata."""
import concurrent.futures,hashlib,html,importlib.util,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'build/research/death-stranding2-complete-score'
(OUT/'discovery').mkdir(exist_ok=True)
sp=importlib.util.spec_from_file_location('p',ROOT/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(sp);sp.loader.exec_module(p)
rooms=[{'id':'woodkid','title':'Woodkid','composer':'Woodkid','files':['woodkid.html'],'source':'https://www.qobuz.com/fr-fr/album/woodkid-for-death-stranding-2-on-the-beach-woodkid/oilotusifva7b','expected':16},{'id':'forssell','title':'Ludvig Forssell','composer':'Ludvig Forssell','files':['forssell.html','forssell-public-pagination-last4.html'],'source':'https://www.qobuz.com/us-en/album/death-stranding-2-on-the-beach-original-video-game-score-ludvig-forssell/hx3knoh4y4dmb','expected':56}]
targets=[]
for room in rooms:
 room['tracks']=[]
 for file in room['files']:
  raw=(OUT/file).read_text(encoding='utf-8')
  for b in raw.split('<div class="player__item">')[1:]:
   m=re.search(r'data-track-v2="(.*?)"',b,re.S)
   if not m:continue
   row=json.loads(html.unescape(m[1]));dur=re.search(r'track__item--duration">(.*?)<',b)
   row.update(room_id=room['id'],room_artist=room['composer'],album_number=len(room['tracks'])+1,source=room['source'],duration=dur[1],credits=[html.unescape(x)for x in re.findall(r'<p class="track__info">(.*?)</p>',b,re.S)])
   room['tracks'].append(row);targets.append(row)
 assert len(room['tracks'])==room['expected']
p.write(OUT/'both-rooms-complete72-inventory.json',{'rooms':rooms})
def norm(t):return re.sub('[^a-z0-9]','',t.lower())
def exact_publication_title(row,watch):
 expected=norm(row['item_name'])
 title=re.sub(r'^(?:Woodkid(?:[^-–—]*?)|Ludvig Forssell)\s*[-–—]\s*','',watch['title'],flags=re.I)
 title=re.split(r'\s*(?:\(|\|)\s*(?:from|DEATH STRANDING)',title,flags=re.I)[0]
 title=re.sub(r'\s*\((?:Official (?:Video|Audio)|Lyric Video)\)\s*$','',title,flags=re.I)
 if norm(title)==expected:return True
 first=watch['shortDescription'].splitlines()[0]
 quoted=re.match(r'^["“](.+?)["”]\s+from\b',first,flags=re.I)
 return bool(quoted and norm(quoted[1])==expected)
def find(row):
 dest=OUT/'discovery'/(row['room_id']+'-'+str(row['album_number'])+'.json')
 if dest.exists():
  previous=json.loads(dest.read_text())
  if previous.get('state')=='source_publication_read'and exact_publication_title(row,previous['publication']):return previous
 q='"'+row['item_name']+'" "'+row['room_artist']+'" "Death Stranding 2"'
 try:
  hits=p.search(q)
  for hit in hits:
   if norm(row['item_name'])not in norm(hit.get('title','')):continue
   w=p.watch(hit['id']);head=w['shortDescription'][:1800]
   if not exact_publication_title(row,w):continue
   if not('Provided to YouTube by'in head and any(x in head for x in ['Milan','Sony','Universal','UMG']))and w['channelId']not in ['UCGkX_HCD_T5XOwxi_KR6YoQ']:continue
   if 'Death Stranding 2'not in head and 'DEATH STRANDING 2'not in head:continue
   parts=[int(x)for x in row['duration'].split(':')];secs=sum(x*60**i for i,x in enumerate(reversed(parts)))
   if abs(float(w['lengthSeconds'])-secs)>6:continue
   out={**row,'candidate_id':hit['id'],'publication':w,'state':'source_publication_read'};p.write(dest,out);return out
  out={**row,'state':'unresolved','query':q,'hits':[{'id':h['id'],'title':h.get('title'),'channel':h.get('channel')}for h in hits]}
 except Exception as exc:out={**row,'state':'unresolved','error':str(exc)}
 p.write(dest,out);return out
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=1)as executor:
 for row in executor.map(find,targets):
  results.append(row);p.write(OUT/'both-rooms-complete72-discovery.json',{'records':results,'expected':72});print(row['room_id'],row['album_number'],row['item_name'],row['state'],row.get('candidate_id',''),flush=True)
