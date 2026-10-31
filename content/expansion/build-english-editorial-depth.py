"""Expand the remaining brief English exhibits from their exact English Wikipedia articles."""
from pathlib import Path
import json,re,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
sources=json.loads((ROOT/'build/research/english-editorial-depth/source-pages.json').read_text(encoding='utf8'))
by_title={p['title']:p for p in sources['pages']};current={e['id']:e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']}
result={};review=[]
headings={
 'workbook-02-22-ed-boon':['Education and roots','From pinball to Mortal Kombat','Programming Mortal Kombat'],
 'oregon-trail':['A classroom experiment','An evolving educational series','Survival through decisions'],
 'karateka':['An original idea at Yale','Cinema meets fighting','Rotoscoping on the Apple II'],
 'tomb-raider':['Creating Lara Croft','Making 3D exploration work','The sound of silence'],
 'braid':['Time is a tool','Time and Forgiveness','Time and Mystery'],
 'bioshock-2':['Inside a Big Daddy','Rethinking familiar systems','Protecting a Little Sister'],
 'pokemon-go':['The world becomes a map','Pokémon in your surroundings','The act of catching'],
 'ghost-recon-wildlands':['Reconnaissance and equipment','A changing landscape','Planning together'],
 'the-division-2':['Building an agent','Skills and cooperation','A city to rebuild'],
 'dance-dance-revolution':['From Japan to Dancing Stage','Following the rhythm','Reading a performance'],
 'dreamcast':['Arcade DNA and online play','A final console launch','An enduring homebrew community'],
 'workbook-06-05-tabletop-simulator':['Pieces with physical weight','A shared tabletop','Building a physics sandbox'],
 'workbook-04-17-yakuza-6-the-song-of-life':['The Dragon Engine','One fighter, two cities','Kiryu and Haruka'],
 'oddworld-soulstorm':['Rescue in 2.5D','Improvising with items','Commanding a fragile crowd'],
 'workbook-04-18-minecraft-legends':['Defending the Overworld','A generated battlefield','Resources and reinforcements'],
 'workbook-05-02-age-of-wonders-4':['Tomes of magic','Affinity and identity','Developing a fantasy strategy game']
}

for identifier,requested in sources['subjects'].items():
 resolved={'Yakuza 6':'Yakuza 6: The Song of Life'}.get(requested,requested);page=by_title.get(resolved)
 if not page or not page.get('extract'):raise ValueError('Missing exact article '+requested)
 text=re.split(r'\n(?:References|External links|Further reading)\n',page['extract'])[0]
 paragraphs=[];heading='From the archive'
 for line in text.splitlines():
  line=line.strip()
  if not line:continue
  if len(line.split())<8 and len(line)<80:heading=line;continue
  if len(line.split())>=30 and not line.startswith(('*','^')):paragraphs.append((line,heading))
 selection_indices={
  'tomb-raider':[1,16,20], 'braid':[4,5,6], 'karateka':[7,8,9],
  'bioshock-2':[7,9,10], 'pokemon-go':[2,3,8], 'ghost-recon-wildlands':[3,4,7],
  'the-division-2':[3,4,5], 'workbook-05-02-age-of-wonders-4':[11,12,18],
 }
 indices=selection_indices.get(identifier,[1,2,3] if len(paragraphs)>3 else range(len(paragraphs)))
 selected=[paragraphs[n] for n in indices]
 existing=current[identifier]['body'];selected=[(p,h) for p,h in selected if p not in existing]
 revision=page['revisions'][0];article='https://en.wikipedia.org/wiki/'+page['title'].replace(' ','_');url='https://en.wikipedia.org/w/index.php?oldid='+str(revision['revid'])
 row={'body_append':[p for p,h in selected],'story_headings_append':headings.get(identifier,[h for p,h in selected]),'sources':[{'title':page['title']+' - English Wikipedia revision '+str(revision['revid']),'url':url,'publisher':'English Wikipedia contributors','attribution':'Additional narrative paragraphs reproduced verbatim under CC BY-SA 4.0. Prose reproduced verbatim; card headings supplied editorially. Existing exhibition text unchanged.','license':'CC BY-SA 4.0','license_url':'https://creativecommons.org/licenses/by-sa/4.0/'},{'title':'Article contributors and history','url':article+'?action=history','publisher':'English Wikipedia contributors'}],'provenance':{'exact_article_title':page['title'],'page_id':page['pageid'],'revision_id':revision['revid'],'revision_timestamp':revision['timestamp'],'text_treatment':'Selected substantive prose paragraphs, unchanged and in source order. Existing curatorial text retained.'}}
 if len(' '.join(row['body_append']).split())<100:raise ValueError('Insufficient new substantive prose '+identifier)
 result[identifier]=row;review.append({'entry_id':identifier,'title':current[identifier]['title'],'existing_words':sum(len(p.split()) for p in existing),'added_words':len(' '.join(row['body_append']).split()),'paragraphs':[{'heading':h,'text':p} for p,h in selected]})
page=by_title['The Stanley Parable'];text=page['extract'];section=text.split('\nDevelopment\n',1)[1].split('\n2013 remake\n',1)[0];paras=[p.strip() for p in section.splitlines() if len(p.split())>=30];revision=page['revisions'][0]
result['wikipedia-38097022']={'body_replace':paras,'story_headings_replace':['A narrator to disobey','Making the Source mod','The original 2011 release'],'summary_replace':'Davey Wreden\u2019s original Half-Life 2 modification explores what happens when a player follows, questions or disobeys an unseen narrator.','sources':[{'title':'The Stanley Parable - original Half-Life 2 mod development, English Wikipedia revision '+str(revision['revid']),'url':'https://en.wikipedia.org/w/index.php?oldid='+str(revision['revid']),'publisher':'English Wikipedia contributors','attribution':'Original 2011 mod section reproduced verbatim under CC BY-SA 4.0;2013 remake lead excluded.','license':'CC BY-SA 4.0','license_url':'https://creativecommons.org/licenses/by-sa/4.0/'}],'provenance':{'exact_article_title':'The Stanley Parable','revision_id':revision['revid'],'section':'Development, before2013 remake subsection','edition':'Original2011Half-Life 2 modification; not2013 standalone or Ultra Deluxe'}}
review.append({'entry_id':'wikipedia-38097022','title':'The Stanley Parable (original 2011 mod)','existing_words':sum(len(p.split()) for p in current['wikipedia-38097022']['body']),'replacement_words':sum(len(p.split()) for p in paras),'paragraphs':[{'heading':h,'text':p} for h,p in zip(result['wikipedia-38097022']['story_headings_replace'],paras)]})
stanley=result['wikipedia-38097022'];stanley['date_replace']={'month':7,'day':31,'precision':'day','region':''}
stanley['remove_image_url_parts']=['/apps/221910/']
stanley['images_prepend']=[]
for name,url,title,source,licence,licence_url,paragraph in [
 ('stanley-mod-2011-office.jpg','https://media.moddb.com/images/mods/1/19/18377/SSC_12.JPG','The Stanley Parable original 2011 Half-Life 2 mod: office 427','https://www.moddb.com/mods/the-stanley-parable/images','Copyright Davey Wreden; developer-published historical screenshot. Original rights retained.','',0),
 ('stanley-mod-2011-logo.png','https://upload.wikimedia.org/wikipedia/commons/1/1e/The_Stanley_Parable_Logo.png','The Stanley Parable: original 2011 mod logo','https://commons.wikimedia.org/wiki/File:The_Stanley_Parable_Logo.png','PD-textlogo; trademark rights may apply','https://commons.wikimedia.org/wiki/Template:PD-textlogo',1),
]:
 path=ROOT/'build/research/english-editorial-depth'/name
 with Image.open(path) as im:im.load();width,height=im.size
 stanley['images_prepend'].append({'url':url,'title':title,'creator':'Davey Wreden','source_page':source,'license':licence,'license_url':licence_url,'credit':'Davey Wreden / The Stanley Parable original 2011 mod','width':width,'height':height,'story_paragraph':paragraph,'recovery_local_source':str(path),'verification':{'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'context_review':'Viewed actual original 2011 mod screenshot and dated originalmod logo; not the 2013 standalone Steam edition.'}})
stanley['preferred_image_url']=stanley['images_prepend'][0]['url']
(ROOT/'content/expansion/museum-english-editorial-depth.json').write_text(json.dumps({'schema_version':1,'publication_status':'awaiting_text_review','entries':result},ensure_ascii=True,indent=2)+'\n',encoding='utf8');(ROOT/'build/research/english-editorial-depth/selection-review.json').write_text(json.dumps(review,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
print('DRAFT',len(result),'ADDED_WORDS',sum(len(' '.join(r.get('body_append',r.get('body_replace',[]))).split()) for r in result.values()))
