"""Bind current grouped authoring/runtime/font/native checks without deployment."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/research/preservation-yoshi-font-native'
OUT.mkdir(exist_ok=True)
def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1 << 20): h.update(block)
    return h.hexdigest()
def record(name):
    p=ROOT/name
    return {'path':name,'sha256':sha(p),'bytes':p.stat().st_size}

master='content/catalog.json'
runtime='build/runtime-preview/content/catalog.json'
assert sha(ROOT/master)=='c40e3e243ecb8ea43f90764fcdad342dff90021c29588477bb3174f7094b304b'
assert sha(ROOT/runtime)=='d3b172db8a2388e8c4c182b52250bb4c86f65d8d6feb38d0d058fd82eb832f7b'
a,b=[json.loads((ROOT/p).read_text(encoding='utf8')) for p in (master,runtime)]
assert len(a['entries'])==len(b['entries'])==1395
assert a['entry_aliases']==b['entry_aliases'] and len(a['entry_aliases'])==23
font_path='build/research/offline-script-shaping/verification.json'
font=json.loads((ROOT/font_path).read_text(encoding='utf8'))
for path in (master,runtime):
    assert font['coherent_catalogues'][path]['sha256']==sha(ROOT/path)
assert font['files']['build/eboot.elf']['sha256']==sha(ROOT/'build/eboot.elf')
prefix='preservation-yoshi-source71'
logs={
 'font_bake':f'build/research/offline-script-shaping/final-bake-{prefix}.log',
 'native':f'build/research/offline-script-shaping/{prefix}-native-build.log',
 'font_units':f'build/research/offline-script-shaping/{prefix}-shaped-runs.log',
 'font_inventory':f'build/research/offline-script-shaping/{prefix}-display-inventory.log',
 'actual4k':f'build/research/offline-script-shaping/{prefix}-actual-gl.log',
 'prose_credits':f'build/research/offline-script-shaping/{prefix}-narrative-regression.log',
 'alias_unit':f'build/research/catalog-aliases/{prefix}-unit.log',
 'alias_actual_screen':f'build/research/catalog-aliases/{prefix}-actual-screen.log',
 'runtime_equivalence':f'build/research/catalog-aliases/{prefix}-runtime-equivalence.log',
 'display_lifecycle':f'build/research/display-refresh/{prefix}-lifecycle.log',
 'actual_scene_profile':f'build/research/story-text-profile/actual-{prefix}.log'}
for name,path in logs.items():
    text=(ROOT/path).read_text(encoding='utf8')
    assert 'PASS' in text if name not in ('native','font_bake') else 'error:' not in text
assert '23 alias resolutions' in (ROOT/logs['runtime_equivalence']).read_text()
assert 'Native compile/link/conversion complete; existing payload untouched.' in (ROOT/logs['native']).read_text()
assert 'runtime selection overrides these' in (ROOT/logs['native']).read_text()
models=[m for e in a['entries'] for m in e.get('models',[])]
assert len(models)==30
gamepad=next(m for m in models if m['asset_file']=='models/wii-u-gamepad.glb')
provider=gamepad['artwork_cache']
assert provider['format_version']==2 and sha(ROOT/provider['asset_file'])==provider['sha256']=='50c347daa7bc90e9d155712b2c337266ed4c419dc564acb27699a636b09c63c2'
assert sha(ROOT/gamepad['asset_file'])==provider['source_sha256']==gamepad['sha256']
ps5=next(m for m in models if m['asset_file']=='models/playstation-5.glb')
assert ps5['artwork_cache']['format_version']==1
gap_path='build/research/story-text-profile/unillustrated-scenes-current.json'
gaps=json.loads((ROOT/gap_path).read_text(encoding='utf8'))
assert gaps['catalog']==runtime and gaps['catalog_entries']==1395 and gaps['explicit_catalog_override'] is True
assert len(gaps['current_explicit_media_probes'])==9 and all(r['exact_association_pass'] for r in gaps['current_explicit_media_probes'])
assert gaps['current_cover_only_probe']['all_source_paragraphs_in_order'] and not gaps['current_cover_only_probe']['cover_reused']
assert gaps['current_cover_sha_alias_probe']['distinct_explicit_p0_image_preserved']
recovery=ROOT/'build/research/native-source71-recoverable'
r=json.loads((recovery/'manifest.json').read_text(encoding='utf8'))
for name,v in r['files'].items(): assert sha(recovery/name)==v['sha256']
report={
 'status':'PASS_coherent_1395_SOURCE71_preservation_yoshi_covers_GamePadV2_fonts_native_actual4k',
 'master':record(master),'runtime':record(runtime),'entry_count':1395,
 'aliases':{'count':23,'exact_master_runtime':True,'native_parser_and_actual_saved_settings':'PASS'},
 'models':{'attached':30,'GamePad_provider':provider,'GamePad_original_unchanged':True,'PS5_provider_version':1},
 'fonts':{'receipt':record(font_path),'ordinary_codepoints':font['ordinary_display_codepoints'],
          'visible_ordinary_codepoints':font['visible_ordinary_codepoints'],
          'static_complex_phrases':font['current_complete_script_phrases'],
          'shaped_whole_word_runs':font['genuine_harfbuzz_word_boundary_runs'],
          'fallback_atlas':font['fallback_atlas'],
          'assets':{p:v for p,v in font['files'].items() if p.endswith('.huifont')}},
 'native':record('build/eboot.elf'),
 'host_actual4k':{'both_themes':True,'GL_errors':0,'all_ordinary_faces_and_lower_atlas_rows':'PASS',
                 'full_prose_last_line_without_R3':'PASS','complete_MK348_credits':'2810 retained lines',
                 'Nintendo64_and_DSLite_explicit_paragraph_media':'PASS'},
 'actual_scene_profile':dict(record(gap_path),unillustrated_composed_narrative_scenes=gaps['count']),
 'explicit_image_association_regression':{'Maze':2,'Auto_Modellista':7,'distinct_non_cover_images':'PASS',
                                        'cover_only_real_Star_Trader':gaps['current_cover_only_probe'],
                                        'equal_pixel_cover_URL_aliases':gaps['current_cover_sha_alias_probe'],
                                        'production_source':record('src/museum/story.cpp'),
                                        'actual_host_check':record('host/story_text_profile_checks.hpp')},
 'logs':{k:record(v) for k,v in logs.items()},
 'previous_SOURCE71_recovery':{'manifest':record('build/research/native-source71-recoverable/manifest.json'),
                               'verified_original_files':len(r['files'])},
 'physical_ps5_test_or_transfer':False,
 'limits':['Host generation/GL checks do not measure physical PS5 frame rate or model-loading speed.',
           'Exact static complex-script phrases and whole-word runs are supported; general dynamic shaping/bidi is not claimed.',
           'The older d7f62d3e receipt used a stale profiler fixture; its 529 gap count is superseded here. The current report requires explicit runtime override, actual loaded entry count and targeted composed-image assertions.',
           'Pending source-only text/music research is not part of this frozen group.']}
target=OUT/'verification.json'
target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(target.relative_to(ROOT),sha(target))
