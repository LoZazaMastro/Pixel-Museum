"""Resume-safe soundtrack publishing research. No media/audio is downloaded.
Each admitted recording retains watch-page, album, uploader and composer evidence.
Metadata verification is not an audio-fingerprint or PS5-playback assertion.
"""
from __future__ import annotations
import argparse,concurrent.futures,copy,hashlib,html,json,re,subprocess,threading,time,unicodedata
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import unquote,urlparse,quote
ROOT=Path(__file__).resolve().parents[2]
RESEARCH=ROOT/'build/research/soundtrack-broad'
YTDLP=Path(r'C:/Users/Andrea/homebrew/plugins/themedeck/yt-dlp.exe')
STAMP='2026-10-21'
PIPELINE_VERSION=7
TITLE_YEARS={}
YOUTUBE_LOCK=threading.Lock()
YOUTUBE_NEXT=0.0
for folder in ['games','search','watch','wiki']: (RESEARCH/folder).mkdir(parents=True,exist_ok=True)

def norm(s):
 s=unicodedata.normalize('NFKD',html.unescape(s).replace('™','').replace('®','').replace('©','')).encode('ascii','ignore').decode().lower().replace('&','and')
 s=re.sub(r'\([^)]*\)','',s)
 return re.sub('[^a-z0-9]','',s).removeprefix('sidmeiers')

def write(path,data):
 temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(data,ensure_ascii=True,indent=2)+'\n',encoding='utf-8');temp.replace(path)

def fetch(url):
 global YOUTUBE_NEXT
 if 'youtube.com/watch?' in url:
  with YOUTUBE_LOCK:
   wait=max(0,YOUTUBE_NEXT-time.monotonic())
   if wait:time.sleep(min(wait,45))
   YOUTUBE_NEXT=time.monotonic()+.85
 with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 PixelMuseumEditorial/1.0'}),timeout=24) as response:return response.read(8<<20).decode('utf-8','replace')

def text(raw):
 raw=re.sub(r'<(?:style|script)\b[^>]*>.*?</(?:style|script)>','',raw,flags=re.S)
 raw=re.sub(r'<sup\b.*?</sup>','',raw,flags=re.S)
 raw=re.sub(r'</li>|<br\s*/?>','; ',raw)
 return html.unescape(re.sub('<[^>]+>','',raw)).strip(' ;\n\t')

SOURCE_IDENTITY_PAGES=None
SOURCE_IDENTITIES_BY_GAME={}
def source_identity_pages():
 global SOURCE_IDENTITY_PAGES,SOURCE_IDENTITIES_BY_GAME
 if SOURCE_IDENTITY_PAGES is None:
  path=RESEARCH/'game-source-identities.json'
  SOURCE_IDENTITY_PAGES=json.loads(path.read_text()).get('pages',{}) if path.exists() else {}
  for title,info in SOURCE_IDENTITY_PAGES.items():SOURCE_IDENTITIES_BY_GAME.setdefault(album_core(title),[]).append((title,info))
 return SOURCE_IDENTITY_PAGES

def wiki_source_identity(entry,url,subject_metadata=None):
 if 'en.wikipedia.org/wiki/' not in url:return False,'Not an exact Wikipedia game article URL'
 title=unquote(url.split('/wiki/',1)[1].split('?')[0].split('#')[0]).replace('_',' ')
 if album_core(title)!=album_core(entry['title']):return False,'Article title belongs to a different game or a multi-game date wrapper: '+title
 if re.search(r'\((?:[^)]*\b(?:TV series|television|film|novel|character|franchise|cancelled video game|album)|series)\)',title,re.I):return False,'Different media adaptation/franchise or cancelled game article'
 info=subject_metadata or source_identity_pages().get(title,{})
 desc=info.get('description','');intro=info.get('intro','')[:500]
 if re.search(r'\b(?:animation|graphics|drawing|presentation)\s+(?:software|program|application)\b|\b(?:software library|operating system|graphics editor)\b',desc+' '+intro,re.I):return False,'Same-title software/tool article is not the video game'
 intro_without_subject=re.sub(r'^'+re.escape(re.sub(r'\s*\([^)]*\)','',title))+r'\b','',intro,flags=re.I)
 if re.search(r'^(?:video )?game series|^series |franchise|^list of|^company|^character',desc,re.I) or re.search(r'^.{0,100}\bis (?:a|an) .{0,45}(?:video game series|game franchise|cancelled [^.]*game|[^.]{0,25}television series)',intro,re.I):return False,'Article is a franchise/list rather than the original game'
 year=re.search(r'\(((?:19|20)\d{2}) video game\)',title)
 if not year:year=re.search(r'\b((?:19|20)\d{2})\s+(?:video\s+)?game\b',desc,re.I)
 if not year:year=re.search(r'\bis (?:a|an)\s+((?:19|20)\d{2})\b[^.]{0,100}\bgame\b',intro_without_subject,re.I)
 if not year:year=re.search(r'\b(?:was\s+)?(?:first\s+)?released\b[^.!?]{0,100}?\b((?:19|20)\d{2})\b',intro_without_subject,re.I)
 # A predecessor's date, early-access date or fictional setting year is not
 # the release year of this subject (e.g. DeusEx2000 cited by HumanRevolution).

 years=TITLE_YEARS.get(norm(entry['title']),set())
 if len(years)>1 and (not year or abs(int(year.group(1))-entry['year'])>1):return False,'Same-title original/remake article year not independently matched'
 if year and abs(int(year.group(1))-entry['year'])>1:return False,'Article concerns a different-year original/remake edition'
 return True,'Exact original-game title matched'+(' and article year '+year.group(1) if year else '')

def composer_source_identity_verified(entry,url):
 if not url.startswith('https://en.wikipedia.org/'):return bool(url)
 if not wiki_source_identity(entry,url)[0]:return False
 title=unquote(url.split('/wiki/',1)[1].split('?')[0]).replace('_',' ')
 if title in source_identity_pages():return True
 path=RESEARCH/'wiki'/(hashlib.sha256(quote(url,safe=':/?=&%()#,;+').encode()).hexdigest()[:20]+'.json')
 if path.exists():
  d=json.loads(path.read_text());actual_title=d.get('actual_page_title','')
  return bool(d.get('source_identity_verified')) and bool(actual_title) and wiki_source_identity(entry,'https://en.wikipedia.org/wiki/'+quote(actual_title.replace(' ','_')),{'intro':d.get('actual_page_intro','')})[0]
 return False

WIKI_COMPOSER_CACHE=None
def cached_exact_composer(entry):
 global WIKI_COMPOSER_CACHE
 if WIKI_COMPOSER_CACHE is None:
  WIKI_COMPOSER_CACHE={}
  for path in (RESEARCH/'wiki').glob('*.json'):
   try:row=json.loads(path.read_text())
   except Exception:continue
   if not row.get('composers') or row.get('pipeline_version',0)<5:continue
   url=row.get('source_page','')
   if '/wiki/' not in url:continue
   title=row.get('actual_page_title') or unquote(url.split('/wiki/',1)[1].split('?')[0]).replace('_',' ')
   WIKI_COMPOSER_CACHE.setdefault(album_core(title),[]).append((title,url,row))
 for title,url,row in WIKI_COMPOSER_CACHE.get(album_core(entry['title']),[]):
  metadata={'intro':row.get('actual_page_intro','')} if row.get('actual_page_intro') else None
  canonical='https://en.wikipedia.org/wiki/'+quote(title.replace(' ','_'))
  if wiki_source_identity(entry,canonical,metadata)[0] and (title in source_identity_pages() or row.get('source_identity_verified')):
   return row['composers'],url,row.get('evidence','')
 return None

