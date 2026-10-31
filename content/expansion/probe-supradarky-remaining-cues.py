import importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('v',R/'tools/discover-museum-videos.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v);B=R/'build/research/soundtrack-broad';source=B/'supradarky-remaining73-reviewed-candidates.json';doc=json.loads(source.read_text());holds=[]
for e in doc['entries']:
 kept=[]
 for t in e['tracks']:
  try:
   m=v.metadata(t['youtube_id'],{'title':t['title'],'channel':t['uploader']});t['native_codec_metadata_verified']=True;t['native_codec_metadata_receipt']='build/research/video-discovery/video-'+t['youtube_id']+'.json';kept.append(t);print(e['match_title'],t['youtube_id'],'PASS',flush=True)
  except Exception as ex:holds.append({'entry_id':e['entry_id'],'youtube_id':t['youtube_id'],'error':str(ex)});print(e['match_title'],t['youtube_id'],'HOLD',str(ex),flush=True)
 e['tracks']=kept
 out={**doc,'entries':[e for e in doc['entries'] if e['tracks']],'codec_holds':holds};p=B/'supradarky-remaining73-codec-candidates.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
print('FINAL',len(out['entries']),sum(len(e['tracks']) for e in out['entries']),len(holds),flush=True)
