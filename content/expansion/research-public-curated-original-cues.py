"""Research individual cues from pinned public archival channel catalogues.
The flat index discovers candidates only; actual watch identity, every declared
music contributor, exact game/platform and independent game credits are checked.
No media is downloaded and these results never directly enter publication.
"""
import concurrent.futures,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('broad',ROOT/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
doc=json.loads((ROOT/'content/catalog.json').read_text());catalog=doc if isinstance(doc,list) else doc['entries'];games={e['id']:e for e in catalog if e.get('kind')=='game'}
for e in games.values():p.TITLE_YEARS.setdefault(p.norm(e['title']),set()).add(e['year'])
source=json.loads((p.RESEARCH/'public-curated-catalog-matches.json').read_text())
skip={e['entry_id'] for e in json.loads((ROOT/'content/expansion/soundtrack-independent-approved.json').read_text())['entries']}
# Prioritize genuinely new coverage; keep other source routes separately intact.
supra=json.loads((p.RESEARCH/'supradarky-original-cue-candidates.json').read_text())
skip.update(e['entry_id'] for e in supra['entries'] if e.get('tracks'))
OUT=p.RESEARCH/'public-curated-original-cue-candidates.json';CACHE=p.RESEARCH/'curated-catalogs/candidate-receipts';CACHE.mkdir(exist_ok=True)
def process(match):
 entry=games[match['entry_id']];cache=CACHE/(entry['id']+'.json')
 if cache.exists():
  cached=json.loads(cache.read_text())
  if cached.get('policy_version')==2:return cached
 names,url,evidence=p.composer(entry);names=p.clean_composer_names(names,entry['title'])
 out={'policy_version':2,'entry_id':entry['id'],'title':entry['title'],'year':entry['year'],'independent_composer_credit':{'composers':names,'composer_source':url,'composer_evidence':evidence},'tracks':[],'holds':[]}
 if not names or not p.composer_source_identity_verified(entry,url):
  out['state']='independent_composer_required';p.write(cache,out);return out
 for row in match['candidates'][:3]:
  vid=row['id']
  try:
   v=p.watch(vid)
   if v['channelId']!=row['expected_channel_id']:
    out['holds'].append({'youtube_id':vid,'reason':'Actual uploader ID differs from pinned public catalogue'});continue
   flat={'id':vid,'title':v['title'],'channel':v['author'],'channel_id':v['channelId'],'description':v['shortDescription']}
   track,reason=p.consider(entry,flat,names,url)
   if not track:out['holds'].append({'youtube_id':vid,'reason':reason});continue
   declared=p.published_music_credits(v)
   if v['channelId']=='UC4bD7uDwMsPBnUo4CBcYk1g' and len(declared)>1:
    out['holds'].append({'youtube_id':vid,'reason':'Catalogue repeats whole-gameComposer(s) roster for individual cues; individual authorship needs a cue-level source, not game-wide attribution.'});continue
   # Preserve actual cue names; whole-game roster is only a fallback when the
   # archival publication makes no narrower authorship assertion.
   if declared:
    track['creator']=', '.join(declared);track['archive_cue_credit']=', '.join(declared)
   track['archive_context_source']=row['catalog_source'];track['archive_catalogue_record']={'youtube_id':vid,'title':row['title'],'channel_id':row['expected_channel_id']}
   out['tracks'].append(track)
  except Exception as ex:out['holds'].append({'youtube_id':vid,'reason':str(ex)})
 out['state']='candidate_original_cues' if out['tracks'] else 'research_hold';p.write(cache,out);return out
rows=[r for r in source['entries'] if r['entry_id'] not in skip]
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for result in pool.map(process,rows):
  results.append(result);print(result['state'],result['title'],len(result['tracks']),flush=True)
  p.write(OUT,{'publication_status':'auditing','scope':'Discovery and actual publication metadata only; independently reviewed subset and native codec receipts required before admission. No media downloaded.','entries':results})
print('FINAL',len(results),'checked',sum(bool(r['tracks']) for r in results),'candidate rooms',sum(len(r['tracks']) for r in results),'cues',flush=True)
