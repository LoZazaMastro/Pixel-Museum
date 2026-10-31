"""Import the user's finished PNGs and the two transparent award logo variants."""
from pathlib import Path
import copy,hashlib,json,runpy,shutil
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/user-media-updates-20261031'
OUT.mkdir(parents=True,exist_ok=True)
catalog_path=ROOT/'content/catalog.json'
original=catalog_path.read_bytes()
catalog=json.loads(original)
owners={e['id']:e for e in catalog['entries']}
manifest_path=ROOT/'assets/images/manifest.json'
manifest=json.loads(manifest_path.read_bytes())
helper=runpy.run_path(str(ROOT/'tools/bundle-editorial-images.py'))
assets=[]

def bundle(path,title,creator,credit,source_page,license_text,transparent_required=False):
    raw=path.read_bytes();identity=hashlib.sha256(raw).hexdigest()
    key='https://pixel-museum.invalid/local/user-supplied/'+identity[:24]+'.png'
    # .invalid identifies an offline-only local derivative, never a fictitious
    # download source. Its actual source, author and modifications stay explicit.
    frozen=OUT/path.name
    if not frozen.exists():shutil.copy2(path,frozen)
    assert frozen.read_bytes()==raw,'Received source changed during admission'
    with Image.open(frozen) as source:
        dimensions=source.size;full,small,alpha=helper['prepare_rasters'](source)
        if transparent_required:assert alpha,'Logo must retain transparency'
    relative='assets/images/'+hashlib.sha256(key.encode()).hexdigest()[:24]+'.png'
    preview=relative.replace('assets/images/','assets/images/previews/')
    helper['save_raster'](full,ROOT/relative)
    helper['save_raster'](small,ROOT/preview,preview=True)
    manifest['images'][key]=relative;manifest['previews'][key]=preview
    manifest['metadata'][key]={'source_width':dimensions[0],'source_height':dimensions[1],
        'width':full.width,'height':full.height,'preview_width':small.width,'preview_height':small.height,
        'sha256':hashlib.sha256((ROOT/relative).read_bytes()).hexdigest(),
        'alpha_preserved':alpha,'alpha_composited':False,'alpha_policy_version':1,
        'acquisition':'user_supplied_local_asset','title':title,'source_page':source_page,
        'creator':creator,'credit':credit,'license':license_text}
    assets.append({'key':key,'file':relative,'received_source':str(frozen.relative_to(ROOT)),
                   'source_sha256':identity})
    return key,dimensions,str(frozen.relative_to(ROOT)).replace('\\','/')

for owner,name in [('xbox-one','Xbox-One-originale.png'),('switch-2','Nintendo-Switch-2-originale.png')]:
    e=owners[owner];old=copy.deepcopy(e['images'][e['preferred_image']])
    key,dimensions,source=bundle(ROOT/'build/photoshop'/name,old.get('title',e['title']),
        old.get('creator',''),old.get('credit','')+' / image adjusted by Andrea Sgarro',
        old.get('source_page',''),old.get('license','Copyright retained by its owner'))
    for other in catalog['entries']:
        for i,image in enumerate(other.get('images') or []):
            if image.get('url')!=old['url']:continue
            replacement=copy.deepcopy(image)
            replacement.update(url=key,width=dimensions[0],height=dimensions[1],
                original_url=old.get('original_url',old['url']),recovery_local_source=source,
                modifications_note='User-supplied Photoshop revision; no further crop or retouch applied.')
            replacement['verification']={'sha256':hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),
                                         'native_dimensions':list(dimensions),'processing':'User-supplied Photoshop revision'}
            other['images'][i]=replacement

logos={}
for mode in ['light','dark']:
    logos[mode]=bundle(ROOT/'build/research/golden-joystick-theme-logo-20261031'/('golden-joystick-'+mode+'.png'),
        'Golden Joystick Awards logo','Golden Joystick Awards / Future',
        'Original SVG supplied by Andrea Sgarro; '+('white wordmark only' if mode=='dark' else 'original colours'),
        '', 'Brand imagery; rights retained by the original owner. Transparent rasterization of supplied SVG.',True)
golden_count=0
for e in catalog['entries']:
    if not e['id'].startswith('golden-joystick-awards-'):continue
    key,dimensions,source=logos['light']
    e['images'][0].update(url=key,dark_url=logos['dark'][0],source_page='',
        title='Golden Joystick Awards logo',creator='Golden Joystick Awards / Future',
        credit='Original SVG supplied by Andrea Sgarro; dark variant changes the wordmark fill only',
        license='Brand imagery; rights retained by the original owner',license_url='',width=dimensions[0],height=dimensions[1],
        story_paragraph=0,recovery_local_source=source)
    e['images'][0]['verification']={'sha256':hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),
        'native_dimensions':list(dimensions),'processing':'Transparent SVG rasterization; white wordmark in dark variant only'}
    e['preferred_image']=0;golden_count+=1

identity='workbook-12-04-prince-of-persia-2008'
before=copy.deepcopy(owners[identity]);owners[identity]['title']='Prince of Persia'
source_hash=runpy.run_path(str(ROOT/'tools/project-reviewed-locales.py'))['source_hash']
localized=[]
for language in ['it','fr','de','es']:
    path=ROOT/'content/museum-locales'/(language+'.json');raw=path.read_bytes();document=json.loads(raw)
    translation=document['entries'].get(identity)
    if translation:
        assert translation['provenance']['source_fields_sha256']==source_hash(before),(language,'stale text')
        translation['title']='Prince of Persia'
        translation['provenance']['source_fields_sha256']=source_hash(owners[identity])
        localized.append((path,document,raw))
assert catalog_path.read_bytes()==original,'Concurrent catalogue change'
(OUT/'catalog-before-user-assets.json').write_bytes(original)
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for path,document,raw in localized:
    assert path.read_bytes()==raw,'Concurrent translation change'
    path.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(OUT/'receipt.json').write_text(json.dumps({'assets':assets,'golden_entries':golden_count,
    'renamed':identity,'localized_titles':len(localized)+1},indent=2)+'\n',encoding='utf8')
print('USER_ASSETS_APPLIED',len(assets),'GOLDEN_ENTRIES',golden_count,'PRINCE_TITLE_LANGUAGES',len(localized)+1)
