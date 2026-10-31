"""Bind two actually viewed artifacts to their precise restored source chapters."""
from pathlib import Path
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'content/expansion/playhub-theme-semantic-restorations.json'
doc=json.loads(path.read_text(encoding='utf8'));catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
by_id={e['id']:e for e in catalog['entries']}
local='build/research/playhub-semantic-coverage/native-images/bafta2010-page26-native.jpg'
pdf='https://static.bafta.org/static/site/reviewoftheyear10/BAFTA_Review_of_the_Year_2009_2010.pdf'
photo={'url':pdf+'#page=26&image=Im0','source_page':pdf+'#page=26',
 'title':'Shigeru Miyamoto accepts the BAFTA Fellowship, 19 March2010',
 'caption':'Miyamoto at the 2010 GAME British Academy Video Games Awards.',
 'creator':'Brian Ritchie / BAFTA','credit':'BAFTA / Brian Ritchie',
 'license':'Original BAFTA photograph; photographer and BAFTA rights retained. No open licence claimed.',
 'width':1124,'height':1445,'recovery_local_source':local,
 'verification':{'sha256':hashlib.sha256((ROOT/local).read_bytes()).hexdigest(),
   'native_dimensions':[1124,1445],'no_upscale':True,
   'source_evidence':'BAFTA Review of the Year2009/2010 page26 explicitly identifies Miyamoto, the Fellowship, event19March2010 and BAFTA/BrianRitchie.'},
 'visual_review':'Actual embedded original JPEG viewed fully; Miyamoto in tuxedo at the BAFTA podium, blue stage backdrop. Image extracted without resizing from the primary PDF.'}
row=next(r for r in doc['restorations']if r['theme_id']=='miyamoto')
chapter=next(c for c in row['chapters']if c['source_chapter_index']==4)
chapter['images']=[photo];chapter['illustration_status']='reviewed_primary_source_native_photo'
if pdf not in row['historical_sources']:row['historical_sources'].append(pdf)
dreamcast=by_id['dreamcast'];vmu=copy.deepcopy(next(i for i in dreamcast['images']if i.get('original_url','').endswith('Sega-Dreamcast-Cont-n-VMU.jpg')))
vmu.update(title='Original Dreamcast controller and VMU',caption='North American Dreamcast controller and a separate VMU. Screens are unpowered.',
 creator='Evan-Amos',credit='Evan-Amos / public domain',license='Released into the worldwide public domain by the photographer Evan-Amos.',
 license_url='https://commons.wikimedia.org/wiki/File:Sega-Dreamcast-Cont-n-VMU.jpg',rights_review='Verified photographer public-domain declaration on the original Commons file page.')
row=next(r for r in doc['restorations']if r['theme_id']=='dreamcast');chapter=row['chapters'][0]
chapter['images']=[vmu];chapter['illustration_status']='reviewed_original_controller_and_vmu_photo'
preferred=ROOT/'content/expansion/museum-preferred-game-covers-editorial-reviewed.json'
covers=json.loads(preferred.read_text(encoding='utf8'))
console=copy.deepcopy(next(i for i in dreamcast['images']if'Sega-Dreamcast-Console-FL.jpg'in i['url']))
console.update(story_paragraph=-1,cover_art=True,
 visual_review='Actually viewed the distinct Dreamcast console front-left photograph. The controller/VMU remains inside the precise VMU chapter, never repeated as cover.')
covers['entries']['dreamcast']=console
path.write_text(json.dumps(doc,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
preferred.write_text(json.dumps(covers,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
receipt={'status':'PASS_SOURCE_AND_VISUAL_REVIEW','newly_illustrated_source_chapters':2,
 'miyamoto_source':pdf+'#page=26','miyamoto_native_dimensions':[1124,1445],
 'dreamcast_cover':'console front-left','dreamcast_internal_artifact':'controller and unpowered VMU',
 'not_assembled_yet':True}
(ROOT/'build/research/playhub-semantic-coverage/bafta-dreamcast-two-associations.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
print(json.dumps(receipt))
