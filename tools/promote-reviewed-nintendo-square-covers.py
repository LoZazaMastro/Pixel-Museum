"""Admit five visually reviewed, native eShop icons from exact product records."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/research/cover-post2015'
path=ROOT/'content/expansion/museum-preferred-game-covers-editorial-reviewed.json'
doc=json.loads(path.read_text(encoding='utf8'))
inventory={r['entry_id']:r for r in json.loads((OUT/'inventory.json').read_text(encoding='utf8'))['entries']}
slugs={'workbook-03-16-kirby-star-allies':'kirby-star-allies-switch','workbook-03-29-yoshi-s-crafted-world':'yoshis-crafted-world-switch','wikipedia-2369138':'metroid-dread-switch','wikipedia-74839375':'another-code-recollection-switch','wikipedia-79613753':'donkey-kong-bananza-switch-2'}
for row in json.loads((OUT/'nintendo-square-acquisitions.json').read_text(encoding='utf8')):
 assert row['status']=='pending_visual_review'and row['width']==row['height']==1024
 assert hashlib.sha256((ROOT/row['recovery_local_source']).read_bytes()).hexdigest()==row['sha256']
 eid=row['entry_id']
 doc['entries'][eid]={'url':row['url'],'title':row['title']+' - original official eShop artwork','width':1024,'height':1024,'source_page':'https://www.nintendo.com/us/store/products/'+slugs[eid]+'/',
 'creator':'Nintendo / original game developer and artist','credit':'Nintendo / original official digital game artwork','license':'Original game artwork; publisher, developer, artist and trademark rights retained. Not an open licence.',
 'recovery_local_source':row['recovery_local_source'],'cover_art':True,'story_paragraph':0,'supersedes_urls':[inventory[eid]['preferred_url']],
 'identity_evidence':{'product_key':row['source_product_key'],'product_name':row['source_product_name'],'public_page_snapshot':row['source_snapshot']},
 'verification':{'sha256':row['sha256'],'native_dimensions':[1024,1024],'no_upscale':True},
 'visual_review':'Actually viewed nintendo-native-square-review.jpg: exact original game, clean original digital artwork, no Switch platform strip, demonstration banner or prize ribbon. Native1024 master, never enlarged.'}
path.write_text(json.dumps(doc,indent=2,ensure_ascii=True)+'\n',encoding='utf8')
print('Five exact native eShop artworks promoted to source overrides; no catalog assembly.')
