"""Discover bounded original cues from the public SupraDarky archival index.

The index supplies candidates, never independent composition authorship. Actual
watch metadata, original edition/platform and independent game credits are still
checked. No audio/video is downloaded and no game record is mutated here.
"""
import concurrent.futures,importlib.util,json,re,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('broad',ROOT/'content/expansion/soundtrack-broad-pipeline.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
doc=json.loads((ROOT/'content/catalog.json').read_text());catalog=doc if isinstance(doc,list) else doc['entries']
games={e['id']:e for e in catalog if e.get('kind')=='game'}
for e in games.values():p.TITLE_YEARS.setdefault(p.norm(e['title']),set()).add(e['year'])
source=json.loads((p.RESEARCH/'supradarky-additional-uncovered-matches.json').read_text())
SOURCE_PAGE=source['source_page'];MAIN_CHANNEL='UCjK21_hU5sQoVyxTf5eRU3Q'
OUTPUT=p.RESEARCH/'supradarky-additional-cue-candidates.json'
lock=threading.Lock();channel_evidence={}

def composer_intersection(names,credit):
 # Explicit canonical aliases, not fuzzy matches between unrelated people.
 def canonical(value):return p.norm(value).replace('evelinefischer','evelinenovakovic').replace('bobbyprince','robertprince')
 text=canonical(credit)
 matched=[]
 for name in names:
  aliases=[name]+re.findall(r'\(([^)]+)\)',name)
  if any(canonical(alias) and canonical(alias) in text for alias in aliases):matched.append(name)
 return matched

def unresolved_credit_names(names,credit):
 unknown=[]
 def canonical(value):return p.norm(value).replace('evelinefischer','evelinenovakovic').replace('bobbyprince','robertprince')
 available={canonical(alias) for name in names for alias in [re.sub(r'\s*\([^)]*\)','',name)]+re.findall(r'\(([^)]+)\)',name)}
 for declared in re.split(r'\s*(?:,|;|&|\band\b)\s*',credit):
  if declared and canonical(declared) not in available:unknown.append(declared)
 return unknown

def process(match):
 entry=games[match['entry_id']];record_path=p.RESEARCH/'games'/(entry['id']+'.json')
 record=json.loads(record_path.read_text())
 # Preserve this independent cue research even when a concurrent broad search
 # finds another candidate for the same game. Better isolated cues may replace
 # a collection whose credits still need review.
 names,url,evidence=p.composer(entry);names=p.clean_composer_names(names,entry['title']);record.update(composers=names,composer_source=url,composer_evidence=evidence)
 if not names:return {'entry_id':entry['id'],'title':entry['title'],'state':'independent_composer_required'}
 out={'entry_id':entry['id'],'title':entry['title'],'year':entry['year'],'state':'research_pending','independent_composer_credit':{k:record.get(k) for k in ['composers','composer_source','composer_evidence']},'tracks':[],'holds':[]}
 for indexed in match['candidate_tracks']:
  vid=indexed['YouTube URL'].rstrip('/').split('/')[-1].split('?')[0]
  try:
   years={int(x) for x in re.findall(r'\b(?:19|20)\d{2}\b',indexed.get('Year of release',''))}
   if years and min(abs(y-entry['year']) for y in years)>1:
    out['holds'].append({'youtube_id':vid,'reason':'Public index releaseyear belongs to another edition','index':indexed});continue
   v=p.watch(vid);description=v['shortDescription']
   number=re.search(r'Best\s+VGM\s*0*(\d+)',v['title'],re.I)
   if not number or int(number.group(1))!=int(indexed['BVGM#']):
    out['holds'].append({'youtube_id':vid,'reason':'Actual recording does not match indexed archival collection number'});continue
   if MAIN_CHANNEL not in description or '1Hl11drnPsymQADL1c7bP7p53AU0udT63uEsvyyS2F70' not in description:
    out['holds'].append({'youtube_id':vid,'reason':'Actual archival recording does not link the collection owner and original public index'});continue
   with lock:
    p.ARCHIVE_IDS.add(v['channelId'])
    channel_evidence[v['channelId']]={'publication_kind':'archival_game_recording','evidence':'Actual video links SupraDarky main channel and original public BestVGM index; exact current ID and collection number match that public index. Unofficial preservation archive, not publisher endorsement.','receipt':OUTPUT.relative_to(ROOT).as_posix()}
   # A copied original year must not conceal a later console/PC port. This
   # declaration is attributed to the separately saved public index, not added
   # to or substituted for the actual watch metadata receipt.
   conflict=p.archive_platform_conflict(entry,{**v,'shortDescription':'Platform: '+indexed.get('Platform','')+'\n'+description})
   if conflict:
    out['holds'].append({'youtube_id':vid,'reason':conflict,'index':indexed});continue
   row={'id':vid,'title':v['title'],'channel':v['author'],'channel_id':v['channelId'],'description':description}
   track,reason=p.consider(entry,row,names,url)
   if not track:
    out['holds'].append({'youtube_id':vid,'reason':reason,'index':indexed});continue
   credited=composer_intersection(names,indexed.get('Composer(s)',''))
   if not credited:
    out['holds'].append({'youtube_id':vid,'reason':'Indexed cue composer does not independently match original-game music credits','index':indexed});continue
   unresolved=unresolved_credit_names(names,indexed.get('Composer(s)',''))
   if unresolved:
    out['holds'].append({'youtube_id':vid,'reason':'Indexed cue additionally credits unresolved people/roles; they must not be silently dropped: '+', '.join(unresolved),'index':indexed});continue
   track.update(creator=', '.join(credited),independently_matched_composers=credited,archive_cue_credit=indexed.get('Composer(s)'),archive_context_source=SOURCE_PAGE,archive_index_record=indexed)
   out['tracks'].append(track)
  except Exception as error:out['holds'].append({'youtube_id':vid,'reason':str(error)})
 out['state']='candidate_original_cues' if out['tracks'] else 'research_hold'
 return out

entries=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 futures={pool.submit(process,row):row for row in source['entries'] if row['entry_id'] in games}
 for future in concurrent.futures.as_completed(futures):
  row=futures[future]
  try:result=future.result()
  except Exception as error:result={'entry_id':row['entry_id'],'title':row['title'],'state':'research_hold','error':str(error)}
  entries.append(result);print(result['state'],result['title'],len(result.get('tracks',[])),flush=True)
  if len(entries)%10==0:p.write(OUTPUT,{'publication_status':'auditing','source_page':SOURCE_PAGE,'entries':entries,'reviewed_archive_channels':channel_evidence})
p.write(OUTPUT,{'publication_status':'auditing','scope':'Actual publication metadata, exact archival index identity, original year/platform and independent composition credits. No media downloaded or console playback asserted.','source_page':SOURCE_PAGE,'entries':entries,'reviewed_archive_channels':channel_evidence})
print('FINAL',len(entries),'candidate_rooms',sum(bool(e.get('tracks')) for e in entries),'candidate_cues',sum(len(e.get('tracks',[])) for e in entries),flush=True)
