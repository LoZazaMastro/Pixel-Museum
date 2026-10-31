"""Read-only preferred-cover identity audit; do not silently replace artefacts."""
from pathlib import Path
from urllib.parse import urlparse,parse_qs,unquote
from datetime import datetime,timezone
import json,re,unicodedata
ROOT=Path(__file__).resolve().parents[1]
def norm(text):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().lower())
def wiki(url):
    if not isinstance(url,str) or 'wikipedia.org' not in url:return ''
    part=urlparse(url);name=parse_qs(part.query).get('title',[''])[0]
    if not name and '/wiki/' in part.path:name=part.path.split('/wiki/',1)[1]
    return unquote(name).replace('_',' ').split('#')[0]
platform_floor={'nintendogameboycolor':1998,'nintendogameboyadvance':2001,'nintendogameboy':1989,'nintendods':2004,'nintendo3ds':2011,'nintendogamecube':2001,'nintendowii':2006,'nintendoswitch':2017,'sonicsupergam':1970,'segagenesis':1988,'segamegadrive':1988,'segamastersystem':1985,'segasaturn':1994,'segadreamcast':1998,'sonyplaystation':1994,'sonyplaystation2':2000,'sonyplaystation3':2006,'dragon32':1982,'dragon32and64':1982,'colecovision':1982,'atari2600':1977,'supernintendoentertainmentsystem':1990,'nintendoentertainmentsystem':1983}
entries=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf-8'))['entries'];records=[];checked=0
for entry in entries:
    photos=entry.get('images',[])
    if not photos:continue
    image=photos[min(entry.get('preferred_image',0),len(photos)-1)];evidence=image.get('identity_evidence',{})
    if not evidence:continue
    checked+=1;reasons=[];level='review';year=entry['year'];raw=evidence.get('year','') or ''
    match=re.match(r'(\d{4})',str(raw));actual=int(match.group(1)) if match else None
    platform=evidence.get('platform','');floor=platform_floor.get(norm(platform))
    if actual is None:reasons.append('Archive release year is unknown; must not score as an exact-year match')
    elif abs(actual-year)>3:reasons.append('Archive release year differs by more than three years');level='high'
    if floor and floor>year:reasons.append('Archive platform did not exist in the exhibit release year');level='high'
    expected={wiki(s.get('url','')) for s in entry.get('sources',[])};expected.discard('')
    for field in ['article_url','source_url']:
        value=wiki(entry.get('attribution',{}).get(field,''))
        if value:expected.add(value)
    candidate=wiki(evidence.get('wikipedia_url',''))
    if candidate and expected and norm(candidate) not in {norm(x) for x in expected}:
        reasons.append('Archive Wikipedia subject differs from every exhibit Wikipedia source; canonical redirect/edition review required')
    if reasons:records.append({'entry_id':entry['id'],'title':entry['title'],'exhibit_year':year,'severity':level,'reasons':reasons,
        'preferred_image_url':image['url'],'expected_wikipedia_subjects':sorted(expected),'archive_identity':evidence})
out=ROOT/'build/research/cover-identity-collisions.json';out.write_text(json.dumps({'checked_utc':datetime.now(timezone.utc).isoformat(),'catalog_entries':len(entries),'preferred_images_with_archival_identity':checked,
    'high_priority':[r for r in records if r['severity']=='high'],'review':[r for r in records if r['severity']!='high'],
    'notice':'Read-only candidate audit. Different article names may be legitimate redirects; do not delete or replace them solely from this list.'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checked':checked,'high_priority':sum(r['severity']=='high' for r in records),'review':sum(r['severity']!='high' for r in records),'high_ids':[(r['entry_id'],r['title'],r['archive_identity'].get('name'),r['archive_identity'].get('year'),r['archive_identity'].get('platform')) for r in records if r['severity']=='high']},ensure_ascii=False,indent=2))
