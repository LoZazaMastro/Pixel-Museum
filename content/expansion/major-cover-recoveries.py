"""Recover named original-game covers/artwork from publishers and archival scans.

No image is enlarged. Crops of full printed inserts are recorded explicitly;
the local cache retains the cropped master used by the offline image bundler.
"""
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
import hashlib,io,json
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
CACHE=ROOT/'build/research/image-quality'
CACHE.mkdir(parents=True,exist_ok=True)
PS='https://gmedia.playstation.com/is/image/SIEPDC/'
SOURCE='https://www.playstation.com/en-us/uncharted/'
ROWS=[
 ("Uncharted: Drake's Fortune",None,PS+'uncharted-1-drakes-fortune-keyart-16x9-en-04aug21?scl=1&fmt=jpeg&qlt=95',SOURCE,'Naughty Dog / Sony Interactive Entertainment','artwork',None),
 ('Uncharted 2: Among Thieves',None,PS+'uncharted-2-among-theives-16x9-en-04aug21?scl=1&fmt=jpeg&qlt=95',SOURCE,'Naughty Dog / Sony Interactive Entertainment','artwork',None),
 ("Uncharted 3: Drake's Deception",'workbook-11-01-uncharted-3-drake-s-deception',PS+'uncharted-3-drakes-deception-16x9-en-04aug21?scl=1&fmt=jpeg&qlt=95',SOURCE,'Naughty Dog / Sony Interactive Entertainment','artwork',None),
 ("Uncharted 4: A Thief's End",'workbook-05-10-uncharted-4-a-thief-s-end',PS+'Uncharted-4-keyart-01-en-16jun21?scl=1&fmt=jpeg&qlt=95',SOURCE,'Naughty Dog / Sony Interactive Entertainment','artwork',None),
 ('Uncharted: The Lost Legacy','workbook-08-22-uncharted-the-lost-legacy',PS+'Uncharted-The-Lost-Legacy-keyart-01-en-16jun21?scl=1&fmt=jpeg&qlt=95',SOURCE,'Naughty Dog / Sony Interactive Entertainment','artwork',None),
 ('Batman: Arkham Shadow','wikipedia-76786178','https://static.dc.com/2024-11/2024_10_29_BatmanArkhamShadow_ProdPage_Profile.jpg','https://www.dc.com/games/batman-arkham-shadow-2024','DC / Camouflaj / Oculus Studios','cover',None),
 ('Resident Evil 2 (1998 video game)','workbook-01-29-resident-evil-2-1998-video-game','https://psxdatacenter.com/images/hires/U/R/SLUS-00421/SLUS-00421-F-ALL.jpg','https://psxdatacenter.com/images/hires/U/R/SLUS-00421/SLUS-00421-F-ALL.html','Capcom / scan preserved by PSXDataCenter','cover',(260,0,1695,1390)),
 ('Resident Evil Outbreak','wikipedia-2093486','https://psxdatacenter.com/psx2/images2/hires/SLUS-20765/SLUS-20765-F-ALL.jpg','https://psxdatacenter.com/psx2/images2/hires/SLUS-20765/SLUS-20765-F-ALL.html','Capcom / scan preserved by PSXDataCenter','cover',(1710,0,3206,2136)),
]

def main():
    named={};overrides={};failures=[]
    for title,eid,remote,source,owner,kind,crop in ROWS:
        url=remote+('#front-cover' if crop else '')
        target=CACHE/(hashlib.sha256(url.encode()).hexdigest()[:16]+'.jpg')
        try:
            if target.exists():raw=target.read_bytes();image=Image.open(io.BytesIO(raw));image.load()
            else:
                with urlopen(Request(remote,headers={'User-Agent':'PixelMuseum/0.1 historical collection research'}),timeout=25) as response:raw=response.read(24<<20)
                image=Image.open(io.BytesIO(raw));image.load()
                if crop:image=image.crop(crop)
                image.convert('RGB').save(target,'JPEG',quality=96,subsampling=0);raw=target.read_bytes()
            w,h=image.size
            if max(w,h)<1200 or min(w,h)<700 or w/h>2.2:raise ValueError('Original master is too small or too wide')
            row={'url':url,'source_page':source,'title':title+(': original printed front cover' if crop else ': publisher cover artwork'),
                 'creator':owner,'credit':owner,'license':'Publisher copyright retained; historical editorial illustration. Not an open-licensed asset.',
                 'width':w,'height':h,'native_long_edge':max(w,h),'kind':kind,'cover_role':True,'story_paragraph':0,
                 'quality_verified':'Original file decoded at native resolution; no enlargement.',
                 'verification':{'sha256':hashlib.sha256(raw).hexdigest(),'checked_utc':datetime.now(timezone.utc).isoformat()},
                 'provenance':{'source':'Publisher game page' if not crop else 'Archived scan of original printed game insert',
                               'source_image_url':remote,'crop_pixels':list(crop) if crop else None,
                               'modifications':'Front panel cropped from complete printed insert; no reconstruction or enlargement.' if crop else 'No content changes; JPEG encoding for offline packaging.'}}
            named[title]=row
            if eid:overrides[eid]=row
            print(title,w,h,flush=True)
        except Exception as error:failures.append({'title':title,'error':str(error)})
    (HERE/'major-official-cover-sources.json').write_text(json.dumps({'entries':named,'failures':failures},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (HERE/'museum-cover-recoveries-aaa.json').write_text(json.dumps({'entries':overrides,'failures':failures},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
