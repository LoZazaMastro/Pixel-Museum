import json,copy,re,hashlib,importlib.util,concurrent.futures,html
from pathlib import Path
R=Path(__file__).resolve().parents[2];B=R/'build/research/soundtrack-broad'
def mod(n,f):
 s=importlib.util.spec_from_file_location(n,R/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=mod('pipeline','content/expansion/soundtrack-broad-pipeline.py');v=mod('video','tools/discover-museum-videos.py')
d=json.loads((B/'checkpoints/compound-role-replay101-2026-10-21.json').read_text());D=B/'compound-role-source-reviews';D.mkdir(exist_ok=True)
selected={31,32,33,34,37,38,39,40,41,42,44,45,46,47,48,49,50,51,52,54,55,57,59,61,62,63,64,66,69,70,71,73,74,75,76,77,80,81,82,83,86,89,91,94,97}
only={59:{'1fd5P98Apzg'},71:{'-1VKJB3GAD0'},97:{'a7j8xLTQvfk'}}
excluded={57:{'F-WToBQYZ_A'}}
held={30:'Fan-extended loop edit held; prefer original cue.',35:'Main-theme source omits original Tappi Iwase melody role.',36:'Rez licensed cue authors not established by single game infobox name.',43:'Uploader explicitly mixes dynamic samples into new presentation.',53:'Ryo Yamazaki arrangement role needs exact corroboration.',56:'Joel Eriksson named in label delivery; contributor scope unresolved.',58:'Fan-extended loop edit held.',60:'Long collection requires per-cue full-author/album scope.',65:'Vocal song additional lyrical/performance credits need role-specific source.',67:'Penka Kouneva role needs exact source.',68:'Generic whole-game roster lacks cue-specific original composition source.',72:'Aloy theme assigned whole-game roster; exact cue author needed.',78:'Five-name whole-game roster lacks cue-specific source.',79:'Jose Delgado and arrangers in delivery need exact role scope.',84:'Whole-game roster/cue inconsistency; exact TLOUII authors needed.',85:'Uploader extracted and mixed dynamic stems; exact original composition allocation unresolved.',87:'2020 Bill Hemstapat arrangement role needs source.',88:'Youki Yamamoto/Ayako Tsuchiya role context not explicit.',90:'Existing NieR cue-role HOLD remains; no source correction.',92:'Three-name whole-game roster lacks cue-specific source.',93:'Label includes Nobuo Uematsu omitted from selected creators.',95:'Justin Aucoin and others roles not resolved from unlabelled delivery.',96:'8082 collective source does not identify Listen Not individual song credit.',98:'Existing KCDII per-cue author REVIEW unchanged.',99:'Metadata ambiguously describes full album versus isolated Silver Sisters.',100:'Limp Bizkit erroneously attached to Henry Jackman title cue.'}

def source(e):
 u=e['independent_composer_credit']['source_page'];name=hashlib.sha256(u.encode()).hexdigest()[:20];f=D/(name+'.html');receipt={'url':u,'entry_id':e['entry_id']}
 try:
  body=f.read_text(encoding='utf-8') if f.exists() else p.fetch(u)
  title=re.search(r'<title[^>]*>(.*?)</title>',body,re.S|re.I);actual=p.text(title.group(1)) if title else ''
  if not actual or re.search('client challenge|just a moment|access denied|security check',actual,re.I):raise ValueError('Not actual source body: '+actual)
  f.write_text(body,encoding='utf-8');fields=[]
  for tr in re.findall(r'<tr\b[^>]*>.*?</tr>',body,re.S):
   lab=re.search(r'<th\b[^>]*>(.*?)</th>',tr,re.S);val=re.search(r'<td\b[^>]*>(.*?)</td>',tr,re.S)
   if lab and val and re.fullmatch('Composer(?:s|\(s\))?',p.text(lab.group(1)),re.I):fields.append(p.text(val.group(1)))
  paras=[p.text(x) for x in re.findall(r'<p\b[^>]*>(.*?)</p>',body,re.S)]
  music=[x for x in paras if re.search(r'compos|soundtrack|music|score',x,re.I) and len(x)>40]
  receipt.update(status='ACTUAL_BODY_FETCHED',actual_title=actual,composer_fields=fields,music_context=music[:12],local_source=str(f.relative_to(R)),sha256=hashlib.sha256(f.read_bytes()).hexdigest())
 except Exception as ex:receipt.update(status='SOURCE_HOLD',error=str(ex))
 (D/(name+'.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return receipt
sources={}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for rr in pool.map(source,[d['entries'][i] for i in sorted(selected)]):sources[rr['entry_id']]=rr;print('SOURCE',rr['entry_id'],rr['status'],flush=True)
entries=[];audit=[]
for i in range(30,len(d['entries'])):
 e=copy.deepcopy(d['entries'][i]);row={'index':i,'entry_id':e['entry_id'],'title':e['match_title'],'status':'HOLD','reason':held.get(i,''),'tracks':[]}
 if i not in selected:audit.append(row);continue
 sr=sources[e['entry_id']];row['source_review']=str((D/(hashlib.sha256(sr['url'].encode()).hexdigest()[:20]+'.json')).relative_to(R));row['source_actual_title']=sr.get('actual_title');row['source_composer_fields']=sr.get('composer_fields')
 if sr['status']!='ACTUAL_BODY_FETCHED':row['reason']='Actual source unavailable';audit.append(row);continue
 ts=[]
 for t in e['tracks']:
  vid=t['youtube_id'];q={'youtube_id':vid,'status':'HOLD'}
  if (i in only and vid not in only[i]) or vid in excluded.get(i,set()):q['reason']='Deliberately excluded duplicate, wrong edition or unresolved cue-role context';row['tracks'].append(q);continue
  w=json.loads((B/'watch'/(vid+'.json')).read_text());q.update(actual_publication_title=w['title'],actual_uploader=w['author'])
  try:codec=v.metadata(vid,{'title':w['title'],'channel':w['author']});assert codec.get('native_compatible_avc_aac')
  except Exception as ex:q['reason']='Native codec HOLD: '+str(ex);row['tracks'].append(q);continue
  t['native_codec_metadata_receipt']='build/research/video-discovery/video-'+vid+'.json';t['native_codec_metadata_verified']=True;t['playback_verified_on_ps5']=False
  t['editorial_source_review_receipt']=row['source_review'];t['recording_version']='Archival same-game score; capture hardware not identified.' if not t.get('official_uploader_verified') else 'Official same-game soundtrack release.'
  release=re.search(r'Released on:\s*((?:19|20)\d{2})-\d{2}-\d{2}',w['shortDescription'])
  if t.get('official_uploader_verified') and release:t['recording_release_year']=int(release.group(1));t['recording_version']='Official same-game soundtrack album release ('+release.group(1)+').'
  if i==39:t['additional_recording_roles']={'vocals':'Tenpei Sato'}
  if i==62:t['additional_recording_roles']={'vocals':'Rudy Cardenas'}
  if i==77:t['additional_recording_roles']={'vocals':'Martti Suosalo'}
  if i==80:t['recording_version']='Disco Elysium / The Final Cut same-game score; archival recording, capture hardware not identified.'
  if i==86:t['credit_alias_note']='tatreal is the musical alias of Slava Korystov; actual game/artist soundtrack context retained.'
  if i==73 and vid=='f9DLhlboCSU':t['additional_recording_roles']={'vocals':'Alana Bridgewater'}
  q['status']='PASS_CANDIDATE_PENDING_PEER';q['reason']='Actual exact-game publication, described cue credit and independently fetched exact game composer/primary source reviewed. No fingerprint/listening claim.';ts.append(t);row['tracks'].append(q);print('CUE',e['match_title'],vid,'PASS_CODEC',flush=True)
 if ts:e['tracks']=ts;e['composer']=', '.join(dict.fromkeys(t['creator'] for t in ts));e['curator_note']='Listen to music by '+e['composer']+' from '+e['match_title']+'.';entries.append(e);row['status']='PASS_CANDIDATE_PENDING_PEER'
 audit.append(row)
 for name,data in [('compound-role-editorial-30-100-candidates.json',{'publication_status':'awaiting_independent_review','entries':entries}),('compound-role-editorial-30-100-audit.json',{'snapshot':'build/research/soundtrack-broad/checkpoints/compound-role-replay101-2026-10-21.json','entries':audit})]: (B/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('FINAL',len(entries),sum(len(e['tracks']) for e in entries),flush=True)
