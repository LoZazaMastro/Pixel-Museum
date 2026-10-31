"""Remove six regional/date asides without discarding concrete game accounts."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'build/research/playhub-semantic-coverage/region-caveat-cleanup';folder.mkdir(exist_ok=True)
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'));entries={e['id']:e for e in catalog['entries']}
specs=[
 ('workbook-10-23-super-mario-bros-3','Nintendo radically expands','World maps, flight and transformations','World maps, transformations and secret routes expand Mario\u2019s platforming adventure.'),
 ('workbook-09-28-homeworld','Homeworld brings real-time strategy','A three-dimensional fleet campaign','A real-time strategy game set in three-dimensional space, where ships and losses carry across a journey into exile.'),
 ('workbook-10-22-grand-theft-auto-2','Developed by DMA Design','Gangs and the respect system','A top-down city of rival gangs, missions and consequences built around the respect system.'),
 ('workbook-09-24-ico',"Fumito Ueda's first game",'Ico and Yorda in the castle','Ico and Yorda cross a vast castle through movement, puzzles and the simple act of holding hands.'),
 ('workbook-09-18-eternal-sonata',"tri-Crescendo's project",'Chopin\u2019s dream and light-based combat','A role-playing game built around the imagined final moments of composer Fryderyk Chopin.'),
 ('workbook-10-05-assassin-s-creed-odyssey','Developed mainly by Ubisoft','Choices and naval travel in ancient Greece','An adventure through fifth-century BCE Greece with dialogue choices, naval travel and role-playing progression.'),
]
frozen=folder/'frozen-source-entries.json'
frozen.write_text(json.dumps({'entries':[{k:entries[i].get(k)for k in ['id','title','body','story_headings','summary','sources','year','date']}for i,_,_,_ in specs]},indent=2,ensure_ascii=True)+'\n',encoding='utf8')
source_digest=hashlib.sha256(frozen.read_bytes()).hexdigest();replacements=[];fields=[]
for identifier,start,heading,summary in specs:
    entry=entries[identifier];old=entry['body'][0];offset=old.index(start);body=old[offset:]
    assert len(body.split())>=50
    source=dict(entry['sources'][0]);source['attribution']='Existing editorial game account retained after removing the preceding calendar or regional aside; no new reference-source wording copied.'
    replacements.append(dict(entry_id=identifier,source_chapter_index=0,old_heading=entry['story_headings'][0],old_body=old,
        old_body_sha256=hashlib.sha256(old.encode()).hexdigest(),heading=heading,body=body,body_sha256=hashlib.sha256(body.encode()).hexdigest(),
        source=source,provenance=dict(source_file=frozen.relative_to(ROOT).as_posix(),source_file_sha256=source_digest,
            source_type='frozen_existing_editorial_record',retained_text_span=dict(start=offset,end=len(old)),removed_prefix=old[:offset]),
        reason='Keep the entire concrete game account, remove only the dated lead and regional/edition caution. Correct dates stay in the normal chronology fields. Previous prose is archived in provenance.'))
    fields.append(dict(entry_id=identifier,field='summary',old_value=entry['summary'],value=summary,
        reason='Replace a repeated release-date sentence with a concise description of facts already stated in this entry.'))
candidate=ROOT/'content/expansion/museum-region-caveat-copyedits-candidate.json'
candidate.write_text(json.dumps(dict(schema_version=1,publication_status='awaiting_independent_review',replacements=replacements,field_corrections=fields,
    review_scope='Six exact prefix removals and concise summaries. No source paragraph paraphrase, new historical claim, date mutation, image/video rearrangement or open text licence claim.'),indent=2,ensure_ascii=True)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=candidate.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),paragraphs=6,summary_fields=6)))
