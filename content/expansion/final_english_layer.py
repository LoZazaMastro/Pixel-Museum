"""Private proposal v2. Pure English layer; caller supplies a pinned root review."""
import copy, hashlib, json
from pathlib import Path
FIELDS=('title','subtitle','summary','body','story_headings')
IDENTITY_PIN={'path':'build/research/phase4-root-identity-corrections-private/3d-tic-tac-toe-identity-correction.json','sha256':'6633ce852c8be6236f5395798fa177abd9673dd034a254ddc2a61d657e3b71e1'}
def digest(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def english(e):return {k:copy.deepcopy(e.get(k,[] if k in ('body','story_headings') else ''))for k in FIELDS}
def pinned(root,pin):
 p=(root/pin['path']).resolve()
 if not p.is_relative_to(root)or hashlib.sha256(p.read_bytes()).hexdigest()!=pin['sha256']:raise ValueError('English publication input changed: '+str(p))
 return json.loads(p.read_bytes())
def revise_attribution(current,identity):
 """Keep named source authors, licence metadata, links and source extracts."""
 at=current.get('attribution')
 if isinstance(at,dict):
  current.setdefault('editorial_source_credit',copy.deepcopy(current.get('editorial_credit')))
  at.setdefault('original_source_credit_text',copy.deepcopy(at.get('text')))
  at.setdefault('prior_source_changes',copy.deepcopy(at.get('changes')))
  licence=at.get('license',at.get('licence',''))
  existing=str(at.get('text',''))+' '+str(current.get('editorial_credit',''))
  source_credit='Wikipedia contributors; ' if 'wikipedia' in existing.lower() else 'Previously credited sources; '
  wording=source_credit+'English exhibition prose adapted and revised by Pixel Museum.'
  if licence:wording+=' Source text licence: '+str(licence)+'.'
  at['text']=wording
  at['changes']='English exhibition prose adapted and revised by Pixel Museum; original source links, author attribution and licence metadata retained.'
  current['editorial_credit']=wording+' Individual media retain their credited rights.'
 elif current.get('editorial_credit'):
  current.setdefault('editorial_source_credit',copy.deepcopy(current['editorial_credit']))
  credit=str(current['editorial_credit'])
  if 'wikipedia' in credit.lower():current['editorial_credit']='Wikipedia contributors; English exhibition prose adapted and revised by Pixel Museum. Existing source licences and individual media rights retained.'
 if identity:
  required=identity['metadata_changes_required_at_admission']
  refs=current.setdefault('sources',[])
  for ref in identity['references']:
   if not any(r.get('url')==ref['url'] for r in refs):refs.append(copy.deepcopy(ref))
  current['editorial_credit']=required['update_editorial_credit']
  if isinstance(current.get('attribution'),dict):current['attribution']['changes']=required['update_attribution_changes']
def apply(entries,root,collection,manifest_pin,final_receipt_pin):
 """Validate all rows on copies, then commit in memory. No file writes."""
 root=Path(root).resolve();manifest=pinned(root,manifest_pin);receipt=pinned(root,final_receipt_pin)
 if receipt.get('manifest_sha256')!=manifest_pin['sha256']or receipt.get('status')!='ROOT_FINAL_ENGLISH_PUBLICATION_ACCEPTED':raise ValueError('Final English publication receipt absent/mismatched')
 approved=set(receipt['owner_ids']);planned={r['entry_id']for r in manifest['owners']}
 if approved!=planned:raise ValueError('Final review scope differs')
 identity=pinned(root,IDENTITY_PIN) if any(r['entry_id']=='wikipedia-420457' and r['collection']==collection for r in manifest['owners']) else None
 staged=copy.deepcopy(entries);by={}
 for e in staged:
  for obj in [e]+e.get('editorial_features',[]):
   if obj['id']in by:raise ValueError('Duplicate current English owner')
   by[obj['id']]=obj
 ledger=[]
 for row in manifest['owners']:
  if row['collection']!=collection:continue
  oid=row['entry_id'];target=row['english_after'];assert set(target)==set(FIELDS)
  if row['new_owner']:
   incoming=pinned(root,row['source']);incoming=copy.deepcopy(incoming['entries'][0])
   if incoming['id']!=oid or english(incoming)!=target:raise ValueError('New owner source mismatch')
   if oid in by:
    if by[oid]!=incoming:raise ValueError('New owner already exists with divergent record')
    continue
   staged.append(incoming);by[oid]=incoming;mode='new_original_editorial_draft'
  else:
   if oid not in by:raise ValueError('Missing existing owner '+oid)
   current=by[oid];state=english(current)
   if digest(state)not in (row['english_before_sha256'],digest(target)):raise ValueError('English source drift '+oid)
   for k in FIELDS:current[k]=copy.deepcopy(target[k])
   revise_attribution(current,identity if oid=='wikipedia-420457' else None)
   mode='editorial_revision_of_existing_record'
  ledger.append({'entry_id':oid,'collection':collection,'operation':mode,'english_after_sha256':digest(target),'source':row['editorial_evidence'],'attribution_policy':'Original source references, authors, licence and immutable extracts retained. English exhibition prose revised; not represented as an unchanged source quotation.','factual_research_repeated':False,'translation_review_claimed':False,'media_review_claimed':False})
 entries[:]=staged
 return {'status':'APPLIED_REVIEWED_ENGLISH_FIELDS','owners':len(ledger),'provenance_ledger':ledger}
