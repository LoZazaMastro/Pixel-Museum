"""Pair original-game press images with seven concrete narrative cards."""
from pathlib import Path
import json, hashlib

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/tlou-original-illustrated'
inventory=json.loads((BASE/'native-2013-press-inventory.json').read_text(encoding='utf8'))
plans=[
 (0,17,'Joel in a close-range combat encounter','Joel attacks an opponent in a May 2013 pre-release gameplay image. It illustrates close-range combat, not Ellie intervening or a particular internal AI prototype.'),
 (1,8,'Character animation during a close encounter','Joel in a close combat encounter, from the original game\'s May 2013 press collection. It illustrates the resulting character animation, not developers acting in the studio.'),
 (2,13,'Light inside an abandoned church','Environment artwork in the May 2013 press collection for the original game. Captioned as artwork rather than an in-game frame.'),
 (3,1,'Joel and Ellie in a deserted town','A May 2013 pre-release image of the original PlayStation 3 game; not the 2014 remaster or 2022 remake.'),
 (4,7,'Crafting a health kit','The original game\'s crafting interface, visible in a May 2013 pre-release gameplay image.'),
 (5,4,'Listen Mode reveals an enemy outline','The original game\'s Listen Mode visualisation, from the May 2013 press collection.'),
 (6,19,'Taking cover during an armed encounter','Combat and cover in a May 2013 pre-release image. This frame is not claimed to prove a particular internal AI algorithm.'),
]
images=[]
for paragraph,index,title,caption in plans:
 r=next(x for x in inventory if x['index']==index)
 images.append(dict(url=r['url'],source_page='https://www.gematsu.com/2013/05/the-last-of-us-gameplay-screenshots',
    title=title,caption=caption,story_paragraph=paragraph,creator='Naughty Dog / Sony Computer Entertainment',
    credit='Naughty Dog / Sony Computer Entertainment; original 2013 press imagery archived by Gematsu',
    license='Original developer, publisher, artwork and trademark rights retained; no open licence claimed.',
    width=r['width'],height=r['height'],recovery_local_source=r['file'],
    verification={'sha256':r['sha256'],'native_source_dimensions':[r['width'],r['height']],
                  'no_generated_enlargement':True,'original_2013_game':True,'visually_reviewed':True},
    quality_scope='Original available 1280-pixel press publication. This is historical PS3-era imagery, not a new 4K capture or a remaster substituted for the original.'))
out={'schema_version':1,'publication_status':'independent_review_pending','entry_id':'workbook-06-14-the-last-of-us',
    'images':images,'scope':'Seven distinct original2013 press illustrations. Preserve hero, back-cover artifact and prose; remove the older back-cover explicit paragraph1 association so the animation card has its actual game illustration.',
    'source_receipts':['build/research/tlou-original-illustrated/gematsu-2013-original-screenshots.html',
                       'build/research/tlou-original-illustrated/native-2013-press-inventory.json'],
    'unavailable_higher_resolution_sources':'Original NaughtyDog Flickr originals returned429 and publisher CDN403. No retry or artificial enlargement. Those unavailable originals are not admitted.'}
p=BASE/'seven-original-press-images-candidate.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(p.relative_to(ROOT),hashlib.sha256(p.read_bytes()).hexdigest())
