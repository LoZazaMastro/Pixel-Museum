"""Replace announcement warnings and residual abstract Pac-Man prose only."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'build/research/playhub-semantic-coverage/wiki-clarity'
entries={e['id']:e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']}
specs=[('pong',0,'Pong',0,'An Atari arcade game'),
       ('pong',1,'Pong',7,'Two paddles and eleven points'),
       ('pac-man',0,'Pac-Man',0,'A maze chase from Namco'),
       ('pac-man',1,'Pac-Man',1,'Toru Iwatani and a broader audience'),
       ('pac-man',2,'Pac-Man',7,'Eating every dot in the maze'),
       ('pac-man',3,'Pac-Man',8,'Four ghosts with different strategies')]
changes=[]
for entry_id,index,title,line,heading in specs:
    source_file=folder/(title+'.json');doc=json.loads(source_file.read_text(encoding='utf8'))
    page=next(iter(doc['query']['pages'].values()));body=page['extract'].splitlines()[line]
    assert len(body.split())>=40
    old=entries[entry_id]['body'][index];revision=page['revisions'][0]['revid']
    changes.append(dict(entry_id=entry_id,source_chapter_index=index,
        old_heading=entries[entry_id]['story_headings'][index],old_body=old,old_body_sha256=hashlib.sha256(old.encode()).hexdigest(),
        heading=heading,body=body,body_sha256=hashlib.sha256(body.encode()).hexdigest(),
        source=dict(title=page['title'],url='https://en.wikipedia.org/w/index.php?oldid='+str(revision),
            publisher='English Wikipedia contributors',license='Creative Commons Attribution-ShareAlike4.0',
            license_url='https://creativecommons.org/licenses/by-sa/4.0/',
            attribution='Prose reproduced verbatim from the cited English Wikipedia revision; card heading supplied editorially.'),
        provenance=dict(source_file=source_file.relative_to(ROOT).as_posix(),source_file_sha256=hashlib.sha256(source_file.read_bytes()).hexdigest(),
            page_id=page['pageid'],revision_id=revision,extract_line_index=line),
        reason='Replace calendar/announcement cautions or abstract interpretive filler with a complete Wikipedia game overview or explanation of its mechanics. Preserve previous prose in internal provenance.'))
out=ROOT/'content/expansion/museum-playhub-clarity-pass2-candidate.json'
out.write_text(json.dumps(dict(schema_version=1,publication_status='awaiting_independent_review',replacements=changes,
    review_scope='Six specific paragraphs: Pong overview and rules, Pac-Man overview, design audience, maze and ghosts. No date fields, images, videos, features or independently reviewed broader stories changed.'),ensure_ascii=True,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),paragraphs=len(changes),words=sum(len(x['body'].split())for x in changes))))
