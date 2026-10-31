"""Promote the unbranded original2016 publisher poster, not Royal/Windows editions."""
from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'build/research/cover-post2015/ff15-original-displaycatalog.json'
product=json.loads(source.read_text(encoding='utf8'))['Products'][0]
assert product['ProductId']=='BZX2L7NS942K'
assert product['LocalizedProperties'][0]['ProductTitle']=='FINAL FANTASY XV'
poster=next(i for i in product['LocalizedProperties'][0]['Images']if i['ImagePurpose']=='Poster')
local=ROOT/'build/research/cover-post2015/ff15-original-Poster.bin'
with Image.open(local)as im:im.load();dims=im.size
assert dims==(720,1080)
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
entry=next(e for e in catalog['entries']if e['id']=='wikipedia-5069306')
record={'url':'https:'+poster['Uri'],'title':'Final Fantasy XV: original2016 clean digital poster',
 'creator':'Square Enix','credit':'Square Enix / original game artwork',
 'source_page':'https://www.xbox.com/en-us/games/store/final-fantasy-xv/BZX2L7NS942K',
 'primary_identity_source':'https://news.xbox.com/en-us/2016/11/28/final-fantasy-xv-is-now-available-for-xbox-one/',
 'license':'Original publisher, artist and trademark rights retained. No open licence claimed.',
 'width':720,'height':1080,'story_paragraph':-1,'cover_art':True,
 'recovery_local_source':local.relative_to(ROOT).as_posix(),
 'supersedes_urls':[entry['images'][entry.get('preferred_image',0)]['url']],
 'identity_evidence':{'store_sku':'BZX2L7NS942K','published_title':'FINAL FANTASY XV','edition':'Original2016 game; not WindowsEdition or RoyalEdition',
 'source_api':'https://displaycatalog.mp.microsoft.com/v7.0/products?bigIds=BZX2L7NS942K&market=US&languages=en-us'},
 'visual_review':'Actually viewed native720x1080 original Noctis-and-friends road-trip poster. NoXbox/PS4 platform banner, no Royal/Windows subtitle or image manipulation.',
 'verification':{'sha256':hashlib.sha256(local.read_bytes()).hexdigest(),'native_dimensions':list(dims),'no_upscale':True}}
path=ROOT/'content/expansion/museum-preferred-game-covers-editorial-reviewed.json'
doc=json.loads(path.read_text(encoding='utf8'));doc['entries'][entry['id']]=record
path.write_text(json.dumps(doc,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
(ROOT/'build/research/cover-post2015/ff15-original-cover-reviewed.json').write_text(json.dumps(record,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
progress=ROOT/'build/research/cover-post2015/progress.json';p=json.loads(progress.read_text(encoding='utf8'))
p.update(resolved_source_overrides=54,remaining=3)
progress.write_text(json.dumps(p,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
print('Original FF15 clean cover promoted source-only;54/57clean2016+ solved.')
