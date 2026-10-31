"""Use concrete Wikipedia accounts for nine individually identified passages."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'build/research/playhub-semantic-coverage/style-followup'
owners={e['id']:e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']}
specs=[
    ('daily-09-23',0,'History-of-Nintendo-full.json','History of Nintendo',[7],'The Kyoto playing-card business'),
    ('daily-09-23',1,'nintendo-kojima-lua-full-sources.json','Hanafuda',[0],'Hanafuda: pictures on playing cards'),
    ('daily-09-23',2,'Ultra-Hand-full.json','Ultra Hand',[0,1],'Gunpei Yokoi and the extending Ultra Hand'),
    ('daily-09-23',3,'History-of-Nintendo-full.json','History of Nintendo',[42],'Color TV-Game 6 and 15'),
    ('daily-09-23',4,'History-of-Nintendo-full.json','History of Nintendo',[53],'Game & Watch: a game and a clock'),
    ('daily-09-23',5,'History-of-Nintendo-full.json','History of Nintendo',[60,67],'Famicom and the Nintendo Entertainment System'),
    ('daily-08-24',0,'Hideo-Kojima-full.json','Hideo Kojima',[0],'Hideo Kojima: designer, writer and director'),
    ('workbook-05-30-capcom',1,'capcom-lua-full-sources.json','Capcom',[8],'From electronic game machines to Capcom'),
    ('workbook-07-28-lua',0,'Lua-full.json','Lua',[0,1],'Lua: a language embedded in applications'),
]
changes=[]
for owner_id,index,filename,article,indices,heading in specs:
    path=FOLDER/filename;pages=json.loads(path.read_text(encoding='utf8'))['query']['pages']
    page=next(p for p in pages.values()if p['title']==article);lines=page['extract'].splitlines()
    paragraphs=[lines[n]for n in indices];assert all(len(p.split())>=35 for p in paragraphs)
    body='\n\n'.join(paragraphs);typographic_corrections=[]
    if article=='Hanafuda':
        original="'flower cards'))";replacement="'flower cards')"
        assert body.count(original)==1
        body=body.replace(original,replacement)
        typographic_corrections.append(dict(original=original,replacement=replacement,reason='Remove one unmatched extra closing parenthesis from the plaintext extract. No factual wording changed.'))
    old=owners[owner_id]['body'][index];revision=page['revisions'][0]['revid']
    changes.append(dict(entry_id=owner_id,source_chapter_index=index,old_heading=owners[owner_id]['story_headings'][index],
        old_body=old,old_body_sha256=hashlib.sha256(old.encode()).hexdigest(),heading=heading,body=body,
        body_sha256=hashlib.sha256(body.encode()).hexdigest(),
        source=dict(title=article,url='https://en.wikipedia.org/w/index.php?oldid='+str(revision),publisher='English Wikipedia contributors',
            license='Creative Commons Attribution-ShareAlike4.0',license_url='https://creativecommons.org/licenses/by-sa/4.0/',
            attribution='Complete source paragraphs reproduced with an explicitly recorded typographic correction; card heading supplied editorially.'if typographic_corrections else 'Complete source paragraphs reproduced verbatim; card heading supplied editorially.'),
        provenance=dict(source_file=path.relative_to(ROOT).as_posix(),source_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            page_id=page['pageid'],revision_id=revision,extract_line_indices=indices,source_paragraphs=paragraphs,typographic_corrections=typographic_corrections),
        reason='Replace abstract interpretation, invitation or calendar caution with a concrete description of the same person, artifact or history. Preserve every prior passage in internal provenance and leave all media positions unchanged.'))
out=ROOT/'content/expansion/museum-playhub-clarity-pass3-candidate.json'
out.write_text(json.dumps(dict(schema_version=1,publication_status='awaiting_independent_review',replacements=changes,
    review_scope='Nine specifically reviewed passages only. Nintendo0-5, Kojima0, Capcom1 and Lua0; source-complete paragraphs, no editorial paraphrase. One unmatched closing parenthesis removed from the Hanafuda extract and recorded in provenance. Nintendo19-card structure and all images/videos preserved. YuSuzuki and Nintendo6-18 retained.'),indent=2,ensure_ascii=True)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),paragraphs=len(changes),source_paragraphs=sum(len(c['provenance']['source_paragraphs'])for c in changes),words=sum(len(c['body'].split())for c in changes))))
