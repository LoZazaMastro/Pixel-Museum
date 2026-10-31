"""Read-only checks for the fully assembled museum catalogue."""
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
import json,re,unicodedata
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def norm(text):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().lower())
entries=read(ROOT/'content/catalog.json')['entries'];by_id={e['id']:e for e in entries}
aliases=read(ROOT/'content/museum-revision-audit.json').get('aliases',{})
def resolve(identifier):
    visited=set()
    while identifier not in by_id and identifier in aliases and identifier not in visited:visited.add(identifier);identifier=aliases[identifier]
    return identifier if identifier in by_id else None
failures=[];module_receipts={}
for filename in ['major-release-additions.json','museum-series-splits.json']:
    module=read(HERE/filename)['entries'];direct=0;coalesced=[];missing=[];missing_images=[]
    for source in module:
        target=resolve(source['id'])
        if not target:missing.append([source['id'],source['title']]);continue
        if target==source['id']:direct+=1
        else:coalesced.append([source['id'],target])
        actual={i['url'] for i in by_id[target].get('images',[])}
        absent=[i['url'] for i in source.get('images',[]) if i['url'] not in actual]
        if absent:missing_images.append({'id':source['id'],'target':target,'count':len(absent)})
    module_receipts[filename]={'source_count':len(module),'direct':direct,'canonical_merges':coalesced,'missing':missing,'missing_source_images':missing_images}
    if missing:failures.append([filename,'Source entries have no runtime destination',missing])
    if missing_images:failures.append([filename,'Verified source images not integrated',missing_images])
awards=[]
for year in range(2014,2026):
    eid='the-game-awards-'+str(year);entry=by_id.get(eid)
    if not entry:failures.append([eid,'Missing annual entry']);continue
    preferred=entry.get('preferred_image',0);image=entry['images'][preferred]
    valid=len(entry.get('body',[]))==14 and len(entry.get('story_headings',[]))==14 and str(year) in image.get('title','')
    awards.append({'year':year,'body':len(entry.get('body',[])),'headings':len(entry.get('story_headings',[])),'preferred':preferred,'preferred_title':image.get('title'),'valid':valid})
    if not valid:failures.append([eid,'Annual narrative or preferred artwork mismatch'])
switches=[{'id':e['id'],'title':e['title'],'year':e['year'],'date':e['date'],'models':len(e.get('models',[]))} for e in entries if e['title'] in ['Nintendo Switch','Nintendo Switch 2']]
if len(switches)!=2:failures.append(['Switch','Expected exactly one original and one successor'])
groups=defaultdict(list)
for entry in entries:
    if entry['kind'] in ['game','console','hardware']:groups[norm(entry['title'])].append(entry)
near_duplicates=[]
for title,items in groups.items():
    if title=='dnd':continue # Different historical programs, not regional releases.
    for first in items:
        for second in items:
            if first['id']>=second['id'] or abs(first['year']-second['year'])>3:continue
            near_duplicates.append([[first['id'],first['year']],[second['id'],second['year']]])
if near_duplicates:failures.append(['Chronology','Same-title stops within three years need original/region/announcement identity review',near_duplicates])
report={'checked_utc':datetime.now(timezone.utc).isoformat(),'catalog_entries':len(entries),'modules':module_receipts,'annual_awards':awards,'switch_hardware':switches,
    'nearby_same_title_identities':near_duplicates,'grouped_source_ids_still_present':[eid for eid in ['wikipedia-65079310','wikipedia-77040235','wikipedia-32470667'] if eid in by_id],
    'failures':failures,'scope_notice':'The378-title major-release checklist is explicit editorial scope; this does not claim to enumerate every AAA game.'}
out=ROOT/'build/research/catalog-final-audit.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'catalog_entries':len(entries),'modules':{k:{kk:vv for kk,vv in v.items() if kk!='missing_source_images'} for k,v in module_receipts.items()},'failure_count':len(failures),'failures':failures},ensure_ascii=False,indent=2))
raise SystemExit(bool(failures))
