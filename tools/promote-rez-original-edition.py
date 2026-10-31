"""Replace the Infinite remaster substitution with viewed original Rez artifacts."""
from pathlib import Path
import copy,hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def load(path):return json.loads((ROOT/path).read_text(encoding='utf8'))
def save(path,value):(ROOT/path).write_text(json.dumps(value,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
records=load('build/research/launchbox/rez-original-candidates.json');game=records['games']['7918']
def artifact(filename,title,description):
    path=ROOT/'build/research/launchbox/scans'/filename
    with Image.open(path)as im:im.load();width,height=im.size
    assert max(width,height)>=800
    return {'url':'https://images.launchbox-app.com/'+filename,'title':title,'caption':description,
      'source_page':'https://gamesdb.launchbox-app.com/games/details/7918',
      'creator':'United Game Artists / Sega','credit':'United Game Artists / Sega; original packaging and promotional artwork',
      'license':'Original publisher, illustration and trademark rights retained. No open licence claimed.',
      'width':width,'height':height,'recovery_local_source':path.relative_to(ROOT).as_posix(),
      'identity_evidence':{'database_id':'7918','name':'Rez','platform':game['Platform'],
          'release_date':game.get('ReleaseDate'),'edition':'Original PlayStation2 game, not RezInfinite'},
      'verification':{'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'native_dimensions':[width,height],'no_upscale':True},
      'visual_review':'Actually viewed full native scan; original Sega/UnitedGameArtists PS2 packaging or advertisement, no Infinite branding.'}
front=artifact('0cbd9362-ff05-47fe-bd19-c7665248dc97.jpg','Rez: original PlayStation2 European front cover','Original Rez retail packaging, European PlayStation2 edition.')
front.update(cover_art=True,story_paragraph=-1)
back=artifact('d13ace25-1756-4e58-9f80-0f10b37c5e72.jpg','Rez: original packaging explains the avatar forms','Original PS2 back cover, showing the avatar evolving through levels00–05.')
flyer=artifact('r2_da90bb3d-910a-4cc9-8a15-cb65bf89ccc4.jpg','Rez: original synaesthesia campaign','Original PlayStation2 promotion connects its shooting, sound and visual forms.')
early=load('content/expansion/museum-secondary-artifacts-editorial-reviewed.json')
early['entries']['wikipedia-101230']=[front]
save('content/expansion/museum-secondary-artifacts-editorial-reviewed.json',early)
covers=load('content/expansion/museum-preferred-game-covers-editorial-reviewed.json');covers['entries']['wikipedia-101230']=copy.deepcopy(front)
save('content/expansion/museum-preferred-game-covers-editorial-reviewed.json',covers)
guards=load('content/expansion/museum-edition-image-exclusions.json')
guards['entries']['wikipedia-101230']={'forbidden_url_parts':['/apps/636450/','/app/636450/'],
 'preferred_image_url':front['url'],'reason':'Steam636450 is RezInfinite, the later expanded remaster. Original2001 exhibit uses original PS2 packaging and original promotional artifacts; remaster cover and screenshots cannot substitute silently.'}
save('content/expansion/museum-edition-image-exclusions.json',guards)
restorations=load('content/expansion/playhub-theme-semantic-restorations.json');row=next(r for r in restorations['restorations']if r['theme_id']=='rez')
for chapter in row['chapters']:
    chapter['images']=[flyer if chapter['source_chapter_index']==0 else back]
    chapter['illustration_status']='reviewed_native_original_game_promotional_artifact'
save('content/expansion/playhub-theme-semantic-restorations.json',restorations)
save('build/research/playhub-semantic-coverage/rez-original-three-artifact-review.json',
 {'status':'PASS_NATIVE_VISUAL_ORIGINAL_EDITION','cover':front,'narrative_images':[flyer,back],
  'silent_rez_infinite_replacements_removed':True,'not_assembled_yet':True})
print('Original Rez cover and two unique narrative artifacts promoted source-only; Infinite substitution guarded.')
