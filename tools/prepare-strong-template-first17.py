"""Freeze all 36 templated body cards in the 12 assigned articles; no promotion."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/research/playhub-semantic-coverage/wiki-clarity/strong-first17'
sources = json.loads((OUT / 'source-pages.json').read_text(encoding='utf8'))
frozen = json.loads((OUT / 'original-current-entries.json').read_text(encoding='utf8'))
entries = {e['id']: e for e in frozen['entries']}
sha = lambda b: hashlib.sha256(b).hexdigest()

# Each source selection is a whole paragraph or consecutive complete sentences.
# Existing short factual passages are retained when the Wikipedia article has
# insufficient original-game detail; no generic prose is added to pad them out.
plans = [
 ('workbook-08-20-john-carmack', [
  (1, 'Smooth PC scrolling through adaptive tile refresh', 'Commander Keen', 2, None, 'video game consoles such as the Nintendo Entertainment System.'),
  (2, 'Drawing only the part of Doom the player can see', 'Doom (1993 video game)', 21, None, None),
  (3, 'Building Quake\u2019s 3D engine and network model together', 'Quake (video game)', 15, None, None)]),
 ('workbook-07-09-donkey-kong', [
  (1, 'Turning Radar Scope hardware into Donkey Kong', 'Donkey Kong (1981 video game)', 17, None, None),
  (2, 'Four screens, from rolling barrels to the final rivets', 'Donkey Kong (1981 video game)', 6, None, None),
  (3, 'Characters made legible through animation and a few pixels', 'Donkey Kong (1981 video game)', 10, None, None)]),
 ('workbook-08-13-gyromite', [
  (1, 'Six flashing commands move a real robot', 'Gyromite', 12, None, None),
  (2, 'Planning ahead for R.O.B.\u2019s slow movements', 'Gyromite', 6, None, None),
  (3, 'Spinning gyros hold the gates open', 'Gyromite', 15, None, None)]),
 ('workbook-08-06-metroid', [
  (1, 'Retracing a route with permanent new abilities', 'Metroid (video game)', 9, None, None),
  (2, 'Morph Ball, bombs and the paths they open', 'Metroid (video game)', 3, None, None),
  (3, 'Tanaka makes Zebes sound like a living organism', 'Metroid (video game)', 11, None, None)]),
 ('workbook-08-15-starflight', [
  (1, 'Scanning planets and choosing where to land', 'Starflight', 5, None, None),
  (2, 'A crew, six posts and a ship to equip', 'Starflight', 3, None, None),
  (3, 'Drawing a story network through an open universe', 'Starflight', 16, 'Johnson was guided', 'The story network was also one of the earliest examples of a sandbox game design.')]),
 ('workbook-07-10-yume-kojo-doki-doki-panic', [
  (1, 'Imajin, Lina, Mama and Papa', 'Yume K\u014dj\u014d: Doki Doki Panic', 11, None, None),
  (2, 'A prototype about lifting, carrying and throwing', 'Yume K\u014dj\u014d: Doki Doki Panic', 9, None, None),
  (3, 'How Nintendo converted Doki Doki Panic into Mario', 'Yume K\u014dj\u014d: Doki Doki Panic', 13, None, None)]),
 ('workbook-08-12-famicom-wars', [
  (1, 'Red Star and Blue Moon take turns', 'Famicom Wars', 1, None, 'the Red Star army is given the first turn.'),
  (2, 'Factories build units and captured cities support them', 'Famicom Wars', 1, 'During each turn,', None),
  (3, 'Visible battles make the strategy easier to follow', 'Famicom Wars', 3, None, None)]),
 ('workbook-07-06-super-star-soldier', [
  (1, None, None, None, None, 'optimized routes.'),
  (2, 'Flamethrowers, electricity and heat-seeking missiles', 'Super Star Soldier', 2, None, None),
  (3, None, None, None, None, 'the same place.')]),
 ('workbook-07-20-devil-s-crush', [
  (1, 'A scrolling table three screens high', "Devil's Crush", 2, None, 'There are three pairs of flippers.'),
  (2, None, None, None, None, 'a hostile environment.'),
  (3, 'Nudging the table, risking a tilt and finding bonus rooms', "Devil's Crush", 2, 'The player can nudge/bump', None)]),
 ('workbook-07-27-dr-mario', [
  (1, 'Moving and rotating two-colour capsules', 'Dr. Mario', 2, None, '90 degrees clockwise or counter-clockwise.'),
  (2, 'Four matching colours clear viruses and release falling pieces', 'Dr. Mario', 2, 'When matching colors', 'finishing each level.'),
  (3, 'Choosing the speed and sending capsules to an opponent', 'Dr. Mario', 3, None, None)]),
 ('workbook-08-10-shadow-of-the-ninja', [
  (1, 'Two ninjas, climbing and a costly thunderstorm attack', 'Shadow of the Ninja', [2,3], None, None),
  (2, 'Katana, kusarigama and limited throwing weapons', 'Shadow of the Ninja', 4, None, None),
  (3, 'Five levels and a shared supply of continues', 'Shadow of the Ninja', 5, None, None)]),
 ('workbook-07-01-duke-nukem', [
  (1, 'Three episodes and a shareware first chapter', 'Duke Nukem (video game)', 0, 'The 2D,', 'distributed as shareware.'),
  (2, 'Shooting scenery, collecting upgrades and finding the exit', 'Duke Nukem (video game)', 2, None, None),
  (3, 'Eight-pixel scrolling and the origin of Duke\u2019s name', 'Duke Nukem (video game)', 5, None, None)])
]

replacements, invariants = [], []
for eid, plan in plans:
    e = entries[eid]
    changed = [r[0] for r in plan]
    rest = {k:v for k,v in e.items() if k not in ('body','story_headings','sources')}
    invariants.append({'entry_id':eid, 'body_count':len(e['body']),
                       'changed_indices':changed,
                       'preserved_body':{str(i):b for i,b in enumerate(e['body']) if i not in changed},
                       'all_other_entry_fields_sha256':sha(json.dumps(rest,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())})
    for index, heading, key, line, start, end in plan:
        old = e['body'][index]
        if key is None:
            last = old.index(end) + len(end)
            body = old[:last]
            source = None
            provenance = {'source_kind':'existing concrete passage retained verbatim; only the generic tail removed',
                          'original_record_file':(OUT/'original-current-entries.json').relative_to(ROOT).as_posix(),
                          'original_record_sha256':sha((OUT/'original-current-entries.json').read_bytes()),
                          'selected_character_span':[0,last],
                          'retained_source_references':e.get('sources',[])}
        else:
            s = sources[key]
            lines = [line] if isinstance(line,int) else line
            assert s['title'] not in ['Donkey Kong'], 'Disambiguation source rejected'
            paragraphs = [s['paragraphs'][i] for i in lines]
            original = ' '.join(paragraphs)
            first = original.index(start) if start else 0
            last = original.index(end, first)+len(end) if end else len(original)
            body = original[first:last]
            assert first == 0 or original[first-2:first] == '. '
            assert body[-1] in '.!?"'
            assert body not in e['body']
            source = {'title':s['title'],
                      'url':'https://en.wikipedia.org/w/index.php?oldid='+str(s['revision_id']),
                      'publisher':'English Wikipedia contributors',
                      'license':'Creative Commons Attribution-ShareAlike 4.0',
                      'license_url':'https://creativecommons.org/licenses/by-sa/4.0/',
                      'attribution':('Complete source paragraphs reproduced verbatim; card heading supplied editorially.' if first==0 and last==len(original) else
                                     'Consecutive complete source sentences reproduced verbatim; remaining text omitted and card heading supplied editorially.')}
            assert sha((ROOT/s['source_file']).read_bytes())==s['source_file_sha256']
            provenance = {'source_kind':'Actual full Wikipedia article HTML, HTTP200; reference markers omitted',
                          'requested_title':key, 'actual_title':s['title'],
                          'source_file':s['source_file'], 'source_file_sha256':s['source_file_sha256'],
                          'page_id':s['page_id'], 'revision_id':s['revision_id'],
                          'paragraph_indices':lines, 'source_paragraphs':paragraphs,
                          'selected_character_span':[first,last]}
        assert body and len(body.split())>=20 and body!=old
        replacements.append({'entry_id':eid,'source_chapter_index':index,
                             'index_semantics':'Absolute active body index; no date, card count or media association changes.',
                             'old_heading':e['story_headings'][index], 'old_body':old,
                             'old_body_sha256':sha(old.encode()),
                             'heading':heading or e['story_headings'][index],
                             'body':body,'body_sha256':sha(body.encode()),
                             'source':source,'provenance':provenance})

assert len(replacements)==36 and len(invariants)==12
assert len({(r['entry_id'],r['source_chapter_index']) for r in replacements})==36
bad=['The technical layer matters because','The mechanic does not live in isolation',
     'Writing does not remain separate','The choice needs to be read within',
     'That relationship between','The result remains recognizable because',
     'The story becomes stronger when','A broader principle emerges',
     'The consequence can be felt in the overall rhythm','Visual identity becomes effective']
for row in replacements:
    assert not any(b in row['body'] for b in bad), row['entry_id']
out = {'schema_version':1,'publication_status':'awaiting_independent_review_not_admitted',
       'source_catalog_sha256':frozen['source_catalog_sha256'],
       'source_audit_sha256':frozen['source_audit_sha256'],
       'scope':'All twelve assigned articles, John Carmack through Duke Nukem: replace thirty-six generic-tailed cards, not merely the seventeen originally flagged. Preserve all introductions, card counts, dates, images, media associations and feature articles.',
       'replacements':replacements,'entry_invariants':invariants,
       'research_notes':['Gyromite redirects to R.O.B.; only actual Gyromite hardware/modes passages are selected.',
                         'Doki Doki Panic redirects to Super Mario Bros. 2; only explicit Doki Doki Panic and conversion/prototype passages selected, not later Mario-only gameplay.',
                         'Donkey Kong (video game) is a disambiguation source and was rejected. The exact 1981 game article is used.',
                         'Super Star Soldier has a short Wikipedia article. Two existing specific Caravan passages remain verbatim with their original references; only generic tails removed.',
                         'Devil\'s Crush uses the original PC Engine table mechanics, not Genesis-only final-boss/save differences. Its existing factual animated-target passage is retained verbatim with original references.',
                         'Famicom Wars source phrase destroy all remaining enemy units in one turn is omitted rather than propagating that misleading rule.',
                         'Carmack introduction/timeline says August20, while current Wikipedia lead says August21. This is reported separately; the present copy pass changes no date or introduction.'],
       'new_word_count':sum(len(r['body'].split()) for r in replacements),
       'master_modified':False}
path=OUT/'candidate.json'
path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path.read_bytes()),
                  'replacements':len(replacements),'articles':len(invariants),'words':out['new_word_count']}))
