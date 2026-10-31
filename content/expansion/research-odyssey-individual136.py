"""Read each actual136-cue archival publication, without manufacturing descriptions."""
import concurrent.futures,hashlib,importlib.util,json,pathlib,re,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'build/research/soundtrack-broad/nintendo-full'
s=importlib.util.spec_from_file_location('p',ROOT/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
v_spec=importlib.util.spec_from_file_location('v',ROOT/'tools/discover-museum-videos.py');v=importlib.util.module_from_spec(v_spec);v_spec.loader.exec_module(v)
playlist=json.loads((OUT/'odyssey-alltracks-video-game-stuff-public-flat-playlist.json').read_text())
inventory=json.loads((OUT/'odyssey-nintendo-music-inventory.json').read_text())['media'][0]['tracks']
assert len(playlist['entries'])==len(inventory)==136
def norm(t):return re.sub('[^a-z0-9]','',t.lower())
def read(pair):
 expected,source=pair;id=source['id'];path=OUT/'odyssey-individuals'/(id+'.json')
 if path.exists():return json.loads(path.read_text())
 title=re.sub(r'^\d+\s*-\s*','',source['title']);title=re.sub(r'\s*-\s*Super Mario Odyssey OST$','',title)
 assert norm(expected['title'])==norm(title),(expected['title'],title)
 assert abs(source['duration']-expected['length']/1000)<=4
 try:
  cached=ROOT/f'build/research/soundtrack-broad/watch/{id}.json'
  if cached.exists():watch=json.loads(cached.read_text())
  else:
   result=subprocess.run([str(p.YTDLP),'--skip-download','--dump-single-json','--no-warnings','--ignore-no-formats-error','--no-check-formats','--socket-timeout','12','--retries','1','--extractor-args','youtube:player_skip=webpage,configs;player_client=android','https://www.youtube.com/watch?v='+id],capture_output=True,text=True,encoding='utf-8',timeout=45)
   raw=json.loads(result.stdout)
   watch={'title':raw.get('title'),'author':raw.get('channel'),'channelId':raw.get('channel_id'),'shortDescription':raw.get('description')or'','lengthSeconds':str(raw.get('duration')or 0),'metadata_source':'Actual public Android player metadata; absent descriptions remain empty.'}
   assert watch['title']and watch['channelId'];p.write(cached,watch)
  assert watch['channelId']=='UCiXcXwMP9Saz4yrB7EX87Sg'
  assert norm(watch['title'])==norm(source['title'])
  native=v.metadata(id,{'title':watch['title'],'channel':watch['author']})
  row={'album_track_number':expected['position'],'title':expected['title'],'candidate_id':id,'source':source,'publication':watch,'expected_duration_seconds':expected['length']/1000,'native_codec_receipt':f'build/research/video-discovery/video-{id}.json','native_compatible_avc_aac':native['native_compatible_avc_aac'],'status':'candidate_metadata_verified','description_was_available':bool(watch['shortDescription'])}
 except Exception as exc:row={'album_track_number':expected['position'],'title':expected['title'],'candidate_id':id,'status':'hold','error':str(exc)}
 p.write(path,row);return row
(OUT/'odyssey-individuals').mkdir(exist_ok=True)
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
 for row in pool.map(read,zip(inventory,playlist['entries'])):
  rows.append(row);p.write(OUT/'odyssey136-individual-publication-research.json',{'expected':136,'tracks':rows});print(row['album_track_number'],row['title'],row['status'],flush=True)
