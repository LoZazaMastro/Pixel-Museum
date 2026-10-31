"""Use actual original Sony/SuckerPunch promotional art without platform banners."""
from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'content/expansion/museum-preferred-game-covers-editorial-reviewed.json'
doc=json.loads(path.read_text(encoding='utf8'));catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'));by_id={e['id']:e for e in catalog['entries']}
rows=[
 ('wikipedia-55667140','Ghost of Tsushima','https://pbs.twimg.com/media/ELrjc_lUEAEkYFr?format=jpg&name=4096x4096',
  'build/research/cover-post2015/tsushima-original-publisher-keyart.jpg',
  'https://twitter.com/SuckerPunchProd/status/1205525949690679296',
  'https://blog.playstation.com/archive/2019/12/13/ghost-of-tsushima-out-summer-2020/',
  'Original December2019 SuckerPunch key art for the2020 game, Jin in pampas grass. NoDirectorCut/PC logo, no platform banner. Publisher tweet URL and exact media URL preserved in contemporaneous press coverage.'),
 ('wikipedia-77961727','Ghost of Yotei','https://digitalpr.jp/images.php?r=108788#file=202504231718486808a268720ae.png',
  'build/research/cover-post2015/yotei-primary2025-image-0.png',
  'https://digitalpr.jp/r/108788',
  'https://digitalpr.jp/r/108788',
  'Original SIE24April2025 public press-release image bundle. Atsu seated before MountYotei, gold ginkgo leaves and title; noCompleteEdition/PS5 banner. Actual originalPNG extracted losslessly from the publisher image ZIP, not enlarged from the600px web thumbnail.')]
for eid,title,url,local,source,corroboration,review in rows:
    photo=ROOT/local
    with Image.open(photo)as im:im.load();dims=im.size
    assert min(dims)>=1000
    old=by_id[eid]['images'][by_id[eid].get('preferred_image',0)]['url']
    record={'url':url,'title':title+': original clean publisher key art','creator':'Sucker Punch Productions / Sony Interactive Entertainment',
      'credit':'Sony Interactive Entertainment / Sucker Punch Productions',
      'license':'Original Sony Interactive Entertainment and artist rights retained. No open licence claimed.',
      'source_page':source,'primary_identity_corroboration':corroboration,
      'recovery_local_source':local,'width':dims[0],'height':dims[1],
      'cover_art':True,'story_paragraph':-1,'supersedes_urls':[old],
      'visual_review':'Actually viewed the complete native original: '+review,
      'verification':{'sha256':hashlib.sha256(photo.read_bytes()).hexdigest(),'native_dimensions':list(dims),'no_upscale':True}}
    doc['entries'][eid]=record
path.write_text(json.dumps(doc,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
progress=ROOT/'build/research/cover-post2015/progress.json';p=json.loads(progress.read_text(encoding='utf8'))
p.update(resolved_source_overrides=56,remaining=1)
progress.write_text(json.dumps(p,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
(ROOT/'build/research/cover-post2015/two-original-ghost-keyart-review.json').write_text(
 json.dumps({'status':'PASS_NATIVE_ACTUAL_VISUAL_REVIEW','entries':{eid:doc['entries'][eid]for eid,*_ in rows},'not_assembled_yet':True},ensure_ascii=True,indent=2)+'\n',encoding='utf8')
print('Two original Ghost publisher keyarts promoted source-only;56/57clean2016+ solved.')
