"""Add only five reviewed original-game films after source and music layers."""
import copy,json,hashlib
from pathlib import Path
def apply(entries,root):
 root=Path(root).resolve()
 def digest(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')).hexdigest()
 def pinned(relative,expected):
  p=(root/relative).resolve()
  if not p.is_relative_to(root):raise ValueError('Film path outside project')
  raw=p.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Reviewed film input changed')
  return json.loads(raw)
 policy=json.loads((root/'content/expansion/museum-reviewed-five-2010-films-policy.json').read_bytes())
 if policy.get('publication_status')!='independently_reviewed':raise ValueError('Unreviewed film policy')
 candidate=pinned(policy['candidate_path'],policy['candidate_sha256']);peer=pinned(policy['peer_path'],policy['peer_sha256'])
 if peer.get('status')!='ROOT_FIVE_FILMS_AND_LOCAL_POSTERS_PEER_PASS_PRIVATE_ONLY'or peer.get('candidate_sha256')!=policy['candidate_sha256']:raise ValueError('Exact Root film peer required')
 owners={e['id']:e for e in entries};changes=[]
 for row in candidate['entries']:
  e=owners.get(row['entry_id'])
  if not e or e['title']!=row['title']:raise ValueError('Film source missing')
  current=e.get('videos')
  if current not in (row['before_videos'],row['proposed_videos']):raise ValueError('Would overwrite unreviewed film')
  restored=copy.deepcopy(e);restored['videos']=copy.deepcopy(row['before_videos'])
  if digest(restored)!=policy['source_owner_fingerprints'][e['id']]:raise ValueError('Film source prose or media changed')
  for video in row['proposed_videos']:
   poster=policy['local_posters'][video['poster_url']];path=(root/poster['path']).resolve()
   if not path.is_relative_to(root)or hashlib.sha256(path.read_bytes()).hexdigest()!=poster['sha256']:raise ValueError('Film local poster changed')
  if current!=row['proposed_videos']:changes.append((e,copy.deepcopy(row['proposed_videos'])))
 for e,videos in changes:e['videos']=videos
 return {'status':'PASS','changed':[e['id']for e,_ in changes]}
