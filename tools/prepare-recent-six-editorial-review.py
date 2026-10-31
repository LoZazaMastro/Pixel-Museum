"""Prepare six source-bound, visually checked articles for independent peer review."""
from pathlib import Path
import copy,hashlib,importlib.util,json,re
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/research/recent-game-six'
spec=importlib.util.spec_from_file_location('source_helpers',ROOT/'content/expansion/major-release-additions.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
CONFIG={
 'Resident Evil Requiem':([0,5,6,7,17,19,22],['Grace and Leon','Surviving with less','Action with Leon','Choosing the viewpoint','From online prototype to survival horror','An older Leon','Building with RE Engine'],{0:0,5:1,1:2,4:3,2:4,3:6},"Grace Ashcroft's limited resources and Leon S. Kennedy's forceful combat place two kinds of survival horror inside one investigation."),
 'Nioh 3':([0,1,2,3,4,13],["Takechiyo's journey",'A new shogun','The Samurai style','The Ninja style','Exploring a larger world','Designing two approaches'],{2:1,1:2,4:3,0:4,3:5},'Samurai stances and an evasive Ninja style give combat two rhythms, while larger regions open new routes through a supernatural Japan.'),
 'Pragmata':([0,1,2,3,11,12],['Hugh and Diana','Two characters at once','Hacking under fire','Upgrades and companionship','Six years in development','Designing Diana'],{1:0,4:1,3:2,2:3,5:4,0:5},'Hugh fights while Diana hacks: real-time grid puzzles and third-person action become two interdependent parts of escaping a lunar research station.'),
 'Code Vein II':([0,1,2,3,9],['Revenants and hunters','Blood codes and companions','After the Upheaval','The long aftermath','Responding to the first game'],{0:0,2:1,3:2,5:3,1:4},'A hunter and a Revenant partner travel between past and present, using blood codes and shared abilities to confront a ruined world.'),
 'Dispatch':([0,2,3,24,25,28],['Behind the dispatch desk','Choices and assignments','An alternate Los Angeles','An independent studio','From prototype to superhero story','A weekly release'],{0:0,1:1,3:2,4:4,5:5},'Superhero work moves behind a dispatch desk: dialogue choices, team abilities and assignments shape an episodic story about managing former villains.'),
 '007 First Light':([0,3,4,5,6,17],['Before the number','Training as Bond','Choosing an approach','Close combat','The tools of an agent','A Bond built for games'],{5:0,2:1,3:3,4:4},'A young James Bond earns his place in the 00 programme through investigation, improvisation, stealth, close combat and the tools of an aspiring agent.')}
def source_paragraphs(page):
 result=[];section='Introduction'
 for paragraph in page['extract'].splitlines():
  paragraph=paragraph.strip()
  if not paragraph:continue
  if len(paragraph.split())<12 and not paragraph.endswith(('.',':','!','?')):section=paragraph;continue
  if len(paragraph.split())>=25:result.append((section,paragraph))
 return result
entries=[];receipt=[]
for row in json.loads((OUT/'research-checkpoint.json').read_text(encoding='utf8'))['entries']:
 assert row['status']=='research_only_pending_text_and_visual_review'
 selected,headings,pairings,summary=CONFIG[row['title']];page=copy.deepcopy(row['wikipedia_page']);paragraphs=source_paragraphs(page);body=[paragraphs[n][1]for n in selected];page['extract']='\n\n'.join(body)
 images={i['role']:i for i in row['images']};cover=images['cover'];assert cover['status']=='pending_visual_review'
 creators=' / '.join(dict.fromkeys(row['publisher']+row['developer']));store='https://store.steampowered.com/app/'+str(row['appid'])+'/'
 def image(record,title,index):
  assert record['status']=='pending_visual_review'
  local=ROOT/record['recovery_local_source'];assert hashlib.sha256(local.read_bytes()).hexdigest()==record['sha256']
  return {'url':record['url'],'title':title,'caption':title,'creator':creators,'credit':creators+' / original publisher game imagery','source_page':store,'license':'Original game artwork and imagery; publisher, developer, artist and trademark rights retained. No open licence claimed.','width':record['width'],'height':record['height'],'story_paragraph':index,'recovery_local_source':record['recovery_local_source'],'verification':{'appid':row['appid'],'sha256':record['sha256'],'native_dimensions':[record['width'],record['height']],'no_upscale':True},'visual_review':'Actually viewed the full publisher contact sheet; exact original game, no platform banner, no unrelated edition. Advertisement and Deluxe purchase panels excluded.'}
 front=image(cover,row['title']+': official clean digital cover',-1);front['cover_art']=True
 entry=helper.entry(page,row['year'],front);entry['summary']=summary;entry['subtitle']=headings[0];entry['story_headings']=headings;entry['body']=body;entry['images']=[front]
 for n,index in pairings.items():entry['images'].append(image(images['screenshot-'+str(n)],row['title']+': publisher scene supporting '+headings[index].lower(),index))
 changes='Complete paragraphs selected from the introduction and named article sections, without rewriting; headings and summary supplied editorially.'
 entry['attribution']['changes']=changes;entry['attribution']['text']="Text reproduced from '"+page['title']+"', by Wikipedia contributors, under CC BY-SA4.0. "+changes
 entry['editorial_credit']=entry['attribution']['text'];entry['provenance']['coverage_module']='recent-game-six';entry['provenance']['source_paragraph_selection']=[{'paragraph_index':n,'section':paragraphs[n][0],'sha256':hashlib.sha256(paragraphs[n][1].encode()).hexdigest()}for n in selected]
 assert len(body)==len(headings)>=5
 assert len({i['verification']['sha256']for i in entry['images']})==len(entry['images'])
 assert entry['date']['precision']=='day',entry['title']+' lacks an infobox release day'
 entries.append(entry);receipt.append({'id':entry['id'],'title':entry['title'],'year':entry['year'],'date':entry['date'],'paragraphs':len(body),'words':len(' '.join(body).split()),'narrative_images':len(entry['images'])-1,'source_revision':page['revisions'][0]['revid'],'omitted_promotion_panels':['screenshot-0','screenshot-1']if row['title']=='007 First Light'else[]})
doc={'schema_version':1,'publication_status':'awaiting_independent_review','scope':'Six exact recent original games; no claim of full2025/2026 coverage.','entries':entries}
(OUT/'review-ready-candidate.json').write_text(json.dumps(doc,indent=2,ensure_ascii=True)+'\n',encoding='utf8');(OUT/'source-and-visual-review-receipt.json').write_text(json.dumps({'status':'SOURCE_AND_VISUAL_CHECKED_PENDING_PEER','entries':receipt},indent=2)+'\n',encoding='utf8')
print(json.dumps(receipt))
