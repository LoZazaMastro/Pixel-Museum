"""Publish four exact assets already visually reviewed; does not fetch or delete."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/cover-post2015'
def load(path):return json.loads(path.read_text(encoding='utf8'))
path=ROOT/'content/expansion/museum-preferred-game-covers-editorial-reviewed.json'
doc=load(path)
inventory={r['entry_id']:r for r in load(OUT/'inventory.json')['entries']}
chosen={
 'wikipedia-79613463':('Nintendo','Mario Kart World: official clean publisher artwork'),
 'wikipedia-83404081':('Bandai Namco Entertainment / FromSoftware','Elden Ring Shadow of the Erdtree: official clean key art'),
 'wikipedia-70711554':('Activision / Infinity Ward','Call of Duty Modern Warfare II (2022): official clean key art'),
 'wikipedia-23888095':('Atlus / Sega','Persona 5: original cast illustration from the official western publication'),
}
records=[r for r in load(OUT/'secondary-pages.json')if r['entry_id']in chosen and r.get('status')=='pending_visual_review']
persona=next(r for r in load(OUT/'publisher-specific-assets.json')if r['key']=='persona5-main')
persona.update(entry_id='wikipedia-23888095',source_page='https://www.atlus.com/persona5/home.html')
records.append(persona)
assert len(records)==4
for row in records:
 eid=row['entry_id'];owner,title=chosen[eid];asset=ROOT/row['recovery_local_source']
 assert hashlib.sha256(asset.read_bytes()).hexdigest()==row['sha256']
 assert max(row['width'],row['height'])>=800
 doc['entries'][eid]={
  'url':row['url'],'title':title,'width':row['width'],'height':row['height'],
  'source_page':row['source_page'],'creator':owner,
  'credit':owner+' / original publisher-delivered artwork',
  'license':'Original game artwork; publisher, developer, artist and trademark rights retained. Not an open licence.',
  'recovery_local_source':row['recovery_local_source'],'cover_art':True,'story_paragraph':0,
  'supersedes_urls':[inventory[eid]['preferred_url']],
  'verification':{'sha256':row['sha256'],'native_dimensions':[row['width'],row['height']],'no_upscale':True},
  'visual_review':'Personally viewed secondary-review.jpg or the full publisher-native Persona5 illustration. Exact original game, no platform header; no remaster or platform-labelled packaging substituted.',
 }
path.write_text(json.dumps(doc,indent=2,ensure_ascii=True)+'\n',encoding='utf8')
print('Four reviewed publisher artworks promoted to source overrides; assembly remains separate.')
