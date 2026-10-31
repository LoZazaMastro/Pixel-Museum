"""Source-identified history illustrations; no generic gallery fallback."""
from pathlib import Path
import importlib.util,json,re,hashlib,io,html
from urllib.parse import unquote
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('history_source',ROOT/'content/expansion/build-human-history.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
OUT=ROOT/'build/research/human-history/editorial-artifacts';OUT.mkdir(exist_ok=True)
targets={
 'London Underground':('Metropolitan Railway, Baker Street Station.jpg','Metropolitan Railway at Baker Street, circa1863; contemporary illustration.'),
 'Fall of the Berlin Wall':('Fall of the Berlin Wall 1989, people walking.jpg','People crossing the Berlin Wall during its opening in1989.'),
 'Ingenuity (helicopter)':('Ingenuity Helicopter with fully deployed legs (cropped).png','The actual Ingenuity helicopter on Mars, photographed by Perseverance in2021.'),
 'Event Horizon Telescope':('Black hole - Messier 87 crop max res.jpg','The Event Horizon Telescope image of M87*, first published in2019.'),
 'Oculus Rift':('Oculus Rift - Developer Version - Front.jpg','Original-generation Oculus Rift development hardware; distinguished from the later consumerCV1.'),
 'Pluto':('Pluto in True Color - High-Res.png','Pluto photographed by New Horizons in2015, following the2006classification change.'),
 'Rosetta (spacecraft)':('Rosetta and Philae at comet (11206660686).jpg','ESA artist illustration of Rosetta and Philae approaching their target comet.'),
 'Perseverance (rover)':("PIA24836 Perseverance's Selfie at Rochette.jpg",'Perseverance photographed on Mars at Rochette on10September2021.'),
 'First observation of gravitational waves':('Northern leg of LIGO interferometer on Hanford Reservation.JPG','The actual LIGO Hanford interferometer, part of the2015gravitational-wave discovery.'),
 '2024 Summer Olympics':('France smoke flag 2024 Summer Olympics opening.jpg','The opening ceremony of the Paris2024Olympic Games.'),
 'Falcon Heavy':('Falcon Heavy Side Boosters landing on LZ1 and LZ2 - 2018 (25254688767).jpg','The twin side boosters landing after the first Falcon Heavy demonstration flight,6February2018.'),
 'We Are the World':('USA For Africa 1985 (US Press Kit 001).jpg','USA for Africa in1985, from the original Columbia Records press kit.'),
}
path=ROOT/'content/expansion/human-history-official-images-editorial.json';rows=json.loads(path.read_text(encoding='utf8')).get('entries',{}) if path.exists() else {};errors={}
meta=h.api({'action':'query','titles':'|'.join('File:'+t[0] for t in targets.values()),'prop':'imageinfo','iiprop':'url|size|extmetadata'})
files={p['title'].removeprefix('File:').replace('_',' '):p.get('imageinfo',[{}])[0] for p in meta.get('query',{}).get('pages',[])}
for subject,(filename,caption) in targets.items():
 try:
  image=files[filename];url=image['url'];local=OUT/(hashlib.sha256(url.encode()).hexdigest()[:20]+Path(filename).suffix.lower())
  if not local.exists():local.write_bytes(h.fetch(url))
  with Image.open(local) as im:im.load();w,he=im.size
  if max(w,he)<800:raise ValueError('Native source is below800pixels')
  m=image['extmetadata'];creator=h.clean(m.get('Artist',{}).get('value'));licence=h.clean(m.get('LicenseShortName',{}).get('value'))
  if not creator or not licence:raise ValueError('Missing actual creator or licence')
  rows[subject]={'url':url,'title':filename,'caption':caption,'creator':creator,'credit':creator+' / '+licence,'license':licence,'license_url':m.get('LicenseUrl',{}).get('value',''),'source_page':image['descriptionurl'],'width':w,'height':he,'recovery_local_source':local.relative_to(ROOT).as_posix(),'verification':{'sha256':hashlib.sha256(local.read_bytes()).hexdigest(),'native_dimensions':[w,he]},'context_review_status':'PASS_IDENTIFIED_SUBJECT','story_paragraph':0}
  print(subject,w,he,flush=True)
 except Exception as error:errors[subject]=str(error)
for subject,slug in [('Princess Mononoke','mononoke'),('Spirited Away','chihiro')]:
 try:
  source='https://www.ghibli.jp/works/'+slug+'/'
  receipt=OUT/(slug+'.html')
  if not receipt.exists():receipt.write_bytes(h.fetch(source))
  text=html.unescape(receipt.read_text(encoding='utf8'));images=list(dict.fromkeys(re.findall(r'https://www\.ghibli\.jp/gallery/'+slug+r'\d+\.jpg',text)))
  if not images:raise ValueError('No actual gallery still linked by the official film page')
  url=images[0];local=OUT/(slug+'.jpg')
  if not local.exists():local.write_bytes(h.fetch(url))
  with Image.open(local) as im:im.load();w,he=im.size
  if w<1600:raise ValueError('Official still is below intended native width')
  copyright_line=h.clean(re.search(r'[^<>]*[©\u00a9][^<>]+',text).group(0))
  rows[subject]={'url':url,'title':'Official film still from '+subject,'caption':subject+' — official Studio Ghibli gallery still.','creator':copyright_line,'credit':copyright_line,'license':'Official Studio Ghibli gallery release; original film rights retained. Not a Creative Commons licence.','license_url':'https://www.ghibli.jp/info/013344/','source_page':source,'width':w,'height':he,'recovery_local_source':local.relative_to(ROOT).as_posix(),'verification':{'sha256':hashlib.sha256(local.read_bytes()).hexdigest(),'native_dimensions':[w,he]},'context_review_status':'PASS_OFFICIAL_WORK','story_paragraph':0}
  print(subject,w,he,flush=True)
 except Exception as error:errors[subject]=str(error)
path.write_text(json.dumps({'schema_version':1,'entries':rows},ensure_ascii=True,indent=2)+'\n',encoding='utf8')
(OUT/'audit.json').write_text(json.dumps({'acquired':list(rows),'held':errors},ensure_ascii=True,indent=2)+'\n',encoding='utf8')
print('Held',json.dumps(errors),flush=True)
