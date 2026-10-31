#!/usr/bin/env python3
"""Attach the official complete ceremony for every shared awards archive card."""
from pathlib import Path
from urllib.request import Request,urlopen
from PIL import Image
import json,hashlib,io,concurrent.futures,copy
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'build/research/tga';path=ROOT/'content/expansion/museum-awards-additions.json'
doc=json.loads(path.read_text(encoding='utf8'));original=doc['entries'][0]
year_bodies={int(h[:4]):b for h,b in zip(original['story_headings'],original['body']) if h[:4].isdigit()}
assert set(year_bodies)==set(range(2014,2026))
ids=json.loads((folder/'official-replay-ids.json').read_text(encoding='utf8'))
def photo(year):
 identifier=ids[str(year)];data=json.loads((folder/f'official-youtube-{year}.json').read_text(encoding='utf8'))
 candidates=[f'https://i.ytimg.com/vi/{identifier}/maxresdefault.jpg',f'https://i.ytimg.com/vi/{identifier}/sddefault.jpg']
 candidates.extend(t['url'] for t in sorted(data.get('thumbnails',[]),key=lambda t:t.get('width') or 0,reverse=True))
 for url in candidates:
  try:
   body=urlopen(Request(url,headers={'User-Agent':'PixelMuseum/0.1 historical collection'}),timeout=15).read()
   with Image.open(io.BytesIO(body)) as im:im.load();w,h=im.size
   if max(w,h)<600:continue
   local=ROOT/'build/research/image-quality'/(hashlib.sha256(url.encode()).hexdigest()[:16]+'.jpg');local.write_bytes(body)
   return {'url':url,'title':f'The Game Awards {year} official show archive image','width':w,'height':h,'creator':'The Game Awards','credit':'The Game Awards / official ceremony publication','source_page':f'https://www.youtube.com/watch?v={identifier}','license':'Copyright The Game Awards; historical exhibition reference','license_url':'','story_paragraph':2+year-2014}
  except Exception:continue
 raise ValueError('Official show archive image unavailable: '+str(year))
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:photos=list(pool.map(photo,range(2014,2026)))
intro_photos=[]
for name,title,index in [('8180739b-tga_2018_bg.webp','The Game Awards official archive artwork',0),('c6ded83c-shawn_phil_reggie.jpg','Shawn Layden, Phil Spencer and Reggie Fils-Aime share the stage in 2018',1)]:
 url='https://assets.thegameawards.com/2026/07/'+name;body=urlopen(Request(url,headers={'User-Agent':'PixelMuseum/0.1 historical collection'}),timeout=20).read()
 with Image.open(io.BytesIO(body)) as im:im.load();w,h=im.size
 local=ROOT/'build/research/image-quality'/(hashlib.sha256(url.encode()).hexdigest()[:16]+('.jpg' if name.endswith('.jpg') else '.webp'));local.write_bytes(body)
 intro_photos.append({'url':url,'title':title,'width':w,'height':h,'creator':'The Game Awards','credit':'The Game Awards / official historical archive','source_page':'https://thegameawards.com/rewind/year-2018','license':'Copyright The Game Awards; historical exhibition reference','license_url':'','story_paragraph':index})
videos=[]
for year in range(2014,2026):
 data=json.loads((folder/f'official-youtube-{year}.json').read_text(encoding='utf8'));assert data['availability']=='public' and data['uploader']=='thegameawards'
 videos.append({'youtube_id':data['id'],'url':data['webpage_url'],'title':f'{year} The Game Awards official ceremony','caption':f'Watch the complete official {year} ceremony, published by The Game Awards.','creator':'The Game Awards','source_page':data['webpage_url'],'credit':'The Game Awards / original official YouTube publication','license':'Copyright The Game Awards; remote playback from original publication','license_url':'','verified_on':'2026-10-21','story_paragraph':2+year-2014})
body=["The Game Awards celebrates the people who make games: designers, artists, writers, performers, composers and the teams around them. Created by Geoff Keighley in 2014, the annual show combines awards with performances, announcements and conversations about the medium.","An awards archive is also a record of changing priorities. Categories make room for new ways to play and new kinds of work, from independent production and performance to accessibility and community support. Move through the years to read every category winner, then open the official ceremony beside the list."]+[year_bodies[year] for year in range(2014,2026)]
headings=['What the awards celebrate','A changing medium, a shared stage']+[f'{year} Winners' for year in range(2014,2026)]
for entry in doc['entries']:
 entry['body']=copy.deepcopy(body);entry['story_headings']=headings.copy();entry['images']=copy.deepcopy(intro_photos+photos);entry['videos']=copy.deepcopy(videos);entry['preferred_image']=2+entry['year']-2014
path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('TGA:',len(doc['entries']),'annual stops;',len(body),'shared cards;',len(videos),'official ceremonies;',len(intro_photos+photos),'images')
