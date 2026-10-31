"""Exercise shipped projections, never old Playhub overlays or authoring JSON."""
from pathlib import Path
import hashlib,json,runpy,shutil
root=Path(__file__).resolve().parents[2]
output=root/'build/localization-runtime'
(output/'content/locales').mkdir(parents=True,exist_ok=True)
runtime=runpy.run_path(str(root/'tools/runtime-catalog.py'))
localized=runpy.run_path(str(root/'tools/project-reviewed-locales.py'))
catalogs=[json.loads((root/'content'/p).read_text(encoding='utf8'))for p in ('catalog.json','human-history.json')]
catalog_hash=hashlib.sha256((root/'content/catalog.json').read_bytes()).hexdigest()
projection=runtime['encoded'](runtime['project'](catalogs[0],catalog_hash))
assert len(projection)<=16<<20
(output/'content/catalog.json').write_bytes(projection)
for language in ('en','it','es','fr','de'):
    projected={'locale':language,'entries':{}}
    if language!='en':
        original=json.loads((root/'content/museum-locales'/f'{language}.json').read_text(encoding='utf8'))
        projected,audit=localized['project'](original,catalogs,language)
        assert not audit['stale'] and not audit['not_in_package']
    data=runtime['encoded'](projected)
    assert len(data)<=16<<20
    (output/'content/locales'/f'{language}.json').write_bytes(data)
shutil.copytree(root/'content/ui-locales',output/'content/ui-locales',dirs_exist_ok=True)
print(f'Actual runtime fixture: {len(catalogs[0]["entries"])} entries, {len(projection)} bytes, source-bound reviewed locales; {hashlib.sha256(projection).hexdigest()}')
