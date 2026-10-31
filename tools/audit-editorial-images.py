"""Report actual card illustration and offline image coverage."""
from pathlib import Path
from collections import Counter
import json
ROOT=Path(__file__).resolve().parents[1]
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
manifest=json.loads((ROOT/'assets/images/manifest.json').read_text(encoding='utf8'))
rows=[];urls=set();missing=[];counts=Counter()
for entry in catalog['entries']:
 images=entry.get('images',[]);body=entry.get('body',[])
 illustrated=set()
 for n,image in enumerate(images):
  index=image.get('story_paragraph',n)
  if isinstance(index,int) and 0<=index<len(body):illustrated.add(index)
 all_images=list(images)
 for feature in entry.get('editorial_features',[]):all_images.extend(feature.get('images',[]))
 for image in all_images:
  url=image.get('url')
  if not url:continue
  urls.add(url)
  if not all(manifest.get(field,{}).get(url) and (ROOT/manifest[field][url]).is_file() for field in ['images','previews']):missing.append({'entry_id':entry['id'],'url':url})
 counts['entries']+=1;counts['narrative_cards']+=len(body);counts['narrative_cards_with_image']+=len(illustrated)
 counts['entries_with_cover']+=bool(images)
 if len(body)>len(illustrated):rows.append({'id':entry['id'],'title':entry['title'],'year':entry['year'],'body_cards':len(body),'illustrated_cards':len(illustrated),'unillustrated_indices':[i for i in range(len(body)) if i not in illustrated]})
report={'counts':dict(counts),'unique_image_urls':len(urls),'missing_offline_images':missing,'illustration_percent':round(100*counts['narrative_cards_with_image']/max(1,counts['narrative_cards']),2),'entries_needing_more_illustrations':rows}
(ROOT/'content/editorial-image-coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='entries_needing_more_illustrations' and k!='missing_offline_images'}|{'missing_offline_images':len(missing)},indent=2))
