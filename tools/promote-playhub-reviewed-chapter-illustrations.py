"""Associate visually reviewed source masters with exact preserved source chapters."""
from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/research/playhub-semantic-coverage/native-images'
path=ROOT/'content/expansion/playhub-theme-semantic-restorations.json'
doc=json.loads(path.read_text(encoding='utf8'))
rows={r['file']:r for r in json.loads((OUT/'inventory.json').read_text(encoding='utf8'))['images']}
# Each association was read alongside the English paragraph and the actual image.
# Source screenshots remain credited to their original rightsholders.
selected=[
 ('wikipedia-45641123',0,'science-1.jpg','Mobius Digital / Annapurna Interactive','Outer Wilds: a translated clue describes the disappearing moon.'),
 ('wikipedia-45641123',1,'science-2.jpg','Mobius Digital / Annapurna Interactive','Outer Wilds: an anglerfish encountered during exploration.'),
 ('wikipedia-47581011',0,'stardew-1.jpg','ConcernedApe','Stardew Valley: an autumn farm and its seasonal crops.'),
 ('wikipedia-47581011',1,'stardew-0.jpg','ConcernedApe','Stardew Valley: villagers and cultivated spaces form the player\'s neighbourhood.'),
 ('feature-kondo-functional-music',1,'kondo-mario-rhythm.jpg','Nintendo','Super Mario Bros.: movement and jumping across World 1-1.'),
 ('feature-kondo-functional-music',3,'kondo-ocarina-playing.jpg','Nintendo','The Legend of Zelda: Ocarina of Time: the player performs notes using the controller.'),
 ('wikipedia-23307442',0,'gta-1.jpg','Rockstar Games / DMA Design','Grand Theft Auto: original top-down city gameplay.'),
 ('wikipedia-362641',2,'gta3-0.jpg','Rockstar Games / DMA Design','Grand Theft Auto III: a street-level third-person view at Portland Docks.'),
 ('wikipedia-238677',3,'vicecity-0.jpg','Rockstar Games / Rockstar North','Grand Theft Auto: Vice City: a motorcycle amid palm trees and 1980s-inspired streets.'),
 ('wikipedia-31795249',7,'gtav-0.jpg','Rockstar Games / Rockstar North','Grand Theft Auto V: a helicopter heist scene from the original release campaign.'),
 ('wikipedia-31795249',8,'gtav-hamlet.jpg','Grand Theft Hamlet / Pinny Grylls and Sam Crane / Tull Stories','Grand Theft Hamlet (2024): a film made within Grand Theft Auto Online, discussed in this chapter.')
]
receipt=[]
for eid,index,filename,creator,caption in selected:
 row=rows[filename];assert row['status']=='pending_visual_review'
 local=ROOT/row['recovery_local_source'];assert hashlib.sha256(local.read_bytes()).hexdigest()==row['sha256']
 with Image.open(local)as im:im.load();assert list(im.size)==[row['width'],row['height']]
 target=next(r for r in doc['restorations']if r['entry_id']==eid)
 chapter=next(c for c in target['chapters']if c['source_chapter_index']==index)
 image={'url':row['url'],'title':caption,'caption':caption,'creator':creator,'credit':creator,
  'source_page':row.get('sourceUrl')or row['url'],'license':row.get('rights','Original game imagery; all respective rights retained.'),
  'width':row['width'],'height':row['height'],'recovery_local_source':row['recovery_local_source'],
  'verification':{'sha256':row['sha256'],'native_dimensions':[row['width'],row['height']],'no_upscale':True},
  'visual_review':'Actually viewed native-images/review-01.jpg or review-02.jpg and compared with this exact preserved source chapter. No cover repetition.'}
 chapter['images']=[image];chapter['illustration_status']='visually_reviewed_unique_contextual_artifact'
 receipt.append({'entry_id':eid,'source_chapter_index':index,'file':filename,'url':row['url'],'sha256':row['sha256']})
path.write_text(json.dumps(doc,indent=2,ensure_ascii=True)+'\n',encoding='utf8')
(OUT/'admitted-chapter-associations.json').write_text(json.dumps({'status':'PASS_VISUAL_AND_CHAPTER_CONTEXT','associations':receipt},indent=2)+'\n',encoding='utf8')
print(json.dumps({'new_illustrated_source_chapters':len(receipt),'total_restored_source_chapters':sum(len(r['chapters'])for r in doc['restorations']),'pending_unique_illustrations':sum(not(c.get('images')or c.get('existing_image_urls'))for r in doc['restorations']for c in r['chapters'])}))
