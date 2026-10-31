"""One exhibit per subject, local photographs and a chronology of actual releases.

Authoring imports stay untouched. This final projection removes obsolete calendar
wrappers and preserves their useful writing and provenance on the subject itself.
"""
from __future__ import annotations
import copy,json,re,runpy,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def key(text):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',text.replace('\u2122','').replace('\u00ae','')).encode('ascii','ignore').decode().lower())
def read(path,default):return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def apply(entries):
 report={'schema_version':1,'removed':[],'aliases':{},'split_groups':[],'added':[],'cover_changes':[],'template_paragraphs_held':0}
 by_id={e['id']:e for e in entries};groups={}
 def remove(e,reason):report['removed'].append({'id':e['id'],'title':e['title'],'reason':reason})
 def enrich(target,source,body=None,headings=None):
  existing=set(target.get('body',[]));incoming=source.get('body',[]) if body is None else body
  titles=source.get('story_headings',[]) if headings is None else headings
  target.setdefault('story_headings',[])
  while len(target['story_headings'])<len(target.get('body',[])):target['story_headings'].append(target.get('subtitle') or target['title'])
  for n,paragraph in enumerate(incoming):
   if paragraph in existing:continue
   if re.search(r'belongs in this calendar|this chapter turns on|The useful way to read this part|becomes easier to understand when|The key question here is how|Concrete reference points such as|changes scale when this chapter',paragraph):report['template_paragraphs_held']+=1;continue
   target.setdefault('body',[]).append(paragraph);target['story_headings'].append(titles[n] if n<len(titles) else target.get('subtitle') or target['title']);existing.add(paragraph)
  known={i['url'] for i in target.get('images',[])}
  for image in source.get('images',[]):
   if image.get('url') not in known:
    image=copy.deepcopy(image);image.pop('story_paragraph',None);target.setdefault('images',[]).append(image);known.add(image['url'])
  for field,unique in [('videos','youtube_id'),('sources','url')]:
   known={i.get(unique) for i in target.get(field,[])}
   for item in source.get(field,[]):
    if item.get(unique) not in known:target.setdefault(field,[]).append(copy.deepcopy(item));known.add(item.get(unique))
  known_features={feature.get('id') for feature in target.get('editorial_features',[])}
  for feature in source.get('editorial_features',[]):
   if feature.get('id') not in known_features:target.setdefault('editorial_features',[]).append(copy.deepcopy(feature));known_features.add(feature.get('id'))
  if not target.get('soundtrack') and source.get('soundtrack'):target['soundtrack']=copy.deepcopy(source['soundtrack'])
  if not target.get('models') and source.get('models'):target['models']=copy.deepcopy(source['models'])
 def from_group(source_id,title,identifier,year,date,segments,subject_token,kind='game',target_id=None,extra_body=None):
  if source_id not in by_id:return by_id.get(target_id or identifier)
  source=by_id[source_id];paragraphs=[source['body'][n] for n in segments];headings=[source['story_headings'][n] for n in segments]
  target=by_id.get(target_id or identifier)
  if target is None:
   target={k:copy.deepcopy(source.get(k,[] if k in ['sources','tags'] else '')) for k in ['sources','tags','editorial_credit','provenance']}
   target.update(id=identifier,title=title,subtitle=headings[0] if headings else title,summary=paragraphs[0] if paragraphs else extra_body[0],year=year,kind=kind,era_id='origins' if year<1970 else 'public-play' if year<1983 else 'personal' if year<1990 else 'dimensions' if year<2000 else 'connected' if year<2010 else 'everywhere',date={'month':date[0],'day':date[1],'precision':'day' if date[1] else 'year','region':''},body=[],story_headings=[],images=[],videos=[],models=[],related_ids=[],layout='essay',editorial_mode='playhub_story',calendar_only=False)
   entries.append(target);by_id[identifier]=target;report['added'].append(identifier)
  passage_source={**source,'images':[],'videos':[],'models':[]}
  enrich(target,passage_source,paragraphs,headings)
  # Group media is re-associated by named subject, never by its old shared position.
  target['images']=[i for i in target.get('images',[]) if source_id not in i.get('title','')]
  for image in source.get('research_media_refs',{}).get('images',[]):
   subject=key(image.get('subject','')+' '+image.get('file',''))
   if key(subject_token) not in subject:continue
   file=ROOT.parent.parent/'Plugin/Playhub/assets/on-this-day/v1'/image.get('file','')
   if not file.is_file():continue
   try:
    from PIL import Image
    with Image.open(file) as photo:w,h=photo.size
   except Exception:continue
   if max(w,h)<1200:continue
   if image['url'] in {i['url'] for i in target['images']}:continue
   target['images'].append({'url':image['url'],'title':title+' — archive image','width':w,'height':h,'credit':image.get('credit') or 'Game imagery: respective publisher and rights holders / Playhub collection','source_page':image['url'],'license':'Original publisher rights; historical illustration','license_url':''})
  if extra_body:
   enrich(target,{'body':extra_body,'story_headings':[title,'Reading the systems','Playing together'],'images':[],'videos':[],'sources':[]})
  groups.setdefault(source_id,[]).append(target['id']);return target
 # Original cross-subject editions are split at their actual chapter boundaries.
 from_group('daily-10-18','Nintendo Entertainment System','nes',1985,(10,18),range(1,7),'nintendoentertainmentsystem','console','nes')
 from_group('daily-10-18','Shadow of the Colossus','shadow-of-the-colossus',2005,(10,18),range(7,13),'shadowofthecolossus')
 from_group('daily-10-18','Batman: Arkham City','batman-arkham-city',2011,(10,18),range(13,19),'arkhamcity')
 from_group('daily-04-06',"Conker's Bad Fur Day",'conkers-bad-fur-day',2001,(4,6),range(1,7),'conkersbadfurday')
 from_group('daily-04-06','Oddworld: Soulstorm','oddworld-soulstorm',2021,(4,6),[],'soulstorm',extra_body=["Oddworld: Soulstorm follows Abe and a community of Mudokons through factories, moving trains and industrial landscapes. Guiding followers turns movement into a collective problem: an escape is successful only when the people following Abe can survive it too.","Crafting and scavenging introduce tools made from the resources found along the route. The player reads machinery, patrols and safe spaces before deciding when to move a group. Its cinematic presentation frames that planning as part of a larger struggle over labour and control."])
 from_group('daily-03-07','NieR:Automata','workbook-02-23-nier-automata',2017,(2,23),range(1,7),'nierautomata',target_id='workbook-02-23-nier-automata')
 from_group('daily-03-07','Burnout Revenge','burnout-revenge',2005,(9,13),range(7,10),'burnoutrevenge')
 from_group('daily-03-07','I Am Alive','i-am-alive',2012,(3,7),range(10,13),'iamalive')
 from_group('daily-03-07',"Tom Clancy's Ghost Recon Wildlands",'ghost-recon-wildlands',2017,(3,7),range(13,16),'wildlands',extra_body=["Tom Clancy's Ghost Recon Wildlands places a four-person squad in an open reconstruction of Bolivia. Reconnaissance, synchronized shots and approaches from different directions give cooperative players room to plan a fight before they begin it."])
 from_group('daily-02-09',"Dante's Inferno",'dantes-inferno',2010,(2,4),range(1,4),'dantesinferno')
 from_group('daily-02-09','BioShock 2','bioshock-2',2010,(2,9),range(4,7),'bioshock',extra_body=["BioShock 2 returns to Rapture through Subject Delta, a Big Daddy linked to a Little Sister. The drill and weapons can be combined with plasmid powers, turning familiar corridors into spaces for preparing traps, controlling crowds and protecting a vulnerable companion."])
 from_group('daily-03-15','Homefront','homefront',2011,(3,15),range(1,4),'homefront')
 from_group('daily-03-15',"Tom Clancy's The Division 2",'the-division-2',2019,(3,15),[],'2221490',extra_body=["Tom Clancy's The Division 2 places a squad of agents in Washington, DC. Its open-world structure connects patrols, missions and a base of operations, while the cover-based firefights reward the team that reads sightlines and combines its equipment.","Weapons, crafted gear and unlockable skills let agents specialize without locking them into a single permanent role. Dark Zones add other players to the danger, while the endgame introduces a new faction and signature weapons. The city becomes a space for both repeated cooperation and contested resources."])
 # A current hardware exhibit is included without borrowing the previous console's 3D mesh.
 if 'switch-2' not in by_id:
  imagebase='https://www.nintendo.co.jp/corporate/release/2025/img_250402/'
  sourceurl='https://www.nintendo.co.jp/corporate/release/2025/250402.html'
  switch2={'id':'switch-2','title':'Nintendo Switch 2','subtitle':'The familiar hybrid, with a new set of inputs','year':2025,'kind':'hardware','era_id':'everywhere','date':{'month':6,'day':5,'precision':'day','region':''},'summary':'Nintendo Switch 2 keeps the hybrid console idea while changing how its controllers attach, move and connect players.','body':["Nintendo Switch 2 keeps the portable screen and television dock at the centre of its design. Its larger 7.9-inch display gives that familiar arrangement more room, while the new dock supports higher-resolution output on a television.","Joy-Con 2 controllers attach magnetically and can also act as mouse-like pointing devices in supported software. A physical connection, a hand-held gesture and a movement across a table become different ways to control the same machine.","GameChat adds conversation and screen sharing to the system interface. Compatibility with much of the first Nintendo Switch library connects the new hardware to an existing collection rather than treating every generation as a clean break."],'story_headings':['A larger window','Controllers that change roles','A collection that continues'],'images':[{'url':imagebase+name,'title':title,'width':w,'height':h,'creator':'Nintendo','credit':'Nintendo / official product photography','source_page':sourceurl,'license':'Nintendo promotional imagery; original publisher rights','license_url':''} for name,title,w,h in [('mainvisual.png','Nintendo Switch 2 with Joy-Con 2 controllers',1960,974),('img02_01.png','Nintendo Switch 2 display',1960,842),('img03_01.png','Magnetic Joy-Con 2 connection',2368,984)]],'videos':[],'models':[],'sources':[{'title':'Nintendo Switch 2 release and hardware details','url':sourceurl,'publisher':'Nintendo'}],'tags':['Console','Hybrid design'],'related_ids':['switch'],'layout':'essay','calendar_only':False,'editorial_mode':'curated_story','editorial_credit':'Original exhibition text for Pixel Museum.','model_pending':True}
  entries.append(switch2);by_id['switch-2']=switch2;report['added'].append('switch-2')
 # This exhibit is introduced after the base assembler's model join. Attach
 # the newly approved real Switch 2 asset here as well, without another stop.
 authoring_models=runpy.run_path(str(ROOT/'content/expansion/user_console_png_policy.py'))['authoring_models'](ROOT)
 switch2_model=next((m for m in authoring_models if m.get('exhibit_id')=='switch-2'),None)
 if switch2_model:
  by_id['switch-2']['models']=[{k:copy.deepcopy(v)for k,v in switch2_model.items()if k!='exhibit_id'}]
  by_id['switch-2']['kind']='console';by_id['switch-2']['model_pending']=False
 for filename in ['museum-awards-additions.json','major-release-additions.json','franchise-mainline-additions.json','user-requested-game-additions.json','museum-person-additions.json','museum-series-splits.json']:
  for e in read(ROOT/'content/expansion'/filename,{}).get('entries',[]):
   if e['id'] not in by_id:entries.append(copy.deepcopy(e));by_id[e['id']]=entries[-1];report['added'].append(e['id'])
 for entry_id,related in read(ROOT/'content/expansion/museum-person-additions.json',{}).get('related_links',{}).items():
  if entry_id in by_id:
   target=by_id[entry_id];target['related_ids']=list(dict.fromkeys(target.get('related_ids',[])+related))
 corrections={}
 for correction_file in ['museum-release-date-corrections.json','museum-identity-corrections.json']:
  corrections.update(read(ROOT/'content/expansion'/correction_file,{}).get('entries',{}))
 for entry_id,correction in corrections.items():
  if entry_id not in by_id:continue
  target=by_id[entry_id]
  for field in ['year','date','factual_note']:
   if field in correction:target[field]=copy.deepcopy(correction[field])
  if 'year' in correction:
   year=target['year'];target['era_id']='origins' if year<1970 else 'public-play' if year<1983 else 'personal' if year<1990 else 'dimensions' if year<2000 else 'connected' if year<2010 else 'everywhere'
  target['sources'].extend(copy.deepcopy(correction.get('sources',[])))
  if correction.get('release_date_audit'):target.setdefault('provenance',{})['release_date_audit']=copy.deepcopy(correction['release_date_audit'])
  if entry_id=='wikipedia-11556966':target['body']=[text.replace('It was released for the Microsoft Windows platform in December 2001.','The Windows game entered public open beta on 18 December 2003, followed by commercial operation in January 2004.') for text in target.get('body',[])]
 # Franchise redirects are useful context, but the exhibit introduces the
 # original game. Keep the imported series prose after an explicit game lead.
 original_leads=read(ROOT/'content/expansion/museum-original-game-leads.json',{}).get('query',{}).get('pages',[])
 lead_ids={'Bubble Bobble (video game)':'wikipedia-75994825','Bayonetta (video game)':'wikipedia-65005347','Splatoon (video game)':'wikipedia-52874820'}
 for page in original_leads:
  target=by_id.get(lead_ids.get(page.get('title')))
  if not target:continue
  lead=page.get('extract','').split('\n')[0].strip()
  if not lead:continue
  target['body'][0]=lead+'\n\nSeries context: '+target['body'][0]
  target.setdefault('provenance',{})['article_title']=page['title']
  revision=page.get('revisions',[{}])[0].get('revid')
  target['sources'].insert(0,{'title':page['title']+' — original game article revision','url':'https://en.wikipedia.org/w/index.php?oldid='+str(revision),'publisher':'English Wikipedia contributors'})
  if page['title'].startswith('Bubble Bobble'):
   target['summary']='Bub and Bob trap enemies in bubbles across one hundred single-screen stages. Taito’s 1986 arcade game turns shared space, timing and cooperation into a playful system of chain reactions.'
   target['date']={'month':9,'day':0,'precision':'month','region':''}
   target['body']=[text.replace('originally released on June 16, 1986 in Japan','originally released in September 1986 in Japan') for text in target['body']]
  elif page['title'].startswith('Bayonetta'):
   target['summary']='Bayonetta turns a last-second dodge into an opening for attack. PlatinumGames’ 2009 action game connects Witch Time, flowing combos and Mari Shimazaki’s character design in a precise combat system.'
   target['date']={'month':10,'day':29,'precision':'day','region':''}
  else:
   target['summary']='Ink is both a weapon and a route through the map. Nintendo’s 2015 Wii U shooter links territory control, movement and transformation in four-player teams of Inklings.'
   target['date']={'month':5,'day':28,'precision':'day','region':''}
 for e in entries:
  translations={'Pokémon Giallo':'Pokémon Yellow','Pokémon Smeraldo':'Pokémon Emerald','Pokémon X e Pokémon Y':'Pokémon X and Y','Kinect per Xbox 360':'Kinect for Xbox 360'}
  for old,new in translations.items():
   if old in e['title']:
    e['title']=e['title'].replace(old,new);e['subtitle']=e.get('subtitle','').replace(old,new);e['summary']=e.get('summary','').replace(old,new);e['body']=[text.replace(old,new) for text in e.get('body',[])];e['story_headings']=[text.replace(old,new) for text in e.get('story_headings',[])]
 split_spec=read(ROOT/'content/expansion/museum-series-splits.json',{})
 held=set(groups)|set(split_spec.get('replace_map',{}))|set(split_spec.get('context_only',[]))
 for source_id,destinations in split_spec.get('replace_map',{}).items():
  report['split_groups'].append({'source_id':source_id,'destinations':destinations});report['aliases'][source_id]=destinations[0]
 for source_id in split_spec.get('context_only',[]):
  if source_id in by_id:remove(by_id[source_id],'Franchise context retained in authoring; not a single-game release')
 for source_id,destinations in groups.items():report['split_groups'].append({'source_id':source_id,'destinations':destinations});report['aliases'][source_id]=destinations[0]
 forbidden={'maddennfl22','maddennfl21','maddennfl2001','fifa23','tomclancysghostreconbreakpoint'}
 incidental={'holiday','ricorrenza_globale','ricorrenza'}
 for e in entries:
  if e['id'] in held:remove(e,'Cross-subject edition split into individual exhibits');continue
  if key(e['title']) in forbidden:held.add(e['id']);remove(e,'Routine annual edition or specifically excluded title');continue
  theme=e.get('provenance',{}).get('source_theme_kind')
  if e.get('calendar_only') and theme in incidental:held.add(e['id']);remove(e,'Calendar occasion is not this subject’s release');continue
 # Preserve a real accessibility device on its commercial release, not the
 # unrelated United Nations observance used by the original calendar edition.
 adaptive=by_id.get('daily-12-03')
 if adaptive:
  held.discard(adaptive['id']);report['removed']=[item for item in report['removed'] if item['id']!=adaptive['id']];adaptive['calendar_only']=False;adaptive['date']={'month':9,'day':4,'precision':'day','region':''}
  adaptive['summary']='Two large buttons form a hub for switches, joysticks and other assistive devices. The Xbox Adaptive Controller makes the arrangement of physical controls a design choice shaped around each player.'
  adaptive['event_semantics']='Commercial release of the Xbox Adaptive Controller, 4 September 2018.'
  adaptive['body'][0]='The Xbox Adaptive Controller turns a controller into a configurable system. Two large programmable buttons sit on a central hub, while external switches, buttons and joysticks can be connected and arranged around a player. Microsoft developed the device with players with limited mobility and accessibility organizations, treating physical differences as design requirements. It reached commercial release on 4 September 2018.'
  adaptive['body']=[text.replace('The December 3 observance offers an appropriate context for remembering this method without reducing disability to a celebratory theme. ','') for text in adaptive['body']]
  adaptive['sources'].append({'title':'Xbox Adaptive Controller commercial launch, 4 September 2018','url':'https://news.xbox.com/en-us/2018/09/04/gaming-gets-more-inclusive-with-the-launch-of-the-xbox-adaptive-controller/','publisher':'Microsoft Xbox Wire'})
 # The Switch announcement is not another console; regional launches share one object.
 forced={'wikipedia-846968':'workbook-06-21-driv3r','daily-09-09':'playstation','daily-01-12':'switch','daily-08-31':'wikipedia-2053053','wikipedia-417121':'pokemon','workbook-06-03-super-mario-bros-2-famicom-disk-system':'wikipedia-147941','wikipedia-81801001':'wikipedia-75726993','workbook-08-23-nintendo-64':'nintendo-64','workbook-05-11-sega-saturn':'sega-saturn','daily-09-05':'workbook-12-08-yakuza','workbook-01-05-bayonetta-video-game':'wikipedia-65005347','workbook-10-06-baldur-s-gate-3':'wikipedia-60979422'}
 canonical={}
 for e in entries:
  if e['id'] not in held and not e.get('calendar_only'):
   identity=(key(e['title']),e['year'])
   if e['id'].startswith('the-game-awards-'):identity=e['id']
   rank=(bool(e.get('models')),e.get('editorial_mode')=='curated_story',not e['id'].startswith('wikipedia-'),len(e.get('body',[])))
   if identity not in canonical or rank>canonical[identity][0]:canonical[identity]=(rank,e)
 for e in entries:
  if e['id'] in held:continue
  identity=(key(e['title']),e['year']);target=by_id.get(forced.get(e['id']) or e.get('linked_exhibit_id',''))
  if target and (target['id'] in held or target is e):target=None
  if target is None and not e['id'].startswith('the-game-awards-'):target=canonical.get(identity,(None,None))[1]
  if target is not None and target is not e:
   enrich(target,e);report['aliases'][e['id']]=target['id'];held.add(e['id']);remove(e,'Same subject; narrative and media retained on its canonical exhibit')
   if target.get('date',{}).get('precision')!='day' and target['year']==e['year'] and e.get('date',{}).get('precision')=='day':target['date']=copy.deepcopy(e['date'])
   elif target.get('date',{}).get('precision')!='day' and target['year']==e['year'] and e.get('calendar') and e.get('provenance',{}).get('source_theme_kind','').startswith(('uscita','release','lancio')):target['date']={**e['calendar'],'precision':'day','region':''}
 # Keep real release metadata, not a scheduled editorial slot, in the runtime chronology.
 for e in entries:
  if e['id'] in held:continue
  if e.get('calendar_only'):
   theme=e.get('provenance',{}).get('source_theme_kind','')
   release=theme.startswith(('uscita','release','lancio')) or theme in {'nascita','birth','fondazione','foundation'}
   if release and e.get('date',{}).get('precision')!='day' and e.get('calendar'):
    e['date']={**e['calendar'],'precision':'day','region':''}
   e['calendar_only']=False
  e.pop('calendar',None);e.pop('linked_exhibit_id',None)
  e['date']['region']=''
  if e['id']=='xbox-halo':e['title']='Xbox'
  if e['id']=='switch':e['date']={'month':3,'day':3,'precision':'day','region':''}
  if e['id']=='nes':e['date']={'month':10,'day':18,'precision':'day','region':''}
  if e['id']=='workbook-01-29-resident-evil-2-1998-video-game':e['date']={'month':1,'day':21,'precision':'day','region':''}
  for image in e.get('images',[]):
   changes={'https://upload.wikimedia.org/wikipedia/commons/2/2d/John_Carmack_2025.jpg':'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/John_Carmack_2025.jpg/1920px-John_Carmack_2025.jpg','https://upload.wikimedia.org/wikipedia/commons/3/32/Signed_Pong_Cabinet.jpg':'https://thumb.wikimedia.org/wikipedia/commons/thumb/3/32/Signed_Pong_Cabinet.jpg/1920px-Signed_Pong_Cabinet.jpg'}
   if image['url'] in changes:image['original_url']=image['url'];image['url']=changes[image['url']]
  e['images']=[i for i in e.get('images',[]) if i['url']!='https://upload.wikimedia.org/wikipedia/commons/e/e2/Carol_Shaw_photo.jpg']
  # Recover named, useful-size original illustrations from the existing Playhub
  # archive. No cross-subject calendar image or generic banner is substituted.
  if not e.get('images'):
   for image in e.get('research_media_refs',{}).get('images',[]):
    subject=key(image.get('subject',''));title_key=key(e['title'])
    if not subject or not (subject==title_key or (len(title_key)>8 and title_key in subject)):continue
    if ' / ' in image.get('subject',''):continue
    file=ROOT.parent.parent/'Plugin/Playhub/assets/on-this-day/v1'/image.get('file','')
    if not file.is_file():continue
    try:
     from PIL import Image
     with Image.open(file) as photo:w,h=photo.size
    except Exception:continue
    if max(w,h)<1200:continue
    e['images'].append({'url':image['url'],'title':e['title']+' — archive image','width':w,'height':h,'credit':image.get('credit') or 'Original rights holders / Playhub historical collection','source_page':image['url'],'license':'Original rights retained; historical illustration from the Playhub collection','license_url':''})
  # Prefer a genuine game cover or a normally proportioned artwork to a strip hero.
  override=None
  for coverfile in ['cover-proportion-overrides.json','museum-cover-recoveries-games.json','museum-cover-recoveries-origins.json','museum-cover-recoveries-origins-extra.json','museum-cover-recoveries-root.json','museum-cover-recoveries-semantic.json','museum-cover-recoveries-aaa.json','museum-cover-recoveries-aliases.json','museum-cover-recoveries-people.json','museum-cover-recoveries-identity.json','museum-cover-recoveries-arcade.json','museum-cover-recoveries-priority.json','museum-cover-recoveries-portraits.json','museum-cover-recoveries-quality-root.json','museum-cover-recoveries-quality-editorial.json']:
   candidate=read(ROOT/'content/expansion'/coverfile,{}).get('entries',{}).get(e['id'])
   if candidate:override=candidate
  if override:
   superseded=set(override.get('supersedes_urls',[]))|{override['url']}
   e['images']=[i for i in e['images'] if i['url'] not in superseded];e['images'].insert(0,copy.deepcopy(override));report['cover_changes'].append(e['id'])
  if e['id']=='workbook-01-17-shinichi-nakamoto':e['images']=[i for i in e['images'] if 'wonder boy' not in i.get('title','').lower()]
  rejected_database_ids={'128443','22409','210111','452938','457652','174886','181595','195241','453172','27521','184369','462845','175958','184248'}
  e['images']=[i for i in e.get('images',[]) if str((i.get('identity_evidence') if isinstance(i.get('identity_evidence'),dict) else {}).get('database_id','')) not in rejected_database_ids]
  if e.get('images'):
   photos=e['images'];candidates=[(0 if any(x in i.get('title','').lower() for x in ['cover','box art','key art']) else 1,n) for n,i in enumerate(photos) if i.get('height',0)>0 and i.get('width',0)/i['height']<=1.95]
   if candidates:e['preferred_image']=min(candidates)[1]
   portraits=[n for n,image in enumerate(photos) if image.get('portrait')]
   if e.get('kind')=='person' and portraits:e['preferred_image']=portraits[0]
  if e['id'].startswith('the-game-awards-'):
   annual=[n for n,image in enumerate(e.get('images',[])) if image.get('story_paragraph')==2+e['year']-2014]
   if annual:e['preferred_image']=annual[0]
  e['related_ids']=[report['aliases'].get(i,i) for i in e.get('related_ids',[]) if i not in held or i in report['aliases']]
 artifacts={}
 for artifactfile in ['museum-narrative-artifacts.json','museum-secondary-artifacts-people.json','museum-secondary-artifacts-kates.json','museum-secondary-artifacts-root-reviewed.json','museum-secondary-artifacts-editorial-reviewed.json']:
  for entry_id,photos in read(ROOT/'content/expansion'/artifactfile,{}).get('entries',{}).items():artifacts.setdefault(entry_id,[]).extend(photos)
 for e in entries:
  known={i['url'] for i in e.get('images',[])}
  for image in ([] if e['id'] in {'wikipedia-878616','wikipedia-6896436','tetris'} else artifacts.get(e['id'],[])):
   if str(image.get('identity_evidence',{}).get('database_id','')) in rejected_database_ids:continue
   if image['url'] not in known:e['images'].append(copy.deepcopy(image));known.add(image['url'])
 # Listening rooms and archive films are attached to the game, never to a calendar wrapper.
 report['soundtracks_added']=[];report['archive_videos_added']=[];report['unmatched_media']=[]
 music_selections=read(ROOT/'content/expansion/soundtrack-more-selections.json',{}).get('entries',[])+read(ROOT/'content/expansion/soundtrack-additional-official.json',{}).get('entries',[])
 broad_music=read(ROOT/'content/expansion/soundtrack-broad-selections.json',{})
 if broad_music.get('publication_status')=='validated':music_selections+=broad_music.get('entries',[])
 independent_music=read(ROOT/'content/expansion/soundtrack-independent-approved.json',{})
 if independent_music.get('publication_status')=='validated':music_selections+=independent_music.get('entries',[])
 complete_music=read(ROOT/'content/expansion/soundtrack-battlefield1-complete.json',{})
 if complete_music.get('publication_status')=='validated':
  music_selections+=[{**selection,'full_album_collection':True} for selection in complete_music.get('entries',[])]
 licensed_music=read(ROOT/'content/expansion/soundtrack-licensed-game-selections.json',{})
 if licensed_music.get('publication_status')=='validated':
  music_selections+=[{**selection,'replace_existing_tracks':True,'music_kind':'licensed_playlist'} for selection in licensed_music.get('entries',[])]
 # Reviewed multi-track corrections replace earlier minimal selections last.
 # Keep the independently frozen broad checkpoint unchanged.
 multitrack_music=read(ROOT/'content/expansion/soundtrack-multitrack-priority-overrides.json',{})
 if multitrack_music.get('publication_status')=='validated':
  music_selections+=[{**selection,'replace_existing_tracks':not selection.get('append_existing_tracks',False)} for selection in multitrack_music.get('entries',[])]
 for selection in music_selections:
  selected_id=report['aliases'].get(selection.get('entry_id'),selection.get('entry_id'))
  matches=[e for e in entries if e['id'] not in held and (e['id']==selected_id if selected_id else (e['year']==selection['match_year'] and key(e['title'])==key(selection['match_title'])))]
  if not matches and selection['match_title']=='Doom':matches=[e for e in entries if e['id'] not in held and e['year']==2016 and key(e['title']).startswith('doom')]
  if not matches:report['unmatched_media'].append(selection['match_title']);continue
  target=matches[0]
  if selection.get('full_album_collection') or selection.get('replace_existing_tracks'):
   target['soundtrack']={k:copy.deepcopy(selection[k]) for k in ['title','composer','curator_note','tracks']}
   for metadata_key in ['full_album_collection','coverage_status','completeness','album_completeness','recording_collection_scope','independent_review_receipt']:
    if metadata_key in selection:target['soundtrack'][metadata_key]=copy.deepcopy(selection[metadata_key])
   if selection.get('full_album_collection'):target['soundtrack']['full_album_collection']=True
   if selection.get('music_kind'):target['soundtrack']['music_kind']=selection['music_kind']
  elif target.get('soundtrack'):
   soundtrack=target['soundtrack'];known_tracks={track.get('youtube_id') for track in soundtrack.get('tracks',[])}
   for track in selection['tracks']:
    if track.get('youtube_id') not in known_tracks:soundtrack.setdefault('tracks',[]).append(copy.deepcopy(track));known_tracks.add(track.get('youtube_id'))
  else:target['soundtrack']={k:copy.deepcopy(selection[k]) for k in ['title','composer','curator_note','tracks']}
  if selection.get('append_existing_tracks'):
   soundtrack=target['soundtrack'];soundtrack['coverage_status']='partial';soundtrack['full_album_collection']=False
   soundtrack['recording_collection_scope']='Existing game-score selections retained, supplemented by explicitly versioned official same-game DLC/port recordings; not a complete base-game album claim.'
  for track in selection['tracks']:
   if track['source_page'] not in {source['url'] for source in target['sources']}:target['sources'].append({'title':('Official music publication: ' if track.get('official_uploader_verified',False) else 'Soundtrack publication: ')+track['title'],'url':track['source_page'],'publisher':track['uploader'],'attribution':'Music remains on its original YouTube publication. Original rights retained by the recording owner.'})
   if track.get('composer_source'):target['sources'].append({'title':'Music credit source: '+track['creator'],'url':track['composer_source'],'publisher':track['creator']})
  report['soundtracks_added'].append(target['id'])
 # Separately curated complete albums produce separate listening-room cards.
 # The first room is also retained as a legacy fallback for older readers;
 # current runtime deliberately prefers the nonempty soundtrack_rooms array.
 multiple_rooms=read(ROOT/'content/expansion/soundtrack-multiple-room-overrides.json',{})
 if multiple_rooms.get('publication_status')=='validated':
  for addition in multiple_rooms.get('entries',[]):
   targets=[entry for entry in entries if entry['id'] not in held and entry['year']==addition['match_year'] and key(entry['title'])==key(addition['match_title'])]
   if not targets:report['unmatched_media'].append(addition['match_title']+' (multiple albums)');continue
   target=targets[0];rooms=copy.deepcopy(addition['soundtrack_rooms'])
   if not rooms:continue
   target['soundtrack_rooms']=rooms
   target['soundtrack']=copy.deepcopy(rooms[0])
   known_sources={source['url'] for source in target.get('sources',[])}
   for room in rooms:
    for track in room['tracks']:
     for url,title,publisher in [(track['source_page'],'Official music publication: '+track['title'],track['uploader']),(track['composer_source'],'Published album and cue credits: '+room['composer'],room['composer'])]:
      if url not in known_sources:target['sources'].append({'url':url,'title':title,'publisher':publisher});known_sources.add(url)
   report['soundtracks_added'].append(target['id'])
 # Candidate discovery is not publication approval. Keep a frozen compatible
 # checkpoint until the full edition/subject audit has explicitly cleared it.
 video_additions=read(ROOT/'content/expansion/archive-video-additions.json',{}).get('entries',[])
 approved_films=read(ROOT/'content/expansion/museum-video-approved-checkpoint.json',{})
 if approved_films.get('publication_status')=='semantic_validated':video_additions+=approved_films.get('entries',[])
 for addition in video_additions:
  selected_id=report['aliases'].get(addition.get('entry_id'),addition.get('entry_id'))
  matches=[e for e in entries if e['id'] not in held and (e['id']==selected_id if selected_id else (e['year']==addition['match_year'] and key(e['title'])==key(addition['match_title'])))]
  if not matches:continue
  target=matches[0]
  existing_images={i['url'] for i in target.get('images',[])}
  for image in addition.get('images',[]):
   if image['url'] not in existing_images:target['images'].append(copy.deepcopy(image));existing_images.add(image['url'])
  for video in addition.get('videos',[]):
   if video['youtube_id'] not in {v.get('youtube_id') for v in target['videos']}:target['videos'].append(copy.deepcopy(video));report['archive_videos_added'].append({'entry_id':target['id'],'youtube_id':video['youtube_id']})
 teasers={
  'conkers-bad-fur-day': 'Rare turns a familiar platforming world into a bawdy cartoon. Conker moves between film parodies, physical jokes and unexpectedly elaborate set pieces, testing how far a cheerful mascot can be pushed.',
  'burnout-revenge': 'Speed is only the beginning. Burnout Revenge builds its races around traffic, close calls and deliberate collisions, making risk a resource that can carry a driver from a near miss into a spectacular takedown.',
  'shadow-of-the-colossus': 'A rider and his horse cross an immense, quiet landscape in search of sixteen colossi. Climbing each moving creature turns scale, balance and observation into the central language of the adventure.',
  'dantes-inferno': "Dante's Inferno reshapes the Divine Comedy as an action game. Its descent through Hell combines scythe combat, mythic creatures and monumental environments, turning a literary journey into a physical ordeal.",
  'bioshock-2': 'Rapture returns through the eyes of Subject Delta, a Big Daddy linked to a Little Sister. Weapons and plasmids work together, while protecting a vulnerable companion changes the rhythm of exploration and combat.',
  'homefront': 'Homefront places its resistance fighters in a fictional occupied United States. Familiar streets, civilian spaces and military spectacle frame a shooter built around the uneasy distance between home and battlefield.',
  'batman-arkham-city': 'Arkham City gives Batman a district to read from above and investigate at street level. Gliding, detective tools and fluid combat connect its rooftops, interiors and rival gangs into one dense urban playground.',
  'i-am-alive': 'I Am Alive makes survival a matter of reading a situation before acting. Stamina, scarce supplies and the threat of an unloaded weapon turn climbing and confrontation into tense decisions in a ruined city.',
  'ghost-recon-wildlands': 'A four-person squad works across a fictionalized Bolivia in Ghost Recon Wildlands. Reconnaissance, coordinated shots and open approaches let players plan together, then adapt when a careful operation becomes chaotic.'
 }
 poster_quality=read(ROOT/'content/expansion/video-poster-quality-overrides.json',{}).get('entries',{})
 for e in entries:
  if e['id'] in teasers:e['summary']=teasers[e['id']]
  preferred=e.get('images',[])[e.get('preferred_image',0)].get('url') if e.get('images') and e.get('preferred_image',0)<len(e['images']) else None
  for owner in [e]+list(e.get('editorial_features',[])):
   kept=[]
   for image in owner.get('images',[]):
    upgrade=poster_quality.get(image.get('url'),{})
    if upgrade.get('status')=='native_maxres':
     image=copy.deepcopy(image);image.setdefault('provenance',{})['original_poster_url']=image['url'];image.update({k:copy.deepcopy(v) for k,v in upgrade.items() if k!='status'})
    elif upgrade.get('status')=='fallback_editorial_art':continue
    kept.append(image)
   owner['images']=kept
   for video in owner.get('videos',[]):
    upgrade=poster_quality.get(video.get('poster_url'),{})
    if upgrade.get('status')=='native_maxres':video['poster_url']=upgrade['url']
    elif upgrade.get('status')=='fallback_editorial_art':video['poster_url']='';video['poster_treatment']='Native thumbnail too small; use this exhibit’s local editorial artwork.'
  if preferred:
   preferred=poster_quality.get(preferred,{}).get('url',preferred)
   e['preferred_image']=next((n for n,i in enumerate(e.get('images',[])) if i['url']==preferred),min(e.get('preferred_image',0),max(0,len(e.get('images',[]))-1)))
  # A collection is provenance, never a claim to own the photograph or artwork.
  photos=list(e.get('images',[]))
  for feature in e.get('editorial_features',[]):photos.extend(feature.get('images',[]))
  for image in photos:
   old_credit=image.get('credit','')
   old_creator=image.get('creator','')
   if not any(term in (old_credit+' '+old_creator).lower() for term in ['playhub','lozazamastro']):continue
   provenance=image.get('provenance',{})
   if not isinstance(provenance,dict):provenance={'upstream_record':provenance};image['provenance']=provenance
   provenance.setdefault('collection_credit_before_rights_review',old_credit)
   original=provenance.get('original_metadata',{})
   if not isinstance(original,dict):original={}
   actual=original.get('creator') or original.get('author')
   if actual and not any(term in str(actual).lower() for term in ['playhub','lozazamastro']):image['creator']=actual
   elif any(term in old_creator.lower() for term in ['playhub','lozazamastro']):image['creator']='Original photographer or artwork creator not identified in the source record'
   credited=original.get('credit') or original.get('rights') or old_credit
   credited=re.sub(r'\s*[/·]\s*Playhub historical collection','',credited,flags=re.I)
   credited=re.sub(r'\s*[/·]?\s*LoZazaMastro','',credited,flags=re.I)
   credited=re.sub(r'in the Playhub record','in the original source record',credited,flags=re.I)
   credited=re.sub(r'from the Playhub collection','from the original source archive',credited,flags=re.I)
   if credited.strip().lower() in ['original rights holders','playhub historical collection','']:
    credited='Original photographic or artwork rights holders; consult the preserved source record'
   image['credit']=credited.strip(' /·')
   if 'Playhub' in image.get('license',''):image['license']=re.sub('Playhub collection','original source archive',image['license'])
 quality_replacements=read(ROOT/'content/expansion/museum-image-quality-replacements.json',{})
 if quality_replacements.get('publication_status')=='visual_validated':
  upgrades={(row['entry_id'],row['match_url']):row['image'] for row in quality_replacements.get('replacements',[])}
  for exhibit in entries:
   if not exhibit.get('images'):continue
   preferred=exhibit['images'][min(exhibit.get('preferred_image',0),len(exhibit['images'])-1)]['url']
   selected_upgrade=upgrades.get((exhibit['id'],preferred))
   if selected_upgrade:preferred=selected_upgrade['url']
   unique=set();photos=[]
   for photo in exhibit['images']:
    photo=copy.deepcopy(upgrades.get((exhibit['id'],photo['url']),photo))
    if photo['url'] in unique:continue
    unique.add(photo['url']);photos.append(photo)
   exhibit['images']=photos
   exhibit['preferred_image']=next((n for n,i in enumerate(photos) if i['url']==preferred),0)
 # English depth additions are published only after a frozen source/text review.
 depth=read(ROOT/'content/expansion/museum-english-editorial-depth.json',{})
 if depth.get('publication_status')=='validated':
  depth_targets={entry['id']:entry for entry in entries}
  report['english_depth_applied']=[]
  for identifier,addition in depth.get('entries',{}).items():
   target=depth_targets.get(identifier)
   if not target:raise ValueError('Reviewed English depth target missing: '+identifier)
   if addition.get('body_replace'):
    target['body']=copy.deepcopy(addition['body_replace'])
    target['story_headings']=copy.deepcopy(addition['story_headings_replace'])
   else:
    headings=list(target.get('story_headings',[]))
    headings=(headings+['']*len(target['body']))[:len(target['body'])]
    for paragraph,heading in zip(addition.get('body_append',[]),addition.get('story_headings_append',[])):
     if paragraph not in target['body']:target['body'].append(paragraph);headings.append(heading)
    target['story_headings']=headings
   if addition.get('summary_replace'):target['summary']=addition['summary_replace']
   if addition.get('date_replace'):target['date']=copy.deepcopy(addition['date_replace'])
   sources=target.setdefault('sources',[]);known_sources={source.get('url') for source in sources}
   for source in addition.get('sources',[]):
    if source['url'] not in known_sources:sources.append(copy.deepcopy(source));known_sources.add(source['url'])
   rejected_parts=addition.get('remove_image_url_parts',[])
   removed=[image for image in target.get('images',[]) if any(part in image['url'] for part in rejected_parts)]
   photos=copy.deepcopy(addition.get('images_prepend',[]))+[image for image in target.get('images',[]) if image not in removed]
   seen=set();target['images']=[]
   for image in photos:
    if image['url'] not in seen:target['images'].append(image);seen.add(image['url'])
   if addition.get('preferred_image_url'):
    target['preferred_image']=next(n for n,image in enumerate(target['images']) if image['url']==addition['preferred_image_url'])
   provenance=target.setdefault('provenance',{})
   if not isinstance(provenance,dict):provenance={'original_record':provenance};target['provenance']=provenance
   provenance['english_depth_review']=copy.deepcopy(addition.get('provenance',{}))
   if removed:provenance['excluded_later_edition_image_urls']=[image['url'] for image in removed]
   report['english_depth_applied'].append(identifier)
 summary_fixes=read(ROOT/'content/expansion/museum-summary-integrity-fixes.json',{})
 if summary_fixes.get('publication_status')=='editorial_reviewed':
  for exhibit in entries:
   fix=summary_fixes.get('entries',{}).get(exhibit['id'])
   if fix:exhibit['summary']=fix['summary']
 # Some reference imports stored both a shortened lead and the full identical
 # lead immediately afterwards. Retain the complete prose once, and preserve
 # illustration paragraph alignment rather than displaying the opening twice.
 report['duplicate_lead_prefixes_removed']=[]
 for exhibit in entries:
  while len(exhibit.get('body',[]))>1 and len(exhibit['body'][0].split())>20 and exhibit['body'][1].startswith(exhibit['body'][0]) and len(exhibit['body'][1])>len(exhibit['body'][0]):
   exhibit['body'].pop(0)
   if exhibit.get('story_headings'):exhibit['story_headings'].pop(0)
   for image in exhibit.get('images',[]):
    if isinstance(image.get('story_paragraph'),int) and image['story_paragraph']>=1:image['story_paragraph']-=1
   report['duplicate_lead_prefixes_removed'].append(exhibit['id'])
 # Illuminate the existing biographical insert instead of duplicating a full
 # person profile in the object's story.
 person_feature_overrides=read(ROOT/'content/expansion/museum-person-additions.json',{}).get('feature_overrides',{})
 for exhibit in entries:
  for feature in exhibit.get('editorial_features',[]):
   change=person_feature_overrides.get(feature['id'])
   if not change or change.get('parent_id')!=exhibit['id']:continue
   if feature.get('story_headings'):feature['story_headings'][0]=change['first_heading']
   urls={image['url'] for image in change.get('images_prepend',[])}
   feature['images']=copy.deepcopy(change.get('images_prepend',[]))+[image for image in feature.get('images',[]) if image['url'] not in urls]
   feature['related_ids']=list(dict.fromkeys(feature.get('related_ids',[])+change.get('related_ids',[])))
 # Reject known cross-edition assets after all enrichment stages. Keep rejected
 # evidence in internal provenance rather than crediting another game publicly.
 edition_guards=read(ROOT/'content/expansion/museum-edition-image-exclusions.json',{}).get('entries',{})
 report['edition_images_excluded']=[]
 for exhibit in entries:
  guard=edition_guards.get(exhibit['id'])
  if not guard:continue
  parts=guard.get('forbidden_url_parts',[])
  bad=lambda url:any(part in url for part in parts)
  rejected=[image for image in exhibit.get('images',[]) if bad(image['url'])]
  rejected_sources=[source for source in exhibit.get('sources',[]) if bad(source.get('url',''))]
  preferred_url=guard.get('preferred_image_url')
  if not preferred_url and exhibit.get('images'):
   preferred_url=exhibit['images'][min(exhibit.get('preferred_image',0),len(exhibit['images'])-1)]['url']
  exhibit['images']=[image for image in exhibit.get('images',[]) if not bad(image['url'])]
  exhibit['sources']=[source for source in exhibit.get('sources',[]) if not bad(source.get('url',''))]
  if not exhibit['images']:raise ValueError('Edition correction left no image: '+exhibit['id'])
  exhibit['preferred_image']=next((n for n,image in enumerate(exhibit['images']) if image['url']==preferred_url),0)
  if guard.get('preferred_image_url') and exhibit['images'][exhibit['preferred_image']]['url']!=preferred_url:
   raise ValueError('Reviewed edition cover missing: '+exhibit['id'])
  provenance=exhibit.setdefault('provenance',{})
  if not isinstance(provenance,dict):provenance={'original_record':provenance};exhibit['provenance']=provenance
  provenance['edition_image_correction']={'reason':guard['reason'],'excluded_images':rejected,'excluded_sources':rejected_sources}
  report['edition_images_excluded'].append({'id':exhibit['id'],'removed_images':len(rejected),'removed_sources':len(rejected_sources)})
 # A person profile must retain its reviewed face-first cover even when
 # unrelated article artwork is later added or the generic cover ranking changes.
 person_cover_review=read(ROOT/'content/expansion/museum-person-cover-reviewed.json',{})
 if person_cover_review.get('publication_status')=='visual_reviewed':
  for exhibit in entries:
   if exhibit['id'] in held or exhibit.get('kind')!='person':continue
   reviewed=person_cover_review.get('entries',{}).get(exhibit['id'])
   if not reviewed:raise ValueError('Person cover lacks a subject-specific visual review: '+exhibit['id'])
   selected=next((n for n,image in enumerate(exhibit.get('images',[])) if image['url']==reviewed['url']),None)
   if selected is None:raise ValueError('Reviewed person cover absent: '+exhibit['id'])
   exhibit['preferred_image']=selected;exhibit['images'][selected]['portrait']=True
 image_associations=read(ROOT/'content/expansion/museum-story-image-associations-root.json',{}).get('entries',{})
 for exhibit in entries:
  association=image_associations.get(exhibit['id'])
  if not association:continue
  excluded=association.get('excluded_url_parts',[])
  exhibit['images']=[i for i in exhibit.get('images',[]) if not any(part in i['url'] for part in excluded)]
  exhibit['explicit_story_media_only']=bool(association.get('explicit_story_media_only',False))
 # Exact, visually reviewed game packaging wins over generic collection
 # advertisements and later database ranking passes.
 for reviewed_file in ['museum-preferred-game-covers-reviewed.json','museum-preferred-game-covers-editorial-reviewed.json','museum-preferred-game-covers-origins-reviewed.json']:
  reviewed_covers=read(ROOT/'content/expansion'/reviewed_file,{})
  if reviewed_covers.get('status')!='visually_reviewed':continue
  for exhibit in entries:
   image=reviewed_covers.get('entries',{}).get(exhibit['id'])
   if not image:continue
   superseded=set(image.get('supersedes_urls',[]))|{image['url']}
   exhibit['images']=[copy.deepcopy(image)]+[i for i in exhibit.get('images',[]) if i['url']not in superseded]
   exhibit['preferred_image']=0
 # Language-reviewed replacements override the discovery checkpoint. A
 # playable regional dub must not displace the international publication.
 international_videos=read(ROOT/'content/expansion/museum-international-video-reviewed.json',{})
 if international_videos.get('status')=='language_and_native_metadata_reviewed':
  for exhibit in entries:
   change=international_videos.get('entries',{}).get(exhibit['id'])
   if not change:continue
   replacements=change.get('replacements',{})
   exhibit['videos']=[copy.deepcopy(replacements.get(video.get('youtube_id'),video)) for video in exhibit.get('videos',[])]
 # A company-spanning, illustrated account cannot inherit the old calendar
 # feature's sparse positional gallery or front-loaded film ordering.
 nintendo_join=runpy.run_path(str(ROOT/'content/expansion/nintendo_complete_story.py'))
 report['nintendo_complete_story']=nintendo_join['apply'](entries,ROOT)
 creator_join=runpy.run_path(str(ROOT/'content/expansion/reviewed_creator_stories.py'))
 report['reviewed_creator_stories']=creator_join['apply'](entries,ROOT)
 n64_join=runpy.run_path(str(ROOT/'content/expansion/n64_specific_story.py'))
 report['n64_specific_story']=n64_join['apply'](entries,ROOT)
 minecraft_join=runpy.run_path(str(ROOT/'content/expansion/minecraft_release_consolidation.py'))
 report['minecraft_release_consolidation']=minecraft_join['apply'](entries)
 if report['minecraft_release_consolidation']['status']=='PASS':report['aliases']['daily-05-17']='minecraft'
 snes_join=runpy.run_path(str(ROOT/'content/expansion/snes_release_consolidation.py'))
 report['snes_release_consolidation']=snes_join['apply'](entries)
 if report['snes_release_consolidation']['status']=='PASS':report['aliases']['snes-pal']='daily-11-21'
 modern_cover_join=runpy.run_path(str(ROOT/'content/expansion/reviewed_modern_cover_corrections.py'))
 report['reviewed_modern_cover_corrections']=modern_cover_join['apply'](entries,ROOT)
 report['reviewed_nintendogs_cover_correction']=modern_cover_join['apply'](entries,ROOT,'museum-nintendogs-cover-correction-reviewed.json')
 report['reviewed_ffxiv2010_cover_correction']=modern_cover_join['apply'](entries,ROOT,'museum-ffxiv2010-cover-correction-reviewed.json')
 report['reviewed_original_subject_cover_corrections']=modern_cover_join['apply'](entries,ROOT,'museum-original-subject-cover-corrections-reviewed.json')
 report['reviewed_fable_chibi_cover_corrections']=modern_cover_join['apply'](entries,ROOT,'museum-fable-chibi-cover-corrections-reviewed.json')
 report['reviewed_spelunky_classic_cover']=modern_cover_join['apply'](entries,ROOT,'museum-spelunky-classic-cover-reviewed.json')
 report['reviewed_original_2004_2014_covers']=modern_cover_join['apply'](entries,ROOT,'museum-original-2004-2014-covers-reviewed.json')
 report['reviewed_classic_original_boxes']=modern_cover_join['apply'](entries,ROOT,'museum-classic-original-box-corrections-reviewed.json')
 report['reviewed_eight_original_boxes']=modern_cover_join['apply'](entries,ROOT,'museum-eight-original-box-corrections-reviewed.json')
 # A same-name game must never replace the Lua programming-language logo.
 entries[:]=[e for e in entries if e['id'] not in held]
 report['entry_count']=len(entries);report['grouped_titles_remaining']=[e['id'] for e in entries if e['id'].startswith('daily-') and ' / ' in e['title']]
 return report
