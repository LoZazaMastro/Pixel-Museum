#!/usr/bin/env python3
"""Select the complete illustrated museum, with explicit unresolved artefact holds."""
from pathlib import Path
import hashlib,json
from hardware_presentation import photograph_only_console_ids
ROOT=Path(__file__).resolve().parents[1]
photo_only_ids=photograph_only_console_ids(ROOT)
catalogfile=ROOT/'content/catalog.json';catalog=json.loads(catalogfile.read_text(encoding='utf8'));accepted=[];held=[]
for entry in catalog['entries']:
 reason=''
 if entry['kind']=='console' and not entry.get('models') and entry['id'] not in photo_only_ids:reason='Console 3D asset not available yet'
 elif not entry.get('images'):reason='No identified image acquired yet'
 if reason:held.append({'id':entry['id'],'title':entry['title'],'year':entry['year'],'reason':reason})
 else:accepted.append(entry['id'])
selector={'schema_version':1,'edition':'Complete illustrated museum development build','initial_id':'game-boy','source_catalog_sha256':hashlib.sha256(catalogfile.read_bytes()).hexdigest(),'entry_ids':accepted,'held':held}
(ROOT/'content/full-museum-selector.json').write_text(json.dumps(selector,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'included':len(accepted),'held':len(held),'missing_3d':[e for e in held if e['reason'].startswith('Console')],'missing_images':sum(e['reason'].startswith('No identified') for e in held)},indent=2))