def composer(entry):
 for filename in ['soundtrack-composer-source-overrides-fourth.json','soundtrack-composer-credit-completeness-extra.json','soundtrack-composer-source-overrides-third.json','soundtrack-composer-source-overrides-primary.json','soundtrack-composer-source-overrides-extra.json','soundtrack-composer-source-overrides.json']:
  override_path=ROOT/'content/expansion'/filename
  if override_path.exists():
   override=json.loads(override_path.read_text()).get('entries',{}).get(entry['id'])
   if override and override.get('composers') and not override.get('name_correction_only') and not any('Credited artist' in role for role in override.get('roles',{}).values()):
    url=override['source_page']
    if 'en.wikipedia.org/wiki/' in url and not wiki_source_identity(entry,url)[0] and override.get('source_identity_verified_for_entry')!=entry['id']:continue
    return override['composers'],url,override.get('evidence','')
 cached=cached_exact_composer(entry)
 if cached:return cached
 urls=[]
 # Date wrappers can cite many unrelated games. Never select their first URL.
 for source in entry.get('sources',[]):
  url=source.get('url','')
  if wiki_source_identity(entry,url)[0]:urls.append(url)
 exact=[]
 source_identity_pages()
 for title,info in SOURCE_IDENTITIES_BY_GAME.get(album_core(entry['title']),[]):
  url='https://en.wikipedia.org/wiki/'+quote(title.replace(' ','_'))
  if wiki_source_identity(entry,url)[0]:exact.append((0 if f"({entry['year']} video game)" in title else 1 if '(video game)' in title else 2,url))
 urls=[u for _,u in sorted(exact)]+urls
 # Unindexed games use exact-title candidates, not arbitrary date-page citations.
 for title in [f"{entry['title']} ({entry['year']} video game)",entry['title']+' (video game)',entry['title']]:
  url='https://en.wikipedia.org/wiki/'+quote(title.replace(' ','_'))
  if wiki_source_identity(entry,url)[0]:urls.append(url)
 errors=[]
 for url in dict.fromkeys(urls):
  url=quote(url,safe=':/?=&%()#,;+');path=RESEARCH/'wiki'/(hashlib.sha256(url.encode()).hexdigest()[:20]+'.json')
  if path.exists():
   d=json.loads(path.read_text())
   cached_title=unquote(url.split('/wiki/',1)[1]).replace('_',' ')
   actual_title=d.get('actual_page_title','')
   cached_identity_known=cached_title in source_identity_pages() or (actual_title and wiki_source_identity(entry,'https://en.wikipedia.org/wiki/'+quote(actual_title.replace(' ','_')),{'intro':d.get('actual_page_intro','')})[0])
   if d.get('composers') and d.get('pipeline_version',0)>=5 and cached_identity_known:return d['composers'],url,d.get('evidence','')
   if d.get('source_identity_verified') and not d.get('composers'):continue
  # Avoid needless nonexistent year/disambiguation probes where an exact cached article exists.
  if exact and unquote(url.split('/wiki/',1)[1]).replace('_',' ') not in source_identity_pages():continue
  try:
   page=fetch(url);names=[];evidence=''
   page_title_match=re.search(r'<title[^>]*>(.*?)</title>',page,re.S|re.I)
   actual_title=html.unescape(text(page_title_match.group(1))).removesuffix(' - Wikipedia') if page_title_match else ''
   actual_url='https://en.wikipedia.org/wiki/'+quote(actual_title.replace(' ','_'))
   # The canonical original article may not be in our older API index. Verify
   # the fetched lead itself instead of trusting the requested year/redirect.
   paragraphs=[text(raw) for raw in re.findall(r'<p\b[^>]*>(.*?)</p>',page,re.S)[:35]]
   actual_intro=next((value for value in paragraphs if re.search(r'\bis (?:a|an)\b|\bwas (?:a|an)\b',value[:180],re.I) and re.search(r'\bgame\b',value[:500],re.I) and album_core(entry['title']) in album_core(value[:180])), '')
   actual_metadata={'intro':actual_intro} if actual_intro else None
   # A bare-title page can also be an animation program (Fantavision1985).
   # The fetched lead must positively identify this subject as a game before
   # any infobox author field can be used as a composition source.
   actual_identity_ok=bool(actual_title) and bool(actual_intro) and wiki_source_identity(entry,actual_url,actual_metadata)[0]
   if not actual_identity_ok:
    write(path,{'pipeline_version':PIPELINE_VERSION,'composers':[],'source_page':url,'actual_page_title':actual_title,'actual_page_intro':actual_intro,'source_identity_verified':False,'identity_hold':'Actual fetched article title/edition differs from requested subject; redirects are not proof of identity','checked':STAMP});continue
   for tr in re.findall(r'<tr\b[^>]*>.*?</tr>',page,re.S):
    label=re.search(r'<th\b[^>]*>(.*?)</th>',tr,re.S);value=re.search(r'<td\b[^>]*>(.*?)</td>',tr,re.S)
    if label and value and re.fullmatch(r'Composer(?:s|\(s\))?',text(label.group(1)),re.I):
     evidence=text(value.group(1));names=[n.strip() for n in evidence.split(';') if n.strip()];break
   names=[re.sub(r'^List of composers\s*','',re.sub(r'\s*\[[a-z]{2,3}\]','',n)).strip() for n in names if len(n)<160 and not n.startswith(('See ','Unknown')) and not any(x in n for x in ['{','}','.mw-'])]
   write(path,{'pipeline_version':PIPELINE_VERSION,'composers':names,'source_page':url,'source_identity_verified':wiki_source_identity(entry,actual_url,actual_metadata)[1],'actual_page_title':actual_title,'actual_page_intro':actual_intro,'evidence':evidence,'checked':STAMP})
   if names:return names,url,evidence
  except Exception as error:errors.append(str(error))
 return [],urls[0] if urls else '', 'Exact-game composer research unresolved'+(': '+errors[-1] if errors else '')

