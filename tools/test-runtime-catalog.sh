#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/host-env.sh"
cd "$root"
python3 - <<'PY'
import copy,json,runpy
from pathlib import Path
m=runpy.run_path('tools/runtime-catalog.py');source=Path('content/catalog.json').read_bytes();c=json.loads(source)
before=copy.deepcopy(c);r=m['project'](c)
assert c==before,'Projection mutated authoring data'
assert [e['id'] for e in r['entries']]==[e['id'] for e in c['entries']]
for old,new in zip(c['entries'],r['entries']):
    assert old['body']==new['body'] and old.get('story_headings')==new.get('story_headings')
    assert old.get('sources')==new.get('sources') and old.get('models')==new.get('models')
    assert len(old['images'])==len(new['images'])
    for a,b in zip(old['images'],new['images']):
        for key in m['IMAGE_FIELDS']:
            assert (key in a)==(key in b) and a.get(key)==b.get(key),(old['id'],key)
    assert len(old.get('editorial_features',[]))==len(new.get('editorial_features',[]))
    for a,b in zip(old.get('editorial_features',[]),new.get('editorial_features',[])):
        assert a['body']==b['body'] and a['sources']==b['sources']
    for originals,projected,fields in ((old.get('videos',[]),new.get('videos',[]),m['VIDEO_FIELDS']),
            (old.get('soundtrack',{}).get('tracks',[]),new.get('soundtrack',{}).get('tracks',[]),m['SOUNDTRACK_TRACK_FIELDS'])):
        assert len(originals)==len(projected)
        for a,b in zip(originals,projected):
            for key in fields:
                assert (key in a)==(key in b) and a.get(key)==b.get(key),(old['id'],key)
Path('build/runtime-catalog.json').write_bytes(m['encoded'](r))
Path('build/runtime-authoring-compact.json').write_bytes(m['encoded'](c))
receipt=m['receipt'](c,r,source)
assert receipt['runtime_bytes']<receipt['compact_authoring_bytes'] and receipt['runtime_bytes']<=16<<20
Path('build/runtime-catalog-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
PY
clang++-18 -std=c++20 -O2 -Wall -Wextra -Werror -fno-exceptions -fno-rtti -Isrc \
 tests/runtime_catalog_test.cpp src/museum/catalog.cpp src/core/save_file.cpp -o build/runtime-catalog-test
build/runtime-catalog-test build/runtime-authoring-compact.json build/runtime-catalog.json
