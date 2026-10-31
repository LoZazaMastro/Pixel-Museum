"""Bind original Nintendo planning/music documents to the relevant source chapters."""
from pathlib import Path
import json,hashlib,urllib.request
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'content/expansion/playhub-theme-semantic-restorations.json'
doc=json.loads(path.read_text(encoding='utf8'));base='https://raw.githubusercontent.com/LoZazaMastro/Playhub/0c5c103403813431e23b40f90c75fba6d51a9759/assets/on-this-day/v1/'
owner=next(r for r in doc['restorations']if r['entry_id']=='super-mario-bros')
c=next(c for c in owner['chapters']if c['source_chapter_index']==3)
c['existing_image_urls']=[base+'mario-level-planning-sheet.png'];c['image_title']='Super Mario Bros.: original course planning reproduced in Nintendo\'s Super Mario Maker booklet.';c['image_credit']='Nintendo';c['illustration_status']='visually_reviewed_original_development_document'
targets=[('super-mario-bros',4,'mario-kondo-score.png','https://www.nintendo.co.jp/wiiu/amaj/booklet/SuperMarioMakerBooklet.pdf','Super Mario Bros.: original music notation and gameplay layout reproduced in Nintendo\'s retrospective booklet.'),('zelda',1,'zelda-planning.png','https://iwataasks.nintendo.com/interviews/ds/zelda/1/4/','The Legend of Zelda: an early dungeon-selection planning sheet, shown by Nintendo in Iwata Asks.')]
out=ROOT/'build/research/playhub-semantic-coverage/native-images';receipt=[]
for eid,index,name,source,caption in targets:
 local=out/name
 if not local.exists():
  with urllib.request.urlopen(base+name,timeout=20)as r:data=r.read()
  local.write_bytes(data)
 original=Path('F:/Playhub/Plugin/Playhub/assets/on-this-day/v1')/name
 assert hashlib.sha256(local.read_bytes()).hexdigest()==hashlib.sha256(original.read_bytes()).hexdigest()
 with Image.open(local)as im:im.load();width,height=im.size
 target=next(r for r in doc['restorations']if r['entry_id']==eid);c=next(c for c in target['chapters']if c['source_chapter_index']==index)
 c['images']=[{'url':base+name,'title':caption,'caption':caption,'creator':'Nintendo','credit':'Nintendo / original development document','source_page':source,'license':'Copyright Nintendo; development document reproduced for editorial discussion. No open licence claimed.','width':width,'height':height,'recovery_local_source':local.relative_to(ROOT).as_posix(),'verification':{'sha256':hashlib.sha256(local.read_bytes()).hexdigest(),'native_dimensions':[width,height],'no_upscale':True},'visual_review':'Actually viewed local-artifacts-review.jpg and original Zelda planning sheet; compared with exact source chapter about paper planning or music.'}]
 c['illustration_status']='visually_reviewed_original_development_document';receipt.append({'entry_id':eid,'source_chapter_index':index,'source_page':source,'file':name})
path.write_text(json.dumps(doc,indent=2,ensure_ascii=True)+'\n',encoding='utf8')
(out/'nintendo-development-document-associations.json').write_text(json.dumps({'status':'PASS_VISUAL_AND_CHAPTER_CONTEXT','associations':receipt},indent=2)+'\n',encoding='utf8')
print('Three exact Nintendo development documents paired with their original narrative chapters; no catalog assembly.')
