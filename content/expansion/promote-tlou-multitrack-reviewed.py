"""Apply the independently read Sony/Qobuz per-cue credits to the frozen proposal."""
import copy,hashlib,html,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'build/research/last-of-us-score-review'
source=OUT/'two-games18-candidate.json'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='23c3369368c6e86049edfb5005e268607d53f91025473faff834ebf8e3fad2bd'
proposal=json.loads(source.read_text())
watch={r['id']:r for r in json.loads((OUT/'independent-actual-publications18.json').read_text())}
urls=[
'https://www.qobuz.com/ie-en/album/the-last-of-us-video-game-soundtrack-gustavo-santaolalla/0886443853973',
'https://www.qobuz.com/us-en/album/the-last-of-us-part-ii-original-soundtrack-gustavo-santaolalla-mac-quayle/glm0nel3uk1wb']
review=[];production=copy.deepcopy(proposal)
for part,e in enumerate(production['entries']):
 raw=(OUT/('part1-qobuz-actual.html' if part==0 else 'part2-qobuz-actual.html')).read_text(encoding='utf-8')
 table={}
 for block in raw.split('<div class="player__item">')[1:]:
  m=re.search(r'data-track-v2="(.*?)"',block,re.S)
  if not m:continue
  item=json.loads(html.unescape(m.group(1)));credits=[html.unescape(v) for v in re.findall(r'<p class="track__info">(.*?)</p>',block,re.S)]
  table[item['item_name']]={'title':item['item_name'],'artist':item['item_brand'],'credits':credits,'album':item['item_category']}
 e['replace_existing_tracks']=True
 for t in e['tracks']:
  identifier=t['youtube_id'];w=watch[identifier]
  assert w['ok'] and w['channel']=='UCGkX_HCD_T5XOwxi_KR6YoQ'
  assert ('Video Game Soundtrack' if part==0 else 'Part II') in w['title']
  assert ('Video Game Soundtrack' if part==0 else 'Part II') in w['description']
  title=t['title'].replace(' (Main Theme)','')
  if part and title=='The Last of Us Part II':title='The Last of Us Part II'
  row=table[title]
  composer='Mac Quayle' if part and title in ['The Cycle of Violence','The WLF','The Cycle Continues'] else 'Gustavo Santaolalla'
  assert any(composer+', Composer' in line or composer+', Associated Performer, Composer' in line for line in row['credits'])
  native=ROOT/t['native_codec_metadata_receipt'].replace('\\','/')
  meta=json.loads(native.read_text());assert meta['native_compatible_avc_aac'] and meta['id']==identifier
  t['creator']=composer
  t['composer_source']=urls[part]
  t['label_published_track_credits']=row['credits']
  t['artist_credit_scope']='Individual cue composition follows the Sony-delivered album credits; the publication artist field is preserved separately. Producer credits are not treated as composition.'
  t['recording_year']=2013 if part==0 else 2020
  t['recording_album']=row['album']
  t['recording_version']=f"Original {t['recording_year']} video-game soundtrack album; official Sony Music publication."
  t['native_codec_metadata_receipt']=native.relative_to(ROOT).as_posix()
  t['publication_metadata_receipt']=f'build/research/soundtrack-broad/watch/{identifier}.json'
  t['additional_recording_roles']={'production':['Gustavo Santaolalla','Mac Quayle'] if part else ['Gustavo Santaolalla','Anibal Kerpel','Jonathan Mayer']}
  t['independent_identity_review']='PASS: actual Sony publication, exact game-album track and Sony-delivered cue credits read independently.'
  review.append({'entry_id':e['entry_id'],'youtube_id':identifier,'status':'PASS','title':t['title'],'creator':composer,'composer_source':urls[part],'native_avc_aac':True,'publication_read':True,'notes':'Later HBO marketing in some descriptions does not change the explicitly named original game-album publication; no television album is selected.'})
production['publication_status']='validated'
production['validation_scope']='Eighteen individual official game-album publications; actual public descriptions, original Sony-delivered album credits and native AVC/AAC metadata checked. No audio fingerprint, listening or PS5 playback assertion.'
production['independent_review_receipt']='build/research/last-of-us-score-review/independent-two-games18-review.json'
dest=ROOT/'content/expansion/soundtrack-multitrack-priority-overrides.json'
dest.write_text(json.dumps(production,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
receipt={'status':'PASS','candidate':source.relative_to(ROOT).as_posix(),'candidate_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'production':dest.relative_to(ROOT).as_posix(),'production_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'rooms':2,'recordings':18,'scope':production['validation_scope'],'required_corrections_applied':'Main PartII theme and Unbound composition narrowed to Gustavo Santaolalla from per-cue label credits; Mac Quayle retained as producer and original combined publication artist. All ten PartII cues follow actual per-track roles.','primary_sources':'independent-primary-source-receipts.json','tracks':review}
(OUT/'independent-two-games18-review.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PASS',len(review),'records; production',receipt['production_sha256'])
