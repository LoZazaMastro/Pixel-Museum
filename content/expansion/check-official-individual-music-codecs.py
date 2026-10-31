import json,importlib.util,concurrent.futures,hashlib,copy
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('v',R/'tools/discover-museum-videos.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
r=R/'build/research/soundtrack-broad';source=json.loads((r/'official-individual-direct-credits-candidates.json').read_text());approved={e['entry_id'] for e in json.loads((R/'content/expansion/soundtrack-independent-approved.json').read_text())['entries']};rows=[e for e in source['entries'] if e['entry_id'] not in approved]
def process(e):
 e=copy.deepcopy(e);out=[];held=[]
 for t in e['tracks']:
  vid=t['youtube_id']
  try:receipt=v.metadata(vid,{'title':t['title'],'channel':t['uploader']})
  except Exception as ex:
   held.append({'youtube_id':vid,'reason':str(ex)});continue
  if receipt.get('native_compatible_avc_aac'):
   t.update(native_codec_metadata_verified=True,native_codec_metadata_receipt='build/research/video-discovery/video-'+vid+'.json',playback_verified_on_ps5=False);out.append(t)
  else:held.append({'youtube_id':vid,'reason':'NativeAVC/AAC metadata did not resolve; not retried repeatedly.'})
 e['tracks']=out;e['codec_holds']=held;return e
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for e in pool.map(process,rows):
  results.append(e);print(e['match_title'],len(e['tracks']),'codec candidates',flush=True)
  (r/'official-individual-direct-credits-codec-live.json').write_text(json.dumps({'publication_status':'awaiting_independent_review','entries':results},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
out=r/'checkpoints/official-individual-direct-credits-codec-2026-10-21.json';out.write_text(json.dumps({'publication_status':'awaiting_independent_review','scope':'Exact official individual cues with all delivered named artists independently matched. Actual nativeAVC/AAC metadata passed; no listening or console playback claim. Separate independent identity/credit review still required.','entries':[e for e in results if e['tracks']]},ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('FINAL',len([e for e in results if e['tracks']]),sum(len(e['tracks']) for e in results),hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
