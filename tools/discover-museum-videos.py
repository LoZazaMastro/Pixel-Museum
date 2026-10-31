"""Resume exact-game YouTube archive discovery without downloading video media.

Flat search discovers candidates; full extractor metadata must resolve public
playable formats before a selection is admitted. Credits distinguish publisher
channels from original gameplay-capture authors. No stream URLs are retained.
"""
from __future__ import annotations
from pathlib import Path
from urllib.parse import urlparse,parse_qs,unquote
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import argparse,hashlib,html,io,json,os,re,subprocess,threading,time,unicodedata
from PIL import Image

ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'content/expansion';CACHE=ROOT/'build/research/video-discovery';CACHE.mkdir(parents=True,exist_ok=True)
EXCLUSIONS_FILE=HERE/'museum-video-identity-exclusions.json'
IDENTITY_EXCLUSIONS=json.loads(EXCLUSIONS_FILE.read_text(encoding='utf-8')).get('entries',{}) if EXCLUSIONS_FILE.exists() else {}
YTDLP=Path('C:/Users/Andrea/homebrew/plugins/themedeck/yt-dlp.exe')
OFFICIAL={re.sub('[^a-z0-9]','',s.lower()) for s in ['Nintendo','Nintendo of America','Nintendo UK','PlayStation','PlayStation Europe','PlayStation Japan','Xbox','SEGA','SegaAmerica','Sega Europe','Capcom USA','CapcomChannel','Bandai Namco Entertainment America','Bandai Namco Europe','BANDAI NAMCO Entertainment','Square Enix','FINAL FANTASY','Ubisoft','Ubisoft North America','Rockstar Games','RockstarGames','Bethesda Softworks','Bethesda','Blizzard Entertainment','World of Warcraft','Diablo','Warcraft','Electronic Arts','EA','EA Star Wars','EA SPORTS','Activision','Call of Duty','KONAMI','Konami','Atari','SNK OFFICIAL','SNK OFFICIAL CHANNEL','Valve','Valve Software','Steam','2K','2K United Kingdom','Warner Bros. Games','WB Games','Bungie','Remedy Entertainment','Naughty Dog','Insomniac Games','Santa Monica Studio','Sucker Punch Productions','Guerrilla','Larian Studios','CD PROJEKT RED','Cyberpunk 2077','The Witcher','THQ Nordic','DevolverDigital','Devolver Digital','Team Cherry','Supergiant Games','RemedyGames','id Software','Digital Eclipse','Sega Genesis Classics','GOG','Game Freak','Limited Run Games']}
CAPTURE={re.sub('[^a-z0-9]','',s.lower()) for s in ['NintendoComplete','World of Longplays','LongplayArchive','xRavenXP','Al82 Retrogaming Longplays','Shirrako','MKIceAndFire','IGN','GameSpot','NoClip','Noclip - Video Game Documentaries','Digital Foundry','PlayStation Access','GDC','Game Developers Conference','Game Developer','Computer History Museum','The Strong National Museum of Play','Video Game History Foundation','TheGameAwards','Geoff Keighley','Brookhaven Lab','Brookhaven National Laboratory']}
KNOWN_TITLES=set()
KNOWN_HARDWARE=set()
AMBIGUOUS=set()
RELEASE_YEARS={}
IDENTITY_ONLY=False
TITLE_ALIASES={'donkeykongcountry2':['donkeykongcountry2diddyskongquest'],'donkeykongcountry3':['donkeykongcountry3dixiekongsdoubletrouble'],'supermariorpg':['supermariorpglegendofthesevenstars'],'ageofempiresii':['ageofempiresiitheageofkings'],'streetfighterii':['streetfighteriitheworldwarrior'],'metalgearsolid2sonsofliberty':['metalgearsolid2'],'metalgearsolid3snakeeater':['metalgearsolid3'],'ridgeracer':['ridgeracers'],'finalfantasyxvi':['finalfantasy16'],'kingdomcomedeliveranceii':['kingdomcomedeliverance2'],'warhammer40000spacemarine2':['warhammer40kspacemarine2','spacemarine2'],'pokemonredandgreen':['pokemonredgreen','pokemonred','pokemongreen','pocketmonstersred','pocketmonstersgreen']}
YEAR_TITLE_ALIASES={('counterstrike',2000):['counterstrike16','counterstrike10','counterstrike13'],('finalfantasyxiv',2010):['ffxiv10','finalfantasyxiv10'],('finalfantasyxiv',2013):['ffxiv20','finalfantasyxiv20','finalfantasyxivarealmreborn','ffxivarealmreborn']}
YEAR_PLATFORMS={('ridgeracer',1993):'arcade',('ridgeracer',2004):'psp',('finalfantasyxiv',2010):'1.0',('finalfantasyxiv',2013):'arr',('ninjagaiden',1988):'nes',('ninjagaiden',2004):'xbox',('godofwar',2005):'ps2',('godofwar',2018):'ps4',('residentevil',1996):'ps1',('residentevil',2002):'gamecube',('residentevil2',1998):'ps1',('residentevil2',2019):'ps4',('residentevil4',2005):'gamecube',('residentevil4',2023):'ps5',('silenthill2',2001):'ps2',('silenthill2',2024):'ps5',('tombraider',1996):'ps1',('tombraider',2013):'ps3',('doom',1993):'dos',('doom',2016):'ps4',('demonsouls',2009):'ps3',('demonsouls',2020):'ps5',('aloneinthedark',1992):'dos',('aloneinthedark',2024):'ps5'}
HARDWARE_ALIASES={'atarivideocomputersystem':['atari2600','atarivcs'],'megadrivegenesis':['megadrive','segagenesis'],'familycomputer':['famicom'],'commodore64':['c64'],'nintendogameboy':['gameboy'],'gameboy':['nintendogameboy'],'nintendogamecube':['gamecube'],'gamecube':['nintendogamecube'],'nintendoentertainmentsystem':['nes','famicom'],'supernintendoentertainmentsystem':['snes','superfamicom'],'nintendoswitch':['switch'],'nintendoswitch2':['switch2'],'nintendo3ds':['3ds'],'nintendods':['nds'],'playstation':['ps1','psone'],'playstation2':['ps2'],'playstation3':['ps3'],'playstation4':['ps4'],'playstation5':['ps5'],'playstationportable':['psp'],'playstationvita':['psvita','vita'],'segagenesis':['megadrive','genesis'],'segamegadrive':['megadrive','genesis'],'segasaturn':['saturn'],'segadreamcast':['dreamcast'],'gameboyadvance':['gba'],'segagamegear':['gamegear']}
SOURCE_FILMS={'tennis-for-two':{'id':'u6mu5B-YZU8','title':'First Video Game?','channel':'Brookhaven Lab','duration':180}}
SPECIAL_QUERIES={'tennis-for-two':'Tennis for Two Brookhaven Lab oscilloscope demonstration','spacewar':'Spacewar PDP-1 Computer History Museum demonstration','daily-01-18':"Takeshi Kitano Takeshi's Challenge game history",'xbox':'Original Xbox 2001 Microsoft console history documentary'}
ORIGINAL_PLATFORM={'baseball':'nes','deusex':'pc','ridgeracer':'psp','gearsofwar':'xbox 360','iceclimber':'nes','halo2':'xbox','haloreach':'xbox 360','kingdomhearts':'ps2','masseffect2':'xbox 360','okami':'ps2','fable':'xbox','crossfire':'pc','rambo':'zx spectrum','ghostbusters':'c64','superman':'atari 2600','killerinstinct':'arcade','avatar':'plato','startrader':'basic','startrek':'basic','deathrace':'arcade','touchme':'arcade','teenagemutantninjaturtles':'arcade','maniacmansion':'c64','lemmings':'amiga','pikmin2':'gamecube','littlebigplanet':'ps3','forzamotorsport':'original xbox','ratchetandclank':'ps2','assassinscreed':'ps3','mortalkombat':'arcade','finalfantasyix':'ps1','finalfantasyxii':'ps2','starwarsknightsoftheoldrepublic':'xbox','shadowofthecolossus':'ps2','guitarhero':'ps2','ghostsngoblins':'arcade','gradius':'arcade','metalgear':'msx','contra':'arcade','goldenaxe':'arcade','doubledragon':'arcade','streetfighterii':'arcade','virtuafighter':'arcade','virtuafighter2':'arcade','finalfight':'arcade','tekken':'arcade','tekken2':'arcade','pacman':'arcade','mspacman':'arcade','donkeykong':'arcade','galaga':'arcade','galaxian':'arcade','frogger':'arcade','asteroids':'arcade','spaceinvaders':'arcade','outrun':'arcade','outrunners':'arcade','hangon':'arcade','afterburner':'arcade','rtype':'arcade','princeofpersia':'apple ii'}
def norm(text):
    text=html.unescape(text).replace('\u2122','').replace('\u00ae','')
    text=unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().lower()
    return re.sub('[^a-z0-9]','',text.replace('&','and'))
