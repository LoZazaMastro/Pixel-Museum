"""Keep nine existing paragraphs, illustrate four historically identified chapters."""
import copy
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/home-run-existing-prose-original-controls-and-review'
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((ROOT/'build/research/current1392-native-qa/master.json').read_text())
old=next(e for e in m['entries'] if e['id']=='wikipedia-66830767')
new=copy.deepcopy(old)
new['images'][0]['story_paragraph']=-1
new['images'][1]['story_paragraph']=3
new['images'][1]['caption']='The original Atari Home Run packaging back, copyright 1978, with Atari and Warner branding and its joystick requirement. Contemporary publication context for the development and promotion discussion, not a photograph of Bob Whitehead, Cliff Spohn or Pete Rose.'
new['images'].append({'url':'https://www.atarimania.com/2600/boxes/hi_res/home_run_color_pal_i_4.jpg?v=1659953105',
    'source_page':'https://www.atarimania.com/games/atari-2600-games-home-run-40188',
    'title':'Batting, pitching and moving the fielders',
    'caption':'The complete English controller-action page from Atari Home Run instructions, preserved in the PAL manual archive. Its diagrams explain pitching and fielder movement. Original published 600x845 scan, not a newly typeset or enlarged manual.',
    'creator':'Atari, Inc.','credit':'Atari / Atarimania scan archive',
    'license':'Original Atari manual rights retained; no open licence asserted.',
    'width':600,'height':845,'story_paragraph':1,
    'recovery_local_source':'build/research/home-run-existing-prose-original-controls-and-review/home_run_color_pal_i_4.jpg',
    'verification':{'sha256':sha(BASE/'home_run_color_pal_i_4.jpg'),'processing':'Complete original published manual page, no crop, enlargement or retouch.'}})
new['images'].append({'url':'https://www.atarimania.com/pubs/hi_res/two_pictures_are_worth_a_thousand_words_ad_v2.jpg?v=1649251377',
    'source_page':'https://www.atarimania.com/games/atari-2600-games-home-run-40188',
    'title':'Home Run in the console comparison campaign',
    'caption':'The complete Mattel advertisement, copyright 1981, compares Atari Home Run with Intellivision Major League Baseball. The spokesperson is George Plimpton, not Pete Rose. This is the competitor advertising described in the text, not one of the independent reviews that follow.',
    'creator':'Mattel Electronics','credit':'Mattel Electronics / Atarimania scan archive; Atari game image rights retained',
    'license':'Original Mattel advertising, photographic and respective game rights retained; no open licence asserted.',
    'width':1252,'height':1614,'story_paragraph':6,
    'recovery_local_source':'build/research/home-run-existing-prose-original-controls-and-review/two_pictures_are_worth_a_thousand_words_ad_v2.jpg',
    'verification':{'sha256':sha(BASE/'two_pictures_are_worth_a_thousand_words_ad_v2.jpg'),'processing':'Complete original published advertisement, no crop, enlargement or retouch.'}})
new['explicit_story_media_only']=True
new['sources'].append({'title':'Home Run: original Atari instructions and contemporary Mattel comparison advertisement',
    'url':'https://www.atarimania.com/games/atari-2600-games-home-run-40188','publisher':'Atari / Mattel Electronics; Atarimania archive'})
files=[BASE/'atarimania-source.html',BASE/'home_run_color_pal_i_4.jpg',BASE/'two_pictures_are_worth_a_thousand_words_ad_v2.jpg']+[ROOT/i['recovery_local_source'] for i in old['images'][:2]]
x={'status':'CANDIDATE_PENDING_INDEPENDENT_PEER','rows':[{'entry_id':old['id'],'old_entry':old,'new_entry':new}],
    'source_files':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in files},
    'expected_main_paragraph_groups':[[0],[1,2],[3,4,5],[6,7,8]],
    'scope':'All nine complete prose paragraphs and headings retained unchanged. Existing cover exclusive and film unchanged; redistribute oversized eight-paragraph scene into mechanics, production/promotion and competitor/reception chapters using original identified artifacts.',
    'quality_limits':['Manual page is only 600x845 native; no false HD claim.','Mattel advertising contains a real named Home Run comparison, but is not an independent review or a Pete Rose endorsement.']}
out=BASE/'nine-existing-home-run-paragraphs-four-period-game-chapters-candidate.json'
out.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');print(out.relative_to(ROOT),sha(out))
