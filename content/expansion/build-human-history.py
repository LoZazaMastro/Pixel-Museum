"""A separate, attributed history rail: actual subjects, never invented game links."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode, quote, unquote, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json, hashlib, re, html, io, time, sys, copy, threading, runpy
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/'build/research/human-history';CACHE.mkdir(parents=True,exist_ok=True)
# The year locates the stated milestone, not an invented precise date of a subject.
SEEDS=[
(1833,'Difference engine','Babbage demonstrates mechanical calculation','The partially assembled first Difference Engine was demonstrated in 1833; this is not a claim that the later Analytical Engine was completed then.'),
(1843,'Ada Lovelace','Ada Lovelace and the possibilities of computation','Publication of her notes on the Analytical Engine.'),
(1854,'The Laws of Thought','An algebra of logic','Publication of George Boole\'s book.'),
(1877,'Phonograph','Sound becomes a recording','Edison announces his phonograph.'),
(1895,'Auguste and Louis Lumière','The Lumière cinematograph','Their public commercial film screening in Paris.'),
(1897,'Cathode-ray tube','Drawing with an electron beam','Karl Ferdinand Braun develops his cathode-ray tube.'),
(1901,'Guglielmo Marconi','Radio crosses the Atlantic','Marconi reports reception of the transatlantic wireless signal.'),
(1906,'Triode','The amplifying valve','Lee de Forest develops the three-electrode Audion.'),
(1896,'1896 Summer Olympics','The first modern Olympic Games','The Games of the I Olympiad in Athens.'),
(1922,'BBC','A public voice on the air','Formation of the British Broadcasting Company.'),
(1926,'John Logie Baird','Television becomes a demonstration','Baird demonstrates live moving television images to members of the Royal Institution.'),
(1927,'Metropolis (1927 film)','Metropolis imagines the machine city','Original film release.'),
(1936,'Turing machine','A machine defined by its rules','Alan Turing\'s paper On Computable Numbers.'),
(1937,'A Symbolic Analysis of Relay and Switching Circuits','Logic meets the electrical switch','Claude Shannon\'s master\'s thesis.'),
(1941,'Z3 (computer)','Zuse builds the Z3','Completion of the original relay computer.'),
(1946,'ENIAC','Electronic computation at room scale','Public dedication of ENIAC.'),
(1947,'Transistor','A smaller switch','The first working point-contact transistor at Bell Labs.'),
(1948,'Manchester Baby','The stored program runs','First successful program on the experimental machine.'),
(1951,'UNIVAC I','Computing enters commercial service','Delivery of the first UNIVAC I to the United States Census Bureau.'),
(1953,'NTSC','A standard for colour television','Adoption of the compatible NTSC colour standard.'),
(1954,'Seven Samurai','Seven Samurai','Original Japanese theatrical release.'),
(1958,'Integrated circuit','A circuit on a chip','Jack Kilby demonstrates an integrated circuit.'),
(1958,'Vertigo (film)','Hitchcock changes the viewer\'s perspective','Original theatrical release of Vertigo.'),
(1959,'MOSFET','The transistor that scales','Mohamed Atalla and Dawon Kahng develop the MOSFET at Bell Labs.'),
(1960,'PDP-1','A computer made for interaction','First delivery of Digital Equipment Corporation\'s PDP-1.'),
(1963,'Please Please Me','The Beatles on record','Release of the Beatles\' debut studio album.'),
(1964,'Computer mouse','Pointing at the screen','Douglas Engelbart\'s team constructs its first mouse prototype.'),
(1965,'Programma 101','Olivetti brings calculation to the desk','The Programma 101 is introduced at the New York World\'s Fair.'),
(1965,'Highway 61 Revisited','Dylan goes electric','Release of Bob Dylan\'s album.'),
(1968,'2001: A Space Odyssey','Kubrick imagines tomorrow','Original theatrical release.'),
(1969,'ARPANET','Computers become a network','The first ARPANET link.'),
(1970,'Intel 1103','Memory on a chip','Introduction of Intel\'s commercial dynamic RAM chip.'),
(1971,'Intel 4004','The microprocessor','Commercial announcement of Intel\'s 4004.'),
(1973,'Ethernet','A local network','Robert Metcalfe\'s Ethernet memorandum at Xerox PARC.'),
(1973,'Xerox Alto','The graphical desktop takes shape','The first Xerox Alto becomes operational.'),
(1975,'Altair 8800','A computer kit for enthusiasts','The January Popular Electronics cover introduces the Altair.'),
(1977,'Apple II','The personal computer reaches home','Introduction of the Apple II.'),
(1975,'Dolby Stereo','Cinema surrounds the audience','Dolby Stereo optical sound enters commercial theatrical use with Lisztomania in1975; full LCRS encoding follows with A Star Is Born in1976.'),
(1981,'High-definition television','More detail on television','Japan demonstrates the Hi-Vision high-definition television system in the United States; HDTV research predates this milestone.'),
(1981,'IBM Personal Computer','The IBM PC','Introduction of IBM\'s model 5150.'),
(1982,'Compact disc','Music in digital form','Commercial introduction of the audio compact disc.'),
(1982,'Blade Runner','A city built from the future','Original theatrical release.'),
(1983,'MIDI','Musical instruments learn to communicate','Public demonstration of MIDI at the NAMM show.'),
(1983,'Motorola DynaTAC','The portable cellular telephone','Approval of the DynaTAC 8000X.'),
(1984,'Macintosh 128K','The Macintosh arrives','Introduction of the original Macintosh.'),
(1984,'16:9 aspect ratio','A wider television image','The 16:9 ratio is proposed for high-definition television standards; later consumer adoption is gradual.'),
(1984,'Flash memory','Memory without a battery','Fujio Masuoka presents flash memory at IEDM.'),
(1989,'World Wide Web','A web of linked documents','Tim Berners-Lee writes his original proposal at CERN.'),
(1991,'Linux','An operating system built in public','First public release of the Linux kernel.'),
(1993,'Schindler\'s List','Schindler\'s List','Original theatrical release.'),
(1995,'Windows 95','A desktop for a mass audience','Commercial release of Windows 95.'),
(1996,'Voodoo Graphics','Dedicated hardware for 3D','Release of the first Voodoo Graphics chipset.'),
(1997,'Diana, Princess of Wales','A shared moment of mourning','The death of Diana, Princess of Wales, on 31 August.'),
(1998,'Google','Searching a growing web','Google is incorporated.'),
(1998,'Digital television transition in the United States','Television enters the digital era','Major American networks begin digital television broadcasts; this is not a claim that HDTV was invented in 1998.'),
(2000,'Nokia 3310','A telephone becomes an everyday object','Introduction of the Nokia 3310.'),
(2000,'Memento (film)','Nolan rearranges the story','Premiere of Christopher Nolan\'s film at Venice.'),
(2001,'September 11 attacks','September 11','The attacks of 11 September 2001.'),
(2001,'IPod','A music collection in a pocket','Introduction of the first iPod in 2001. The source article describes the iPod product family.'),
(2007,'IPhone (1st generation)','The touchscreen becomes a platform','Commercial release of the first iPhone.'),
(2008,'2008 Summer Olympics','Beijing on the world stage','The Games of the XXIX Olympiad.'),
(2009,'Avatar (2009 film)','Cinema returns to stereoscopic depth','Original theatrical release.'),
(2012,'Raspberry Pi','A small computer for learning','First sale of the Raspberry Pi Model B.'),
(2012,'Ultra-high-definition television','A new scale of screen detail','ITU-R Recommendation BT.2020 defines UHD television parameters, including 3840 by 2160.'),
(2015,'First observation of gravitational waves','Listening to spacetime','LIGO records GW150914; the public announcement follows in 2016.'),
(2020,'COVID-19 pandemic','A world connected at a distance','The World Health Organization characterises COVID-19 as a pandemic.'),
(2022,'James Webb Space Telescope','A deeper view of the universe','Release of Webb\'s first full-colour scientific images.'),
(2024,'2024 Summer Olympics','Paris, a century later','The Games of the XXXIII Olympiad.')
]

# These selections are deliberate subject/era checks, not a search-result order.
PHOTO_FILES={
 'Apollo 11':['Aldrin Looks Back at Tranquility Base - GPN-2000-001102.jpg'],
 'Animal Farm':['Animal Farm - 1st edition.jpg','George Orwell press photo.jpg'],
 'Incandescent light bulb':['Edison Carbon Bulb.jpg','Edison incandescent lights.jpg'],
 'AC motor':['Galileo Ferraris Alternating Current Motor.jpg'],
 'NTSC':['Prototype RCA color television at the Early Television Museum June 2022.jpg','RCA Model 5 Color TV Prototype (1953-1954) (53998050203).jpg'],
 'Raspberry Pi':['RaspberryPi.jpg'],
 'Dolby Stereo':['35mm film audio macro.jpg'],
 'High-definition television':['Analog Sony HDVS equipment.jpg'],
 'Voodoo Graphics':['3Dfx@Voodoo Graphics FrontsideB.jpg','3dfxvoodoo1diamond.jpg'],
 '16:9 aspect ratio':['SAMSUNG VA LCD TV LA40C550J1F.jpg'],
 'World Wide Web':['First Web Server.jpg'],
 'Computer mouse':["Douglas Engelbart's prototype mouse - Computer History Museum.jpg",'Computer mouse prototype top.jpg'],
 'Transistor':['A replica of the first working transistor.jpg','Bardeen Shockley Brattain 1948.JPG'],
 'Integrated circuit':['Kilby solid circuit.jpg'],
 'MOSFET':['D2PAK.JPG'],
 'Google':['Google Campus, Mountain View, CA.jpg','Googleplex central courtyard.jpg'],
 'BBC':['New Broadcasting House (14561681425).jpg','BBCBroadcastingHouse.JPG','Bbc broadcasting house front.jpg'],
 '2008 Summer Olympics':['2008 Summer Olympics Opening Ceremony 11.jpg','Beijing China Beijing-National-Stadium-02.jpg'],
 '1896 Summer Olympics':['Panathinaiko Stadium 1896.jpg','1896 Olympic marathon.jpg'],
 "Schindler's List":['Steven Spielberg, Berlinale 2023-3.jpg','MKr25402 Steven Spielberg (Berlinale 2023) (3x4 cropped).jpg'],
 'September 11 attacks':['World Trade Center towers, New York, New York LCCN2015645969 - restoration1.png'],
 'IBM Personal Computer':['Ibm pc 5150.jpg','IBM 5150 PC.JPG'],
 'Macintosh 128K':['Macintosh 128k computer, January 1984, by Bernard Gotfryd - (cropped to remove individual).jpg','Macintosh 128k Enter Museum.jpg'],
 'ARPANET':['First-IMP.jpg','Interface Message Processor.jpg'],
 'Compact disc':['Compact Disc Digital Audio (Back).jpg','CompactDisc.jpg'],
 'MIDI':['Korg M1 - audio & MIDI connectors (2017-02-15 18.31.24 by deepsonic).jpg'],
 'Motorola DynaTAC':['DynaTAC8000X.jpg','Motorola DynaTAC 8000X.jpg'],
 'Nokia 3310':['Nokia 3310 blue R7309170 (retouch).png','Nokia 3310.JPG'],
 'Windows 95':['Disquetes y CD-ROM de instalacion de Windows 95.jpg'],
}

SEED_ALIASES={
 'Telegraph':'Electrical telegraph',
 'China':"Proclamation of the People's Republic of China",
 'Michelson?Morley experiment':'Michelson–Morley experiment',
 'Soviet?Afghan War':'Soviet–Afghan War',
 'Long-playing record':'LP record',
 'Oil crisis of 1973':'1973 oil crisis',
 "Nelson Mandela's inauguration":'Presidency of Nelson Mandela',
}

REQUEST_LOCK=threading.Lock()
NEXT_REQUEST=0.0
COOLDOWN_PATH=CACHE/'network-cooldowns.json'
HOST_COOLDOWNS=json.loads(COOLDOWN_PATH.read_text(encoding='utf8')) if COOLDOWN_PATH.exists() else {}

def atomic(path,value):
 tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=True,indent=2)+'\n',encoding='utf8');tmp.replace(path)
def fetch(url):
 global NEXT_REQUEST
 if '--offline-only' in __import__('sys').argv:raise RuntimeError('Source is not in the local research cache; no request made')
 host=urlparse(url).hostname
 with REQUEST_LOCK:
  if HOST_COOLDOWNS.get(host,0)>time.time():raise RuntimeError('Source rate-limit cooldown active; no repeated request made')
  wait=max(0,NEXT_REQUEST-time.monotonic())
  if wait:time.sleep(wait)
  NEXT_REQUEST=time.monotonic()+1.1
 try:
   with urlopen(Request(url,headers={'User-Agent':'PixelMuseum/0.1 archival research (https://github.com/LoZazaMastro)'}),timeout=25) as response:return response.read(64<<20)
 except HTTPError as error:
  if error.code==429:
   try:seconds=max(60,int(error.headers.get('Retry-After','300')))
   except ValueError:seconds=300
   with REQUEST_LOCK:
    HOST_COOLDOWNS[host]=time.time()+seconds;atomic(COOLDOWN_PATH,HOST_COOLDOWNS)
  raise
def api(params):
 url='https://en.wikipedia.org/w/api.php?'+urlencode({'format':'json','formatversion':2,**params});p=CACHE/(hashlib.sha256(url.encode()).hexdigest()[:24]+'.json')
 if not p.exists():
  for attempt in range(3):
   try:p.write_bytes(fetch(url));break
   except Exception as error:
    if getattr(error,'code',0)==429 or 'cooldown' in str(error):raise
    if attempt==2:raise
    time.sleep(2+attempt*3)
 return json.loads(p.read_text(encoding='utf8'))
def clean(value):
 value=re.sub(r'<(?:style|script)\b[^>]*>.*?</(?:style|script)>','',value or '',flags=re.S|re.I)
 return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',value))).strip()

def html_photo_info(filename):
 url='https://commons.wikimedia.org/wiki/File:'+quote(filename.replace('_',' '))
 p=CACHE/('commons-'+hashlib.sha256(url.encode()).hexdigest()[:20]+'.html')
 if not p.exists():p.write_bytes(fetch(url))
 text=p.read_text(encoding='utf8');link=re.search(r'<div class="fullImageLink".*?<a href="([^"]+)"',text,re.S)
 if not link:return {}
 w=re.search(r'data-file-width="(\d+)"',text);h=re.search(r'data-file-height="(\d+)"',text)
 artist=re.search(r'id="fileinfotpl(?:_|&#95;)aut"[^>]*>.*?</td>\s*<td[^>]*>(.*?)</td>',text,re.S)
 lic=re.search(r'<span class="licensetpl(?:_|&#95;)short"[^>]*>(.*?)</span>',text,re.S)
 lu=re.search(r'<span class="licensetpl(?:_|&#95;)link"[^>]*>(.*?)</span>',text,re.S)
 description=re.search(r'id="fileinfotpl(?:_|&#95;)desc"[^>]*>.*?</td>\s*<td[^>]*>(.*?)</td>',text,re.S)
 return {'url':html.unescape(link.group(1)).split('?',1)[0],'descriptionurl':url,'width':int(w.group(1)) if w else 0,'height':int(h.group(1)) if h else 0,'extmetadata':{'Artist':{'value':clean(artist.group(1)) if artist else 'Photographer not identified in the source file description'},'LicenseShortName':{'value':clean(lic.group(1)) if lic else ''},'LicenseUrl':{'value':clean(lu.group(1)) if lu else ''},'ImageDescription':{'value':clean(description.group(1)) if description else filename}}}

def main():
 review_rows=[]
 for review_name in ['candidate-root-review.json','candidate-independent-review.json','candidate-editorial-review.json','candidate-milestone-followup-review.json']:
  review_path=CACHE/review_name
  review=json.loads(review_path.read_text(encoding='utf8')) if review_path.exists() else {}
  rows=review.get('entries',review.get('results',[]))
  if isinstance(rows,dict):rows=list(rows.values())
  review_rows.extend(rows)
 for row in review_rows:
  corrected_subject=row.get('subject_override') or row.get('corrected_subject')
  if row.get('status')=='verified' and corrected_subject:
   SEED_ALIASES[row['subject']]=corrected_subject
 approved={(row.get('year'),SEED_ALIASES.get(row.get('subject',''),row.get('subject','')).casefold()):row for row in review_rows if row.get('status')=='verified'}
 seeds=[(s[0],SEED_ALIASES.get(s[1],s[1]),s[2],s[3]) for s in SEEDS]
 curation_path=ROOT/'content/expansion/human-history-curation.json'
 curation=json.loads(curation_path.read_text(encoding='utf8')) if curation_path.exists() else {}
 display_titles={'Steamboat Willie':'The debut of Mickey Mouse'}
 extra_path=ROOT/'content/expansion/human-history-seeds-extra.json'
 if extra_path.exists():
  extras=json.loads(extra_path.read_text(encoding='utf8')).get('entries',[])
  user_extra_path=ROOT/'content/expansion/human-history-user-additions.json'
  if user_extra_path.exists():extras+=json.loads(user_extra_path.read_text(encoding='utf8')).get('entries',[])
  extras+=curation.get('requested_films',[])+curation.get('requested_awards',[])
  display_titles.update({e['subject']:e['display_title'] for e in extras if e.get('display_title')})
  extras=[{**extra,'subject':SEED_ALIASES.get(extra['subject'],extra['subject'])} for extra in extras]
  known={(s[0],s[1].casefold()) for s in seeds}
  for extra in extras:
   subject=extra['subject'];year=extra['year']
   if (year,subject.casefold()) in known:continue
   seeds.append((year,subject,subject,extra.get('date_note','A documented historical milestone associated with the subject.')))
   known.add((year,subject.casefold()))
 seeds.sort(key=lambda seed:(seed[0],seed[1]))
 curation_path=ROOT/'content/expansion/human-history-curation.json'
 excluded_subjects=curation.get('excluded_subjects',{})
 # The first published LOTR volume is a specific requested work; its broad
 # trilogy overview remains research context rather than a second1954stop.
 if any(seed[1]=='The Fellowship of the Ring' for seed in seeds):
  seeds=[seed for seed in seeds if seed[1]!='The Lord of the Rings']
 excluded_aliases={SEED_ALIASES.get(subject,subject) for subject in excluded_subjects}
 seeds=[seed for seed in seeds if seed[1] not in excluded_subjects and seed[1] not in excluded_aliases]
 selection_path=ROOT/'content/expansion/human-history-film-selection.json'
 film_keep=set(json.loads(selection_path.read_text(encoding='utf8')).get('keep_subjects',[])) if selection_path.exists() else set()
 film_keep.update(e['subject'] for e in curation.get('requested_films',[]))
 date_overrides={e['subject']:e['date'] for e in extras if e.get('date')} if extra_path.exists() else {}
 official_path=ROOT/'content/expansion/human-history-official-images.json'
 official_images=json.loads(official_path.read_text(encoding='utf8')).get('entries',{}) if official_path.exists() else {}
 extra_image_path=ROOT/'content/expansion/human-history-official-images-extra.json'
 if extra_image_path.exists():official_images.update(json.loads(extra_image_path.read_text(encoding='utf8')).get('entries',{}))
 root_image_path=ROOT/'content/expansion/human-history-official-images-root.json'
 if root_image_path.exists():official_images.update(json.loads(root_image_path.read_text(encoding='utf8')).get('entries',{}))
 for override_path in sorted((ROOT/'content/expansion').glob('human-history-official-images-*.json')):
  official_images.update(json.loads(override_path.read_text(encoding='utf8')).get('entries',{}))
 milestone_path=ROOT/'content/expansion/human-history-milestone-images.json'
 milestone_images=json.loads(milestone_path.read_text(encoding='utf8')).get('entries',{}) if milestone_path.exists() else {}
 def official_for(subject,year):return milestone_images.get(str(year)+'|'+subject) or official_images.get(subject)
 article_cache=CACHE/'articles.json'
 pages=json.loads(article_cache.read_text(encoding='utf8')) if article_cache.exists() else {}
 unresolved=[s for s in seeds if not pages.get(s[1],{}).get('extract')]
 for start in range(0,len(unresolved),12):
  batch=unresolved[start:start+12]
  try:result=api({'action':'query','titles':'|'.join(s[1] for s in batch),'redirects':1,'prop':'extracts|revisions|pageimages|images','exintro':1,'explaintext':1,'exlimit':'max','rvprop':'ids|timestamp','piprop':'original|name','pilicense':'any','imlimit':30})
  except Exception as error:
   print('History article batch held:',str(error),flush=True)
   if getattr(error,'code',0)==429 or 'cooldown' in str(error):break
   continue
  redirects={r['from']:r['to'] for r in result.get('query',{}).get('normalized',[])+result.get('query',{}).get('redirects',[])}
  for p in result.get('query',{}).get('pages',[]):pages[p['title']]=p
  for seed in batch:
   title=seed[1]
   while title in redirects:title=redirects[title]
   if title in pages:pages[seed[1]]=pages[title]
  atomic(article_cache,pages)
 atomic(CACHE/'articles.json',pages)
 # The images module limit applies to the entire query, not to each page.
 # Follow continuation explicitly: otherwise only a lead poster survives for
 # most batch members and useful native archival illustrations disappear.
 incomplete=list(dict.fromkeys(s[1] for s in seeds if pages.get(s[1],{}).get('pageid') and not pages[s[1]].get('_museum_images_complete')))
 for start in range(0,len(incomplete),18):
  batch=incomplete[start:start+18];pageids={pages[t]['pageid'] for t in batch};collected={pid:[] for pid in pageids};continuation={}
  try:
   while True:
    result=api({'action':'query','pageids':'|'.join(map(str,sorted(pageids))),'prop':'images','imlimit':'max',**continuation})
    for p in result.get('query',{}).get('pages',[]):collected.setdefault(p['pageid'],[]).extend(p.get('images',[]))
    continuation=result.get('continue',{})
    if not continuation:break
   for title in batch:
    pages[title]['images']=list({i['title']:i for i in collected[pages[title]['pageid']]}.values());pages[title]['_museum_images_complete']=True
   atomic(article_cache,pages)
   print('History complete image index',min(start+18,len(incomplete)),'/',len(incomplete),flush=True)
  except Exception as error:
   print('History image index held:',str(error),flush=True)
   if getattr(error,'code',0)==429 or 'cooldown' in str(error):break
 # Resolve source metadata in batches, retaining native dimensions and licence
 # fields. One file-description request per candidate is unnecessary and makes
 # a large attributed collection slower and more likely to hit rate limits.
 metadata_path=CACHE/'image-metadata.json'
 image_metadata=json.loads(metadata_path.read_text(encoding='utf8')) if metadata_path.exists() else {}
 filenames=[]
 for seed in seeds:
  page=pages.get(seed[1],{})
  names=PHOTO_FILES.get(seed[1],[page.get('pageimage','')]+[i['title'].removeprefix('File:') for i in page.get('images',[])])
  names=list(dict.fromkeys(f for f in names if re.search(r'\.(?:jpe?g|png|webp)$',f,re.I) and not re.search(r'logo|icon|flag|symbol|map|signature|Commons|Question|Broom|Wikimedia|Folder|Speaker|Ambox',f,re.I)))[:5]
  filenames.extend(names)
 missing_files=list(dict.fromkeys(f for f in filenames if f.replace('_',' ') not in image_metadata))
 for start in range(0,len(missing_files),40):
  try:
   result=api({'action':'query','titles':'|'.join('File:'+f for f in missing_files[start:start+40]),'prop':'imageinfo','iiprop':'url|size|extmetadata'})
   for p in result.get('query',{}).get('pages',[]):
    image_metadata[p['title'].removeprefix('File:').replace('_',' ')]=p.get('imageinfo',[{}])[0]
   atomic(metadata_path,image_metadata)
   print('History image metadata',min(start+40,len(missing_files)),'/',len(missing_files),flush=True)
  except Exception as error:
   print('History metadata batch held:',str(error),flush=True)
   if getattr(error,'code',0)==429 or 'cooldown' in str(error):break
 prior=json.loads((ROOT/'content/human-history.json').read_text(encoding='utf8')) if (ROOT/'content/human-history.json').exists() else {}
 candidate_path=CACHE/'illustrated-candidate-checkpoint.json'
 prior_candidates=json.loads(candidate_path.read_text(encoding='utf8')).get('entries',[]) if candidate_path.exists() else []
 done={(e.get('year'),e.get('provenance',{}).get('seed_title')):e for e in prior_candidates+prior.get('entries',[])}
 entries=[];held=[]
 def process(seed):
  year,requested,title,note=seed
  cached_key=(year,requested)
  prior_image=done.get(cached_key,{}).get('images',[{}])[0]
  manual_matches=requested not in PHOTO_FILES or requested in official_images or any(name.replace('_',' ').casefold() in unquote(prior_image.get('source_page','')).replace('_',' ').casefold() for name in PHOTO_FILES.get(requested,[]))
  if cached_key in done and manual_matches and '--refresh-images' not in sys.argv:
   record=copy.deepcopy(done[cached_key]);record['year']=year
   if official_for(requested,year):record['images']=[copy.deepcopy(official_for(requested,year))]
   if requested in date_overrides:record['date']=copy.deepcopy(date_overrides[requested])
   return record,None
  page=pages.get(requested,{})
  if not page.get('extract'):return None,{'title':requested,'reason':'No substantive English article'}
  photo_alias={'The Laws of Thought':'George Boole','Turing machine':'Alan Turing','A Symbolic Analysis of Relay and Switching Circuits':'Claude Shannon','BBC':'Broadcasting House','Cathode-ray tube':'Oscilloscope','NTSC':'Color television','Integrated circuit':'Jack Kilby','MOSFET':'MOSFET','MIDI':'MIDI keyboard','16:9 aspect ratio':'Widescreen','Ethernet':'Ethernet','Google':'Googleplex','Digital television transition in the United States':'High-definition television','Linux':'Linus Torvalds','September 11 attacks':'World Trade Center (1973–2001)','Flash memory':'Flash memory','Ultra-high-definition television':'4K resolution','Seven Samurai':'Akira Kurosawa','Vertigo (film)':'Alfred Hitchcock','Please Please Me':'The Beatles','Highway 61 Revisited':'Bob Dylan','2001: A Space Odyssey':'Stanley Kubrick','Blade Runner':'Ridley Scott',"Schindler's List":'Steven Spielberg','Memento (film)':'Christopher Nolan','Avatar (2009 film)':'James Cameron'}
  photo_page=page
  if requested in photo_alias:
   try:
    alias_result=api({'action':'query','titles':photo_alias[requested],'redirects':1,'prop':'pageimages|images','piprop':'original|name','pilicense':'any','imlimit':20})
    photo_page=alias_result.get('query',{}).get('pages',[page])[0]
   except Exception:
    article_url='https://en.wikipedia.org/wiki/'+quote(photo_alias[requested].replace(' ','_'));f=CACHE/('article-html-'+hashlib.sha256(article_url.encode()).hexdigest()[:20]+'.html')
    if not f.exists():f.write_bytes(fetch(article_url))
    names=re.findall(r'resource="[^"]*/(?:wiki/)?File:([^"]+)"',f.read_text(encoding='utf8'))
    photo_page={'images':[{'title':'File:'+unquote(html.unescape(name))} for name in names]}
  filenames=[photo_page.get('pageimage','')]+[i['title'].removeprefix('File:') for i in photo_page.get('images',[])]
  if requested in PHOTO_FILES:filenames=PHOTO_FILES[requested]
  filenames=list(dict.fromkeys(f for f in filenames if re.search(r'\.(?:jpe?g|png|webp)$',f,re.I) and not re.search(r'logo|icon|flag|symbol|map|signature|Commons|Question|Broom|Wikimedia|Folder|Speaker|Ambox',f,re.I)))[:9]
  choices={f.replace('_',' '):image_metadata.get(f.replace('_',' '),{}) for f in filenames}
  selected=None;photo_errors=[]
  captions={'Difference engine':'Difference Engine No.2, built later by the Science Museum from Babbage’s plans.','World Wide Web':'The NeXT computer used as the first web server at CERN, photographed later.','Computer mouse':'Engelbart’s early mouse prototype, photographed in a museum collection.','September 11 attacks':'Lower Manhattan and the World Trade Center in July2001, before the attacks.','Transistor':'The first point-contact transistor represented by a later museum replica.','Google':'The Google campus in Mountain View, photographed after the company’s foundation.','IBM Personal Computer':'IBM Personal Computer model5150, with its original-generation monitor and keyboard.'}
  for filename in filenames:
   image=choices.get(filename.replace('_',' '),{})
   meta=image.get('extmetadata',{})
   if not image.get('url') or not meta.get('LicenseShortName',{}).get('value'):
    try:image=html_photo_info(filename)
    except Exception:pass
   if max(image.get('width',0),image.get('height',0))<800:photo_errors.append(filename+': source below800px');continue
   url=image.get('url','').split('?',1)[0]
   # Acquire the public native master once. The bundler derives display sizes;
   # a remote thumbnail is neither the only source nor proof of native quality.
   f=CACHE/(hashlib.sha256(url.encode()).hexdigest()[:20]+Path(filename).suffix.lower())
   # An acquired derivative remains valid when a larger rendition is rate-limited.
   # Reuse it before issuing another request, including previously successful URLs
   # returned by the API rather than the file-description page.
   bases=[image.get('url','').split('?',1)[0],choices.get(filename.replace('_',' '),{}).get('url','').split('?',1)[0]]
   local_urls=[url]
   for base in bases:
    if '/commons/' not in base:continue
    local_urls.append(base)
    stem=base.split('/commons/',1)[1]
    for edge in [1920,1280,960,640]:
     if edge<=image.get('width',0):local_urls.append('https://upload.wikimedia.org/wikipedia/commons/thumb/'+stem+'/'+str(edge)+'px-'+stem.rsplit('/',1)[-1])
   for candidate_url in local_urls:
    candidate=CACHE/(hashlib.sha256(candidate_url.encode()).hexdigest()[:20]+Path(filename).suffix.lower())
    if candidate.is_file():url=candidate_url;f=candidate;break
   try:
    if not f.exists():
     try:f.write_bytes(fetch(url))
     except Exception as download_error:
      if getattr(download_error,'code',0)==429:raise
      if '/1920px-' in url:url=url.replace('/1920px-','/1280px-')
      elif image.get('width',0)>640 and '/commons/' in url and '/thumb/' not in url:
       stem=url.split('/commons/',1)[1];edge=1280 if image.get('width',0)>1280 else 960 if image.get('width',0)>960 else 640;url='https://upload.wikimedia.org/wikipedia/commons/thumb/'+stem+'/'+str(edge)+'px-'+stem.rsplit('/',1)[-1]
      else:raise
      f=CACHE/(hashlib.sha256(url.encode()).hexdigest()[:20]+Path(filename).suffix.lower())
      try:f.write_bytes(fetch(url))
      except Exception:
       if '/1280px-' not in url:raise
       url=url.replace('/1280px-','/960px-');f=CACHE/(hashlib.sha256(url.encode()).hexdigest()[:20]+Path(filename).suffix.lower());f.write_bytes(fetch(url))
    with Image.open(f) as im:im.load();w,h=im.size
    if max(w,h)<800:raise ValueError('Decoded image is below800px; no enlargement allowed')
    meta=image.get('extmetadata',{});artist=clean(meta.get('Artist',{}).get('value'));license=clean(meta.get('LicenseShortName',{}).get('value'));description=clean(meta.get('ImageDescription',{}).get('value'))
    if not license or not artist:photo_errors.append(filename+': absent author or licence');continue
    selected={'url':url,'title':description or filename,'creator':artist,'source_page':image.get('descriptionurl','https://commons.wikimedia.org/wiki/File:'+quote(filename)),'license':license,'license_url':meta.get('LicenseUrl',{}).get('value',''),'credit':artist+' / '+license,'width':w,'height':h,'recovery_local_source':f.relative_to(ROOT).as_posix(),'verification':{'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'native_dimensions':[w,h]},'story_paragraph':0,'caption':captions.get(requested,'')};break
   except Exception as ex:photo_errors.append(filename+': '+str(ex));continue
  selected=official_for(requested,year) or selected
  if not selected:return None,{'title':requested,'reason':'No attributed native-quality photograph acquired','filenames':filenames,'errors':photo_errors}
  text=page['extract'];paragraphs=[p for p in text.split('\n') if p.strip()]
  chosen=[];words=0
  for paragraph in paragraphs:
   sentences=re.split(r'(?<=[.!?])\s+',paragraph)
   part=[]
   for sentence in sentences:
    if words+len(sentence.split())>190 and words>=90:break
    part.append(sentence);words+=len(sentence.split())
   if part:chosen.append(' '.join(part))
   if words>=130 or len(chosen)>=3:break
  description='\n\n'.join(chosen);revision=page.get('revisions',[{}])[0].get('revid');source='https://en.wikipedia.org/w/index.php?title='+quote(page['title'].replace(' ','_'))+'&oldid='+str(revision)
  short=re.split(r'(?<=[.!?])\s+',description)[0]
  if len(short)>240:short=page['title']
  record={'id':'history-'+str(year)+'-'+re.sub('[^a-z0-9]+','-',requested.lower()).strip('-'),'title':page['title'],'kind':'history','year':year,'date':{'month':0,'day':0,'precision':'year'},'summary':short,'body':[description],'story_headings':[page['title']],'images':[selected],'sources':[{'title':page['title']+' — English Wikipedia, revision '+str(revision),'url':source,'publisher':'Wikipedia contributors','attribution':'Text excerpt from English Wikipedia; CC BY-SA 4.0. Revision and contributor history retained.','license':'CC BY-SA 4.0','license_url':'https://creativecommons.org/licenses/by-sa/4.0/'}],'provenance':{'seed_title':requested,'article_title':page['title'],'pageid':page['pageid'],'revision':revision,'date_note':note,'full_source_extract':text,'text_treatment':'Verbatim consecutive opening sentences; no invented connection to videogames.'}}
  if requested in date_overrides:record['date']=copy.deepcopy(date_overrides[requested])
  return record,None
 with ThreadPoolExecutor(max_workers=2) as pool:
  futures=[pool.submit(process,seed) for seed in seeds]
  for n,f in enumerate(as_completed(futures),1):
   try:entry,error=f.result()
   except Exception as ex:
    held.append({'reason':str(ex)});continue
   if entry:entries.append(entry)
   if error:held.append(error)
   if n%5==0:
    atomic(CACHE/'progress.json',{'planned':len(seeds),'processed':n,'admitted':len(entries),'held':len(held)})
    print('History',n,'/',len(seeds),'admitted',len(entries),'held',len(held),flush=True)
 atomic(CACHE/'illustrated-candidate-checkpoint.json',{'schema_version':1,'publication_status':'date_review_required','entries':entries})
 base_keys={(s[0],s[1].casefold()) for s in SEEDS}
 admitted=[]
 semantic_hold_path=ROOT/'content/expansion/human-history-image-holds.json'
 semantic_holds=json.loads(semantic_hold_path.read_text(encoding='utf8')).get('entries',{}) if semantic_hold_path.exists() else {}
 semantic_hold_rows=list(semantic_holds.items())
 visual_passes=set()
 def visual_subject(subject):
  subject=SEED_ALIASES.get(subject,subject)
  return pages.get(subject,{}).get('title',subject).casefold()
 for review_name in ['root-300-image-review.json','editorial-image-review.json']:
  review_path=CACHE/review_name
  if not review_path.exists():continue
  for row in json.loads(review_path.read_text(encoding='utf8')).get('entries',[]):
   if row.get('status') in ['pass','visual_pass']:
    for subject in [row.get('subject'),row.get('seed_subject'),row.get('article_title')]:
     if subject:visual_passes.add((visual_subject(subject),row.get('image_url')))
 for subject,image in official_images.items():
  if image.get('context_review_status','').upper().startswith('PASS') or image.get('context_review_status')=='verified':
   visual_passes.add((visual_subject(subject),image.get('url')))
 for milestone,image in milestone_images.items():
  if image.get('context_review_status','').upper().startswith('PASS'):
   visual_passes.add((visual_subject(milestone.split('|',1)[1]),image.get('url')))
 for hold_path in sorted((ROOT/'content/expansion').glob('human-history-image-holds-*.json')):
  semantic_hold_rows.extend(json.loads(hold_path.read_text(encoding='utf8')).get('entries',{}).items())
 for entry in entries:
  seed_subject=entry['provenance']['seed_title']
  lead=entry['provenance'].get('full_source_extract','').split('\n',1)[0]
  # Film stops are a finite curated selection. Actor biographies, television
  # series and articles discussing film technology do not enter this filter.
  is_film=bool(re.search(r'\bis an? \d{4}[^.;()]{0,150}\bfilm\b',lead[:320]))
  if is_film and film_keep and seed_subject not in film_keep:
   held.append({'title':seed_subject,'year':entry['year'],'reason':'Outside the focused foundational-film selection; research retained'})
   continue
  image_hold=next((row for subject,row in semantic_hold_rows if subject==entry['provenance']['seed_title'] and row.get('url')==entry['images'][0]['url']),{})
  if image_hold.get('url')==entry['images'][0]['url']:
   held.append({'title':entry['provenance']['seed_title'],'year':entry['year'],'reason':'Visual subject review: '+image_hold['reason']})
   continue
  visual_key=(visual_subject(entry['provenance']['seed_title']),entry['images'][0]['url'])
  if visual_key not in visual_passes:
   held.append({'title':entry['provenance']['seed_title'],'year':entry['year'],'reason':'Exact subject and era image review pending','image_url':entry['images'][0]['url']})
   continue
  key=(entry['year'],entry['provenance']['seed_title'].casefold())
  if key not in base_keys and key not in approved:
   held.append({'title':entry['provenance']['seed_title'],'year':entry['year'],'reason':'Illustrated source acquired; independent milestone/date review pending'})
   continue
  if key in approved:
   checked=copy.deepcopy(approved[key]);entry['provenance']['milestone_verification']=checked
   if checked.get('date_note_override') or checked.get('review_note'):entry['provenance']['date_note']=checked.get('date_note_override') or checked['review_note']
   if checked.get('corrected_year'):entry['year']=checked['corrected_year']
   if checked.get('date'):entry['date']=copy.deepcopy(checked['date'])
  admitted.append(entry)
 entries=admitted
 image_overrides=json.loads((ROOT/'content/expansion/human-history-image-overrides.json').read_text(encoding='utf8')).get('entries',{}) if (ROOT/'content/expansion/human-history-image-overrides.json').exists() else {}
 for entry in entries:
  entry['title']=display_titles.get(entry['provenance']['seed_title'],{'IPod':'iPod','IPhone (1st generation)':'iPhone'}.get(entry['provenance']['article_title'],entry['provenance']['article_title']));entry['story_headings']=[entry['title']]
  subject=entry['provenance']['seed_title']
  entry['id']='history-'+str(entry['year'])+'-'+re.sub('[^a-z0-9]+','-',subject.lower()).strip('-')
  if subject=='Marie Curie' and entry['year']==1903:
   entry['title']="Marie Curie's Nobel Prizes";entry['story_headings']=[entry['title']]
   sentences=re.split(r'(?<=[.!?])\s+',entry['provenance']['full_source_extract'])
   prize_text=' '.join(s.strip() for s in sentences if re.search(r'Nobel|\b1903\b|\b1911\b',s) and not re.search(r'In addition|Poland declared',s))
   if prize_text:entry['body']=[prize_text];entry['summary']=next((s for s in sentences if '1903 Nobel' in s),entry['summary'])
  if subject=='Pluto' and entry['year']==2006:
   entry['title']="Pluto's reclassification";entry['story_headings']=[entry['title']]
  override=image_overrides.get(entry['id'],{})
  if override.get('url')==entry['images'][0]['url']:
   for field in ['caption','title','context_review','context_review_status']:
    if field in override:entry['images'][0][field]=override[field]
 entries.sort(key=lambda e:(e['year'],e['id']))
 # Explicit corrections must be reflected by the published asset, not merely
 # stored under an unused canonical article-title alias.
 for entry in entries:
  seed_subject=entry.get('provenance',{}).get('seed_title')
  if seed_subject=='Sinclair ZX80':
   expected=official_for(seed_subject,entry['year'])
   if not expected or entry['images'][0]['url']!=expected['url'] or 'ZXSpectrum' in entry['images'][0]['url']:
    raise ValueError('ZX80 correction failed to reach the published image')
 recent_path=ROOT/'content/expansion/human-history-recent-reviewed.json'
 if recent_path.exists():
  recent=json.loads(recent_path.read_text(encoding='utf8'))
  if recent.get('status')=='text_date_and_image_reviewed':
   additions=recent.get('entries',[]);ids={e['id'] for e in additions}
   for record in additions:
    if not record.get('body') or not record.get('images') or not record.get('sources'):raise ValueError('Incomplete recent history record: '+record.get('id',''))
   entries=[e for e in entries if e['id'] not in ids]+copy.deepcopy(additions)
   entries.sort(key=lambda e:(e['year'],e.get('date',{}).get('month',0),e.get('date',{}).get('day',0),e['id']))
 september11_join=runpy.run_path(str(ROOT/'content/expansion/reviewed_history_september11.py'))
 atomic(CACHE/'september11-reviewed-integration-audit.json',september11_join['apply'](entries,ROOT))
 era_text_join=runpy.run_path(str(ROOT/'content/expansion/reviewed_history_era_text.py'))
 atomic(CACHE/'historic-era-text-integration-audit.json',era_text_join['apply'](entries,ROOT))
 reviewed_media_join=runpy.run_path(str(ROOT/'content/expansion/reviewed_ready_three_editorial.py'))
 atomic(CACHE/'youtube2005-image-integration-audit.json',reviewed_media_join['apply'](entries,ROOT,'museum-youtube2005-image-reviewed.json'))
 atomic(CACHE/'rita-selected-portrait-integration-audit.json',reviewed_media_join['apply'](entries,ROOT,'museum-rita-selected-portrait-reviewed.json'))
 film_display_join=runpy.run_path(str(ROOT/'content/expansion/history_film_display_titles.py'))
 atomic(CACHE/'film-display-title-integration-audit.json',film_display_join['apply'](entries))
 person_event_join=runpy.run_path(str(ROOT/'content/expansion/reviewed_history_person_events.py'))
 atomic(CACHE/'person-event-text-integration-audit.json',person_event_join['apply'](entries,ROOT))
 # Reviewed user-requested whole history owners, after existing corrections.
 user_join=runpy.run_path(str(ROOT/'content/expansion/reviewed_2012_mixed_owner_layer.py'))
 atomic(CACHE/'user-requested-reviewed-integration-audit.json',user_join['apply'](entries,ROOT,ROOT/'content/expansion/human-history-user-requested-reviewed-layer.json'))
 final_english=runpy.run_path(str(ROOT/'content/expansion/final_english_layer.py'))
 final_policy=json.loads((ROOT/'content/expansion/final-english-publication-policy.json').read_bytes())
 atomic(CACHE/'final-english-integration-audit.json',final_english['apply'](entries,ROOT,'human-history',final_policy['manifest'],final_policy['review']))
 # Category metadata is independent of editorial prose and survives regeneration.
 category_map=json.loads((ROOT/'content/expansion/culture-categories.json').read_text(encoding='utf8'))['entries']
 for entry in entries:
  if entry['id'] in category_map:entry['culture_category']=category_map[entry['id']]
 entries.sort(key=lambda e:(e['year'],e.get('date',{}).get('month',0),e.get('date',{}).get('day',0),e['id']))
 if len({e['id'] for e in entries})!=len(entries):raise ValueError('Duplicate historical milestone IDs; publication aborted')
 atomic(ROOT/'content/human-history.json',{'schema_version':1,'title':'A wider history','entries':entries})
 atomic(CACHE/'audit.json',{'planned':len(seeds),'admitted':len(entries),'held':held})
 print('HISTORY',len(entries),'HELD',len(held),flush=True)

if __name__=='__main__':main()
