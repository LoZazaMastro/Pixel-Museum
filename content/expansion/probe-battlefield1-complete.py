import json,importlib.util,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('v',R/'tools/discover-museum-videos.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v);B=R/'build/research/soundtrack-broad/battlefield1-complete';folder=B/'codec';folder.mkdir(exist_ok=True)
for f in sorted((B/'tracks').glob('*.json')):
 row=json.loads(f.read_text())
 for t in row.get('candidates',[]):
  vid=t['youtube_id'];out=folder/(vid+'.json')
  if out.exists():continue
  try:
   m=v.metadata(vid,{'title':t['actual_title'],'channel':t['actual_uploader']});r={'youtube_id':vid,'status':'PASS','native_compatible_avc_aac':True,'native_codec_metadata_receipt':'build/research/video-discovery/video-'+vid+'.json','scope':'Public native resolver AVC/AAC formats; no listening or PS5 playback claim.'}
  except Exception as ex:r={'youtube_id':vid,'status':'HOLD','error':str(ex)}
  out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(row['expansion'],row['title'],r['status'],flush=True)
