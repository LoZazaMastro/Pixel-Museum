"""Admit exact-game original artifacts reviewed against their chapter subjects."""
from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'build/research/playhub-semantic-coverage/native-images'
semantic=ROOT/'content/expansion/playhub-theme-semantic-restorations.json'
doc=json.loads(semantic.read_text(encoding='utf8'))
cover_path=ROOT/'content/expansion/museum-preferred-game-covers-editorial-reviewed.json'
covers=json.loads(cover_path.read_text(encoding='utf8'))
early=json.loads((folder/'early-design-artifacts/inventory.json').read_text(encoding='utf8'))
later=json.loads((folder/'last-theme-context/inventory.json').read_text(encoding='utf8'))

def artifact(row,title,caption,creator):
    local=ROOT/row['path'].replace('\\','/')
    with Image.open(local)as image:
        image.load();width,height=image.size
    assert max(width,height)>=800
    return dict(url=row['url'],source_page='https://gamesdb.launchbox-app.com/games/details/'+row['DatabaseID'],
        title=title,caption=caption,creator=creator,
        credit=creator+'; original artifact scan preserved by LaunchBox Games Database',
        license='Original game, packaging, artist and trademark rights retained. No open licence claimed.',
        width=width,height=height,recovery_local_source=local.relative_to(ROOT).as_posix(),
        identity_evidence=dict(database_id=row['DatabaseID'],image_type=row['Type'],region=row.get('Region'),
                               game=row.get('game',row.get('identity',{}))),
        verification=dict(sha256=hashlib.sha256(local.read_bytes()).hexdigest(),native_dimensions=[width,height],no_upscale=True),
        visual_review='Actual original scanned artifact viewed; title, original game edition and stated chapter context checked.')

def pair(theme,index,image):
    row=next(row for row in doc['restorations']if row['theme_id']==theme and any(c['source_chapter_index']==index for c in row['chapters']))
    chapter=next(c for c in row['chapters']if c['source_chapter_index']==index)
    chapter['images']=[image];chapter['existing_image_urls']=[]
    chapter['illustration_status']='reviewed_original_artifact_with_precise_chapter_context'
    return dict(entry_id=row['entry_id'],source_chapter_index=index,image=image)

records=[]
specs=[('pacman',1,'f5066974-de81-4d16-a06e-cdf08b7e06ee.jpg',
        'Pac-Man: the original arcade flyer explains the energizers',
        'Back of the original Midway arcade flyer: the maze, ghosts and energizer rules.', 'Namco / Midway'),
       ('kondo',0,'0a286259-49eb-4ea3-a03c-6214520dd4c6.jpg',
        'Devil World: Nintendo\'s original game packaging',
        'European NES packaging of the original 1984 game; this later regional package is not a development screenshot.', 'Nintendo'),
       ('miyamoto',0,'ad554207-b04d-4111-b69f-1824b09c867e.png',
        'Donkey Kong: the original arcade flyer introduces Jumpman',
        'Original 1981 arcade flyer, depicting Jumpman and the cabinet; not a pixel-design worksheet.', 'Nintendo')]
for theme,index,name,title,caption,creator in specs:
    image=artifact(next(row for row in early if row['FileName']==name),title,caption,creator)
    image['visual_review']+=' Independent parent visual review approved the exact artifact and association on22October2026.'
    records.append(pair(theme,index,image))

local=folder/'gta-original-artifacts/san-andreas-original-map1536.jpg'
with Image.open(local)as photo:photo.load();assert photo.size==(1536,1536)
image=dict(url='https://gtwfilesie.grandtheftwiki.com/SanAndreas-GTASA-map.jpg',
    source_page='https://www.grandtheftwiki.com/File:SanAndreas-GTASA-map.jpg',
    title='Grand Theft Auto: San Andreas: three cities and the country between them',
    caption='Original-game map archived in2010, showing Los Santos, San Fierro and Las Venturas; not the Definitive Edition.',
    creator='Rockstar Games / Rockstar North',credit='Rockstar Games / Rockstar North; map preserved by Grand Theft Wiki (Gtabot,2010)',
    license='Original Rockstar game artwork copyright retained. No open licence to the map is claimed.',
    width=1536,height=1536,recovery_local_source=local.relative_to(ROOT).as_posix(),
    verification=dict(sha256=hashlib.sha256(local.read_bytes()).hexdigest(),native_dimensions=[1536,1536],no_upscale=True),
    visual_review='Actually viewed by author and independent parent reviewer; all three named cities and intervening countryside correspond to the distance chapter.')
records.append(pair('gta',4,image))

ds_front=artifact(later[29],'Grand Theft Auto: Chinatown Wars: original Nintendo DS cover',
    'North American packaging of the original Nintendo DS game, released inMarch2009; not the subsequent PSP port.', 'Rockstar Games / Rockstar Leeds / Rockstar North')
assert later[29]['DatabaseID']=='11056' and later[29]['Type']=='Box - Front'
ds_front.update(story_paragraph=-1,cover_art=True,supersedes_urls=[
    'https://images.launchbox-app.com/ee437ed9-6036-495a-9d92-c4fbad01e609.jpg',
    'https://raw.githubusercontent.com/LoZazaMastro/Playhub/0c5c103403813431e23b40f90c75fba6d51a9759/assets/on-this-day/v1/chinatown-0.jpg',
    'https://raw.githubusercontent.com/LoZazaMastro/Playhub/0c5c103403813431e23b40f90c75fba6d51a9759/assets/on-this-day/v1/jan-jun-review-03-17-intro-extra-1.jpg'],
    superseded_reason='Original DS article previously used a PSP package and later single-screen captures with unverified edition identity. Replaced by actual original DS artifacts; source import records remain unchanged.')
covers['entries']['workbook-03-17-grand-theft-auto-chinatown-wars']=ds_front
ds_back=artifact(later[25],'Grand Theft Auto: Chinatown Wars: the original DS package shows its touch interaction',
    'Back of the2009North American Nintendo DS package; its screwdriver minigame is shown alongside the original dual-screen platform marks.', 'Rockstar Games / Rockstar Leeds / Rockstar North')
records.append(pair('gta',6,ds_back))

zelda=artifact(later[5],'The Legend of Zelda: original NES retail cover',
    'Spanish retail packaging for the original NES game, including its map-and-guide notice; not a remaster.', 'Nintendo')
assert later[5]['DatabaseID']=='113' and later[5]['Type']=='Box - Front'
zelda.update(story_paragraph=-1,cover_art=True,supersedes_urls=['https://images.launchbox-app.com/cf17144e-91bb-4727-953b-905aa894644c.png'])
covers['entries']['zelda']=zelda
semantic.write_text(json.dumps(doc,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
cover_path.write_text(json.dumps(covers,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
receipt=dict(status='PASS_EXACT_ORIGINAL_ARTIFACT_VISUAL_REVIEW',reviewed_on='2026-10-22',
    chapter_associations=records,cover_changes=[ds_front,zelda],no_prose_changed=True,
    constraints=['No fictional North American Pokemon Green package admitted.',
                 'No newer-port gameplay falsely described as Nintendo DS.',
                 'Regional packaging represents the same original game without creating another release stop.'])
(folder/'early-design-and-ds-artifact-review.json').write_text(json.dumps(receipt,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
print('Source only: five specific chapters illustrated; Chinatown original DS and Zelda high-resolution original covers corrected.')
