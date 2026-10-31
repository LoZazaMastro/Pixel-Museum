"""Prepare an incremental, independently reviewed music subset.

Only exact recordings already marked PASS by the separate reviewer, or their
bounded original-cue research receipts, are considered. Every still-current
identity/credit rule is replayed and native AVC/AAC metadata must resolve. No
media is downloaded and no console playback is claimed.
"""
import concurrent.futures,importlib.util,json,copy,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);out=importlib.util.module_from_spec(spec);spec.loader.exec_module(out);return out
p=module('broad',ROOT/'content/expansion/soundtrack-broad-pipeline.py')
video=module('video',ROOT/'tools/discover-museum-videos.py')
doc=json.loads((ROOT/'content/catalog.json').read_text());catalog=doc if isinstance(doc,list) else doc['entries'];games={e['id']:e for e in catalog if e.get('kind')=='game'}
for e in games.values():p.TITLE_YEARS.setdefault(p.norm(e['title']),set()).add(e['year'])
approved={};holds=set();review_receipts={}
audits=['independent-20-room-audit.json','independent-second20-room-audit.json','independent-delta108-20-room-audit.json','independent-supradarky-20-room-audit.json','independent-supradarky-second20-room-audit.json','official-direct-credits-editorial-audit-30-59.json','official-direct-credits-editorial-audit-60-89.json','official-direct-credits-independent-audit-0-29.json','official-direct-credits-editorial-audit-120-141.json','official-direct-credits-independent-audit-90-119.json','public-curated-single-platform-editorial-audit.json','independent-expanded-version-four-cue-normalized.json','steam-primary-four-editorial-audit.json','public-curated-remaining-editorial-audit.json','cached-official-remainder-editorial-audit.json','mixed-composer-role-five-credit-corrections-audit.json']
for filename in audits:
 path=p.RESEARCH/filename;d=json.loads(path.read_text());snapshot=ROOT/str(d['snapshot']).replace('\\','/')
 source={e['entry_id']:e for e in json.loads(snapshot.read_text())['entries']}
 for row in d.get('rows',d.get('entries',[])):
  eid=row['entry_id'];ids={t['youtube_id'] for t in row.get('tracks',[])}
  if row['status']!='PASS' and not any(t.get('status')=='PASS' for t in row.get('tracks',[])):holds.update(ids);continue
  if row['status']!='PASS':
   holds.update(t['youtube_id'] for t in row.get('tracks',[]) if t.get('status')!='PASS');ids={t['youtube_id'] for t in row.get('tracks',[]) if t.get('status')=='PASS'}
  for track in source.get(eid,{}).get('tracks',[]):
   if track['youtube_id'] in ids:
    approved[(eid,track['youtube_id'])]=copy.deepcopy(track);review_receipts[(eid,track['youtube_id'])]=path.relative_to(ROOT).as_posix()
    decision=next((t for t in row.get('tracks',[]) if t['youtube_id']==track['youtube_id']),{})
    approved[(eid,track['youtube_id'])].update(decision.get('corrected_track_fields',{}))
    if decision.get('corrected_track_fields'):approved[(eid,track['youtube_id'])]['independent_track_field_corrections']=decision['corrected_track_fields']
    if decision.get('additional_recording_roles'):approved[(eid,track['youtube_id'])]['additional_recording_roles']=decision['additional_recording_roles']
# An individually recovered replacement cue is distinct from an earlier held
# cover/port/collection for that game. Never reopen the old held recording.
flags=p.RESEARCH/'independent-supradarky-creator-intersection-flags.json'
if flags.exists():holds.update(row['youtube_id'] for row in json.loads(flags.read_text()).get('flags',[]))
for filename in ['independent-original-ten-recovery.json','independent-original-ten-archive-contexts.json']:
 path=p.RESEARCH/filename
 if not path.exists():continue
 for row in json.loads(path.read_text())['entries']:
  if not row.get('native_avc_aac_metadata'):continue
  track=row.get('track');vid=track.get('youtube_id') if track else row.get('candidate',{}).get('id')
  if vid:approved[(row['entry_id'],vid)]=copy.deepcopy(track or {});review_receipts[(row['entry_id'],vid)]=path.relative_to(ROOT).as_posix()
path=p.RESEARCH/'independent-original-track-exceptions.json'
if path.exists():
 for row in json.loads(path.read_text())['entries']:
  if row.get('native_avc_aac_metadata'):
   approved[(row['entry_id'],row['youtube_id'])]={};review_receipts[(row['entry_id'],row['youtube_id'])]=path.relative_to(ROOT).as_posix()

# Preserve individually validated increments across reruns; exact current gates
# are still replayed, including bounded same-game-version contextual reviews.
production=ROOT/'content/expansion/soundtrack-independent-approved.json'
if production.exists():
 old=json.loads(production.read_text())
 if old.get('publication_status')=='validated':
  for entry in old['entries']:
   for track in entry['tracks']:
    key=(entry['entry_id'],track['youtube_id']);approved[key]=copy.deepcopy(track)
    review_receipts[key]=track.get('independent_review_receipt') or str(old.get('independent_subset_confirmation'))

