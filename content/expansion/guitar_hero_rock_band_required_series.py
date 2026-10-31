"""Append reviewed original music-game owners without altering existing rows."""
from pathlib import Path
import json,copy,hashlib
def apply(entries,root):
 p=json.loads((Path(root)/'content/expansion/guitar-hero-rock-band-required-series.json').read_text(encoding='utf-8'))
 exclusions=json.loads((Path(root)/'content/expansion/user-selected-game-exclusions.json').read_text(encoding='utf-8'))
 excluded={row['id']for row in exclusions['rows']}
 index={e['id']:e for e in entries};added=[];skipped=[]
 for row in p['entries']:
  digest=hashlib.sha256(json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  if digest!=p['source_fingerprints'][row['id']]:raise ValueError('Reviewed music-game source changed: '+row['id'])
  if row['id']in excluded:
   skipped.append(row['id']);continue
  if row['id']in index:
   if index[row['id']]!=row:raise ValueError('Reviewed music-game owner collision: '+row['id'])
   continue
  entries.append(copy.deepcopy(row));index[row['id']]=row;added.append(row['id'])
 return {'status':'PASS_REVIEWED_GUITAR_HERO_ROCK_BAND_SERIES_APPEND_ONLY','added':added,'skipped_user_exclusions':skipped}
