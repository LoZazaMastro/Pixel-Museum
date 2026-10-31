"""Rebind an unchanged baked font superset only after actual glyph checks.

Run the full baker instead if new display characters or shaped phrases are
missing. This command never edits a font or substitutes source-language text.
"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
from font_display_text import ROOT,collect,complex_runs,script_class

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
output=args.output.resolve()
assert output.is_relative_to((ROOT/'build/research').resolve())
audit=runpy.run_path(str(ROOT/'tools/audit-font-coverage.py'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fonts=ROOT/'assets/fonts'
paths=sorted(fonts.glob('*.huifont'))
before={p.name:sha(p) for p in paths}
points,records,sources=collect()
ordinary={p for p in points if script_class(p)=='ordinary_glyph'}
fallback=audit['glyphs'](fonts/'unicode-fallback.huifont')|audit['glyphs'](fonts/'cjk-subset.huifont')
for face in ('inter-regular','inter-semibold','montserrat-medium','dejavu-sans-mono'):
    missing=ordinary-(audit['glyphs'](fonts/(face+'.huifont'))|fallback)
    assert not missing, f'{face}: missing glyphs {sorted(missing)}; run tools/bake-fonts.sh'
phrases=complex_runs(records)
available=audit['shaped_runs'](fonts/'cjk-subset.huifont')
assert set(phrases)<=available, 'New complex phrase: run the genuine shaping/baking pipeline'
assert collect()[2]==sources, 'Display sources changed during inventory collection; retry on a stable snapshot'
manifest_path=fonts/'cjk-source.json'
old_bytes=manifest_path.read_bytes()
manifest=json.loads(old_bytes)
manifest.setdefault('baked_display_source_sha256',manifest.get('display_source_sha256',{}))
manifest.setdefault('baked_glyph_request_sha256',manifest.get('glyph_request_sha256'))
requested=''.join(chr(p) for p in sorted(points)).encode('utf8')
manifest['display_source_sha256']=sources
manifest['glyph_request_sha256']=hashlib.sha256(requested).hexdigest()
manifest['revalidated_display_codepoint_count']=len(points)
manifest['inventory_revalidation']={
    'method':'Existing actual font glyphs and genuine shaped-run mappings cover the complete current display inventory. No font bytes changed.',
    'receipt':output.relative_to(ROOT.resolve()).as_posix(),
    'ordinary_codepoints':len(ordinary),'static_complex_phrases':len(phrases),
    'font_sha256':before}
assert before=={p.name:sha(p) for p in paths}, 'Font changed during validation'
temporary=manifest_path.with_suffix('.json.tmp')
temporary.write_bytes((json.dumps(manifest,indent=2)+'\n').encode('utf8'))
temporary.replace(manifest_path)
(ROOT/'build/catalog-codepoints.txt').write_bytes(requested)
report=dict(status='PASS_UNCHANGED_ACTUAL_FONT_SUPERSET_REBOUND_TO_CURRENT_DISPLAY',
    previous_manifest_sha256=hashlib.sha256(old_bytes).hexdigest(),
    current_manifest_sha256=sha(manifest_path),display_source_sha256=sources,
    glyph_request_sha256=manifest['glyph_request_sha256'],
    ordinary_codepoints=len(ordinary),static_complex_phrases=len(phrases),
    font_sha256=before,font_bytes_changed=False,source_text_changed=False,
    limits=['Does not add missing glyphs or fabricate shaping. Full baking is required if any check fails.',
        'Actual rendering was verified separately; this is a current-inventory rebinding, not a new visual test.'])
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(status=report['status'],output=str(output))))
