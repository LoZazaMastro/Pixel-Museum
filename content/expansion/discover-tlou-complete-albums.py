"""Resume exact-track public metadata discovery for both original Sony albums."""
import concurrent.futures,html,importlib.util,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'build/research/last-of-us-score-review'
spec=importlib.util.spec_from_file_location('p',ROOT/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
existing=json.loads((ROOT/'content/expansion/soundtrack-multitrack-priority-overrides.json').read_text())
def norm(s):return re.sub('[^a-z0-9]','',s.lower())
def cue_title(s):
 s=re.sub(r'^(?:Gustavo Santaolalla(?:, Mac Quayle)?|Mac Quayle)\s*[-–—]\s*','',s,flags=re.I)
 s=s.split('|',1)[0]
 s=re.sub(r'\s*\(?from\s+[\"“].*$', '',s,flags=re.I)
 s=re.sub(r'\s*\(Official (?:Video|Audio)\)\s*$','',s,flags=re.I)
 return norm(s)
targets=[]
for part in range(2):
 raw=(OUT/('part1-qobuz-actual.html' if part==0 else 'part2-qobuz-actual.html')).read_text(encoding='utf-8')
 for block in raw.split('<div class="player__item">')[1:]:
  m=re.search(r'data-track-v2="(.*?)"',block,re.S)
  if not m:continue
  row=json.loads(html.unescape(m.group(1)));dur=re.search(r'track__item--duration">(.*?)<',block)
  row.update({'part':part,'credits':[html.unescape(x) for x in re.findall(r'<p class="track__info">(.*?)</p>',block,re.S)],'duration':dur.group(1),'album_number':sum(t['part']==part for t in targets)+1})
  targets.append(row)
def discover(row):
 title=row['item_name'];part=row['part'];expected=existing['entries'][part]
 old=next((t for t in expected['tracks'] if norm(t['title'].replace(' (Main Theme)',''))==norm(title)),None)
 if old:return {**row,'candidate':old,'state':'reviewed_individual'}
 query='"'+title+'" "'+('The Last of Us Part II (Original Soundtrack)' if part else 'The Last of Us (Video Game Soundtrack)')+'" SonySoundtracksVEVO'
 try:
  results=p.search(query)
  for r in results:
   if norm('SonySoundtracksVEVO') not in norm((r.get('channel') or '')+' '+(r.get('uploader') or '')):continue
   if cue_title(r.get('title',''))!=norm(title):continue
   w=p.watch(r['id'])
   if w['channelId']!='UCGkX_HCD_T5XOwxi_KR6YoQ':continue
   if cue_title(w['title'])!=norm(title):continue
   expected_album='The Last of Us Part II (Original Soundtrack)' if part else 'The Last of Us (Video Game Soundtrack)'
   if norm(expected_album) not in norm(w['title']+' '+w['shortDescription'][:350]):continue
   return {**row,'candidate_id':r['id'],'publication':w,'state':'actual_sony_publication_read'}
  return {**row,'state':'unresolved','search':query,'results':[{'id':r['id'],'title':r.get('title'),'channel':r.get('channel')} for r in results]}
 except Exception as exc:return {**row,'state':'unresolved','error':str(exc)}
records=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
 for d in executor.map(discover,targets):
  records.append(d);p.write(OUT/'complete58-individual-discovery.json',{'rooms':2,'expected_tracks':58,'records':records});print(d['part'],d['album_number'],d['item_name'],d['state'],d.get('candidate_id',''),flush=True)
assert len(records)==58,(len(records),'Label album tables must be30+28')