# A later explicit cue-role correction supersedes older narrow-parser output.
# This changes candidate metadata only; production still requires independent
# reconciliation before promotion.
correction_path=p.RESEARCH/'mixed-composer-role-five-credit-corrections-audit.json'
if correction_path.exists():
 for entry in json.loads(correction_path.read_text())['entries']:
  for decision in entry['tracks']:
   key=(entry['entry_id'],decision['youtube_id'])
   if key in approved and decision['status']=='PASS':
    approved[key].update(decision['corrected_track_fields']);approved[key]['independent_track_field_corrections']=decision['corrected_track_fields']
    review_receipts[key]=correction_path.relative_to(ROOT).as_posix()

def check(item):
 (eid,vid),prior=item
 if vid in holds and not p.independently_resolved_hold(eid,vid,p.watch(vid)) and not p.official_version_context(eid,{**p.watch(vid),'youtube_id':vid}):return {'entry_id':eid,'youtube_id':vid,'state':'held_by_independent_review'}
 entry=games.get(eid)
 if not entry:return {'entry_id':eid,'youtube_id':vid,'state':'entry_not_current'}
 names,source,evidence=p.composer(entry);names=p.clean_composer_names(names,entry['title'])
 if not names:return {'entry_id':eid,'youtube_id':vid,'state':'composer_unresolved'}
 try:
  v=p.watch(vid);flat={'id':vid,'title':v['title'],'channel':v['author'],'channel_id':v['channelId'],'description':v['shortDescription'],'channel_is_verified':prior.get('official_uploader_verified',False)}
  track,reason=p.consider(entry,flat,names,source)
  if not track:return {'entry_id':eid,'youtube_id':vid,'state':'current_identity_hold','reason':reason}
  if p.official_version_context(eid,{**v,'youtube_id':vid}):
   track.update({key:prior[key] for key in ['title','creator','independently_matched_composers','recording_platform','recording_version','recording_context_sources'] if key in prior})
  if prior.get('independent_track_field_corrections'):
   track.update(prior['independent_track_field_corrections']);track['independent_track_field_corrections']=prior['independent_track_field_corrections']
  if prior.get('credit_role_note'):
   track.update({key:prior[key] for key in ['creator','credit_role_note','independently_matched_composers'] if key in prior})
  if prior.get('additional_recording_roles'):track['additional_recording_roles']=prior['additional_recording_roles']
  if prior.get('archive_index_record'):
   # This cue-specific creator list has been independently reconciled, including
   # every named contributor; do not replace it with a whole-game fallback.
   track.update({key:prior[key] for key in ['creator','independently_matched_composers','archive_cue_credit','archive_context_source','archive_index_record'] if key in prior})
  selection={'entry_id':eid,'match_title':entry['title'],'match_year':entry['year'],'title':'Listen to '+entry['title'],'composer':track['creator'],'tracks':[track]}
  selected,issues=p.final_identity_gate({'entry_id':eid,'composers':names,'selection':selection},list(games.values()))
  if not selected['tracks']:return {'entry_id':eid,'youtube_id':vid,'state':'current_final_hold','reason':issues}
  codec=video.metadata(vid,{'title':v['title'],'channel':v['author']})
  if not codec.get('native_compatible_avc_aac'):return {'entry_id':eid,'youtube_id':vid,'state':'native_codec_hold'}
  track.update(independent_review_receipt=review_receipts[(eid,vid)],native_codec_metadata_receipt='build/research/video-discovery/video-'+vid+'.json',native_codec_metadata_verified=True,playback_verified_on_ps5=False)
  return {'entry_id':eid,'title':entry['title'],'year':entry['year'],'state':'complete_candidate','independent_composer_credit':{'composers':names,'source_page':source,'evidence':evidence},'track':track}
 except Exception as error:return {'entry_id':eid,'youtube_id':vid,'state':'verification_hold','reason':str(error)}

results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for result in pool.map(check,approved.items()):
  results.append(result);print(result['state'],result.get('title',result['entry_id']),result.get('youtube_id') or result.get('track',{}).get('youtube_id'),flush=True)
  p.write(p.RESEARCH/'incremental-independent-subset-audit.json',{'publication_status':'awaiting_subset_confirmation','entries':results})
entries={}
for row in results:
 if row['state']!='complete_candidate':continue
 eid=row['entry_id'];entry=entries.setdefault(eid,{'entry_id':eid,'match_title':row['title'],'match_year':row['year'],'title':'Listen to '+row['title'],'tracks':[],'independent_composer_credit':row['independent_composer_credit']});entry['tracks'].append(row['track'])
for entry in entries.values():
 entry['tracks']=entry['tracks'][:3];entry['composer']=p.selected_music_credit(entry['tracks'],entry['independent_composer_credit']['composers']);entry['curator_note']='Listen to music by '+entry['composer']+' from '+entry['match_title']+'.'
p.write(p.RESEARCH/'incremental-independent-subset-candidate.json',{'schema_version':1,'publication_status':'awaiting_independent_subset_confirmation','validation_scope':'Exact independently reviewed recordings; current game/edition/platform/composer gates replayed; native AVC/AAC public metadata verified. No media downloaded, listening/audio-fingerprint or PS5-playback claim.','verified_on':p.STAMP,'entries':list(entries.values())})
print('FINAL',len(entries),'rooms',sum(len(e['tracks']) for e in entries.values()),'tracks',flush=True)
