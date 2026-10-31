"""Two illustrated chapters from existing text and an original period review."""
import copy
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/computer-golf-existing-prose-period-review'
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((ROOT/'build/research/current1387-after-storage-native-qa/master.json').read_text())
old=next(e for e in m['entries'] if e['id']=='wikipedia-896706')
new=copy.deepcopy(old)
new['images'][0]['story_paragraph']=-1
new['images'][1]['story_paragraph']=0
new['images'].append({'url':'https://vtda.org/pubs/Electronic_Games%28Reese%29/Electronic_Games_Issue_01_Vol_01_01_1981_Winter_Premiere.pdf#page=45&embedded=Im0.jpg',
    'source_page':'https://vtda.org/pubs/Electronic_Games%28Reese%29/Electronic_Games_Issue_01_Vol_01_01_1981_Winter_Premiere.pdf',
    'title':'A contemporary review of Computer Golf',
    'caption':'The complete original page 45 of Electronic Games, Winter 1981. Its Computer Golf review appears in the upper-left columns, with the game image below. Other Odyssey2 games remain visible on the unaltered magazine page; the page is not presented as a review by the different critics also discussed in the text.',
    'creator':'Electronic Games / original game-image rights Magnavox',
    'credit':'Electronic Games / VTDA preservation archive; game imagery Magnavox',
    'license':'Original magazine and game-image rights retained by their respective holders; no open licence asserted.',
    'width':1047,'height':1440,'story_paragraph':2,
    'recovery_local_source':'build/research/computer-golf-existing-prose-period-review/original-review-pdf45-Im0.jpg',
    'verification':{'sha256':sha(BASE/'original-review-pdf45-Im0.jpg'),'processing':'Exact complete embedded JPEG from PDF page 45, unchanged bytes; no crop, retouching or enlargement.'}})
new['explicit_story_media_only']=True
new['sources'].append({'title':'Odyssey2 Emphasizes Sports and Science Fiction, Electronic Games Winter 1981, page 45',
    'url':new['images'][-1]['source_page'],'publisher':'Electronic Games / VTDA preservation archive'})
files=[BASE/'electronic-games-winter1981-original.pdf',BASE/'original-review-pdf45-Im0.jpg']+[ROOT/i['recovery_local_source'] for i in old['images']]
x={'status':'CANDIDATE_PENDING_INDEPENDENT_PEER','rows':[{'entry_id':old['id'],'old_entry':old,'new_entry':new}],
    'source_files':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in files},
    'expected_main_paragraph_groups':[[0,1],[2,3,4]],
    'scope':'All five existing complete paragraphs retained verbatim, two illustrated chapters. Existing original back packaging moves to opening mechanics chapter; exact period review illustrates reception. Exclusive front cover unchanged.',
    'quality_limits':['The review page is a native 1047x1440 archive scan, not a fabricated HD screenshot.', 'The illustrated source is Electronic Games; separate Kubey and Tilt opinions remain clearly distinct in the prose.']}
out=BASE/'five-existing-computer-golf-paragraphs-two-period-game-chapters-candidate.json'
out.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');print(out.relative_to(ROOT),sha(out))
