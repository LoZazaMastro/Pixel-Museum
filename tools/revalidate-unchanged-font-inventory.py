"""Refresh catalogue provenance only when the exact baked inventory is unchanged.

This is not a font bake. New codepoints or complex phrases explicitly refuse
this path, preserving the previous coherent snapshot for a real fresh bake.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import json
from font_display_text import ROOT,collect,complex_runs

args=argparse.ArgumentParser()
args.add_argument('--expected-master-sha256',required=True)
args.add_argument('--expected-runtime-sha256',required=True)
args.add_argument('--receipt-dir',required=True)
options=args.parse_args()
out=ROOT/options.receipt_dir
assert out.resolve().is_relative_to((ROOT/'build/research').resolve())
out.mkdir(parents=True,exist_ok=True)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def atomic_json(path,value):
    pending=path.with_suffix(path.suffix+'.revalidated')
    pending.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    pending.replace(path)
master=ROOT/'content/catalog.json';runtime=ROOT/'build/runtime-preview/content/catalog.json'
assert sha(master)==options.expected_master_sha256 and sha(runtime)==options.expected_runtime_sha256
manifest_path=ROOT/'assets/fonts/cjk-source.json'
runs_path=ROOT/'build/research/offline-script-shaping/script-runs.json'
audit_path=ROOT/'build/research/font-coverage.json'
manifest=json.loads(manifest_path.read_text(encoding='utf8'))
runs=json.loads(runs_path.read_text(encoding='utf8'))
baseline=json.loads(audit_path.read_text(encoding='utf8'))
points,records,sources=collect()
request=hashlib.sha256(''.join(chr(c) for c in sorted(points)).encode()).hexdigest()
assert request==manifest['glyph_request_sha256'],'Glyph inventory changed: run the real font bake'
assert request==hashlib.sha256((ROOT/'build/catalog-codepoints.txt').read_bytes()).hexdigest()
assert complex_runs(records)==baseline['static_complex_runs_required'],'Complex phrases changed: run the real shaped-font bake'
assert baseline['ordinary_glyph_status']=='pass' and not baseline['stale_subset_inputs']
assert not baseline['complex_shaping_unresolved'] and not baseline['static_complex_runs_unsupported']
assert manifest['display_source_sha256']==runs['source_sha256']==baseline['input_source_sha256']
font_paths=sorted((ROOT/'assets/fonts').glob('*.huifont'))
fonts={p.relative_to(ROOT).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in font_paths}
for p in font_paths:
    assert sha(ROOT/'build/runtime-preview/assets/fonts'/p.name)==sha(p),'Runtime font differs from verified baked asset'
old_receipt=json.loads((ROOT/'build/research/offline-script-shaping/verification.json').read_text(encoding='utf8'))
for name,value in fonts.items():assert old_receipt['files'][name]==value,'Font bytes differ from previous verified snapshot'
snapshots=out/'prior-metadata';snapshots.mkdir(exist_ok=True)
for name,path in [('cjk-source.json',manifest_path),('script-runs.json',runs_path),('font-coverage.json',audit_path)]:
    target=snapshots/name
    assert not target.exists(),'Use a fresh receipt directory; previous provenance is immutable'
    target.write_bytes(path.read_bytes())
run_digest=hashlib.sha256(canonical(runs['runs'])).hexdigest()
note={'action':'unchanged_glyph_and_shaped_run_inventory_revalidated_without_rebake',
      'checked_utc':datetime.now(timezone.utc).isoformat(),'previous_display_source_sha256':manifest['display_source_sha256'],
      'current_display_source_sha256':sources,'glyph_request_sha256':request,'run_geometry_sha256':run_digest,
      'font_bytes_unchanged':True,'previous_bake_metadata':str(snapshots.relative_to(ROOT)).replace('\\','/')}
manifest.setdefault('original_bake_display_source_sha256',manifest['display_source_sha256'])
runs.setdefault('original_bake_source_sha256',runs['source_sha256'])
manifest['display_source_sha256']=sources;runs['source_sha256']=sources
manifest['inventory_revalidation']=note;runs['inventory_revalidation']=note
assert hashlib.sha256(canonical(runs['runs'])).hexdigest()==run_digest
assert sha(master)==options.expected_master_sha256 and sha(runtime)==options.expected_runtime_sha256
atomic_json(manifest_path,manifest);atomic_json(runs_path,runs)
for name,value in fonts.items():assert sha(ROOT/name)==value['sha256']
report={'status':'PASS_unchanged_font_inventory_provenance_refreshed_NO_REBAKE',
        'master':{'sha256':sha(master),'bytes':master.stat().st_size},
        'runtime':{'sha256':sha(runtime),'bytes':runtime.stat().st_size},
        'font_assets':fonts,'ordinary_codepoints':len(baseline['ordinary_codepoints']),
        'complex_phrases':len(baseline['static_complex_runs_required']),'shaped_runs':len(runs['runs']),
        'revalidation':note,'native_recompile_needed':False,'physical_PS5_test_or_transfer':False}
atomic_json(out/'font-inventory-revalidation.json',report)
print('PASS unchanged font bytes/inventory; catalogue provenance revalidated without bake or native compilation.')
