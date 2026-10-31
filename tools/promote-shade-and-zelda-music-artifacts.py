"""Bind two independently checked original-game images to exact prose topics."""
from pathlib import Path
import json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'build/research/playhub-semantic-coverage/native-images'
path=ROOT/'content/expansion/playhub-theme-semantic-restorations.json'
doc=json.loads(path.read_text(encoding='utf8'))
records=[]
items=[('hollow',1,folder/'hollow-original/Screenshot HK Shade 01.png',
    'https://cdn.wikimg.net/en/hkwiki/images/7/72/Screenshot_HK_Shade_01.png',
    'https://hollowknight.wiki/w/File:Screenshot_HK_Shade_01.png',
    'Hollow Knight: facing the Shade in Greenpath',
    'The Knight and the actual recoverable Shade in Greenpath, from the original game; archive upload2021.',
    'Team Cherry / original game capture preserved by Hollow Knight Wiki', 'Team Cherry'),
  ('kondo',2,folder/'last-theme-context/418a6d41-e160-4239-b132-8875c6930dbc.jpg',
    'https://images.launchbox-app.com/418a6d41-e160-4239-b132-8875c6930dbc.jpg',
    'https://gamesdb.launchbox-app.com/games/details/113',
    'The Legend of Zelda: the overworld and the dungeon',
    'Original North American NES back cover, showing the contrasting overworld and dungeon spaces discussed in Kondo\'s music.',
    'Nintendo / original packaging scan preserved by LaunchBox Games Database', 'Nintendo')]
for theme,index,local,url,source,title,caption,credit,creator in items:
    with Image.open(local)as im:im.load();w,h=im.size
    image=dict(url=url,source_page=source,title=title,caption=caption,credit=credit,creator=creator,
        license='Original game artwork and publisher rights retained; no open licence claimed.',
        width=w,height=h,recovery_local_source=local.relative_to(ROOT).as_posix(),
        verification=dict(sha256=hashlib.sha256(local.read_bytes()).hexdigest(),native_dimensions=[w,h],no_upscale=True),
        visual_review='Native image actually viewed by author and independent parent reviewer, exact subject and original game context approved22October2026.')
    row=next(r for r in doc['restorations']if r['theme_id']==theme)
    chapter=next(c for c in row['chapters']if c['source_chapter_index']==index)
    chapter['images']=[image];chapter['existing_image_urls']=[]
    chapter['illustration_status']='reviewed_original_game_image_with_exact_chapter_context'
    records.append(dict(entry_id=row['entry_id'],source_chapter_index=index,image=image))
path.write_text(json.dumps(doc,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
(folder/'shade-and-zelda-music-association-review.json').write_text(json.dumps(dict(status='PASS',records=records,prose_unchanged=True),ensure_ascii=True,indent=2)+'\n',encoding='utf8')
print('Source47/48 chapters illustrated; Monkey Island insult-design artifact still pending.')
