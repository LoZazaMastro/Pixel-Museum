"""Admit four actually viewed original publisher posters without platform branding."""
from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/cover-post2015'
path=ROOT/'content/expansion/museum-preferred-game-covers-editorial-reviewed.json'
doc=json.loads(path.read_text(encoding='utf8'))
inventory={r['entry_id']:r for r in json.loads((OUT/'inventory.json').read_text(encoding='utf8'))['entries']}
rows=[]
for name in ['microsoft-native-artwork.json','microsoft-additional-native-artwork.json']:
    rows+=json.loads((OUT/name).read_text(encoding='utf8'))
targets={
 'gears4':('wikipedia-36085652','Xbox Game Studios / The Coalition','https://www.xbox.com/en-us/games/store/gears-of-war-4/9NBLGGH4PBBM','Original JD, Kait and Del composition; no platform strip.'),
 'halo-infinite-campaign':('wikipedia-57650958','Xbox Game Studios / 343 Industries','https://www.xbox.com/en-us/games/store/halo-infinite-campaign/9NP1P1WFS0LB','Original Master Chief and Zeta Halo campaign artwork; no multiplayer season or platform strip.'),
 'kingdom-hearts-iii':('wikipedia-10007933','Disney / Square Enix','https://www.xbox.com/en-us/games/store/kingdom-hearts-/C08MW8XHQN9G','Original 2019 ensemble artwork; no Re Mind, remaster or platform strip.'),
 'witcher-blood-wine':('wikipedia-50816870','CD Projekt RED','https://www.xbox.com/en-us/games/store/The-Witcher-3-Wild-Hunt-Blood-and-Wine/C1FJDP6X42GD','Geralt with wine and vampire, exact Blood and Wine expansion title; no platform strip.')}
for row in rows:
    if row['image_purpose']!='Poster' or row['name'] not in targets:continue
    eid,creator,source,review=targets[row['name']]
    local=ROOT/row['recovery_local_source']
    assert hashlib.sha256(local.read_bytes()).hexdigest()==row['sha256']
    with Image.open(local) as im:
        im.load();assert list(im.size)==[row['width'],row['height']]
    doc['entries'][eid]={
      'url':row['url'],'title':row['title']+' - original official digital poster',
      'width':row['width'],'height':row['height'],'source_page':source,
      'creator':creator,'credit':creator+' / original game artwork',
      'license':'Original game artwork; publisher, developer, artist and trademark rights retained. Not an open licence.',
      'recovery_local_source':row['recovery_local_source'],'cover_art':True,'story_paragraph':0,
      'supersedes_urls':[inventory[eid]['preferred_url']],
      'identity_evidence':{'product_id':row['product_id'],'product_name':row['title'],'source':'Anonymous Microsoft DisplayCatalog v7.0 public publisher product record; exact original title.'},
      'verification':{'sha256':row['sha256'],'native_dimensions':[row['width'],row['height']],'no_upscale':True},
      'visual_review':'Actual native image viewed in full. '+review}
path.write_text(json.dumps(doc,indent=2,ensure_ascii=True)+'\n',encoding='utf8')
progress={'resolved_source_overrides':sum(eid in doc['entries'] for eid in inventory),'initial_flagged':57,'catalog_assembled_resolved':38,'note':'Four Microsoft posters and five Nintendo icons are source-reviewed, pending next coordinated assembly.'}
progress['remaining']=progress['initial_flagged']-progress['resolved_source_overrides']
(OUT/'progress.json').write_text(json.dumps(progress,indent=2)+'\n',encoding='utf8')
print(json.dumps(progress))
