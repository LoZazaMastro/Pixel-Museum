"""Read-only semantic, native-codec and offline-poster publication audit."""
import importlib.util,json,re
from pathlib import Path
from collections import Counter
from urllib.parse import urlparse,parse_qs
from datetime import datetime,timezone
from PIL import Image
p=Path(__file__).with_name('discover-museum-videos.py');sp=importlib.util.spec_from_file_location('discovery',p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
catalog=json.loads((m.ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries'];by={e['id']:e for e in catalog};assembled_ids=set(by)
extra=m.ROOT/'build/research/franchise-mainline/media-research-targets.json'
if extra.exists():
 for e in json.loads(extra.read_text(encoding='utf8'))['entries']:
  by.setdefault(e['entry_id'],{'id':e['entry_id'],'title':e['title'],'year':e['year'],'kind':'game','awaiting_article_admission':True})
for identity,title in [('zelda-oracle-of-seasons','The Legend of Zelda: Oracle of Seasons'),('zelda-oracle-of-ages','The Legend of Zelda: Oracle of Ages')]:
 by.setdefault(identity,{'id':identity,'title':title,'year':2001,'kind':'game','awaiting_article_admission':True})
m.KNOWN_TITLES={m.canonical(e['title']) for e in by.values() if e['kind']=='game'}
m.RELEASE_YEARS={key:{e['year'] for e in by.values() if e['kind']=='game' and m.canonical(e['title'])==key} for key in m.KNOWN_TITLES}
m.KNOWN_HARDWARE={m.canonical(e['title']) for e in by.values() if e['kind'] in ['console','computer','hardware']}
m.KNOWN_HARDWARE|={k.removeprefix('nintendo').removeprefix('sega').removeprefix('sony') for k in list(m.KNOWN_HARDWARE)}
m.AMBIGUOUS={key for key in m.KNOWN_TITLES if len({e['year'] for e in by.values() if e['kind']=='game' and m.canonical(e['title'])==key})>1}
m.AMBIGUOUS|={m.canonical(e['title']) for e in by.values() if e['kind']=='game' and re.search(r'\((?:19|20)\d{2}.*?game',e.get('provenance',{}).get('article_title',''))}
source=json.loads((m.HERE/'museum-video-selections.json').read_text(encoding='utf8'))['entries'];results=[]
for row in source:
 entry=by.get(row['entry_id']);errors=[]
 if not entry:results.append({'entry_id':row['entry_id'],'errors':['No canonical exhibit identity']});continue
 v=row['videos'][0];allowed,reason=m.relevant(entry,v)
 if not allowed:errors.append(reason)
 vid=v['youtube_id'];verify=v.get('verification',{})
 if not re.fullmatch('[A-Za-z0-9_-]{11}',vid) or parse_qs(urlparse(v['url']).query).get('v',[''])[0]!=vid:errors.append('Watch URL and video ID disagree')
 if verify.get('native_codec_metadata_verified') is not True or verify.get('avc_format_count',0)<1 or verify.get('aac_format_count',0)<1:errors.append('Native AVC/AAC pair has no verified receipt')
 poster=v.get('poster_url','')
 if poster:
  matches=[i for i in row.get('images',[]) if i['url']==poster]
  if not matches:errors.append('Offline poster image record missing')
  else:
   image=matches[0];path=m.ROOT/image.get('recovery_local_source','missing')
   try:
    with Image.open(path) as im:im.load();w,h=im.size
    if w<600 or max(w,h)<600:errors.append('Poster source is below native threshold')
   except Exception as error:errors.append('Poster original cannot be decoded: '+str(error))
 if not v.get('creator') or not v.get('title'):errors.append('Original uploader/title identity missing')
 results.append({'entry_id':entry['id'],'title':entry['title'],'year':entry['year'],'kind':entry['kind'],'video_id':vid,'video_title':v['title'],'awaiting_article_admission':entry['id'] not in assembled_ids,'errors':errors})
report={'checked_utc':datetime.now(timezone.utc).isoformat(),'rows_checked':len(results),'pass':sum(not r['errors'] for r in results),'held':sum(bool(r['errors']) for r in results),'kind_coverage':dict(Counter(r['kind'] for r in results if not r['errors'])),'rows':results,'scope':'Automated exact-edition/source-context gates, AVC/AAC native metadata receipts, decoded original posters; PS5 playback is not asserted.'}
passing={(r['entry_id'],r['video_id']) for r in results if not r['errors']}
reviewed=[r for r in source if (r['entry_id'],r['videos'][0]['youtube_id']) in passing]
for row in reviewed:
 entry=by[row['entry_id']];v=row['videos'][0]
 if entry['kind']=='person':
  text=v['title'].lower();kind='interview and conversation' if any(t in text for t in ['interview','q&a','conversation']) else 'design lecture and public talk' if any(t in text for t in ['lecture','talk','summit']) else 'archive demonstration of the creator?s work' if any(t in text for t in ['gameplay','longplay','playthrough','space hamburger']) else 'creator profile and historical film'
  v['caption']='Original recording published by '+v['creator']+'. '+entry['title']+' ('+str(entry['year'])+'): '+kind+'.'
m.save(m.HERE/'museum-video-reviewed-checkpoint.json',{'schema_version':1,'entries':reviewed,'checked_utc':report['checked_utc'],'verification_scope':report['scope']})
m.save(m.CACHE/'semantic-publication-audit.json',report);print('SEMANTIC',report['pass'],'pass',report['held'],'held',flush=True)
