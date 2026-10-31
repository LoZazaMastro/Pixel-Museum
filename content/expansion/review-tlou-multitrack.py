"""Bounded metadata-only peer research for the two original game albums."""
import concurrent.futures, hashlib, importlib.util, json, pathlib, urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'build/research/last-of-us-score-review'
spec=importlib.util.spec_from_file_location('soundtrack_research',ROOT/'content/expansion/soundtrack-broad-pipeline.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
candidate=json.loads((OUT/'two-games18-candidate.json').read_text())
sources={
 'part2-qobuz':'https://www.qobuz.com/us-en/album/the-last-of-us-part-ii-original-soundtrack-gustavo-santaolalla-mac-quayle/glm0nel3uk1wb',
 'part1-apple':'https://classical.music.apple.com/us/album/655118434',
}
receipts=[]
for name,url in sources.items():
 try:
  raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read()
  text=p.text(raw.decode('utf-8'))
  assert ('Gustavo' in text and ('Sony' in text or 'Santaolalla' in text)) and len(text)>4000
  dest=OUT/(name+'-actual.html');dest.write_bytes(raw)
  (OUT/(name+'-actual.txt')).write_text(text,encoding='utf-8')
  receipts.append({'url':url,'path':str(dest.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(raw).hexdigest(),'actual_body_retrieved':True})
 except Exception as exc:receipts.append({'url':url,'actual_body_retrieved':False,'error':str(exc)})
p.write(OUT/'independent-primary-source-receipts.json',receipts)
def read(track):
 try:
  d=p.watch(track['youtube_id']);return {'id':track['youtube_id'],'ok':True,'title':d['title'],'author':d['author'],'channel':d['channelId'],'description':d['shortDescription'],'seconds':d['lengthSeconds']}
 except Exception as exc:return {'id':track['youtube_id'],'ok':False,'error':str(exc)}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
 results=list(executor.map(read,[t for e in candidate['entries'] for t in e['tracks']]))
p.write(OUT/'independent-actual-publications18.json',results)
for r in results:print(json.dumps(r,ensure_ascii=False))
