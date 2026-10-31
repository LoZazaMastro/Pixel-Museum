"""Replace twenty generic appended cards, preserving primary-source reporting."""
from pathlib import Path
import hashlib, json

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/playhub-semantic-coverage/wiki-clarity/pass4'
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
plans={
 'workbook-06-11-ratchet-clank-rift-apart':[(5,'Ratchet, Rivet and their arsenal'),(6,'Crossing dimensional rifts'),(22,'Linking traversal moves'),(29,'A retro-futuristic score')],
 'workbook-06-02-valorant':[(5,'Agents, weapons and the round economy'),(9,'Planting and defending the Spike'),(13,'Short rounds in Spike Rush'),(29,'Practising gunplay in Deathmatch')],
 'workbook-06-18-bloodstained-ritual-of-the-night':[(6,'Exploring the castle as Miriam'),(7,'Weapons, equipment and monster shards'),(8,'Save rooms, warp rooms and crafting'),(39,'Music and returning collaborators')],
 'workbook-06-16-desperados-iii':[(6,'Reading enemy vision cones'),(8,'Civil zones and reinforcements'),(9,'Hiding bodies and avoiding alarms'),(10,'Different abilities for each specialist')],
 'workbook-06-14-the-last-of-us':[(7,'Crossing a post-pandemic America'),(9,'Scavenging weapons and crafting supplies'),(10,'Listen Mode, cover and exploration'),(11,'Enemies and companions react to combat')],
}
rows=[]
for id,plan in plans.items():
 old=next(e for e in catalog['entries'] if e['id']==id)
 source_file=BASE/(id+'.json'); data=json.loads(source_file.read_text(encoding='utf8'))
 page=next(iter(data['query']['pages'].values())); lines=page['extract'].splitlines()
 for target,(line,heading) in enumerate(plan,3):
  original=lines[line];body=original
  if id=='workbook-06-02-valorant' and line==5:
   body=original.split(' As of May 2026,')[0]
  if id=='workbook-06-02-valorant' and line==9:
   body=original.split(' If both teams win 12 rounds,')[0]
  assert body and body in original and body.endswith(('.', '"'))
  row={'entry_id':id,'source_chapter_index':target,'index_semantics':'Absolute active body index, not thematic-append-relative.',
       'old_heading':old['story_headings'][target], 'old_body':old['body'][target],
       'old_body_sha256':hashlib.sha256(old['body'][target].encode()).hexdigest(),
       'heading':heading,'body':body,'body_sha256':hashlib.sha256(body.encode()).hexdigest(),
       'source':{'title':page['title'],'url':'https://en.wikipedia.org/w/index.php?oldid='+str(page['revisions'][0]['revid']),
                 'publisher':'English Wikipedia contributors','license':'Creative Commons Attribution-ShareAlike 4.0',
                 'license_url':'https://creativecommons.org/licenses/by-sa/4.0/',
                 'attribution':('Complete source paragraph reproduced verbatim; card heading supplied editorially.' if body==original else 'Consecutive complete source sentences reproduced verbatim; remaining paragraph omitted and heading supplied editorially.')},
       'provenance':{'source_file':source_file.relative_to(ROOT).as_posix(),'source_file_sha256':hashlib.sha256(source_file.read_bytes()).hexdigest(),
                     'page_id':page['pageid'],'revision_id':page['revisions'][0]['revid'],
                     'extract_line_indices':[line],'source_paragraphs':[original],
                     'selected_character_span':[original.index(body),original.index(body)+len(body)]}}
  rows.append(row)
out={'schema_version':1,'publication_status':'awaiting_independent_review','scope':'Twenty generic appended cards across five games. Preserve the first three concrete primary-source cards per entry, all images/videos/music/models/dates and card counts.', 'replacements':rows}
p=ROOT/'content/expansion/museum-playhub-clarity-pass4-candidate.json'
p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(p.relative_to(ROOT),len(rows),hashlib.sha256(p.read_bytes()).hexdigest())
