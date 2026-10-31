"""Measure additive acquisition against an immutable catalogue snapshot."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json
from publication_readiness import evaluate

ROOT=Path(__file__).resolve().parents[2]
FILES=('steam-media-additions.json','publisher-media-additions.json','media-wikidata-steam-additions.json')

def main():
    raw=(ROOT/'content/catalog.json').read_bytes()
    catalog=json.loads(raw);entries=copy.deepcopy(catalog['entries'])
    lookup={e['id']:e for e in entries};before=evaluate(entries)
    inputs=[];unknown=[];images_checked=0;urls=set()
    for filename in FILES:
        path=ROOT/'content/expansion'/filename;body=path.read_bytes();data=json.loads(body)
        inputs.append({'file':filename,'sha256':hashlib.sha256(body).hexdigest(),'records':len(data['entries'])})
        for row in data['entries']:
            entry=lookup.get(row['entry_id'])
            if not entry:unknown.append(row['entry_id']);continue
            seen={i['url'] for i in entry.get('images',[])}
            for image in row.get('images',[]):
                assert max(image['width'],image['height'])>=1600,(row['entry_id'],image['url'])
                assert image.get('quality_verified') and image.get('source_page') and image.get('credit')
                assert image.get('verification',{}).get('sha256'),(row['entry_id'],'Missing image hash')
                images_checked+=1;urls.add(image['url'])
                if image['url'] not in seen:entry.setdefault('images',[]).append(image);seen.add(image['url'])
    assert not unknown,unknown
    after=evaluate(entries);old={r['entry_id']:r for r in before['entries']}
    added=[{'entry_id':r['entry_id'],'title':r['title'],'year':r['year'],'hd_images':r['hd_images']}
           for r in after['entries'] if r['hd_images'] and not old[r['entry_id']]['hd_images']]
    report={'schema_version':1,'checked_utc':datetime.now(timezone.utc).isoformat(),
        'baseline_catalog_sha256':hashlib.sha256(raw).hexdigest(),
        'master_catalog_modified':False,'inputs':inputs,
        'distinct_articles':after['distinct_runtime_articles'],
        'before_hd_cover_articles':before['articles_with_verified_hd_cover'],
        'after_additive_hd_cover_articles':after['articles_with_verified_hd_cover'],
        'new_distinct_covered_articles':len(added),'newly_covered':added,
        'verified_image_records_checked':images_checked,'distinct_image_urls':len(urls),
        'editorial_signoffs':0,
        'limitations':['This is an acquisition receipt, not editorial signoff or a rights clearance.',
            'Publisher copyright and edition context remain explicit. Unmapped screenshots are gallery media, not invented paragraph illustrations.',
            'Original Breakout HD cover remains unresolved; correct Strong photo public endpoint is capped at1200px. No enlargement or modern game substitution.',
            'DDR photograph is dated2011 and illustrates continued arcade play, not1998 launch hardware.'],
        'unknown_ids':unknown}
    path=ROOT/'content/expansion/media-batch-02-receipt.json'
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='newly_covered'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