def search(query):
 p=RESEARCH/'search'/(hashlib.sha256(query.encode()).hexdigest()[:20]+'.json')
 if p.exists():return json.loads(p.read_text())
 result=subprocess.run([str(YTDLP),'--flat-playlist','--playlist-end','5','--dump-json','--no-warnings','--socket-timeout','15','--retries','1','ytsearch5:'+query],capture_output=True,text=True,encoding='utf-8',timeout=50)
 rows=[json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
 write(p,rows);return rows

def watch(id):
 p=RESEARCH/'watch'/(id+'.json')
 if p.exists():return json.loads(p.read_text())
 # The regular public Android player endpoint avoids watch-page throttling.
 result=subprocess.run([str(YTDLP),'--skip-download','--dump-single-json','--no-warnings','--ignore-no-formats-error','--no-check-formats','--socket-timeout','12','--retries','1','--extractor-args','youtube:player_skip=webpage,configs;player_client=android','https://www.youtube.com/watch?v='+id],capture_output=True,text=True,encoding='utf-8',timeout=45)
 if result.returncode or not result.stdout.strip():raise RuntimeError('Public player metadata unavailable: '+result.stderr[-250:])
 data=json.loads(result.stdout);out={'title':data.get('title',''),'author':data.get('channel') or data.get('uploader',''),'channelId':data.get('channel_id',''),'shortDescription':data.get('description',''),'lengthSeconds':str(data.get('duration') or 0),'status':'OK','availability':data.get('availability'),'checked':STAMP,'metadata_source':'Official YouTube Android player via yt-dlp; media download disabled'}
 if not out['title'] or not out['channelId'] or not out['shortDescription']:raise RuntimeError('Player returned incomplete publication metadata')
 write(p,out);return out

# These are exact original releases with no composed score. Do not invent music.
SILENT={
 'pong':'Original arcade release has game sound effects rather than a composed soundtrack.',
 'tennisfortwo':'The original1958 analog demonstration has no composed musical soundtrack.',
 'oxo':'Original1952 EDSAC game has no composed soundtrack.',
 'bertiethebrain':'Original1950 machine has no composed musical soundtrack.',
 'nimrod':'Original1951 Nim machine has no composed musical soundtrack.',
 'spacewar':'Original1962 PDP-1 game has no composed musical soundtrack.',
 'computerspace':'Original arcade game uses electronic effects rather than a composed musical score.',
 'breakout':'Original1976 arcade game has sound effects rather than a composed musical score.',
 'colossalcaveadventure':'Original text adventure has no composed musical score.',
 'zork':'Original text-only release has no composed musical soundtrack.',
 'rogue':'Original text-mode release has no composed musical soundtrack.',
 'nethack':'Original terminal release has no composed musical soundtrack.',
 'hunthewumpus':'Original text-only release has no composed musical soundtrack.'}
OFFICIAL_NAMES=['valve','squareenixmusic','squareenixmusicchannel','bethesdasoftworks','nintendoofamerica','nintendouk','nintendoofeurope','atluswest','atlustube','capcomusa','capcomeurope','capcomasia','supergiantgames','playstation','nintendo','konami','ubisoft','bethesda','rockstargames','sonysoundtracksvevo','rockstargamesmusic','atlus','capcom','segamusic','sega','bandainamco','electronicarts','eagames','eaoriginals','xbox','halo','blizzard','riotgames','lacedrecords','wayorecords','data discs','datadiscs','iam8bit','devolverdigital','annapurnainteractive','teamcherry','chucklefish','ghostshipgames','cdprojektred','ubisoftmusic','larianstudios','sonic the hedgehog','sonicthehedgehog','monsterhunter','monst erhunter'.replace(' ',''),'capcomchannel','atlusgamechannel','marvelmusicvevo','hospitalrecords','microsoftflightsimulator','playoverwatch','forza']
ARCHIVES=['officialtf2wiki','gilvasunner','supraadarky','supradarky','deoxysprime','dystifymusic','peacheslamb','nintendocomplete','snesost','khinsider','zophar','vgmrips','ostproject','brawlbrstms','videogameost','gamerip','gamesoundtrack','soundtrack','vgm','ostmusic','ostarchive','musicarchive','officialsoundtrack','gamemusic','videogamemusic']
ARCHIVE_IDS={'UCuj7xbym2NGwpizCc13Ub1A','UC4zd43CVepW6h_Fc_HmUVaw','UCegMKhl_pAk1psvSja3sYpw','UCE5EjWAuCFqChJ5GEU6cgzg','UCZCeOBZjL5KNQj5KpSSRDUQ','UCzvn2Xomxqf2znPHSVYP0Ew','UC152XjKOzfYwxW0xFHPgosg','UC7F5TW53jPApb3C_-AyXxig'}
_reviewed_archives=ROOT/'content/expansion/soundtrack-reviewed-archive-channels.json'
if _reviewed_archives.exists():ARCHIVE_IDS.update(json.loads(_reviewed_archives.read_text()).get('entries',{}))
_reviewed_official=ROOT/'content/expansion/soundtrack-reviewed-official-channels.json'
OFFICIAL_IDS=set(json.loads(_reviewed_official.read_text()).get('entries',{})) if _reviewed_official.exists() else set()
# Instrument/genre words alone also occur in genuine original-album cue titles.
# Reject a recording claim (cover/arrangement), not a piano or orchestra itself.
REJECT=re.compile(r'\b(remix|arrangement|arranged|tribute|mashup|nightcore|slowed|sped up|lofi|lo-fi|lullaby|karaoke|reaction|review|medley|8-bit cover|epic version|reimagined)\b|[\[(]\s*cover\s*[\])]|\bcover\s+by\b',re.I)

# Human-reviewed cross-edition conflicts. Metadata may contain a series title while
# the actual album belongs to another game; retain the specific matching edition.
RECORDING_EDITION_ALLOW={
 'QvuuKFjUCNc':{'wikipedia-2146590'},
 'McDARzZIw_I':{'workbook-12-01-rainbow-six-siege'},
 '-32-6FqGW2E':{'wikipedia-65333536'},
 'fQAVUpCGM0I':{'wikipedia-69475062'},
 'fb8Otini3Zk':{'wikipedia-70711554'},
 '5iGoLmFK8jw':{'workbook-10-26-red-dead-redemption-2'},
}
ENTRY_EDITION_HOLDS={'wikipedia-38097022':'2011 Half-Life2 mod:2013 standalone score requires a separate2013 exhibit; original-mod music remains unresolved.'}
RECORDING_REJECT={
 'b5cchtusa0w':'Resident Evil motion-picture soundtrack; not game music',
 'iie76SKXSnk':'Resident Evil motion-picture soundtrack; not game music',
 'BT3ibARJrkU':'Multi-game Prince of Persia trilogy; not the 2008 reboot soundtrack',
 'lWKdsawDSvU':'Special live performance, not the original in-game recording',
 'AYjChqfZBTw':'Lame Genie metal/rock cover, not the original Sonic2 recording',
 'NEtgCLNG20w':'NES port recording, not the1982 Bump and Jump arcade score',
 '98XSpU9fhkE':'ENDWALKER2022 album context; original2010 Answers recording identity unverified',
 'GnyAC84Qnuc':'Whole publication combines Mortal Kombat II and Mortal Kombat I tracklists; cannot select the first game section separately',
 'ogn0gFmd9Ak':'DOOM3 full collection includes opening-theme contributors absent from independently verified ambient-score credits',
 'nuv9YsSeTpE':'Jet Set Radio full collection contains licensed songs whose performers are absent from the selected composer-only credits',
 'TI04brMLXQE':'Composer-issued unreleased outtake, not the original in-game loading theme recording',
 'Fj7_Rb777AM':'Generic PC collection does not distinguish1987AGI score from1991SCI remake recording',
 'KwfgqAG4lj8':'MGS2 full album includes Muranaka song and Iwase underlying main-theme composition absent from current independently verified roster; original piano cue is valid but full collection credits remain incomplete',
 'Ppnsz4l-FoI':'Explicit1995DOS SpecialEdition collection; unchanged1993original recording/platform context not yet established',
 'scsHQiTE6dE':'Tekken2 EmotionlessPassion PlayStation arrangement; original1995arcade recording context not yet established',
}
RECORDING_CONTEXT_EXCEPTIONS={
 'd7V3M2DAq1E':{'entry_id':'wikipedia-25992553','note':'Publisher archive labels this cue [OG] and explicitly states the track was NOT remastered; unchanged2010original recording in a2020collection.','receipt':'build/research/soundtrack-broad/independent-global-manual-findings.json'},
}
def official_version_context(entry_id,v):
 path=ROOT/'content/expansion/soundtrack-official-version-contexts.json'
 if not path.exists():return None
 row=json.loads(path.read_text()).get('entries',{}).get(entry_id+'::'+v.get('youtube_id',''))
 if not row or row.get('status')!='independently_reviewed_same_game_version':return None
 lines=[line.strip() for line in v.get('shortDescription','').splitlines() if line.strip()]
 if v.get('channelId')!=row['channel_id'] or v.get('title')!=row['expected_title']:return None
 if len(lines)<3 or not lines[0].startswith('Provided to YouTube by ') or lines[2]!=row['expected_album']:return None
 return row

def independently_resolved_hold(entry_id,video_id,v):
 path=ROOT/'content/expansion/soundtrack-editorial-recording-holds.json'
 row=json.loads(path.read_text()).get('resolved',{}).get(entry_id+'::'+video_id,{}) if path.exists() else {}
 return row.get('status')=='PASS' and row.get('expected_title')==v.get('title') and row.get('expected_channel_id')==v.get('channelId') and (ROOT/row.get('independent_review_receipt','missing')).is_file()

def recording_identity_policy(video_id,entry_id,v):
 review_path=ROOT/'content/expansion/soundtrack-editorial-recording-holds.json'
 if review_path.exists():
  decision=json.loads(review_path.read_text()).get('entries',{}).get(entry_id+'::'+video_id)
  if decision and not official_version_context(entry_id,{**v,'youtube_id':video_id}):return 'Independent editorial hold ('+decision['status']+'): '+decision['reason']
 if entry_id in ENTRY_EDITION_HOLDS:return ENTRY_EDITION_HOLDS[entry_id]
 if video_id in RECORDING_REJECT:return RECORDING_REJECT[video_id]
 if video_id in RECORDING_EDITION_ALLOW and entry_id not in RECORDING_EDITION_ALLOW[video_id]:return 'Human-reviewed publication belongs to a different game/edition'
 if re.search(r'motion[ -]picture|original television|television soundtrack|television series|HBO original|Netflix original|from the film|from the movie',v.get('title','')+'\n'+v.get('shortDescription',''),re.I):return 'Film/television adaptation rather than original game recording'
 if any(x in norm(v.get('author','')) for x in ['siivagunner','giivagunner','tripleq','gamechops']):return 'Parody or arrangement publication'
 return ''

def album_core(value):
 value=unicodedata.normalize('NFKC',html.unescape(value).replace('™','').replace('®','').replace('©','')).lower()
 roman={'ii':'2','iii':'3','iv':'4','v':'5','vi':'6','vii':'7','viii':'8','ix':'9','x':'10','xi':'11','xii':'12','xiii':'13','xiv':'14','xv':'15','xvi':'16'}
 value=re.sub(r'\b(?:xvi|xv|xiv|xiii|xii|xi|viii|vii|vi|iv|iii|ii|ix|x|v)\b',lambda m:roman[m.group()],value)
 value=re.sub(r'\b(?:original|official|game|video|special|sound\s*track|score|ost|music|from|the music of)\b',' ',value)
 value=re.sub(r'\b(?:vol\.?|volume|part|disc)\s*\d+\b',' ',value)
 value=re.sub(r'\b\d+(?:st|nd|rd|th)\s+anniversary\s+edition\b',' ',value)
 value=re.sub(r'\b(?:selected|special|complete)\s+edition\b',' ',value)
 value=re.sub(r'\bspecial\s+(?=sound\s*track)',' ',value)
 return norm(value)

# Exact album spellings that differ from the exhibit's ordinary English title.
ALBUM_ALIASES={
 'wikipedia-1562965':{'spiderman2themovie','spiderman2themoviegame'}, # Reviewed2004Treyarch game naming, not the film soundtrack.

 'wikipedia-76755904':{'bandletalealeagueoflegendsstory'}, # Full official RiotForge game subtitle, same MaxLL-scored title.

 'wikipedia-4843160':{'pspridgeracer'},
 'wikipedia-74154986':{'likeadragon8'},
 'wikipedia-2146590':{'r4ridgeracertype4'},
 'wikipedia-61416573':{'genshinimpactthewindandthestartraveler','genshinimpactthestellarmoments'},
 'wikipedia-66659306':{'broktheinvestigator'},
 'wikipedia-31125095':{'thewalkingdeadthetell taleseriesseason1pt1'.replace(' ',''),'thewalkingdeadthetell taleseriesseason1pt2'.replace(' ','')},
 'workbook-05-21-senua-s-saga-hellblade-ii':{'senuassagahellblade2'},
 'wikipedia-77133067':{'anno117paxromana'},
 'wikipedia-165824':{'zeldamajorasmask'},
}
def credit_key(value):
 value=unicodedata.normalize('NFKD',html.unescape(value).replace('\u2122','')).encode('ascii','ignore').decode().lower()
 return re.sub(r'[^a-z0-9]','',value.replace('&','and'))

def licensed_recording_context(entry,v):
 description=v.get('shortDescription','')
 if not description.startswith('Provided to YouTube by '):return None
 lines=[x.strip() for x in description.splitlines() if x.strip()]
 if len(lines)<3:return None
 path=ROOT/'content/expansion/soundtrack-licensed-recording-contexts.json'
 if not path.exists():return None
 context=json.loads(path.read_text()).get('entries',{}).get(entry['id'],{})
 for track in context.get('tracks',[]):
  if credit_key(v.get('title',''))==credit_key(track['title']) and credit_key(track['artist']) in credit_key(lines[1]+' '+v.get('author','')) and credit_key(lines[2])==credit_key(track['album']):return {**track,'source_page':context['source_page']}
 return None

def original_recording_context(entry,v):
 exception=RECORDING_CONTEXT_EXCEPTIONS.get(v.get('youtube_id',''))
 if not exception:
  exception=next((value for key,value in RECORDING_CONTEXT_EXCEPTIONS.items() if value['entry_id']==entry['id'] and (RESEARCH/'watch'/(key+'.json')).exists() and json.loads((RESEARCH/'watch'/(key+'.json')).read_text()).get('title')==v.get('title')),None)
 return exception if exception and exception['entry_id']==entry['id'] else None

def recording_work_error(entry,v):
 title=v.get('title','');description=v.get('shortDescription','')
 exception=original_recording_context(entry,v)
 # Sony/VEVO publications often identify the actual game album in a pipe-
 # delimited title rather than a Provided-to-YouTube block. Composer names
 # before the dash must not let a subtitled sequel bypass exact work checks.
 explicit_album=re.search(r'\|\s*([^|]+?)\s*\((?:original|official)(?:\s+(?:video|game))*\s+(?:soundtrack|score)\)',title,re.I)
 if explicit_album and not exception:
  actual=album_core(explicit_album.group(1));wanted=album_core(entry['title'])
  allowed={wanted,wanted+str(entry.get('year',''))}|ALBUM_ALIASES.get(entry['id'],set())
  if actual not in allowed:return 'Explicit publication album names a different game/subtitle: '+explicit_album.group(1).strip()
 # An exact original cue may survive unchanged in a later edition, but only an
 # individually reviewed recording/source exception can establish that fact.
 if not exception and re.search(r'\b(?:remake|remaster(?:ed)?|definitive edition|pixel remaster|boost[ -]?mix|outtake|re[- ]?record(?:ing|ed))\b',title,re.I) and not re.search(r'remake|remaster|definitive',entry['title'],re.I):return 'Recording title explicitly identifies a changed edition, altered mix or outtake'
 if not exception and re.search(r'\b(?:special|spezial) edition\b',title,re.I) and not re.search(r'special edition',entry['title'],re.I):return 'Explicit special game edition requires independently established unchanged original-recording context'
 if re.search(r'\brecreat(?:ed|ion)\b|\breconstructed\b|\bboost[ -]?mix\b|\bunreleased outtake\b',description[:1000],re.I):return 'Publishing description explicitly identifies a reconstruction, altered mix or unreleased outtake'
 if re.search(r'\breconstruct(?:ed|ion)\s+(?:long\s+)?(?:mix|by|with|using)|\brecreat(?:ed|ion)\s+(?:by|with|using)',title,re.I):return 'Title explicitly identifies a reconstructed/recreated mix, not the original recording'
 if re.search(r'(?:first|only)\s+\d+\s+seconds?\s+(?:of\s+)?(?:all|each|every)\s+(?:songs?|tracks?)|(?:soundtrack|song|track)\s+(?:sampler|previews?)',title+'\n'+description[:350],re.I):return 'Short samples/previews of separate songs, not a complete original cue'
 # Inspect the opening music claim, not later SEO tags or remaster advertising.
 opening=next((line for line in description.splitlines()[:4] if re.search(r'soundtrack|\bOST\b|music|track|version',line,re.I) and not re.match(r'\s*(?:purchase|buy|playlist|https?://)',line,re.I)), '')
 if not exception and re.search(r'definitive edition|\bremastered\b|\brearrang(?:ed|ement)\b',opening,re.I) and not re.search(r'remake|remaster|definitive',entry['title'],re.I):return 'Opening publication claim identifies a later rearranged/remastered edition'
 if description.startswith('Provided to YouTube by ') or exception:return ''
 # Reject unlisted subtitled sequels, not only numbered sequels already present
 # in the catalogue. A cue after a spaced dash remains separate from the work.
 segment=re.split(r'\s+[\-\u2013\u2014|]\s+|\s+-\d+-\s+',title,maxsplit=1)[0]
 before=re.split(r'\b(?:OST|sound\s*track|score|BGM)\b',segment,flags=re.I)[0]
 before=re.sub(r'\b(?:full|complete|entire|original|official|game|video|music|HQ|HD|4K)\b',' ',before,flags=re.I)
 before=re.sub(r'\[.*?\]|\(.*?\)|#\s*\d+',' ',before)
 work=album_core(before);wanted=album_core(entry['title'])
 if wanted and work.startswith(wanted):
  suffix=work[len(wanted):]
  suffix=re.sub(r'^(?:i|1)(?=(?:19|20)\d{2}|$)','',suffix)
  suffix=re.sub(r'^(?:19|20)\d{2}','',suffix)
  cue=bool(re.match(r'(?:themesong|maintheme|mainmenu|grandprixmode|timetrialmenu|\d{2}[^0-9])',suffix))
  platform=suffix in {'ps1','psx','ps2','ps3','ps4','ps5','psp','pc','nes','snes','n64','gba','gb','nds','wii','arcade','genesis','megadrive','saturn','dreamcast','amiga','msdos','dos','pcengine','turbografx16'}
  if suffix and not cue and not platform and work not in ALBUM_ALIASES.get(entry['id'],set()):return 'Publication work has an additional sequel/subtitle rather than the exact game: '+before.strip()
 # Multiple structured work headings denote an indivisible cross-game file.
 headings=re.findall(r'(?im)^\s*(?:music|soundtrack|OST|score)\s+(?:from|of|for)\s+([^\n:]+)\s*:\s*$',description)
 identities={album_core(x) for x in headings if album_core(x)}
 if len(identities)>1:return 'Whole publication contains separately headed soundtracks from multiple games: '+', '.join(headings)
 otherworld=re.search(r'(?im)^.*(?:terraria\s*:?\s*otherworld|music from mortal kombat(?:\s*1|\s*I)?\s*:).*$' ,description)
 if otherworld and album_core(otherworld.group())!=wanted:return 'Whole publication includes a separately identified other-game album or tracklist'
 return ''

def published_music_credits(v):
 names=[]
 for line in v.get('shortDescription','').splitlines():
  # Delivered labels place Composer anywhere in a comma-delimited role list,
  # e.g. 'Composer, Studio Personnel, Programming: Brian Lee White'. Reading
  # only 'Composer:' silently loses genuine coauthors in these publications.
  prefix,separator,value=line.partition(':')
  role_list=bool(separator and len(prefix)<230 and any(re.fullmatch(r'composer(?:s|\(s\))?(?:\s*lyricist(?:s|\(s\))?)?',role.strip(),re.I) for role in prefix.split(',')))
  if role_list:line='Composer: '+value
  match=re.search(r'(?:^|\b)(?:composer(?:s|\(s\))?\s*:|composed by\s*:?[ ]*|music by\s*:?[ ]*|music composed by\s*:?[ ]*|score by\s*:?[ ]*)(.+)',line,re.I)
  if not match:continue
  clause=re.split(r'\.(?:\s|$)|\b(?:for the|from the|released|published|performed|copyright|all rights|soundtrack for|feat\.?|featuring)\b|\s+in\s+(?:19|20)\d{2}',match.group(1),maxsplit=1,flags=re.I)[0]
  clause=re.sub(r'^both\s+','',clause,flags=re.I)
  if re.search(r'\b(?:the score|blends|capturing|reflective|forming|haunting|combin(?:ing|es)|featur(?:ing|es)|consists|melodic|soundscapes)\b',clause,re.I):continue
  clause=re.sub(r'\s*\((?:DOS|PC|Macintosh|3DO|PlayStation|NES|Arcade)[^)]*\)','',clause,flags=re.I)
  for name in re.split(r'\s*(?:,|;|&|\band\b|\bwith\b)\s*',clause):
   name=name.strip(' .:-()')
   if 2<len(name)<80 and len(name.split())<=7 and not re.search(r'https?://|unknown|not credited|n/a|originally|\bgame\b|\bsoundtrack\b',name,re.I) and name not in names:names.append(name)
 return names

def recording_artists(v):
 description=v.get('shortDescription','')
 if not description.startswith('Provided to YouTube by '):return []
 lines=[x.strip() for x in description.splitlines() if x.strip()]
 if len(lines)<2:return []
 return list(dict.fromkeys(x.strip() for x in lines[1].split('\u00b7')[1:] if x.strip()))

def additional_credit_findings(entry):
 path=ROOT/'content/expansion/soundtrack-composer-credit-completeness-extra.json'
 return json.loads(path.read_text()).get('entries',{}).get(entry['id'],{}) if path.exists() else {}

def music_credit_completeness_error(entry,v,composers):
 if licensed_recording_context(entry,v):return ''
 findings=additional_credit_findings(entry)
 if entry['id']=='workbook-02-20-the-order-1886' and 'theknightstheme' not in norm(v.get('title','')):return 'Primary composer/publisher source assigns Wintory only The Knights Theme; album-wide repeated label credits cannot identify other cue authorship'
 if entry['id']=='wikipedia-28344576' and int(v.get('lengthSeconds') or 0)>1200:return 'BioShock Infinite full collection requires separate licensed-song and arranged-song credits; select an individually credited original-score cue'
 scope_path=ROOT/'content/expansion/soundtrack-composer-source-overrides-third.json'
 if scope_path.exists():
  scope=json.loads(scope_path.read_text()).get('entries',{}).get(entry['id'],{})
  if scope.get('track_titles') and not any(credit_key(title) in credit_key(v.get('title','')) for title in scope['track_titles']):return 'Primary source verifies only specifically named recordings; another cue requires its own author/recording context'
 declared=published_music_credits(v)
 # Some archive titles identify the actual cue artist although the description
 # contains no formal Composer field. Never replace that artist with the game's
 # unrelated menu-score composer merely because the game/year match.
 named=re.search(r'\b(?:OST|soundtrack)\s*:\s*([^\n:|]+?)\s+[\-\u2013\u2014]\s+',v.get('title',''),re.I)
 if named:
  title_artist=named.group(1).strip()
  if 1<len(title_artist)<65 and not re.search(r'\b(?:full|complete|official|track|vol|disc|original)\b',title_artist,re.I):declared.append(title_artist)
 if not declared:return ''
 independent=' '.join(composers)
 group_path=ROOT/'content/expansion/soundtrack-reviewed-cue-group-credits.json'
 if group_path.exists():
  reviewed=json.loads(group_path.read_text()).get('entries',{}).get(entry['id'],{})
  for vid,scope in reviewed.items():
   if scope.get('title')==v.get('title') and norm(scope.get('group','')) in norm(independent) and (ROOT/scope['independent_review_receipt']).exists():
    expected=scope.get('composer_names',[])
    if {credit_key(x) for x in declared}=={credit_key(x) for x in expected}:independent+=' '+' '.join(expected)
 unmatched=[]
 for name in declared:
  name=findings.get('aliases',{}).get(name,name)
  aliases=[name]+re.findall(r'\(([^)]+)\)',name)
  covered=any(norm(alias) and norm(alias) in norm(independent) for alias in aliases)
  if not covered:
   words=re.findall(r'[A-Za-z]+',unicodedata.normalize('NFKD',name).encode('ascii','ignore').decode())
   covered=len(words)>=2 and len(words[0])>=3 and len(words[-1])>=3 and norm(words[0]) in norm(independent) and norm(words[-1]) in norm(independent)
  if not covered:unmatched.append(name)
 if unmatched:return 'Published music-role contributor not covered by independently verified game credits: '+', '.join(unmatched)
 return ''

def album_identity_error(entry,v):
 title=v.get('title','');description=v.get('shortDescription','');uploader=norm(v.get('author',''))
 work_error=recording_work_error(entry,v)
 if work_error:return work_error
 if re.search(r'arrang(?:ement|ed) by|cover by|recreated (?:in|with|using)|reconstruction|soundfont|orchestral rendition|my (?:own )?version|fan-made (?:song|music)|re-engineer|ai.generated|artificial intelligence',description[:900],re.I):return 'Description identifies a reinterpretation/reconstruction rather than the original game recording'
 if re.search(r'\b(?:covers?|remixes|arrangements|parody|mashups)\b',v.get('author',''),re.I):return 'Uploader explicitly publishes cover/remix/arrangement recordings'
 if re.search(r'\b(?:metal|rock|jazz|saxophone|acoustic|guitar|orchestral|chiptune)\s+(?:version|cover|arrangement)\b',title,re.I):return 'Explicit re-recorded genre version'
 if re.search(r'\b(?:rock|metal|piano|guitar|orchestral|jazz|acoustic) cover\b|\b(?:this|our|my|huge)(?: is)?(?: a)? cover\b|(?:^|\n)\s*cover\s+(?:of|by)\b',description[:1000],re.I):return 'Description explicitly identifies a cover recording'
 if any(x in uploader for x in ['geekmusic','andrewsk eet'.replace(' ',''),'londonphilharmonic','videogameslive','gamechops','stringplayergamer','silvagunner','siivagunner','tripleq']):return 'Cover/concert/parody recording artist rather than original game recording'
 if re.search(r'\binterview\b|\bgameplay\b|\btrailer\b|\btrilogy\b|\banthology\b|\bcompilation\b|\barrange(?:d|ment)?\b|re-engineered|pre-console mix|symphony world tour|relaxing soundtrack',title,re.I):return 'Non-original recording, compilation, editorial video or alternate mix'
 lines=[x.strip() for x in description.splitlines() if x.strip()]
 if licensed_recording_context(entry,v):return ''
 if not description.startswith('Provided to YouTube by '):return ''
 if len(lines)<3:return 'Delivered recording lacks complete album identity'
 album=lines[2]
 if re.search(r'greatest video game|piano collections|distant worlds|jazz|\b(?:remake|remaster(?:ed)?|definitive edition|connected|concert|symphon(?:y|ic)|orchestral)\b',album,re.I) and not any(x in entry['title'].lower() for x in ['remake','remaster','definitive','connected']):return 'Later remake, enhanced edition or arranged/concert album'
 wanted=album_core(entry['title']);actual=album_core(album)
 allowed={wanted,wanted+str(entry.get('year',''))}|ALBUM_ALIASES.get(entry['id'],set())
 if actual not in allowed:return 'Original album identity is not exact exhibit edition: '+album
 return ''

def archive_identity_signals(entry,v):
 title=v.get('title','');description=v.get('shortDescription','');lead='\n'.join(description.splitlines()[:18])[:1400]
 game=album_core(entry['title']);game_names={game}|ALBUM_ALIASES.get(entry['id'],set());title_identity=any(name in album_core(title) for name in game_names)
 explicit_game=any(re.match(r'\s*(?:Game|Game title|Album|Soundtrack|Source)\s*:',line,re.I) and any(name in album_core(line.split(':',1)[1]) for name in game_names) for line in description.splitlines()[:18])
 if not title_identity and not explicit_game:return []
 signals=['exact_game_in_recording_title' if title_identity else 'explicit_game_field_in_recording_metadata']
 if re.search(r'\b'+str(entry['year'])+r'\b',title+'\n'+lead):signals.append('original_release_year_in_recording_metadata')
 first_sentence=(entry.get('summary','')+' '+(' '.join(entry.get('body',[])[:1]))).split('. ')[0]
 platforms=[r'gamecube',r'nintendo 64',r'\bn64\b',r'\bnes\b',r'famicom',r'super nintendo',r'\bsnes\b',r'\bsfc\b',r'game boy advance',r'\bgba\b',r'game boy',r'nintendo ds',r'\bnds\b',r'nintendo 3ds',r'wii(?! u)',r'wii u',r'playstation 5',r'\bps5\b',r'playstation 4',r'\bps4\b',r'playstation 3',r'\bps3\b',r'playstation 2',r'\bps2\b',r'playstation(?!\s*[2345])',r'\bps1\b',r'\bpsx\b',r'ps vita',r'\bpsp\b',r'dreamcast',r'saturn',r'mega drive',r'genesis',r'master system',r'game gear',r'commodore 64',r'\bc64\b',r'amiga',r'atari 2600',r'arcade',r'ms-dos',r'\bdos\b',r'windows',r'pc engine',r'turbografx']
 platforms.extend([r'nintendo entertainment system',r'\barcades?\b'])
 aliases={'nintendo entertainment system':['nes','famicom'],'nintendo 64':['n64'],'super nintendo':['snes','sfc'],'gamecube':['gamecube','ngc'],'playstation 2':['ps2'],'playstation 3':['ps3'],'playstation 4':['ps4'],'playstation 5':['ps5'],'playstation(?!\\s*[2345])':['ps1','psx'],'nintendo ds':['nds'],'game boy advance':['gba'],'game boy':['gb'],'mega drive':['genesis'],'windows':['pc']}
 for platform in platforms:
  if re.search(platform,first_sentence,re.I) and (re.search(platform,title+'\n'+lead,re.I) or any(re.search(r'\b'+a+r'\b',title+'\n'+lead,re.I) for a in aliases.get(platform,[]))):signals.append('independently_matched_original_platform');break
 if len(TITLE_YEARS.get(norm(entry['title']),set()))>1 and 'original_release_year_in_recording_metadata' not in signals:return []
 return signals

def archive_declared_game_error(entry,v):
 if v.get('shortDescription','').startswith('Provided to YouTube by '):return ''
 match=re.search(r'(?im)^\s*Game(?: title)?\s*:\s*(.+)',v.get('shortDescription',''))
 if not match:return ''
 actual=album_core(match.group(1));wanted=album_core(entry['title'])
 allowed={wanted,wanted+str(entry['year'])}|ALBUM_ALIASES.get(entry['id'],set())
 if actual not in allowed:return 'Explicit archival Game field disagrees with the exhibit: '+match.group(1)
 return ''

def archive_platform_conflict(entry,v):
 if official_version_context(entry['id'],v):return ''
 desc=v.get('shortDescription','');title=v.get('title','')
 declaration=re.search(r'(?im)^[^A-Za-z\n]*platform(?:s|\(s\))?\s*:\s*(.*)$',desc[:1800])
 standalone=next((line.strip() for line in desc.splitlines()[:18] if re.fullmatch(r'\s*(?:NES|SNES|SFC|N64|GameCube|NGC|Game Gear|GG|Mega Drive|Genesis|Master System|SMS|PS1|PSX|PS2|PS3|PS4|PS5|PSP|PC|Windows|DOS|MS-DOS|Amiga|MSX2?|X68000|Arcade|Game Boy(?: Advance| Color)?|GBA|GB|Nintendo DS|NDS|Nintendo 3DS|Wii U|Wii|Dreamcast|Saturn)(?:\s*[/|,]\s*(?:NES|SNES|SFC|N64|GameCube|PS1|PSX|PS2|PS3|PS4|PS5|PSP|PC|Windows|Wii|Game Gear|GG))*\s*',line,re.I)), '')
 title_platforms=' '.join(a or b for a,b in re.findall(r'\(([^)]*)\)|\[([^\]]*)\]',title))
 published=(declaration.group(1) if declaration else standalone)+' '+title_platforms
 if not published.strip():return ''
 source=(entry.get('summary','').split('. ')[0]+' '+(' '.join(entry.get('body',[])[:1])).split('. ')[0])
 groups={
  'arcade':r'\barcades?\b',
  'nes':r'(?<!super )\bnes\b|(?<!super )(?<!super-)(?:nintendo entertainment system|famicom)',
  'snes':r'\bsnes\b|super nes|super nintendo|super famicom|\bsfc\b',
  'genesis':r'mega drive|genesis',
  'master_system':r'master system|\bsms\b',
  'game_gear':r'game gear|\bgg\b',
  'game_boy_advance':r'game boy advance|\bgba\b',
  'game_boy':r'game boy(?! advance| color)|\bgb\b',
  'nintendo_64':r'nintendo 64|\bn64\b',
  'gamecube':r'gamecube|\bngc\b',
  'playstation_2':r'playstation 2|\bps2\b',
  'playstation':r'playstation(?!\s*[2345])|\bps1\b|\bpsx\b',
  'playstation_3':r'playstation 3|\bps3\b',
  'playstation_4':r'playstation 4|\bps4\b',
  'playstation_5':r'playstation 5|\bps5\b',
  'psp':r'playstation portable|\bpsp\b',
  'nintendo_ds':r'nintendo ds|\bnds\b',
  'nintendo_3ds':r'nintendo 3ds|\b3ds\b',
  'wii':r'\bwii(?! u)\b',
  'wii_u':r'\bwii u\b',
  'computer':r'\bwindows\b|\bpc\b|\bms-dos\b|\bdos\b',
  'amiga':r'\bamiga\b',
  'msx':r'\bmsx2?\b',
  'x68000':r'\bx68000\b|\bx68k\b',
  'dreamcast':r'dreamcast',
  'saturn':r'\bsaturn\b',
 }
 expected={k for k,pattern in groups.items() if re.search(pattern,source,re.I)}
 actual={k for k,pattern in groups.items() if re.search(pattern,published,re.I)}
 if len(expected)==1 and actual and expected.isdisjoint(actual):return 'Archive explicitly identifies a different platform/port: '+published+'; original exhibit platform '+next(iter(expected))
 return ''

def primary_version_authority(entry,v):
 path=ROOT/'content/expansion/soundtrack-composer-source-overrides-fourth.json'
 if not path.exists():return None
 row=json.loads(path.read_text()).get('entries',{}).get(entry['id'],{})
 if not row.get('recording_version'):return None
 return row

def consider(entry,row,composers,composer_url):
 id=row.get('id','');title=row.get('title','');desc=row.get('description') or '';reason=''
 if not re.fullmatch('[A-Za-z0-9_-]{11}',id):return None,'Invalid video ID'
 if REJECT.search(title):return None,'Arrangement/cover/non-original title'
 if any(w in norm(row.get('channel','')) for w in ['siivagunner','giivagunner','tripleq','gamechops']):return None,'Arrangement/parody publication'
 flat_channel=norm(row.get('channel',''));flat_description=row.get('description') or ''
 plausible=(row.get('channel_id') in ARCHIVE_IDS|OFFICIAL_IDS or (flat_channel.endswith('topic') or flat_channel.endswith('ost')) or flat_description.startswith('Provided to YouTube by ') or any(flat_channel==norm(x) for x in OFFICIAL_NAMES) or any(x in flat_channel for x in ARCHIVES) or any(norm(name)==flat_channel for name in composers))
 if not plausible:return None,'Search publisher is not identifiable official delivery or soundtrack archive'

 try:v=watch(id)
 except Exception as ex:return None,'Watch metadata unavailable: '+str(ex)
 if v.get('status')!='OK':return None,'Watch publication not currently available: '+v.get('status','unknown')
 v={**v,'youtube_id':id}
 version_authority=primary_version_authority(entry,v)
 if version_authority:
  years=[int(y) for y in re.findall(r'(?im)(?:Released on:|Release(?:d)?(?:year)?\s*:)\s*((?:19|20)\d{2})',v['shortDescription'])]
  if not years or max(years)<version_authority['minimum_recording_year']:return None,'Primary composer source applies only to explicitly identified later official game edition; original recording cannot inherit those credits'
 identity_error=recording_identity_policy(id,entry['id'],v) or archive_declared_game_error(entry,v) or album_identity_error(entry,v) or archive_platform_conflict(entry,v) or music_credit_completeness_error(entry,v,composers)
 if identity_error:return None,identity_error
 title=v['title'];description=v['shortDescription'];uploader=v['author'];full=title+'\n'+description
 if REJECT.search(title):return None,'Arrangement/cover/non-original title'
 if any(w in norm(uploader) for w in ['siivagunner','giivagunner','tripleq','gamechops']):return None,'Parody or arrangement channel, regardless of copied game credits'
 licensed_context=licensed_recording_context(entry,v)
 game=norm(entry['title']);body=norm(full)
 short_identity=len(game)<4 and not re.search(r'(?<![A-Za-z0-9])'+re.escape(entry['title'])+r'(?![A-Za-z0-9])',full,re.I)
 if short_identity or (not licensed_context and game not in body and album_core(entry['title']) not in album_core(full) and not any(a in body for a in ALBUM_ALIASES.get(entry['id'],set()))):return None,'Game identity is absent from actual publishing description'
 if re.search(r'motion[ -]picture|original television|television soundtrack|television series|HBO original|Netflix original|from the film|from the movie',full,re.I):return None,'Film/television adaptation rather than game score'
 if re.search(r'\btrilogy\b|\banthology\b|\bcompilation\b',title,re.I) and not re.search(r'trilogy|anthology|compilation',entry['title'],re.I):return None,'Multi-game compilation is not an exact game score'
 # Prevent prequel/numbered-sequel matches hidden by prefix matching.
 # Token-aware work identity and the catalogue's complete sequel titles are
 # checked separately; joining game+"v" also falsely matches a cue named Vega.
 duration=int(v.get('lengthSeconds') or 0)
 if not 20<=duration<=14400:return None,'Not a bounded music recording'
 provided=description.startswith('Provided to YouTube by ')
 publishing=norm(uploader);pubofficial=v.get('channelId') in OFFICIAL_IDS or (bool(row.get('channel_is_verified')) and any(publishing==norm(x) for x in OFFICIAL_NAMES))
 pubofficial=pubofficial or bool(row.get('channel_is_verified') and any(norm(name).removesuffix('inc') in publishing for name in composers))
 # A Topic name alone is not proof of original recording: require game OST album evidence.
 original_album=bool(re.search(r'original\s+(?:game\s+)?(?:sound\s*track|score)|official\s+(?:game\s+)?sound\s*track',description,re.I))
 album_lines=[line.strip() for line in description.splitlines() if line.strip()]
 if provided and len(album_lines)>2 and re.search(r'sound\s*track|\bscore\b',album_lines[2],re.I) and not album_identity_error(entry,v):original_album=True
 explicit_composer=bool(published_music_credits(v))
 if provided and not original_album and not explicit_composer and not licensed_context:return None,'Label delivery lacks original-game album/credits evidence'
 musical=provided or bool(re.search(r'\b(?:OST|soundtrack|score|theme|music)\b',full,re.I))
 if not musical:return None,'Publication is not identified as music'
 if pubofficial or (provided and (original_album or explicit_composer or licensed_context)):kind='official_game_recording'
 elif v.get('channelId') in ARCHIVE_IDS or any(x in publishing for x in ARCHIVES) or publishing.endswith('ost') or any(norm(name)==publishing for name in composers):kind='archival_game_recording'
 else:return None,'Uploader is neither verified publisher/artist delivery nor identifiable soundtrack archive'
 if not composers:return None,'No independent composer credit yet'
 if kind=='archival_game_recording' and len(archive_identity_signals(entry,v))<2:return None,'Archive publication requires an exact game title/field plus independently matched original releaseyear or platform'
 matched=[]
 credit_lines=[line for line in description.splitlines() if re.search(r'compos(?:er|ed)|music\s+(?:by|compos)|score\s+by|written\s+by|soundtrack\s+by',line,re.I)]
 # A game-wide composer who appears only as this cue's producer must not
 # become its composer. Prefer explicit delivered composition-role fields;
 # keep performer/producer artists separately without inventing their role.
 declared_music_roles=published_music_credits(v)
 credit_context=(' '.join(declared_music_roles) if declared_music_roles else (album_lines[1] if provided and len(album_lines)>1 else '\n'.join(credit_lines)+' '+uploader+' '+(title if pubofficial or re.search(r'soundtrack.*\bby\b|music.*\bby\b',title,re.I) else '')))
 for name in composers:
  if name in ['PlayStation','NES','NES/Famicom','Amiga','Arcade'] or (re.search(r'\((?:remake|remaster)\)',name,re.I) and not re.search(r'remake|remaster',entry['title'],re.I)):continue
  aliases=[re.sub(r'\s*\([^)]*\)','',name)]+re.findall(r'\(([^)]+)\)',name)+({'Robert Prince':['Bobby Prince'],'Danny Baranowsky':['Daniel Baranowsky'],'David García':['David Garcia Diaz']}.get(name,[]))
  # Parenthesized publication credits are real people, whereas game-title
  # normalization intentionally removes parentheses. Keep them for authors.
  if any(credit_key(alias).removesuffix('inc').removesuffix('llc') and credit_key(alias).removesuffix('inc').removesuffix('llc') in credit_key(credit_context+' '+uploader) for alias in aliases):matched.append(name)
  else:
   words=re.findall(r'[A-Za-z]+',unicodedata.normalize('NFKD',name).encode('ascii','ignore').decode())
   if len(words)>=2 and len(words[0])>=3 and len(words[-1])>=3 and credit_key(words[0]) in credit_key(credit_context) and credit_key(words[-1]) in credit_key(credit_context):matched.append(name)
 if not matched:
  branded_artist=provided and original_album and (publishing.removesuffix('topic')==game or (len(game)>=6 and publishing.removesuffix('topic').startswith(re.sub(r'\d+$','',game))))
  archive_signals=archive_identity_signals(entry,v) if kind=='archival_game_recording' else []
  if branded_artist:return None,'Game-title label brand is not an independently identified cue composer; individual composition/recording authorship needs a source'
  if len(archive_signals)<2:return None,'Neither independently matched music-role credit nor two strong original-game archive identity signals'
  if len(archive_signals)>=2:matched=list(composers)
  # Exact game/publisher album delivery is credited as a sound-team recording; individual track authorship is not invented.
  if not matched:return None,'No independently matched composition credit for this official recording'
 years=TITLE_YEARS.get(game,set())
 released=re.search(r'Released on:\s*((?:19|20)\d{2})',description)
 if len(years)>1 and released:
  recording_year=int(released.group(1))
  if abs(recording_year-entry['year'])>1:return None,'Ambiguous same-title edition/reissue: original recording year not demonstrated'

 # Later remakes/remasters are distinct exhibits, never silent substitutes.
 wanted=entry['title'].lower()
 if any(x in title.lower() for x in ['remake','remaster','pixel remaster','definitive edition']) and not any(x in wanted for x in ['remake','remaster','definitive']) and not original_recording_context(entry,v):return None,'Later remaster/remake recording'
 if original_album and re.search(r'Piano Collections|Distant Worlds|\bremix album\b|\bcover album\b',description,re.I):return None,'Album metadata declares arrangement rather than original recording'
 url='https://www.youtube.com/watch?v='+id
 if version_authority:title=title+' (Steam edition)'
 artists=recording_artists(v);contributors=list(dict.fromkeys(matched))
 # Keep full label artist metadata separately. A publisher/project brand,
 # performer or producer is not automatically another cue composer in Music by.
 return {'youtube_id':id,'url':url,'title':title,'creator':', '.join(contributors),'independently_matched_composers':matched,'label_credited_recording_artists':artists,'artist_credit_scope':'Publication artist credits retained without assigning unspecified performer/arranger/producer names a composer role.','composer_source':composer_url,'game_music_context_source':licensed_context['source_page'] if licensed_context else '', 'original_recording_context':original_recording_context(entry,v) or {},'recording_version':version_authority.get('recording_version','') if version_authority else '', 'recording_context_source':version_authority.get('source_page','') if version_authority else '','uploader':uploader,'channel_url':'https://www.youtube.com/channel/'+v['channelId'],'source_page':url,'verification_url':url,'official_uploader_verified':kind=='official_game_recording','publishing_kind':kind,'duration_seconds':duration,'rights':'Original composition and recording rights remain with the game composer, publisher and recording owner. Archival uploaders are credited without implying official endorsement.','verified_on':STAMP,'verification_method':'Actual YouTube publication/player game/album identity, uploader provenance and independently sourced game composer credits; metadata verification only.','playback_verified_on_ps5':False,'verification_receipt':(RESEARCH/'watch'/(id+'.json')).relative_to(ROOT).as_posix(),'channel_research_receipt':('build/research/soundtrack-broad/channels/'+v['channelId']+'.json') if v['channelId'] in ARCHIVE_IDS else ''},''

def clean_composer_names(names,title):
 out=[]
 for name in names:
  if name in ['PlayStation','NES','NES/Famicom','Amiga','Arcade','MS-DOS','Windows','PC','SNES','Famicom']:continue
  if re.search(r'\((?:remake|remaster)\)',name,re.I) and not re.search(r'remake|remaster',title,re.I):continue
  name=re.sub(r'\s*\((?:Arcade|PlayStation|NES|Famicom|MS-DOS|Macintosh|3DO|PS|Fantastic Worlds)\)','',name,flags=re.I).strip()
  if name and name not in out:out.append(name)
 return out

def source_searches(entry):
 for filename in ['soundtrack-composer-source-overrides-third.json','soundtrack-composer-source-overrides-primary.json','soundtrack-composer-source-overrides-extra.json']:
  path=ROOT/'content/expansion'/filename
  if path.exists():
   row=json.loads(path.read_text()).get('entries',{}).get(entry['id'],{})
   if row.get('recording_searches'):return row['recording_searches'][:3]
   if row.get('track_titles') and row.get('composers'):return [entry['title']+' '+row['composers'][0]+' '+title+' original soundtrack' for title in row['track_titles'][:3]]
 return []

def source_candidate_ids(entry):
 path=ROOT/'content/expansion/soundtrack-composer-source-overrides-primary.json'
 if path.exists():return json.loads(path.read_text()).get('entries',{}).get(entry['id'],{}).get('candidate_youtube_ids',[])
 return []

def selected_music_credit(tracks,fallback):
 names=[]
 for track in tracks:
  for name in track.get('creator','').split(', '):
   if name and name not in names:names.append(name)
 return ', '.join(names or fallback)

def process(entry,retry=False,retry_pending=False):
 path=RESEARCH/'games'/(entry['id']+'.json')
 if path.exists() and not retry:
  old=json.loads(path.read_text())
  if old.get('pipeline_version')==PIPELINE_VERSION and (not retry_pending or old.get('state') in ['admitted','excluded_no_original_score']):return old
 key=norm(entry['title']);audit={'pipeline_version':PIPELINE_VERSION,'entry_id':entry['id'],'title':entry['title'],'year':entry['year'],'checked':STAMP,'state':'research_pending','candidates':[]}
 if key in SILENT:
  audit.update(state='excluded_no_original_score',reason=SILENT[key]);write(path,audit);return audit
 composers,source,evidence=composer(entry);composers=clean_composer_names(composers,entry['title']);audit.update(composers=composers,composer_source=source,composer_evidence=evidence)
 if not composers:
  audit.update(state='composer_research_required',reason='No verified game composer extracted; not replaced by uploader name.');write(path,audit);return audit
 rows=[];tracks=[]
 for candidate_id in source_candidate_ids(entry):
  try:
   v=watch(candidate_id);row={'id':candidate_id,'title':v['title'],'channel':v['author'],'channel_id':v['channelId'],'description':v['shortDescription']};track,reason=consider(entry,row,composers,source);rows.append(row)
   audit['candidates'].append({'youtube_id':candidate_id,'title':v['title'],'uploader':v['author'],'accepted':bool(track),'reason':reason,'research_route':'Primary-source exact recording candidate'})
   if track:tracks.append(track)
  except Exception as error:audit['candidates'].append({'youtube_id':candidate_id,'reason':str(error)})
 for query in source_searches(entry)+[entry['title']+' original soundtrack official Topic',entry['title']+' OST '+composers[0],entry['title']+' '+str(entry['year'])+' original main theme game soundtrack']:
  try:found=search(query)
  except Exception as ex:audit['candidates'].append({'query':query,'reason':'Search unavailable: '+str(ex)});continue
  for row in found:
   if row['id'] in {r['id'] for r in rows}:continue
   rows.append(row);track,reason=consider(entry,row,composers,source)
   audit['candidates'].append({'youtube_id':row['id'],'title':row.get('title'),'uploader':row.get('channel'),'accepted':bool(track),'reason':reason})
   if track:tracks.append(track)
   if len(tracks)>=3:break
  if len(tracks)>=2:break
 if tracks:
  # Prefer individual official recordings to full-album archival files.
  tracks.sort(key=lambda t:(not t['official_uploader_verified'],t['duration_seconds']>1200))
  individual=[t for t in tracks if t['duration_seconds']<=1200]
  if individual:tracks=individual
  tracks=tracks[:3];names=selected_music_credit(tracks,composers)
  audit.update(state='admitted',selection={'entry_id':entry['id'],'match_title':entry['title'],'match_year':entry['year'],'title':'Listen to '+entry['title'],'composer':names,'curator_note':f'Listen to music by {names} from {entry["title"]}.','tracks':tracks})
 else:audit.update(state='recording_research_required',reason='No qualifying original recording verified in this search pass; absence of research evidence is not a claim that the game has no music.')
 write(path,audit);return audit

def final_identity_gate(record,all_games):
 selection=copy.deepcopy(record['selection']);game=norm(selection['match_title']);accepted=[];seen=set();holds=[]
 sequels=[norm(e['title']) for e in all_games if norm(e['title'])!=game and game in norm(e['title']) and len(norm(e['title']))>len(game)]
 expansion_works={
  'eldenring':['shadow of the erdtree'],'cyberpunk2077':['phantom liberty'],
  'thewitcher3wildhunt':['blood and wine','hearts of stone'],'outerwilds':['echoes of the eye'],
  'darksouls3':['the ringed city','ashes of ariandel'],'bloodborne':['the old hunters'],
  'horizonzerodawn':['the frozen wilds'],'horizonforbiddenwest':['burning shores'],
  'destiny2':['the final shape'],'finalfantasy14':['endwalker','a realm reborn','heavensward','stormblood','shadowbringers','dawntrail'],
  'xenobladechronicles':['definitive edition'],'xenobladechronicles2':['torna the golden country'],
  'splatoon2':['octo expansion'],'splatoon3':['side order'],
  'terraria':['otherworld'],'diablo':['hellfire'],'diablo2':['lord of destruction'],
  'warcraft2tidesofdarkness':['beyond the dark portal'],
 }
 expansions=expansion_works.get(album_core(selection['match_title']),[])
 for track in selection['tracks']:
  receipt=RESEARCH/'watch'/(track['youtube_id']+'.json')
  if not receipt.exists():holds.append({'youtube_id':track['youtube_id'],'reason':'Missing publication receipt'});continue
  v={**json.loads(receipt.read_text()),'youtube_id':track['youtube_id']};description=v.get('shortDescription','');lines=[l.strip() for l in description.splitlines() if l.strip()]
  actual_entry=next((e for e in all_games if e.get('id')==record['entry_id']),{'id':record['entry_id'],'title':selection['match_title'],'year':selection['match_year']})
  policy=recording_identity_policy(track['youtube_id'],record['entry_id'],v) or archive_declared_game_error(actual_entry,v) or album_identity_error(actual_entry,v) or archive_platform_conflict(actual_entry,v) or music_credit_completeness_error(actual_entry,v,record.get('composers',[]))
  if policy:holds.append({'youtube_id':track['youtube_id'],'reason':policy});continue
  album=lines[2] if description.startswith('Provided to YouTube by ') and len(lines)>2 else ''
  work_identity=norm(v.get('title','')+' '+album)
  if album and re.search(r'Piano Collections|Distant Worlds|SQUARE ENIX JAZZ|\b(?:cover|remix|tribute|orchestral|symphonic|lullaby|lofi|lo-fi)\b',album,re.I):holds.append({'youtube_id':track['youtube_id'],'reason':'Published album is an arrangement/tribute rather than original score'});continue
  mismatch=next((other for other in sequels if other in work_identity),None)
  if mismatch and not original_recording_context(actual_entry,v):holds.append({'youtube_id':track['youtube_id'],'reason':'Specific sequel/subtitle appears in publication identity: '+mismatch});continue
  expansion=next((name for name in expansions if norm(name) in norm(album+' '+v.get('title','')) and norm(name) not in game),None)
  if expansion and not original_recording_context(actual_entry,v):holds.append({'youtube_id':track['youtube_id'],'reason':'Different expansion score: '+expansion});continue
  title_key=norm(v.get('title','').split('|')[0]).replace(game,'')
  if title_key in seen:holds.append({'youtube_id':track['youtube_id'],'reason':'Duplicate song via another publishing URL'});continue
  seen.add(title_key)
  track['creator']=track['creator'].replace(' (game sound team recording)','')
  accepted.append(track)
 selection['tracks']=accepted
 if accepted:
  selection['composer']=selected_music_credit(accepted,record.get('composers',[]))
  selection['curator_note']=f'Listen to music by {selection["composer"]} from {selection["match_title"]}.'
 return selection,holds

def assemble():
 records=[]
 for p in sorted((RESEARCH/'games').glob('*.json')):
  try:
   record=json.loads(p.read_text())
   if record.get('pipeline_version')==PIPELINE_VERSION:records.append(record)
  except Exception:pass
 catalog=json.loads((ROOT/'content/catalog.json').read_text());all_games=(catalog if isinstance(catalog,list) else catalog['entries'])
 entries=[];identity_holds=[]
 for record in records:
  if record.get('state')!='admitted':continue
  selection,holds=final_identity_gate(record,all_games)
  if selection['tracks']:entries.append(selection)
  if holds:identity_holds.append({'entry_id':record['entry_id'],'tracks':holds})
 states={}
 for r in records:states[r['state']]=states.get(r['state'],0)+1
 output={'schema_version':1,'publication_status':'auditing','validation_scope':'Publishing metadata, exact album/edition identity, independent composer credits; archives additionally require original year/platform evidence when track credits are absent. Duplicate-song filtering. Not an audio-fingerprint or PS5-playback assertion.','verified_on':STAMP,'policy':'Original game music on publisher/artist/label-delivered publications or explicitly credited soundtrack archives. No audio or video is downloaded. Composer credits are independently sourced; archival uploads are never labeled official. Remixes and known later remakes are rejected. Metadata checking does not assert PS5 playback or audio fingerprint verification.','entries':entries}
 write(ROOT/'content/expansion/soundtrack-broad-research-selections.json',output)
 write(ROOT/'content/expansion/soundtrack-broad-audit.json',{'checked':STAMP,'counts':states,'provisional_original_recording_rooms':len(entries),'validated_rooms':0,'publication_status':'auditing','identity_holds':identity_holds,'admitted_recordings':sum(len(e['tracks']) for e in entries),'target':'Most of the1150 game exhibits;600+music-bearing games where verified original recordings exist.','games':[{k:v for k,v in r.items() if k!='selection'} for r in records]})
 return states,len(entries)

def main():
 global TITLE_YEARS
 ap=argparse.ArgumentParser();ap.add_argument('--entry-id',action='append',default=[]);ap.add_argument('--recording-only',action='store_true');ap.add_argument('--workers',type=int,default=8);ap.add_argument('--limit',type=int,default=0);ap.add_argument('--retry',action='store_true');ap.add_argument('--retry-pending',action='store_true');ap.add_argument('--assemble',action='store_true');args=ap.parse_args()
 if args.assemble:print(assemble());return
 doc=json.loads((ROOT/'content/catalog.json').read_text());catalog=doc if isinstance(doc,list) else doc['entries'];TITLE_YEARS={}
 for e in catalog:
  if e.get('kind')=='game':TITLE_YEARS.setdefault(norm(e['title']),set()).add(e['year'])
 games=[e for e in catalog if e.get('kind')=='game' and not e.get('soundtrack',{}).get('tracks')]
 priority=json.loads((ROOT/'content/expansion/major-release-seeds.json').read_text());names={norm(n) for group in priority['years'].values() for n in group};games.sort(key=lambda e:(norm(e['title']) not in names,-e['year'],e['title']))
 if args.recording_only:
  games=[e for e in games if (RESEARCH/'games'/(e['id']+'.json')).exists() and json.loads((RESEARCH/'games'/(e['id']+'.json')).read_text()).get('state') in ['admitted','recording_research_required']]
 if args.entry_id:games=[e for e in games if e['id'] in set(args.entry_id)]
 if args.limit:games=games[:args.limit]
 print('RESEARCH',len(games),'games; workers',args.workers,flush=True)
 done=0
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
  futures={pool.submit(process,e,args.retry,args.retry_pending):e for e in games}
  for f in concurrent.futures.as_completed(futures):
   e=futures[f]
   try:r=f.result();print(r['state'],e['id'],e['title'],flush=True)
   except Exception as ex:print('ERROR',e['id'],repr(ex),flush=True)
   done+=1
   if done%10==0:print('CHECKPOINT',done,assemble(),flush=True)
 print('FINAL',assemble(),flush=True)
if __name__=='__main__':main()
