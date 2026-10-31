"""Replace selected abstract passages with complete, attributed Wikipedia prose."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'build/research/playhub-semantic-coverage/wiki-clarity'
restorations=json.loads((ROOT/'content/expansion/playhub-theme-semantic-restorations.json').read_text(encoding='utf8'))['restorations']
pages={}
for path in folder.glob('*.json'):
    data=json.loads(path.read_text(encoding='utf8'))
    for page in data.get('query',{}).get('pages',{}).values():
        if page.get('pageid')and page.get('extract'):pages[page['pageid']]=(page,path)
# Explicit source-line selection is checked against its revisioned full extract.
# Complete paragraphs are used, never a guessed encyclopedia-style rewrite.
specs=[('books',0,219731,8,'Exploring the Ages'),
       ('books',1,219731,13,'Two voices in the library'),
       ('monkey',0,80981,22,'How insult sword fighting was written'),
       ('monkey',1,80981,11,'Three trials on Mêlée Island'),
       ('hollow',1,53391134,8,'Defeat, the Shade and lost Geo'),
       ('crash',0,8960133,7,'Moving into the screen'),
       ('crash',1,8960133,8,'Fruit, checkpoints and TNT'),
       ('miyamoto',2,100062,11,'Mario moves through three dimensions'),
       ('pokemon',2,417121,25,'The first partner in Pallet Town'),
       ('pokemon',3,269816,7,'Atsuko Nishida and the design of Pikachu'),
       ('pokemon',4,2465537,23,'Designing for beginners'),
       ('kondo',0,219026,10,'Kondo’s first year at Nintendo'),
       ('kondo',1,219026,20,'Music synchronized with movement'),
       ('kondo',2,219026,21,'Different music for different places'),
       ('kondo',4,219026,13,'From solo scores to collaborative soundtracks'),
       ('gta',2,362641,7,'Missions and an open city'),
       ('gta',3,238677,38,'Building the sound of the eighties'),
       ('gta',4,497525,28,'Three cities on one map'),
       ('gta',6,18447783,12,'The Nintendo DS touch screen'),
       ('gta',7,31795249,10,'Three protagonists, different abilities')]
replacements=[];audit=[]
for theme,index,page_id,line,title in specs:
    row=next(row for row in restorations if row['theme_id']==theme and any(c['source_chapter_index']==index for c in row['chapters']))
    old=next(c for c in row['chapters']if c['source_chapter_index']==index)
    page,source_path=pages[page_id]
    lines=page['extract'].splitlines();paragraph=lines[line]
    assert len(paragraph.split())>=40,(theme,index,line,paragraph)
    assert paragraph in page['extract']
    revision=page['revisions'][0]['revid']
    source_url='https://en.wikipedia.org/w/index.php?oldid='+str(revision)
    replacements.append(dict(entry_id=row['entry_id'],theme_id=theme,source_chapter_index=index,
        old_heading=old['title'],old_body=old['body'],old_body_sha256=hashlib.sha256(old['body'].encode()).hexdigest(),
        heading=title,body=paragraph,body_sha256=hashlib.sha256(paragraph.encode()).hexdigest(),
        source=dict(title=page['title'],url=source_url,publisher='English Wikipedia contributors',
            license='Creative Commons Attribution-ShareAlike4.0',license_url='https://creativecommons.org/licenses/by-sa/4.0/',
            attribution='Prose reproduced verbatim from the cited English Wikipedia revision; card heading supplied editorially.'),
        provenance=dict(source_file=source_path.relative_to(ROOT).as_posix(),source_file_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
            page_id=page_id,revision_id=revision,extract_line_index=line),
        reason='Replace interpretive metaphor or implicit mechanics with a concrete description of the same subject, while preserving the old passage in provenance.'))
for row in restorations:
    for chapter in row['chapters']:
        rewrite=next((x for x in replacements if x['entry_id']==row['entry_id']and x['source_chapter_index']==chapter['source_chapter_index']),None)
        audit.append(dict(entry_id=row['entry_id'],theme_id=row['theme_id'],source_chapter_index=chapter['source_chapter_index'],
            heading=chapter['title'],decision='replace_with_revisioned_wikipedia'if rewrite else 'retain_readable_specific_account',
            reason=rewrite['reason']if rewrite else 'The passage identifies concrete actions, objects, design documents or a specific historical event; retain rather than replacing sound material indiscriminately.'))
doc=dict(schema_version=1,publication_status='awaiting_independent_review',replacements=replacements,
    audit=audit,review_scope='All48 restored chapters read individually. Twenty selected replacements preserve full original source paragraphs;28 readable specific passages retained. Main Nintendo, YuSuzuki, N64 and other independent reviewed histories are outside this bounded source review.')
out=ROOT/'content/expansion/museum-playhub-clarity-candidate.json'
out.write_text(json.dumps(doc,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=str(out),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),replacements=len(replacements),audited=len(audit),words=sum(len(x['body'].split())for x in replacements))))
