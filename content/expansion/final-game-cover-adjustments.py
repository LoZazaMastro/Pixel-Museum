"""Record visually checked originals and an evidenced chronology correction."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;CACHE=ROOT/'build/research/image-quality'
path=HERE/'museum-cover-recoveries-aliases.json';data=json.loads(path.read_text(encoding='utf-8'))
url='https://api.army.mil/e2/c/-images/2007/06/29/6116/army.mil-2007-07-02-091852.jpg'
raw=(ROOT/'build/research/major-releases/americas-army-official-2007.jpg').read_bytes()
with Image.open(ROOT/'build/research/major-releases/americas-army-official-2007.jpg') as image:image.load();w,h=image.size
(CACHE/(hashlib.sha256(url.encode()).hexdigest()[:16]+'.jpg')).write_bytes(raw)
eid='workbook-07-04-america-s-army-operations'
data['entries'][eid]={'url':url,'source_page':'https://www.army.mil/article/3865/americas_army_game_celebrates_fifth_anniversary',
    'title':"America's Army: original PC-game obstacle-course screenshot",'creator':'U.S. Army','credit':'U.S. Army / fifth-anniversary publication, 29 June 2007',
    'license':'Original game image supplied by the U.S. Army; original game and third-party rights retained.','width':w,'height':h,'native_long_edge':max(w,h),
    'kind':'screenshot','cover_role':True,'story_paragraph':0,'quality_verified':'Official original decoded at 800x600; not enlarged.',
    'verification':{'sha256':hashlib.sha256(raw).hexdigest(),'checked_utc':datetime.now(timezone.utc).isoformat()},
    'provenance':{'edition_note':'A 2007 screenshot of the original PC game, not a claim to reproduce its 2002 launch packaging.'}}
data.get('failures',{}).pop(eid,None)
# Replace a small social form graphic with a native, unobstructed detail of
# the publisher's own painted game artwork. Keep its exact crop reversible.
original='https://xyq.res.netease.com/pc/gw/20170118103441/img/20260622/bg_119119e.jpg'
source=CACHE/(hashlib.sha256(original.encode()).hexdigest()[:16]+'.jpg')
url=original+'#museum-cover-artwork';crop=(700,0,1920,900)
out=CACHE/(hashlib.sha256(url.encode()).hexdigest()[:16]+'.jpg')
with Image.open(source) as image:image.crop(crop).save(out,quality=96,subsampling=0)
raw=out.read_bytes();eid='wikipedia-11556966'
data['entries'][eid]={'url':url,'source_page':'https://xyq.163.com/','title':'Fantasy Westward Journey: official game character artwork',
    'creator':'NetEase','credit':'NetEase / official Fantasy Westward Journey website artwork','license':'Original promotional artwork; NetEase rights retained.',
    'width':1220,'height':900,'native_long_edge':1220,'kind':'artwork','cover_role':True,'story_paragraph':0,
    'quality_verified':'Native 1220x900 crop of original 1920x3851 publisher artwork; never enlarged.',
    'verification':{'sha256':hashlib.sha256(raw).hexdigest(),'checked_utc':datetime.now(timezone.utc).isoformat()},
    'provenance':{'source_image_url':original,'source_dimensions':[1920,3851],'crop_box':list(crop),
        'modifications':'Cropped to the character group; no generated or reconstructed detail.','edition_note':'Current publisher artwork for the same game; not presented as original 2003 packaging.'}}
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
correction={'entries':{'wikipedia-11556966':{'year':2004,'date':{'month':1,'day':0,'precision':'month','region':''},
    'factual_note':'Canonical commercial release: January 2004, as recorded by NetEase. No exact release day is inferred.',
    'sources':[{'title':'NetEase original announcement: Fantasy Westward Journey public beta opens 18 December 2003','url':'https://games.sina.com.cn/newgames/2003/12/121810271.shtml','publisher':'NetEase announcement republished by Sina Games'},
        {'title':'NetEase annual filing: December 2003 open beta, January 2004 commercial launch','url':'https://ir.netease.com/static-files/b2d7efdd-f301-4d8a-8a97-9b69c02494ec','publisher':'NetEase'}]}}}
(HERE/'museum-identity-corrections.json').write_text(json.dumps(correction,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Final cover overrides',len(data['entries']),'chronology corrections',len(correction['entries']))
