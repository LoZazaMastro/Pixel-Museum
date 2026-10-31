"""Stage the complete offline image set referenced by a runtime catalogue."""
from pathlib import Path
import json, shutil
from package_base_assets import copy_changed

def required_image_urls(*catalogues):
    required=set()
    for catalog in catalogues:
        for entry in catalog['entries']:
            for image in entry.get('images',[]):
                required.add(image['url'])
                if image.get('dark_url'):required.add(image['dark_url'])
            for feature in entry.get('editorial_features',[]):
                for image in feature.get('images',[]):
                    required.add(image['url'])
                    if image.get('dark_url'):required.add(image['dark_url'])
    return required


def stage(catalog, root, destination, additional_catalogs=()):
    root=Path(root);destination=Path(destination)
    source=json.loads((root/'assets/images/manifest.json').read_text(encoding='utf-8'))
    required=required_image_urls(catalog, *additional_catalogs)
    missing=required-source.get('images',{}).keys()
    if missing:raise ValueError('Images are missing from the offline library: '+repr(sorted(missing)))
    manifest={'schema_version':1,'images':{},'previews':{},'metadata':{},'failures':{}}
    for url in sorted(required):
        for field in ['images','previews']:
            relative=source.get(field,{}).get(url)
            if not relative:raise ValueError('Image preview is missing: '+url)
            path=Path(relative)
            if path.is_absolute() or '..' in path.parts or path.parts[:2]!=('assets','images'):raise ValueError('Unsafe image asset path')
            origin=root/path;target=destination/path
            if not origin.is_file():raise ValueError('Bundled image asset is missing: '+str(path))
            target.parent.mkdir(parents=True,exist_ok=True);copy_changed(origin,target);manifest[field][url]=relative
        if url in source.get('metadata',{}):manifest['metadata'][url]=source['metadata'][url]
    target=destination/'assets/images/manifest.json';target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    return len(required)
