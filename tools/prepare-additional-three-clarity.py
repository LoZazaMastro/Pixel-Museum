"""Nine concrete source-exact cards; the active catalogue is never modified."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/playhub-semantic-coverage/wiki-clarity/additional-three'
SOURCES=json.loads((OUT/'source-pages.json').read_text(encoding='utf8'))
sha=lambda b:hashlib.sha256(b).hexdigest()
plans=[
 ('workbook-06-30-tengai-makyo-ziria',[
  (1,'A CD-ROM RPG inspired by the tale of Jiraiya','Tengai Maky\u014d',4,None,'per the fantastic theme).'),
  (2,'Jipang, the Fire Clan and a deliberately distorted Japan','Tengai Maky\u014d',3,None,None),
  (3,'The fictional author behind Far East of Eden','Tengai Maky\u014d',7,None,None)]),
 ('workbook-07-12-castlevania-ii-belmont-s-revenge',[
  (1,'Four themed castles, sub-weapons and passwords',"Castlevania II: Belmont's Revenge",2,None,None),
  (2,'The Japanese cross and North American axe',"Castlevania II: Belmont's Revenge",3,None,None),
  (3,'Reviews notice cleaner graphics and the return of sub-weapons',"Castlevania II: Belmont's Revenge",7,None,None)]),
 ('workbook-07-18-real-sound-kaze-no-regret',[
  (1,'An audio adventure played with a blank screen','Real Sound: Kaze no Regret',1,None,'as the plot unfolds.'),
  (2,'Chimes announce a choice that changes the story','Real Sound: Kaze no Regret',1,'However, at critical points',None),
  (3,'Blind players\u2019 letters and a promise of donated Saturns','Real Sound: Kaze no Regret',[4,7],None,None)])]

frozen_path=OUT/'original-current-entries.json'
if not frozen_path.exists():
    catalog=ROOT/'content/catalog.json'
    content=catalog.read_bytes()
    data=json.loads(content)
    ids={e for e,_ in plans}
    frozen={'source_catalog_sha256':sha(content),'entries':[e for e in data['entries'] if e['id'] in ids]}
    assert len(frozen['entries'])==3
    frozen_path.write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
frozen=json.loads(frozen_path.read_text(encoding='utf8'))
entries={e['id']:e for e in frozen['entries']}
replacements=[]
invariants=[]
for eid,plan in plans:
    e=entries[eid]
    assert len(e['body'])==4
    preserved={k:v for k,v in e.items() if k not in ('body','story_headings','sources')}
    invariants.append({'entry_id':eid,'body_count':4,'changed_indices':[1,2,3],
                       'preserved_body':{'0':e['body'][0]},
                       'all_other_entry_fields_sha256':sha(json.dumps(preserved,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())})
    for index,heading,key,line,start,end in plan:
        s=SOURCES[key]
        lines=[line] if isinstance(line,int) else line
        original_paragraphs=[s['paragraphs'][p] for p in lines]
        original=' '.join(original_paragraphs)
        first=original.index(start) if start else 0
        last=original.index(end,first)+len(end) if end else len(original)
        body=original[first:last]
        assert first==0 or original[first-2:first]=='. '
        assert body[-1] in '.!?"' and len(body.split())>=20
        assert sha((ROOT/s['source_file']).read_bytes())==s['source_file_sha256']
        replacements.append({'entry_id':eid,'source_chapter_index':index,
          'index_semantics':'Absolute active body index; preserve introduction, dates and all images/media.',
          'old_heading':e['story_headings'][index],'old_body':e['body'][index],
          'old_body_sha256':sha(e['body'][index].encode()),
          'heading':heading,'body':body,'body_sha256':sha(body.encode()),
          'source':{'title':s['title'],'url':'https://en.wikipedia.org/w/index.php?oldid='+str(s['revision_id']),
                    'publisher':'English Wikipedia contributors','license':'Creative Commons Attribution-ShareAlike 4.0',
                    'license_url':'https://creativecommons.org/licenses/by-sa/4.0/',
                    'attribution':'Selected complete source paragraphs or consecutive complete sentences reproduced verbatim; card heading supplied editorially.'},
          'provenance':{'source_kind':'Actual full Wikipedia HTML; reference markers omitted from paragraph text',
                        'source_file':s['source_file'],'source_file_sha256':s['source_file_sha256'],
                        'page_id':s['page_id'],'revision_id':s['revision_id'],
                        'actual_title':s['title'],'requested_title':s['requested_title'],
                        'paragraph_indices':lines,'source_paragraphs':original_paragraphs,
                        'selected_character_span':[first,last],
                        'selection_scope':'Whole paragraphs retained in original order.' if isinstance(line,list) else 'Consecutive complete sentences or one complete paragraph.'}})
assert len(replacements)==9 and len({r['body'] for r in replacements})==9
for r in replacements:
    assert not any(p in r['body'] for p in ['The choice needs to be read','The work\'s memory then grows','Readability is part of the mechanic','Sound does not simply accompany','Influence is not the same thing as'])
out={'schema_version':1,'publication_status':'awaiting_independent_review_not_admitted',
     'source_catalog_sha256':frozen['source_catalog_sha256'],
     'scope':'Replace all nine generic-tailed cards in the three assigned articles; retain all three introductions and their dates, four-card body counts, every image and media association.',
     'replacements':replacements,'entry_invariants':invariants,
     'research_notes':['The Ziria game article is a stub; three substantial, explicit original-game/series-context passages come from the separately identified Tengai Maky\u014d series article. No later sequel or remake is represented as the original game.',
                       'The Ziria series source broadly credits Ryuichi Sakamoto for the game music; that sentence is excluded rather than inferring authorship of the entire score.',
                       'The invented Paul Hieronymus Chada book and author are explicitly described as fictional, not presented as authentic history.',
                       'Belmont\u2019s Revenge uses its actual four-castle structure and regional cross/axe differences; no mechanics from Simon\u2019s Quest or the first Game Boy game.',
                       'Real Sound\u2019s optional still-picture mode is explicitly attributed to the later Dreamcast version; no image mode is claimed for the original Saturn release.',
                       'Real Sound accessibility passage combines two complete source paragraphs in original order, omitting the intervening interview preamble and long quotation. No words inside the selected paragraphs are altered.'],
     'new_word_count':sum(len(r['body'].split()) for r in replacements),'master_modified':False}
target=OUT/'candidate.json'
target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':target.relative_to(ROOT).as_posix(),'sha256':sha(target.read_bytes()),'replacements':9,'words':out['new_word_count']}))
