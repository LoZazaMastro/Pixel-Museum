"""Replace remaining abstract Playhub cards with frozen, concrete Wikipedia prose."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'build/research/playhub-semantic-coverage/wiki-clarity/pass6-root'
catalog = json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf-8'))
owners = {e['id']: e for e in catalog['entries']}
# Entry, frozen article filename, (existing card, source extract line, new heading).
plan = [
 ('workbook-07-05-nights-into-dreams', 'Nights into Dreams', [(1,9,'Flight, the Drill Dash and linking'),(2,26,'Designing the Saturn analogue controller'),(3,10,'Grades, bosses and split-screen competition')]),
 ('workbook-07-11-saga-frontier', 'SaGa Frontier', [(1,7,'Seven paths through the Regions'),(2,8,'Learning skills and combining attacks'),(3,9,'Bonuses for completing each scenario')]),
 ('workbook-07-16-brave-fencer-musashi', 'Brave Fencer Musashi', [(1,13,'Fusion, Lumina and absorbed abilities'),(2,19,'Designing a new action role-playing game'),(3,15,'Rest, action figures and new movement abilities')]),
 ('workbook-07-30-soulcalibur','Soulcalibur (video game)',[(1,7,'Moving around an opponent'),(2,24,'Designing each fighter around a weapon'),(3,34,'The expanded Dreamcast version')]),
 ('workbook-08-11-system-shock-2','System Shock 2',[(1,8,'First-person combat and character development'),(2,9,'Audio logs and starting careers'),(3,36,'Building a science-fiction dungeon crawler')]),
 ('workbook-08-16-legacy-of-kain-soul-reaver','Legacy of Kain- Soul Reaver',[(1,7,'Puzzles between the material and spectral realms'),(2,10,'Raziel gains new abilities'),(3,24,'Raziel, Kain and the Elder God')]),
 ('workbook-08-18-re-volt','Re-Volt',[(1,1,'Radio-controlled racing in everyday places'),(3,19,'The original PC car editor')]),
 ('workbook-08-19-dance-dance-revolution-solo-bass-mix','Dance Dance Revolution Solo',[(1,4,'Three-panel and six-panel play'),(2,14,'Sixteen songs and the Dancemania BASS albums'),(3,0,'A separate Solo branch of Dance Dance Revolution')]),
 ('workbook-07-07-final-fantasy-ix','Final Fantasy IX',[(1,38,'The return to a fantasy setting'),(2,14,'Learning abilities from equipment'),(3,28,'Garnet, Zidane and the black mages')]),
 ('workbook-07-04-america-s-army-operations',"America's Army",[(2,16,'Realism and its limitations')]),
 ('daily-03-17','Folklore (video game)',[(0,0,'Ellen and Keats explore an Irish Otherworld'),(1,7,'Doolin as the hub between worlds'),(2,8,'Capturing Folk with Sixaxis movements'),(3,25,'The composers of Folklore')]),
 ('workbook-08-21-bioshock','BioShock',[(4,42,'Designing the Art Deco city of Rapture')]),
 ('workbook-08-01-monster-hunter-tri','Monster Hunter Tri',[(1,19,'Developing underwater hunting')]),
 ('workbook-07-21-limbo','Limbo (video game)',[(2,9,'Traps, checkpoints and learning through failure')]),
 ('workbook-07-03-the-secret-world','The Secret World',[(2,20,'Changing roles through the ability wheel')]),
 ('workbook-08-14-hyrule-warriors','Hyrule Warriors',[(2,8,'Weapons, character growth and local cooperation')]),
 ('never-alone','Never Alone (video game)',[(0,0,'Nuna and the fox in an Iñupiaq story'),(4,10,'The development team visits Alaska'),(7,23,'Never Alone enters the Museum of Modern Art')]),
 ('daily-03-14','The Witness (2016 video game)',[(0,0,'An island of panel and environmental puzzles'),(1,9,'Learning the rules by drawing paths'),(2,10,'Walking and path-drawing modes'),(3,12,'Finding puzzle paths in the environment')]),
 ('workbook-06-29-inside','Inside (video game)',[(2,6,'Exploring and controlling bodies'),(3,37,'Sound and animation respond together')]),
 ('workbook-08-17-humankind','Humankind (video game)',[(1,5,'Choosing a culture in each era'),(2,7,'Fame determines the winner'),(3,6,'Cities, territories and tactical battles')]),
 ('daily-03-18','Terra Nil',[(0,0,'Restoring ecosystems instead of building cities'),(1,7,'Power, clean soil and restored rivers'),(2,9,'Creating biomes for returning wildlife'),(3,10,'Recycling the machinery and leaving')]),
]
changes=[]
for identifier, article, cards in plan:
    path=FOLDER/(article+'.json')
    page=next(iter(json.loads(path.read_text(encoding='utf-8'))['query']['pages'].values()))
    revision=page['revisions'][0]['revid']
    lines=page['extract'].splitlines()
    entry=owners[identifier]
    for index,line,heading in cards:
        source_paragraph=lines[line]
        body=source_paragraph
        edits=[]
        source_lines=[line]
        source_paragraphs=[source_paragraph]
        if identifier=='daily-03-18' and index==0:
            source_lines=[0,1]
            source_paragraphs=[lines[0],lines[1]]
            body='\n\n'.join(source_paragraphs)
        if identifier=='daily-03-18' and index==1:
            start=body.index('Wind turbines')
            body=body[start:]
            edits.append({'type':'complete_sentence_selection','selected_character_spans':[[start,len(source_paragraph)]], 'reason':'Opening sentence with a missing antecedent omitted so the card stands alone.'})
        if identifier=='workbook-08-19-dance-dance-revolution-solo-bass-mix' and index==2:
            start=body.index('It was released')
            body=body[start:]
            edits.append({'type':'complete_sentence_selection','selected_character_spans':[[start,len(source_paragraph)]], 'reason':'Pronunciation and Japanese title omitted; the card heading names the game.'})
        if identifier=='daily-03-14' and index==1:
            removed=', as illustrated to the left'
            assert removed in body
            body=body.replace(removed,'')
            edits.append({'type':'remove_web_layout_reference','removed':removed})
        if identifier=='workbook-08-17-humankind' and index==2:
            removed=' Humankind will include certain persons and events based on historical records that the player will interact with.'
            assert body.endswith(removed)
            body=body[:-len(removed)]
            edits.append({'type':'complete_sentence_selection','selected_character_spans':[[0,len(body)]], 'reason':'Outdated future-tense final sentence omitted.'})
        old=entry['body'][index]
        assert body.strip() and not body.startswith('==') and len(body.split())>=35
        changes.append({'entry_id':identifier,'source_chapter_index':index,'old_heading':entry['story_headings'][index], 'old_body':old,'old_body_sha256':hashlib.sha256(old.encode()).hexdigest(), 'heading':heading,'body':body,'body_sha256':hashlib.sha256(body.encode()).hexdigest(), 'reason':'Replace abstract or repeated editorial framing with concrete reference prose; archive old wording.', 'source':{'title':page['title'],'url':'https://en.wikipedia.org/w/index.php?oldid='+str(revision),'publisher':'English Wikipedia contributors','license':'CC BY-SA 4.0','license_url':'https://creativecommons.org/licenses/by-sa/4.0/','attribution':'Source paragraph(s) reproduced; editorial heading supplied. '+('Explicit selections or removal of a web-layout reference recorded in provenance.' if edits else 'No substantive changes to the source paragraph(s).')},'provenance':{'source_file':path.relative_to(ROOT).as_posix(),'source_file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'page_id':page['pageid'],'revision_id':revision,'extract_line_indices':source_lines,'source_paragraphs':source_paragraphs,'edits':edits}})
result={'schema_version':1,'publication_status':'independent_review_pending','changes':changes,'count':len(changes),'entry_count':len(plan),'preserve_dates_media_and_other_cards':True}
p=FOLDER/'candidate.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(FOLDER/'projected-card-text.txt').write_text('\n\n'.join(x['entry_id']+' / '+str(x['source_chapter_index'])+' / '+x['heading']+'\n'+x['body'] for x in changes)+'\n',encoding='utf-8')
print(len(changes),hashlib.sha256(p.read_bytes()).hexdigest())
