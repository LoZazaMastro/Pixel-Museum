"""Preserve the curator's reviewed image-slot edits and explicit exclusions."""
import json,copy
from pathlib import Path
def apply(entries,root,only_owner_ids=None):
 root=Path(root);p=json.loads((root/'content/expansion/reviewed-user-media.json').read_text(encoding='utf-8'))
 excluded=set(p['excluded_owner_ids']);entries[:]=[e for e in entries if e['id']not in excluded]
 owners={e['id']:e for e in entries};count=0
 # Several reviewed corrections may supersede the same image slot. The
 # latest reviewed state is already final, not drift against an older edit.
 latest_slots={(row['id'],slot['index']):slot['after']for row in p['edits']for slot in row['slots']}
 latest_collections={(row['id'],row.get('feature_id'),field):row['after'][field]for row in p.get('collection_edits',[])for field in row['after']}
 for row in p['edits']:
  if only_owner_ids is not None and row['id']not in only_owner_ids:continue
  e=owners[row['id']]
  for slot in row['slots']:
   n=slot['index'];current=e['images'][n]
   if e['images']==latest_collections.get((row['id'],None,'images'))or current==latest_slots[(row['id'],n)]or current==slot['after']:continue
   if current!=slot['before']:raise ValueError('Reviewed user image preimage changed: '+row['id']+':'+str(n))
   e['images'][n]=copy.deepcopy(slot['after']);count+=1
 for row in p.get('collection_edits',[]):
  if only_owner_ids is not None and row['id']not in only_owner_ids:continue
  e=owners[row['id']]
  if row.get('feature_id'):
   matches=[feature for feature in e.get('editorial_features',[])if feature['id']==row['feature_id']]
   if len(matches)!=1:raise ValueError('Reviewed nested media owner missing or duplicated')
   e=matches[0]
  for field in row['before']:
   if field not in ('images','videos'):raise ValueError('Media-only correction attempted another field')
   if e.get(field,[])==latest_collections[(row['id'],row.get('feature_id'),field)]or e.get(field,[])==row['after'][field]:continue
   if e.get(field,[])!=row['before'][field]:raise ValueError('Reviewed media collection preimage changed: '+row['id']+':'+field)
   e[field]=copy.deepcopy(row['after'][field]);count+=1
 return {'edited_slots':count,'excluded_owner_ids':sorted(excluded)}