def canonical(text):
    text=re.sub(r'\s*\([^)]*\)','',text)
    key=norm(text).removeprefix('sidmeiers')
    return {'mother':'earthboundbeginnings','donkeykongcountry2diddyskongquest':'donkeykongcountry2','pokemonredandblue':'pokemonredandgreen','civilizationi':'civilization'}.get(key,key)
def wiki(url):
    part=urlparse(url);name=parse_qs(part.query).get('title',[''])[0]
    if not name and '/wiki/' in part.path:name=part.path.split('/wiki/',1)[1]
    return unquote(name).replace('_',' ')
def save(path,value):
    temp=path.with_name(path.name+'.'+str(os.getpid())+'.'+str(threading.get_ident())+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for attempt in range(20):
        try:temp.replace(path);return
        except PermissionError:
            if attempt==19:raise
            time.sleep(.1)
def extract(target,flat=False):
    command=[str(YTDLP),'--dump-single-json','--skip-download','--no-warnings','--socket-timeout','8','--retries','0','--extractor-retries','0','--no-playlist']
    if flat:command+=['--flat-playlist']
    result=subprocess.run(command+[target],capture_output=True,encoding='utf-8',errors='replace',timeout=40)
    if result.returncode:raise ValueError(result.stderr.strip()[-900:] or 'Extractor returned no metadata')
    return json.loads(result.stdout)
def app_metadata(mode,value):
    executable='/mnt/f/Playhub/PS5/Pixel Museum/build/video-catalog-metadata-v2'
    result=subprocess.run(['wsl','-d','PSBBN','--',executable,mode,value],capture_output=True,encoding='utf-8',errors='replace',timeout=35)
    if result.returncode:raise ValueError(result.stderr.strip()[-600:] or 'Unsigned app resolver failed')
    return json.loads(result.stdout)
def search(query):
    path=CACHE/('search-'+hashlib.sha256(query.encode()).hexdigest()[:20]+'.json')
    if path.exists():return json.loads(path.read_text(encoding='utf-8'))
    result=app_metadata('--search',query)
    if not result.get('entries'):result=extract('ytsearch8:'+query,True)
    rows=[{k:r.get(k) for k in ['id','title','channel','channel_id','duration','url','channel_is_verified','view_count','description']} for r in result.get('entries',[]) if r.get('id')]
    save(path,{'query':query,'entries':rows});return {'query':query,'entries':rows}
def metadata(video_id,row):
    if IDENTITY_ONLY:return public_identity_metadata(video_id,row)
    path=CACHE/('video-'+video_id+'.json')
    if path.exists():
        cached=json.loads(path.read_text(encoding='utf-8'))
        if cached.get('native_compatible_avc_aac') is True:return cached
        if cached.get('native_compatible_avc_aac') is False:raise ValueError('Native AVC/AAC format pair not resolved at last check')
    meta=app_metadata('--player',video_id)
    if not meta.get('ok') or not meta.get('playable_video_formats') or not meta.get('native_compatible_avc_aac'):
        failure={'id':video_id,'native_compatible_avc_aac':False,'checked_utc':datetime.now(timezone.utc).isoformat(),'error':meta.get('error') or 'No native AVC/AAC formats resolved'}
        save(path,failure);raise ValueError('Unsigned app player: '+str(failure['error']))
    # TV responses can omit presentation text while retaining the correct
    # video/channel IDs and formats. Verify those public fields via oEmbed;
    # retain the actual search renderer text if oEmbed is unavailable.
    try:
        from urllib.parse import urlencode
        endpoint='https://www.youtube.com/oembed?'+urlencode({'url':'https://www.youtube.com/watch?v='+video_id,'format':'json'})
        with urlopen(Request(endpoint,headers={'User-Agent':'PixelMuseum historical collection'}),timeout=8) as response:public=json.load(response)
    except Exception:public={}
    meta['title']=public.get('title') or meta.get('title') or row.get('title')
    meta['channel']=public.get('author_name') or meta.get('channel') or row.get('channel')
    meta['availability']='public-format-resolved';meta['age_limit']=0
    result={k:meta.get(k) for k in ['id','title','channel','channel_id','uploader','uploader_id','duration','upload_date','availability','age_limit','live_status','language','was_live']}
    result.update(format_count=meta.get('format_count'),playable_video_formats=meta.get('playable_video_formats'),video_codecs=meta.get('video_codecs'),audio_codecs=meta.get('audio_codecs'),avc_format_count=meta.get('avc_format_count'),aac_format_count=meta.get('aac_format_count'),native_compatible_avc_aac=meta.get('native_compatible_avc_aac'),native_selection=meta.get('native_selection'),resolver_client=meta.get('client'),
        subtitle_languages=list((meta.get('subtitles') or {}).keys()),automatic_caption_languages=list((meta.get('automatic_captions') or {}).keys()),
        description=(meta.get('description') or '')[:1600],checked_utc=datetime.now(timezone.utc).isoformat())
    save(path,result);return result
def public_identity_metadata(video_id,row):
    # Public extractor identity only: never persist formats or expiring URLs.
    path=CACHE/('identity-'+video_id+'.json')
    if path.exists():return json.loads(path.read_text(encoding='utf-8'))
    command=[str(YTDLP),'--skip-download','--dump-single-json','--no-warnings','--ignore-no-formats-error','--no-check-formats','--socket-timeout','8','--retries','0','--extractor-args','youtube:player_skip=webpage,configs;player_client=android','https://www.youtube.com/watch?v='+video_id]
    result=subprocess.run(command,capture_output=True,encoding='utf-8',errors='replace',timeout=25)
    if result.returncode:raise ValueError('Public identity lookup: '+result.stderr.strip()[-400:])
    raw=json.loads(result.stdout)
    if not raw.get('title') or not raw.get('channel') or raw.get('availability') in ['private','premium_only','subscriber_only','needs_auth']:raise ValueError('Public title/uploader identity unavailable')
    meta={k:raw.get(k) for k in ['id','title','channel','channel_id','duration','upload_date','age_limit','description']}
    meta['description']=(meta.get('description') or '')[:3000]
    formats=raw.get('formats') or []
    meta.update(availability='public-metadata',format_count=len(formats),playable_video_formats=sum(f.get('vcodec') not in [None,'none'] for f in formats),video_codecs=list({f.get('vcodec') for f in formats if f.get('vcodec') not in [None,'none']}),checked_utc=datetime.now(timezone.utc).isoformat())
    save(path,meta);return meta

def poster(video):
    folder=CACHE/'posters';folder.mkdir(exist_ok=True)
    quality=ROOT/'build/research/image-quality';quality.mkdir(exist_ok=True)
    for filename in ['maxresdefault.jpg','sddefault.jpg']:
        url='https://i.ytimg.com/vi/'+video['youtube_id']+'/'+filename
        cached=folder/(video['youtube_id']+'-'+filename)
        try:
            if cached.exists():raw=cached.read_bytes()
            else:
                with urlopen(Request(url,headers={'User-Agent':'PixelMuseum historical collection'}),timeout=8) as response:raw=response.read(12<<20)
            with Image.open(io.BytesIO(raw)) as image:image.load();w,h=image.size
            if max(w,h)<600 or w<600:continue
            cached.write_bytes(raw);(quality/(hashlib.sha256(url.encode()).hexdigest()[:16]+'.jpg')).write_bytes(raw)
            return {'url':url,'title':'Film preview: '+video['title'],'source_page':video['url'],'creator':video['creator'],
                'credit':video['creator']+' / original YouTube publication thumbnail','license':'Original creator and game-publisher rights retained; historical preview of the linked film.',
                'width':w,'height':h,'source_width':w,'source_height':h,'native_long_edge':max(w,h),'kind':'video-poster','story_paragraph':-1,
                'recovery_local_source':cached.relative_to(ROOT).as_posix(),'quality_verified':'Original video-publication thumbnail fully decoded at native dimensions; never enlarged.',
                'verification':{'sha256':hashlib.sha256(raw).hexdigest(),'checked_utc':datetime.now(timezone.utc).isoformat()}}
        except Exception:continue
    return None
def platform_present(platform,text):
    aliases={'arr':['a realm reborn','arr','2.0'],'ps1':['ps1','psx','playstation','playstation 1'],'ps2':['ps2','playstation2','playstation 2'],'ps3':['ps3','playstation3','playstation 3'],'ps4':['ps4','playstation4','playstation 4'],'ps5':['ps5','playstation5','playstation 5'],'psp':['psp','playstation portable'],'xbox 360':['xbox360','xbox 360'],'c64':['c64','commodore 64'],'atari 2600':['atari2600','atari 2600','atari vcs'],'gamecube':['gamecube','game cube'],'nes':['nes','famicom','nintendo entertainment system']}
    if platform=='xbox':return bool(re.search(r'\bxbox\b(?!\s*(?:360|one|series))',text))
    return any(re.search(r'\b'+re.escape(value)+r'\b',text) for value in aliases.get(platform,[platform]))

def original_platform(entry):
    key=canonical(entry['title']);title=entry.get('provenance',{}).get('article_title','').lower()
    if '(nes video game)' in title:return 'nes'
    if '(arcade game)' in title:return 'arcade'
    exact=YEAR_PLATFORMS.get((key,entry['year']))
    if exact:return exact
    years=RELEASE_YEARS.get(key,set())
    return ORIGINAL_PLATFORM.get(key) if not years or entry['year']==min(years) else None

def relevant(entry,row):
    title=html.unescape(row.get('title') or '');lower=title.lower();identifier=canonical(entry['title']);candidate=norm(title)
    # Preserve numbered identities and differentiate the original from named
    # remakes/ports. A familiar franchise word alone is insufficient.
    is_game=entry.get('kind','game')=='game';is_person=entry.get('kind')=='person'
    video_id=row.get('id') or row.get('youtube_id','')
    if video_id in IDENTITY_EXCLUSIONS.get(entry.get('id',''),{}):return False,IDENTITY_EXCLUSIONS[entry['id']][video_id]['reason']
    creator=norm(row.get('channel') or row.get('creator') or '')
    if not is_game and not is_person and (any(int(y)>2026 for y in re.findall(r'\b2\d{3}\b',title)) or 'future' in lower):return False,'Speculative future hardware evolution is not a historical archive film'
    if is_game and (row.get('channel') or row.get('creator') or '').lower().endswith(' - topic'):return False,'Auto-generated music publication is not a game-history film'
    if entry.get('id','') in SOURCE_FILMS and (row.get('id') or row.get('youtube_id'))==SOURCE_FILMS[entry.get('id','')]['id'] and creator=='brookhavenlab':return True,''
    if identifier=='touchme' and entry['year']==1974 and 'arcade' not in lower:return False,'The 1974 arcade game must not be substituted with the 1978 handheld'
    if entry.get('id','')=='tennis-for-two' and 'brookhaven' not in creator:return False,'Prefer the documented Brookhaven oscilloscope demonstration, not a modern recreation app'
    if entry.get('id','')=='spacewar' and not any(v in lower for v in ['pdp','computer history','museum']):return False,'Spacewar needs documented PDP-1 program or museum demonstration context'
    if entry.get('id','')=='daily-01-18' and not any(v in lower for v in ['challenge','game','famicom','nintendo']):return False,'Film-only Kitano interview does not discuss his game work'
    if is_game and entry['year']<1980 and entry.get('id','') not in SOURCE_FILMS and str(entry['year']) not in title and not any(v in lower for v in ['arcade','atari','intellivision','channel f','magnavox','odyssey','commodore','trs-80','apple ii','apple 2','basic','plato','pdp','hp 2000','hp2000','fairchild']):return False,'Early generic title lacks its original-year or documented computer/hardware context'
    keys=[identifier,*(TITLE_ALIASES if is_game else HARDWARE_ALIASES).get(identifier,[]),*YEAR_TITLE_ALIASES.get((identifier,entry['year']),[])]
    if is_person:
        if entry.get('id','')=='daily-01-18':keys += ['takeshischallenge']
        keys += [canonical(re.split(r',| and ',entry['title'],maxsplit=1)[0])]
        keys += {'danibuntenberryandmule':['danbunten','danielleberry','daniellebuntenberry']}.get(identifier,[])
    matches=[key for key in keys if key in candidate and (len(key)>4 or re.search(r'\b'+re.escape(key)+r'\b',lower))]
    if not matches:return False,'Complete game title/number or explicit original-edition alias not matched'
    matched=max(matches,key=len)
    # Prefix matches are franchise matches, not exact-game evidence. Accept
    # only ordinary film descriptors after the complete game title; reject
    # a different subtitle/number even when that sequel is outside our list.
    if is_game and matched in candidate:
        tail=candidate.split(matched,1)[1]
        descriptors=('gameplay','game','trailer','launch','official','cinematic','full','walkthrough','playthrough','longplay','part','version','pc','dos','msdos','psp','plato','basic','onplato','onatari','onapple','oncommodore','ps1','ps2','psx','ps3','ps4','ps5','playstation','xbox','nes','snes','nintendo','n64','gamecube','switch','sega','arcade','amiga','apple','msx','commodore','c64','atari','e3','e320','tokyo','tgs','opening','intro','review','retrospective','history','documentary','makingof','themakingof','behindthescenes','development','anniversary','10th','20th','25th','30th','35th','40th','50th','demo','beta','prototype','interview','199','198','197','200','201','202','2160p','1080p','720p','60fps','4k','8k','remake','remaster','enhancededition','hd','hdremix','original','theoriginal','combat','tga','announce','announcement','reveal','extended','preview','exclusive','releasedate','stateofplay','developer','thefirst','first','normaldifficulty','us','usa','japan','europe')
        descriptors += {'dishonored2':('corvogameplay','emilykaldwingameplay','liveactiontrailer'),'doometernal':('phobosgameplay','marscoretrailer'),'deathloop':('twobirdsonestone','deluxeeditionofficial'),'finalfantasyxvi':('dominance','revengetrailer','salvationlaunch'),'fallout4':('liveactiontrailer','combatgameplay'),'kingdomcomedeliveranceii':('roadmaptrailer','royaleditionofficial','apcgamewecancelebrate'), 'doomthedarkages':('brutalhighaction',)}.get(identifier,())
        if tail and not tail.startswith(descriptors):return False,'A different subtitle/sequel follows the exhibit title'
        if entry['year']<2010 and tail.startswith(('hd','enhancededition','remaster','remake')) and not any(t in entry['title'].lower() for t in ['remake','remaster','hd']):return False,'Later enhanced/HD edition is not the exhibited original'
    for other in KNOWN_TITLES if is_game else KNOWN_HARDWARE if not is_person else []:
        if other not in keys and len(other)>len(matched)+1 and matched in other and other in candidate:return False,'Title identifies a different sequel or hardware successor'
    expected=original_platform(entry)
    if is_game and expected:
        alternatives=['nes','snes','genesis','mega drive','master system','game boy','nintendo switch','switch','psx','ps1','ps2','ps3','ps4','ps5','playstation','dreamcast','saturn','n64','vita','wii','handheld','pc','dos','arcade','psp','pc-8801','pc8801','zx spectrum','c64','atari 2600','plato']
        if not (platform_present(expected,lower) or any(t in lower for t in ['history','retrospective','documentary','interview'])) and any(re.search(r'\b'+re.escape(t)+r'\b',lower) for t in alternatives):return False,'Different home-port edition from the original exhibited platform'
    if any(t in lower for t in ['fan remake','fanmade','fan-made','unreal engine 5','ue5','modded','texture pack','upscaled','ai enhanced','ai-enhanced']) or norm(row.get('channel') or row.get('creator') or '') in ('snazzyai',):return False,'Reconstructed/modded/upscaled film is not an original archive capture'
    if is_game and 'evolution' in lower and len(re.findall(r'\b(?:19|20)\d{2}\b',title))>1:return False,'Multi-release franchise evolution is not a focused film of this game'
    if is_game and any(t in lower for t in ['prototype','promo disc','beta gameplay','beta trailer','e3 demo','collection','trilogy','1 and 2','1+2','multiplaythrough','montage','#shorts']):return False,'Prototype/compilation/short is not a focused release-game film'
    if is_game and identifier in {'forzamotorsport','assassinscreed','ratchetandclank','littlebigplanet','gearsofwar','kingdomhearts','halo2','haloreach','masseffect2','okami','deusex'} and str(entry['year']) not in title+' '+(row.get('description') or ''):
        if not expected or not platform_present(expected,lower):return False,'Original release needs its year or original platform; modern franchise film is ambiguous'
    if is_game and identifier in AMBIGUOUS and str(entry['year']) not in title+' '+(row.get('description') or ''):
        if not expected or not platform_present(expected,lower):return False,'Same-title original/remake needs its release year or exact original platform in metadata'
    if not any(t in entry['title'].lower() for t in ['remake','remaster']):
        if any(t in lower for t in ['remake','remaster','definitive edition','hd collection','anniversary edition']) or ('anniversary' in lower and not any(t in lower for t in ['history','documentary','retrospective','interview','review'])):return False,'Different remake/remaster edition'
    if any(t in lower for t in ['soundtrack','ost full','music mix','theme song','relaxing music']):return False,'Music belongs in the soundtrack room'
    years=[int(y) for y in re.findall(r'\b(?:19|20)\d{2}\b',title)]
    if is_game and entry['year']<2010 and years and entry['year'] not in years and any(y>=entry['year']+6 for y in years) and not any(t in lower for t in ['history','retrospective','review','documentary','making of','interview']):return False,'Video title names a later game/edition year'
    duration=row.get('duration') or row.get('duration_s') or 0
    if duration and duration<50:return False,'Clip too short for the archive card'
    return True,''
def score(entry,row):
    channel=norm(row.get('channel') or '');title=(row.get('title') or '').lower();duration=row.get('duration') or row.get('duration_s') or 0
    value=100 if channel in OFFICIAL else 60 if channel in CAPTURE else 20
    if str(entry['year']) in title:value+=20
    if any(t in title for t in ['gameplay','playthrough','longplay','trailer','interview','documentary','making of']):value+=15
    if 120<=duration<=1800:value+=12
    if duration>14400:value-=15
    if '4k' in title and entry['year']<2000:value-=2
    return value
def resolve(entry):
    path=CACHE/(('pending-selection-' if IDENTITY_ONLY else 'selection-')+entry['id']+'.json')
    verified=CACHE/('selection-'+entry['id']+'.json')
    if IDENTITY_ONLY and verified.exists():
        previous=json.loads(verified.read_text(encoding='utf-8'))
        if previous.get('video') and relevant(entry,previous['video'])[0] and (IDENTITY_ONLY or previous['video'].get('verification',{}).get('native_codec_metadata_verified') is True):return previous
    if path.exists():
        previous=json.loads(path.read_text(encoding='utf-8'))
        if previous.get('video') and relevant(entry,previous['video'])[0] and (IDENTITY_ONLY or previous['video'].get('verification',{}).get('native_codec_metadata_verified') is True):return previous
    errors=[];rejected=[]
    title=re.sub(r'\s*\([^)]*\)','',entry['title'])
    platform=original_platform(entry) or ''
    query=title+' '+str(entry['year'])+' '+platform+(' gameplay playthrough' if entry['year']<2015 else ' official gameplay trailer')
    if entry.get('kind')=='person':query=re.split(r',| and ',title,maxsplit=1)[0]+' video game developer interview oral history'
    elif entry.get('kind')!='game':query=title+' '+str(entry['year'])+' original hardware history documentary'
    query=SPECIAL_QUERIES.get(entry['id'],query)
    try:results=search(query)['entries']
    except Exception as error:result={'entry_id':entry['id'],'title':entry['title'],'year':entry['year'],'reason':'Search failed: '+str(error)};save(path,result);return result
    if entry['id'] in SOURCE_FILMS:results=[SOURCE_FILMS[entry['id']],*results]
    if entry.get('kind')=='game' and entry['year']>=2015:
        try:
            alternate=search(title+' '+str(entry['year'])+' '+platform+' gameplay walkthrough no commentary')['entries']
            known={r['id'] for r in results}; results += [r for r in alternate if r['id'] not in known]
        except Exception as error:errors.append({'stage':'alternate-publication-search','reason':str(error)})
    candidates=[]
    for row in results:
        allowed,reason=relevant(entry,row)
        if allowed:candidates.append(row)
        else:rejected.append({'id':row['id'],'title':row['title'],'reason':reason})
    candidates.sort(key=lambda row:score(entry,row),reverse=True)
    for row in candidates[:6]:
        try:
            meta=metadata(row['id'],row);allowed,reason=relevant(entry,meta)
            if not allowed:rejected.append({'id':row['id'],'title':meta['title'],'reason':reason});continue
            if meta.get('availability') not in ('public','unlisted','public-format-resolved','public-metadata',None) or (meta.get('age_limit') or 0)>0 or (not IDENTITY_ONLY and not meta.get('playable_video_formats')):
                errors.append({'id':row['id'],'reason':'No unrestricted playable video formats in extractor metadata','availability':meta.get('availability'),'formats':meta.get('playable_video_formats')});continue
            creator=meta.get('channel') or meta.get('uploader') or row.get('channel')
            if not creator:raise ValueError('Original uploader identity unavailable')
            official=norm(creator) in OFFICIAL;watch='https://www.youtube.com/watch?v='+meta['id']
            kind='Publisher gameplay and archive film' if official else 'Gameplay capture and archive film'
            if entry.get('kind')=='person':
                text=meta['title'].lower()
                kind='Interview and conversation' if any(t in text for t in ['interview','q&a','conversation']) else 'Design lecture and public talk' if any(t in text for t in ['lecture','talk','summit']) else 'Archive demonstration of the creator?s work' if any(t in text for t in ['gameplay','longplay','playthrough','space hamburger']) else 'Creator profile and historical film'
            elif entry.get('kind')!='game':kind='Hardware demonstration and history'
            video={'youtube_id':meta['id'],'url':watch,'title':meta['title'],'creator':creator,'source_page':watch,
                'credit':creator+' / original YouTube publication','license':'Original creator and game-publisher rights retained; streamed from the original publication.','license_url':'',
                'caption':('Published by '+creator+'. ' if official else 'Original recording published by '+creator+'. ')+entry['title']+' ('+str(entry['year'])+'): '+kind.lower()+'.',
                'verified_on':datetime.now(timezone.utc).date().isoformat(),'channel_id':meta.get('channel_id'),'duration_s':meta.get('duration'),
                'verification':{'metadata_resolved':True,'availability':meta.get('availability'),'playable_formats':meta['playable_video_formats'],'codecs':meta.get('video_codecs'),
                    'checked_utc':meta['checked_utc'],'native_codec_metadata_verified':bool(meta.get('native_compatible_avc_aac')),'avc_format_count':meta.get('avc_format_count',0),'aac_format_count':meta.get('aac_format_count',0),'native_selection':meta.get('native_selection','none'),'check_scope':('Public title/uploader metadata verified; stream format resolution pending.' if not meta.get('playable_video_formats') else 'Public extractor metadata and real video formats resolved; console playback is verified separately.'),'playback_resolution_pending':not bool(meta.get('playable_video_formats'))},
                'identity_review':{'exhibit_title':entry['title'],'exhibit_year':entry['year'],'original_video_title':meta['title'],'publisher_channel':official,'selection_query':query}}
            result={'entry_id':entry['id'],'title':entry['title'],'year':entry['year'],'video':video,'rejected_candidates':rejected};save(path,result);return result
        except Exception as error:errors.append({'id':row['id'],'reason':str(error)})
    result={'entry_id':entry['id'],'title':entry['title'],'year':entry['year'],'reason':'No exact-edition playable candidate admitted','errors':errors,'rejected_candidates':rejected};save(path,result);return result
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--metadata-discovery',action='store_true');parser.add_argument('--all-games',action='store_true');parser.add_argument('--all-exhibits',action='store_true');parser.add_argument('--limit',type=int);parser.add_argument('--workers',type=int,default=2);args=parser.parse_args()
    global IDENTITY_ONLY
    IDENTITY_ONLY=args.metadata_discovery
    catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf-8'))['entries'];lookup={}
    additional=ROOT/'build/research/franchise-mainline/media-research-targets.json'
    if additional.exists():
        known_ids={e['id'] for e in catalog}
        catalog += [{'id':e['entry_id'],'title':e['title'],'year':e['year'],'kind':'game','awaiting_article_admission':True} for e in json.loads(additional.read_text(encoding='utf-8'))['entries'] if e['entry_id'] not in known_ids]
    global KNOWN_TITLES,KNOWN_HARDWARE,AMBIGUOUS,RELEASE_YEARS
    KNOWN_TITLES={canonical(e['title']) for e in catalog if e['kind']=='game'}
    RELEASE_YEARS={key:{e['year'] for e in catalog if e['kind']=='game' and canonical(e['title'])==key} for key in KNOWN_TITLES}
    AMBIGUOUS={key for key in KNOWN_TITLES if len({e['year'] for e in catalog if e['kind']=='game' and canonical(e['title'])==key})>1}
    AMBIGUOUS |= {canonical(e['title']) for e in catalog if e['kind']=='game' and re.search(r'\((?:19|20)\d{2}.*?game',e.get('provenance',{}).get('article_title',''))}
    KNOWN_HARDWARE={canonical(e['title']) for e in catalog if e['kind'] in ['console','hardware','computer']}
    KNOWN_HARDWARE|={key.removeprefix('nintendo').removeprefix('sega').removeprefix('sony') for key in list(KNOWN_HARDWARE)}
    for entry in catalog:
        if entry['kind']!='game':continue
        subjects=[entry['title'],entry.get('provenance',{}).get('article_title','')]
        subjects += [wiki(s.get('url','')) for s in entry.get('sources',[]) if 'wikipedia.org' in s.get('url','')]
        for subject in subjects:
            if subject:lookup[(canonical(subject),entry['year'])]=entry
    seeds=json.loads((HERE/'major-release-seeds.json').read_text(encoding='utf-8'))['years'];wanted=[];unmapped=[]
    for year,titles in seeds.items():
        for title in titles:
            entry=lookup.get((canonical(title),int(year)))
            if entry:wanted.append(entry)
            else:unmapped.append({'title':title,'year':int(year)})
    wanted=list({e['id']:e for e in wanted}.values())
    if args.all_exhibits:wanted += [e for e in catalog if e['kind'] in ['person','console','hardware','computer'] and e['id'] not in {v['id'] for v in wanted}]
    if args.all_games or args.all_exhibits:wanted += [e for e in catalog if e['kind']=='game' and e['id'] not in {v['id'] for v in wanted}]
    if args.limit:wanted=wanted[:args.limit]
    output=HERE/('museum-video-pending.json' if IDENTITY_ONLY else 'museum-video-selections.json');old=json.loads(output.read_text(encoding='utf-8')) if output.exists() else {'entries':[]};runtime={e['id']:e for e in catalog}
    admitted={e['entry_id']:e for e in old['entries'] if e['entry_id'] in runtime and relevant(runtime[e['entry_id']],e['videos'][0])[0] and (IDENTITY_ONLY or e['videos'][0].get('verification',{}).get('native_codec_metadata_verified') is True)};failures={}
    def checkpoint():
        save(output,{'schema_version':1,'entries':list(admitted.values()),'verification_scope':'Real public YouTube metadata and playable format resolution, not an assertion that every stream was played on PS5.'})
        save(CACHE/('pending-coverage-audit.json' if IDENTITY_ONLY else 'coverage-audit.json'),{'checked_utc':datetime.now(timezone.utc).isoformat(),'curated_checklist_titles':sum(map(len,seeds.values())),'unique_runtime_targets':len(wanted),'unmapped_checklist_titles':unmapped,
            'admitted':len(admitted),'official_publisher_selections':sum(e['videos'][0]['identity_review']['publisher_channel'] for e in admitted.values()),'failures':list(failures.values()),
            'remaining_target_ids':[e['id'] for e in wanted if e['id'] not in admitted],'video_media_downloaded':False,'native_poster_images':sum(bool(e.get('images')) for e in admitted.values())})
    checkpoint();print('TARGETS',len(wanted),'UNMAPPED',len(unmapped),'CACHED',len(admitted),flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for count,future in enumerate(as_completed([pool.submit(resolve,e) for e in wanted]),1):
            result=future.result();eid=result['entry_id']
            if result.get('video'):
                previous=admitted.get(eid,{}); old_video=next(iter(previous.get('videos',[])),{})
                old_images=previous.get('images',[])
                image=old_images[0] if old_video.get('youtube_id')==result['video']['youtube_id'] and old_images and (ROOT/old_images[0].get('recovery_local_source','missing')).is_file() else poster(result['video'])
                result['video']['poster_url']=image['url'] if image else ''
                admitted[eid]={'entry_id':eid,'match_title':result['title'],'match_year':result['year'],'videos':[result['video']],'images':[image] if image else []};failures.pop(eid,None)
            else:failures[eid]=result;admitted.pop(eid,None)
            checkpoint()
            if count%10==0:print('CHECKED',count,'ADMITTED',len(admitted),'FAILED',len(failures),flush=True)
    checkpoint();print('DONE',len(admitted),'admitted',len(failures),'failed',flush=True)
if __name__=='__main__':main()
