"""Bundle just the reviewed returned-editorial image patches, reusing originals."""
from pathlib import Path
import hashlib, json, runpy
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
helper=runpy.run_path(str(ROOT/'tools/bundle-editorial-images.py'))
path=ROOT/'assets/images/manifest.json'
manifest=json.loads(path.read_text(encoding='utf8'))
patches=json.loads((ROOT/'content/external-editorial/sol-pro-20261030/media-patches.json').read_text(encoding='utf8'))
count=0
for row in patches['patches']:
    for change in row.get('images',[]):
        im=change['replacement'];url=im['url'];source=ROOT/im['recovery_local_source']
        with Image.open(source) as image:
            original=image.size;full,small,alpha=helper['prepare_rasters'](image)
        name=hashlib.sha256(url.encode()).hexdigest()[:24]+('.png' if alpha else '.jpg')
        target=ROOT/'assets/images'/name;preview=ROOT/'assets/images/previews'/name
        helper['save_raster'](full,target);helper['save_raster'](small,preview,preview=True)
        manifest['images'][url]=target.relative_to(ROOT).as_posix()
        manifest['previews'][url]=preview.relative_to(ROOT).as_posix()
        manifest['metadata'][url]={'source_width':original[0],'source_height':original[1],
            'width':full.width,'height':full.height,'preview_width':small.width,'preview_height':small.height,
            'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'acquisition':'returned_editorial_original_asset',
            'alpha_preserved':alpha,'alpha_composited':False,'alpha_policy_version':1,
            **{k:im.get(k,'') for k in ('title','source_page','creator','credit','license','license_url')}}
        manifest['failures'].pop(url,None);count+=1
path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Returned editorial image originals/previews bundled:',count)
