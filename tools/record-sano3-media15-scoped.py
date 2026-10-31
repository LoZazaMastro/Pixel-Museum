"""Record scoped authoring QA when font/native bytes remain unchanged."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/research/sano3-media15-font-scoped'
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        while b := f.read(1 << 20): h.update(b)
    return h.hexdigest()
def rec(p):
    p = Path(p)
    if not p.is_absolute(): p = ROOT / p
    return {'path':p.relative_to(ROOT).as_posix(), 'bytes':p.stat().st_size, 'sha256':sha(p)}
def read(p): return json.loads((ROOT / p).read_text(encoding='utf8'))

master='content/catalog.json'
runtime='build/runtime-preview/content/catalog.json'
assert sha(ROOT/master)=='1878a7c790f864a4d28b2ca9f2af649923a99c5cf52acbf9c2f57776adb3aec5'
assert sha(ROOT/runtime)=='60db30463f7bac87be323f2c1e2b1d92bf393b283d342cfded0bf37828d66362'
a,b=read(master),read(runtime)
assert len(a['entries'])==len(b['entries'])==1395
assert a['entry_aliases']==b['entry_aliases'] and len(a['entry_aliases'])==23
assert sum(len(e.get('models',[])) for e in a['entries'])==30
proof=read('build/research/sano3-media15-source71-final-proof.json')
for catalog in (a,b):
    index={e['id']:e for e in catalog['entries']}
    for row in proof['body_records']:
        body=index[row['entry_id']]['body'][row['index']]
        assert hashlib.sha256(body.encode('utf8')).hexdigest()==row['body_sha256']
assert len(proof['body_records'])==181
inv=read('build/research/sano3-media15-font-scoped/font-inventory-revalidation.json')
assert inv['revalidation']['font_bytes_unchanged'] and not inv['native_recompile_needed']
for path,v in inv['font_assets'].items(): assert sha(ROOT/path)==v['sha256']
assert sha(ROOT/'build/eboot.elf')=='71aa22952d2f2155c53e90023040270f9bac87e89ca19ec9b37a4639f67046af'
recovery=ROOT/'build/research/native-final16-media22-recoverable'
assert sha(recovery/'manifest.json')=='5709e72cac22c20b8255e6fc1427184716dce0f0f79cfa963d4267dd571ed3af'
backup=json.loads((recovery/'manifest.json').read_text(encoding='utf8'))
for path,v in backup['files'].items(): assert sha(recovery/'files'/path)==v['sha256']
assert len(backup['files'])==63
profile=ROOT/'build/research/story-text-profile/unillustrated-scenes-current.json'
g=json.loads(profile.read_text(encoding='utf8'))
assert g['count']==407 and g['catalog_entries']==1395 and g['explicit_catalog_override']
assert g['catalog']==runtime and len(g['scoped_composed_narrative_checks'])==31
assert all(r['exact_association_pass'] for r in g['current_explicit_media_probes'])
assert g['current_cover_only_probe']['all_source_paragraphs_in_order'] and not g['current_cover_only_probe']['cover_reused']
assert g['current_cover_sha_alias_probe']['distinct_explicit_p0_image_preserved']
shutil.copyfile(profile,OUT/'actual-profile-frozen.json')
mapping=read('build/research/sano3-media15-font-scoped/actual-new-media15-associations.json')
assert mapping['status']=='PASS_ALL15_ACTUAL_COMPOSED'
log=(OUT/'sano-actual-4k.log').read_text(encoding='utf8')
assert sum(f'story-workbook-01-19-nobuyoshi-sano-{i}-4k.png 3840x2160 GL=0x0' in log for i in range(4))==4
screens=[rec(f'build/previews/story-workbook-01-19-nobuyoshi-sano-{i}-4k.png') for i in range(4)]
report={
 'status':'PASS_SCOPED_SOURCE71_SANO3_MEDIA15_UNCHANGED_FONT_NATIVE',
 'master':rec(master),'runtime':rec(runtime),'entry_count':1395,'alias_count':23,'attached_models':30,
 'editorial_coherence':rec('build/research/sano3-media15-source71-final-proof.json'),
 'actual_body_records_verified':181,
 'font_inventory':rec(OUT/'font-inventory-revalidation.json'),
 'font_bake_performed':False,'native_compile_performed':False,
 'reason':'Exact ordinary codepoints, shaped phrases/run geometry, all six baked font files and production code/native bytes remain unchanged; fresh display-source fingerprints are recorded without claiming a new bake.',
 'native_unchanged':rec('build/eboot.elf'),
 'inherited_full_regressions':rec('build/research/final16-media22-font-native/verification.json'),
 'previous_group_recovery':dict(rec(recovery/'manifest.json'),verified_original_files=63),
 'actual_scene_profile':dict(rec(OUT/'actual-profile-frozen.json'),unillustrated_composed_narrative_scenes=407,scoped_actual_narrative_cards=31),
 'actual_new_media_associations':rec(OUT/'actual-new-media15-associations.json'),
 'actual_Sano_4K':{'cards':4,'source_paragraphs':4,'narrative_photos':3,'GL_errors':0,'images':screens,'individual_visual_review':[0,1,2], 'full_text_source_order_and_scroll_endpoints':'PASS in scoped composer checks'},
 'logs':{p.name:rec(p) for p in OUT.glob('*.log')},
 'production_changes_this_scope':False,'physical_PS5_test_or_transfer':False,
 'limits':['Measured composed gaps are 407; previous419 and15newimage records must not be combined by subtraction.',
 'All15new images occur in actual composed cards, while source paragraphs may be grouped into a single card.',
 'Inherited full Unicode/MK348/alias/display regressions were not redundantly rerun; current scoped checks are separately recorded.',
 'Host GL validation does not establish physical PS5 frame rate or loading latency.']}
target=OUT/'verification.json'
target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(target.relative_to(ROOT),sha(target))
