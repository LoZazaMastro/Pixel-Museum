"""Preserve the portrait and associate reviewed artifacts with exact passages."""
from pathlib import Path
import copy,hashlib,json,runpy
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
owner=next(e for e in catalog['entries']if e['id']=='channel-f')
folder=ROOT/'build/research/lawson-complete-images'
doc={'schema_version':1,'publication_status':'independently_visually_reviewed','entries':{}}
console=copy.deepcopy(owner['images'][1]);console['story_paragraph']=0
console['caption']='The original Fairchild Channel F console, introduced in1976; a different artifact from the portrait in the main block.'
doc['entries']['channel-f']=[console]
strong='https://www.museumofplay.org/blog/collection-documents-the-career-of-video-game-pioneer-jerry-lawson/'
specs=[
 ('channel-f',1,'Lawson-design-document-edit.jpg','https://www.museumofplay.org/app/uploads/2013/12/Lawson-design-document-edit.jpg',strong,
  'A Fairchild design document preserved in the Jerry Lawson collection',
  'Historical engineering drawing in the Jerry Lawson Collection; the individual drafter is not identified here.',
  'Fairchild engineering artifact / The Strong, Rochester, New York'),
 ('channel-f',2,'thf185320.jpg','https://thf-prod-blobs.s3.amazonaws.com/images/thehenryfordlibraries/blog-images/thf185320.jpg',
  'https://www.thehenryford.org/collections-and-research/digital-collections/artifact/508238#slide=gs-539600',
  'The Channel F package promises a growing library',
  'Original Channel F packaging, showing multiple interchangeable Videocarts; collection photographTHF185320.',
  'Fairchild packaging / The Henry Ford'),
 ('feature-lawson-cartridge-team',1,'Cartridge_Fairchild_Channel_F.jpg','https://upload.wikimedia.org/wikipedia/commons/1/12/Cartridge_Fairchild_Channel_F.jpg',
  'https://commons.wikimedia.org/wiki/File:Cartridge_Fairchild_Channel_F.jpg',
  'The cartridge door exposes its contacts',
  'Original Channel F cartridge, photographed19July2019 with its protective door open; the electrical contacts are visible.',
  'Schnurrikowski / Wikimedia Commons / CC BY-SA4.0'),
 ('feature-lawson-cartridge-team',0,'fairchild-native/page10-image0-Im0.jpg',
  'https://archive.computerhistory.org/resources/access/text/2023/06/102805215-05-01-acc.pdf#page=10&embedded=Im0.jpg',
  'https://archive.computerhistory.org/resources/access/text/2023/06/102805215-05-01-acc.pdf',
  'An interchangeable game becomes a household object',
  'Original Fairchild Channel F manual, printed page8: inserting, ejecting and caring for a Videocart. Archive PDFpage10.',
  'Fairchild Camera and Instrument Corporation / original manual preserved by Computer History Museum'),
 ('feature-lawson-cartridge-team',2,'LawsonPCB-ChannelF.jpg','https://www.museumofplay.org/app/uploads/2013/12/LawsonPCB-ChannelF.jpg',strong,
  'Inside the Channel F System II',
  'A1979Channel F System II with its circuit board exposed, from The Strong. This is not a1976prototype.',
  'Fairchild SystemII1979 artifact / The Strong, Rochester, New York')]
for identifier,index,name,url,source,title,caption,credit in specs:
    local=folder/name
    with Image.open(local)as image:image.load();w,h=image.size
    image=dict(url=url,source_page=source,title=title,caption=caption,
        creator='Original artifact designers and collection photographer; see source record',credit=credit,
        license='Original artifact and collection-photograph rights retained. No open licence claimed.',
        width=w,height=h,story_paragraph=index,recovery_local_source=local.relative_to(ROOT).as_posix(),
        verification=dict(sha256=hashlib.sha256(local.read_bytes()).hexdigest(),native_dimensions=[w,h],no_upscale=True),
        visual_review='Actually viewed by author and independent parent reviewer; precise artifact, era and narrative association approved22October2026.')
    if name=='Cartridge_Fairchild_Channel_F.jpg':
        image.update(creator='Schnurrikowski',license='Creative Commons Attribution-ShareAlike4.0',license_url='https://creativecommons.org/licenses/by-sa/4.0/')
    doc['entries'].setdefault(identifier,[]).append(image)
(ROOT/'content/expansion/museum-story-illustrations-editorial-reviewed.json').write_text(json.dumps(doc,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
entries=copy.deepcopy(catalog['entries'])
apply=runpy.run_path(str(ROOT/'content/expansion/reviewed_story_illustrations.py'))['apply']
review=apply(entries,ROOT)
after=next(e for e in entries if e['id']=='channel-f')
assert after['body']==owner['body']
assert after['images'][after['preferred_image']]['url']==owner['images'][owner.get('preferred_image',0)]['url']
snapshot=copy.deepcopy(entries);apply(entries,ROOT);assert snapshot==entries
review.update(idempotence=True,hero_and_prose_unchanged=True,
    remaining_gaps={'channel-f':[3],'feature-lawson-cartridge-team':[3],'feature-video-soft-business':[0,1,2,3]})
(folder/'five-reviewed-associations-admission.json').write_text(json.dumps(review,ensure_ascii=True,indent=2),encoding='utf8')
print('PASS: six associations; portrait and prose unchanged; six other paragraph gaps explicit.')
