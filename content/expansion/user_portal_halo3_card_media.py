"""Two explicitly requested final media mappings; never replace owner prose/audio."""
from pathlib import Path
import copy,json,hashlib

def apply(entries,root):
 root=Path(root);policy=json.loads((root/'content/expansion/user-portal-halo3-card-media.json').read_text(encoding='utf8'))
 changed=[]
 for row in policy['entries']:
  matches=[e for e in entries if e['id']==row['id']]
  if len(matches)!=1:raise ValueError('User media override requires exact owner: '+row['id'])
  owner=matches[0];before=copy.deepcopy(owner)
  for file,digest in row['source_files'].items():
   if hashlib.sha256((root/file).read_bytes()).hexdigest()!=digest:raise ValueError('Reviewed media source changed: '+file)
  current={k:copy.deepcopy(owner.get(k))for k in row['after']}
  if current==row['after']:continue
  if current!=row['before']:raise ValueError('User media override preimage changed: '+row['id'])
  for key,value in row['after'].items():owner[key]=copy.deepcopy(value)
  inverse=copy.deepcopy(owner)
  for key in row['after']:
   if key in before:inverse[key]=before[key]
   else:inverse.pop(key,None)
  if inverse!=before:raise ValueError('User media override exceeded bounded fields')
  changed.append(row['id'])
 return {'status':'PASS_USER_PORTAL_OPENING_VIDEO_AND_HALO3_GAMEPLAY_IMAGES','changed':changed,'prose_audio_dates_preserved':True}
