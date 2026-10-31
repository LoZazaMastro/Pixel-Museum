"""Validate the major-game module and its locally retained original masters."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
CACHE=ROOT/'build/research/image-quality'
entries=json.loads((HERE/'major-release-additions.json').read_text(encoding='utf-8'))['entries']
seen=set();words=images=exact=0;failures=[]
for entry in entries:
    eid=entry['id'];assert eid not in seen;seen.add(eid)
    word_count=len(re.findall(r'\S+',' '.join(entry['body'])))
    if word_count<120:failures.append([eid,'Less than 120 substantive source words'])
    words+=word_count
    attribution=entry.get('attribution',{})
    if not attribution.get('revision_id') or attribution.get('license')!='CC BY-SA 4.0' or not attribution.get('contributors_url'):
        failures.append([eid,'Incomplete Wikipedia attribution'])
    exact+=entry['date'].get('precision')=='day'
    for image in entry['images']:
        images+=1;url=image['url'];key=hashlib.sha256(url.encode()).hexdigest()[:16]
        files=list(CACHE.glob(key+'.*'))
        if not files:failures.append([eid,'Original not cached',url]);continue
        source=files[0]
        try:
            with Image.open(source) as master:master.load();w,h=master.size
            if (w,h)!=(image.get('width'),image.get('height')):failures.append([eid,'Native dimensions differ',url,[w,h]])
            expected=image.get('verification',{}).get('sha256')
            if expected and hashlib.sha256(source.read_bytes()).hexdigest()!=expected:failures.append([eid,'Original digest differs',url])
            if image.get('cover_role') and (max(w,h)<600 or min(w,h)<350):failures.append([eid,'Cover below native scan quality bound',url])
        except Exception as error:failures.append([eid,'Master decode failed',str(error)])
audit=json.loads((HERE/'major-release-coverage-audit.json').read_text(encoding='utf-8'))
receipt={'checked_utc':datetime.now(timezone.utc).isoformat(),'entries':len(entries),'words':words,'images':images,
    'covers':sum(bool(e['images']) for e in entries),'exact_dates':exact,'curated_checklist_titles':audit['checklist_titles'],
    'remaining_curated_checklist_gaps':audit['remaining_checklist_gaps'],'failures':failures}
out=ROOT/'build/research/major-releases/validation.json';out.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
raise SystemExit(bool(failures))
