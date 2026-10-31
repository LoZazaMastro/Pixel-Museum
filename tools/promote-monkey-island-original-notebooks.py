"""Replace a redundant regional box back with actual original design documents."""
from pathlib import Path
import json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def load(path):return json.loads((ROOT/path).read_text(encoding='utf8'))
def save(path,value):(ROOT/path).write_text(json.dumps(value,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
def artifact(name,title,caption,source,paragraph):
    local='build/research/playhub-semantic-coverage/native-images/gilbert-original-notebooks/'+name
    with Image.open(ROOT/local)as im:im.load();dims=im.size
    assert dims==(1000,750)
    return {'url':'https://images-grumpygamer.nyc3.digitaloceanspaces.com/'+name,
      'title':title,'caption':caption,'source_page':source,
      'creator':'Ron Gilbert (design notebook)',
      'credit':'Ron Gilbert / original Monkey Island design-notebook archive',
      'license':'Original notebook, game and photographic rights retained. Published by RonGilbert on his own GrumpyGamer site; no open licence claimed.',
      'width':1000,'height':750,'story_paragraph':paragraph,'recovery_local_source':local,
      'verification':{'sha256':hashlib.sha256((ROOT/local).read_bytes()).hexdigest(),'native_dimensions':list(dims),'no_upscale':True},
      'visual_review':'Actually viewed original photograph in full/source contact sheet. Source identifies original MonkeyIsland design notebook; proposed ideas are not represented as the final released game.'}
flow=artifact('IMG_0496.jpg','Monkey Island: Ron Gilbert\u2019s original main-flow notes',
 'Original early planning notes list putting together a crew on M\u00eal\u00e9e Island. These are development ideas, not a final walkthrough.',
 'https://grumpygamer.com/monkey_island_design_scribblings/',1)
world=artifact('IMG_0492.jpg','Monkey Island: early proposed world layout',
 'An early notebook plan labels M\u00eal\u00e9e Island and Monkey Island. The proposed sailing map is not the final game\u2019s navigation screen.',
 'https://grumpygamer.com/monkey_island_design_notebook2/',4)
artifacts=load('content/expansion/museum-secondary-artifacts-editorial-reviewed.json')
rows=artifacts['entries'].setdefault('wikipedia-80981',[])
rows[:]=[i for i in rows if i['url']!=flow['url']];rows.append(flow)
save('content/expansion/museum-secondary-artifacts-editorial-reviewed.json',artifacts)
doc=load('content/expansion/playhub-theme-semantic-restorations.json');row=next(r for r in doc['restorations']if r['theme_id']=='monkey')
chapter=next(ch for ch in row['chapters']if ch['source_chapter_index']==1)
chapter['images']=[world];chapter['illustration_status']='reviewed_original_development_notebook_artifact'
old='https://images.launchbox-app.com/d44b00ed-cd12-420a-86cd-17a4a0ee3a38.jpg'
row['remove_redundant_image_urls']=list(dict.fromkeys(row.get('remove_redundant_image_urls',[])+[old]))
for url in [flow['source_page'],world['source_page']]:
    if url not in row['historical_sources']:row['historical_sources'].append(url)
save('content/expansion/playhub-theme-semantic-restorations.json',doc)
save('build/research/playhub-semantic-coverage/monkey-two-notebook-artifacts-review.json',
 {'status':'PASS_SOURCE_AND_ACTUAL_VISUAL','images':[flow,world],
  'redundant_lower_resolution_regional_box_back_removed':old,
  'source_chapter_now_contextually_illustrated':1,'not_assembled_yet':True,
  'remaining_insult_fighting_chapter_not_marked_illustrated':True})
print('Two original notebook artifacts admitted source-only;30/48 restored chapters now have reviewed image associations.')
