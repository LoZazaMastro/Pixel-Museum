#!/usr/bin/env python3
"""Build the offline photograph library and fast previews without changing source credits.

The resumable manifest maps original display URLs to packaged assets. Existing
Playhub originals and development caches are reused before requesting publishers.
Only images are included; films and music keep their online playback URLs.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, io, json, os, re, threading, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse, unquote
from PIL import Image, ImageOps, ImageFile
ImageFile.MAXBLOCK=64<<20
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/images'
LOCK=threading.Lock()
ALPHA_POLICY_VERSION=1

def prepare_rasters(source):
 """Keep genuine transparency, including palette/LA images and hidden RGB."""
 source=ImageOps.exif_transpose(source)
 possible_alpha=source.mode in ('RGBA','LA') or 'transparency' in source.info
 rgba=source.convert('RGBA') if possible_alpha else None
 preserve_alpha=rgba is not None and rgba.getchannel('A').getextrema()[0]<255
 full=rgba if preserve_alpha else source.convert('RGB')
 full.thumbnail((4096,4096),Image.Resampling.LANCZOS)
 small=full.copy();small.thumbnail((1024,1024),Image.Resampling.LANCZOS)
 return full,small,preserve_alpha

def save_raster(image,path,preview=False):
 if image.mode=='RGBA':image.save(path,'PNG',optimize=True)
 else:image.save(path,'JPEG',quality=91 if preview else 94,subsampling=0,optimize=True)

def fnv(url):
 value=14695981039346656037
 for c in url.encode():value=((value^c)*1099511628211)&((1<<64)-1)
 return f'{value:016x}'

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--catalog',default='content/catalog.json');parser.add_argument('--workers',type=int,default=8);args=parser.parse_args()
 catalog=json.loads((ROOT/args.catalog).read_text(encoding='utf-8'));images={}
 for entry in catalog['entries']:
  photos=list(entry.get('images',[]))
  for feature in entry.get('editorial_features',[]):photos.extend(feature.get('images',[]))
  for image in photos:
   if image.get('url'):images.setdefault(image['url'],image)
 history_path=ROOT/'content/human-history.json'
 if history_path.exists():
  for entry in json.loads(history_path.read_text(encoding='utf8')).get('entries',[]):
   for image in entry.get('images',[]):
    if image.get('url'):images.setdefault(image['url'],image)
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'previews').mkdir(exist_ok=True)
 prior=json.loads((OUT/'manifest.json').read_text(encoding='utf-8')) if (OUT/'manifest.json').exists() else {}
 manifest={'schema_version':1,'images':{},'previews':{},'metadata':{},'failures':{}}
 caches=[]
 for folder in [ROOT/'build/preview-data/cache',ROOT/'build/media-catalog-smoke-cache',ROOT/'build/media-smoke-cache']:
  if folder.is_dir():caches.append(folder)
 for folder in (ROOT/'build/console-slice').glob('**/cache'):
  if folder.is_dir():caches.append(folder)
 cache_files={}
 for folder in caches:
  for file in folder.glob('*.bin'):cache_files.setdefault(file.stem,file)
 playhub=Path('F:/Playhub/Plugin/Playhub/assets/on-this-day/v1')
 def save_manifest():
  temp=OUT/'manifest.json.tmp';temp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(OUT/'manifest.json')
 wiki_files={}
 for cached_url,cached_path in prior.get('images',{}).items():
  if 'wikimedia.org/' not in cached_url:continue
  filename=re.sub(r'^\d+px-','',unquote(urlparse(cached_url).path.rsplit('/',1)[-1]))
  wiki_files.setdefault(filename,cached_url)
 def get(url,image):
  digest=hashlib.sha256(url.encode()).hexdigest()[:24]
  old=prior.get('images',{}).get(url);preview=prior.get('previews',{}).get(url)
  def adequate_existing(path):
   previous=prior.get('metadata',{}).get(url,{})
   # White-composited previews cannot recover transparency. Re-read their
   # authentic source once; never infer an alpha mask from the baked JPEG.
   if previous.get('alpha_composited') and previous.get('alpha_policy_version')!=ALPHA_POLICY_VERSION:return False
   local=ROOT/image.get('recovery_local_source','__no_master__')
   if not local.is_file():return True
   try:
    with Image.open(local) as master:
     if (master.mode in ('RGBA','LA') or 'transparency' in master.info) and previous.get('alpha_policy_version')!=ALPHA_POLICY_VERSION:
      return False
     size=list(master.size);scale=min(1,4096/max(size));expected=(round(size[0]*scale),round(size[1]*scale))
    with Image.open(ROOT/path) as existing:return existing.width>=expected[0]-1 and existing.height>=expected[1]-1
   except Exception:return False
  if old and preview and (ROOT/old).is_file() and (ROOT/preview).is_file() and adequate_existing(old):
   metadata=dict(prior.get('metadata',{}).get(url,{}))
   for field in ['title','source_page','creator','credit','license','license_url']:
    if field in image:metadata[field]=image[field]
   return url,old,preview,metadata,None
  if 'wikimedia.org/' in url:
   filename=re.sub(r'^\d+px-','',unquote(urlparse(url).path.rsplit('/',1)[-1]))
   alias=wiki_files.get(filename)
   if alias and alias!=url:
    other=prior['images'][alias];small=prior.get('previews',{}).get(alias)
    if small and (ROOT/other).is_file() and (ROOT/small).is_file() and adequate_existing(other):
     meta=dict(prior.get('metadata',{}).get(alias,{}));meta['acquisition']='existing_local_same_wikimedia_file'
     for field in ['title','source_page','creator','credit','license','license_url']:
      if field in image:meta[field]=image[field]
     return url,other,small,meta,None
  candidates=[]
  if image.get('recovery_local_source'):candidates.append(ROOT/image['recovery_local_source'])
  if 'raw.githubusercontent.com/LoZazaMastro/Playhub/' in url:candidates.append(playhub/unquote(urlparse(url).path.rsplit('/',1)[-1]))
  cached=cache_files.get(fnv(url));
  if cached:candidates.append(cached)
  for ext in ['jpg','png','webp']:
   candidates.append(ROOT/'build/research/image-quality'/(hashlib.sha256(url.encode()).hexdigest()[:16]+'.'+ext))
  body=None;origin='publisher'
  for path in candidates:
   if path.is_file():
    try:
     data=path.read_bytes();test=Image.open(io.BytesIO(data));test.verify();body=data;origin='existing_local_original';break
    except Exception:pass
  error=''
  for attempt in range(2):
   try:
    if body is None:
     request=Request(url,headers={'User-Agent':'PixelMuseum/0.1 (historical collection; image packaging)'})
     with urlopen(request,timeout=35) as response:
      body=response.read(24<<20)
    with Image.open(io.BytesIO(body)) as source:
     source.load();source=ImageOps.exif_transpose(source);source_size=source.size
     if min(source_size)<32:raise ValueError('Image is too small')
     full,small,preserve_alpha=prepare_rasters(source)
     extension='.png' if preserve_alpha else '.jpg'
     fullpath=OUT/(digest+extension);save_raster(full,fullpath)
     previewpath=OUT/'previews'/(digest+extension);save_raster(small,previewpath,preview=True)
     relative=fullpath.relative_to(ROOT).as_posix();previewrelative=previewpath.relative_to(ROOT).as_posix()
     metadata={'source_width':source_size[0],'source_height':source_size[1],'width':full.width,'height':full.height,'preview_width':small.width,'preview_height':small.height,'sha256':hashlib.sha256(fullpath.read_bytes()).hexdigest(),'acquisition':origin,'alpha_composited':False,'alpha_preserved':preserve_alpha,'alpha_policy_version':ALPHA_POLICY_VERSION}
     for key in ['title','source_page','creator','credit','license','license_url']:
      if key in image:metadata[key]=image[key]
     return url,relative,previewrelative,metadata,None
   except Exception as exc:
    error=str(exc);body=None
    if attempt==0:time.sleep(.3)
  return url,None,None,None,error
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
  futures=[executor.submit(get,url,image) for url,image in images.items()]
  for number,future in enumerate(concurrent.futures.as_completed(futures),1):
   url,path,preview,meta,error=future.result()
   if error:manifest['failures'][url]=error
   else:manifest['images'][url]=path;manifest['previews'][url]=preview;manifest['metadata'][url]=meta
   if number%25==0:save_manifest();print(f'{number}/{len(images)} images processed; {len(manifest["failures"])} unavailable',flush=True)
 save_manifest();print(json.dumps({'requested':len(images),'bundled':len(manifest['images']),'failed':len(manifest['failures'])},indent=2),flush=True)
 return bool(manifest['failures'])
if __name__=='__main__':raise SystemExit(main())
