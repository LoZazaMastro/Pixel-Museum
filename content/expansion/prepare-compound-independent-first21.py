import json,copy,importlib.util,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];B=R/'build/research/soundtrack-broad';sp=importlib.util.spec_from_file_location('v',R/'tools/discover-museum-videos.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
original=json.loads((B/'checkpoints/compound-role-replay101-2026-10-21.json').read_text());source={e['entry_id']:e for e in original['entries']};review=json.loads((B/'independent-compound-replay0-29-review.json').read_text());doc=json.loads((R/'content/expansion/soundtrack-independent-approved.json').read_text());by={e['entry_id']:e for e in doc['entries']};audit=[]
for row in review['entries']:
 e=copy.deepcopy(source[row['entry_id']]);tracks={t['youtube_id']:t for t in e['tracks']};new=[]
 for q in row['tracks']:
  if q['status']!='PASS':continue
  t=tracks[q['youtube_id']];t.update(q.get('corrected_track_fields',{}));t['independent_review_receipt']='build/research/soundtrack-broad/independent-compound-replay0-29-review.json';t['independent_track_field_corrections']=q.get('corrected_track_fields',{})
  try:
   m=v.metadata(t['youtube_id'],{'title':t['title'],'channel':t['uploader']});assert m.get('native_compatible_avc_aac')
   t.update(native_codec_metadata_verified=True,native_codec_metadata_receipt='build/research/video-discovery/video-'+t['youtube_id']+'.json',playback_verified_on_ps5=False);new.append(t);audit.append({'entry_id':e['entry_id'],'youtube_id':t['youtube_id'],'status':'PASS'});print(e['match_title'],t['youtube_id'],'PASS',flush=True)
  except Exception as ex:audit.append({'entry_id':e['entry_id'],'youtube_id':t['youtube_id'],'status':'CODEC_HOLD','reason':str(ex)});print(e['match_title'],t['youtube_id'],'CODEC_HOLD',flush=True)
 if not new:continue
 if e['entry_id'] in by:out=by[e['entry_id']];out['tracks'] += [t for t in new if t['youtube_id'] not in {x['youtube_id'] for x in out['tracks']}]
 else:e['tracks']=new;doc['entries'].append(e);by[e['entry_id']]=e
 out=by[e['entry_id']];out['composer']=', '.join(dict.fromkeys(t['creator'] for t in out['tracks']));out['curator_note']='Listen to music by '+out['composer']+' from '+out['match_title']+'.'
 (B/'compound-independent-first21-codec-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
n=len(doc['entries']);c=sum(len(e['tracks']) for e in doc['entries']);doc['publication_status']='awaiting_incremental_reconciliation';f=B/f'checkpoints/incremental-{n}-{c}-replay-first21-2026-10-21.json';f.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('FINAL',n,c,str(f),hashlib.sha256(f.read_bytes()).hexdigest(),flush=True)
