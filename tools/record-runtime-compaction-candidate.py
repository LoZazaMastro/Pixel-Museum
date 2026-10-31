"""Record actual C++ reader and real StoryCard equivalence, without promotion."""
from pathlib import Path
import hashlib,json,re,statistics
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'build/research/runtime-compaction-source73'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
manifest=read(P/'candidate-manifest.json')
assert sha(P/'original-runtime.json')==manifest['original_runtime_sha256']
assert sha(P/'candidate-runtime.json')==manifest['candidate_runtime_sha256']
original=read(P/'original-composition.json');candidate=read(P/'candidate-composition.json')
assert original==candidate and sha(P/'original-composition.json')==sha(P/'candidate-composition.json')
assert len(candidate['entries'])==1395
cards=sum(len(e['cards']) for e in candidate['entries'])
og=read(P/'original-gap-profile.json');cg=read(P/'candidate-gap-profile.json')
assert og['entries']==cg['entries'] and og['count']==cg['count']==389
for key in ['current_cover_only_probe','current_cover_sha_alias_probe','current_explicit_media_probes']:
 assert og[key]==cg[key]
assert len(cg['current_explicit_media_probes'])==13 and all(r['exact_association_pass'] for r in cg['current_explicit_media_probes'])
native=(P/'native-equivalence.log').read_text(encoding='utf8')
assert 'Native parser equivalence PASS: 1395 entries' in native and '23 alias resolutions' in native
for label in ['original','candidate']:
 assert 'PASS actual native complete composition snapshot: 1395 entries' in (P/f'{label}-actual-composition.log').read_text(encoding='utf8')
measurements=[]
for line in (P/'native-load-benchmark.log').read_text(encoding='utf8').splitlines():
 m=re.fullmatch(r'(original|candidate): Actual Catalog::load PASS entries=1395 rooms=561 distinctgames=559 tracks=6888 wall_ms=([\d.]+) peak_RSS_bytes=(\d+); hostonly, notPS5',line)
 assert m;measurements.append({'variant':m[1],'host_wall_ms':float(m[2]),'host_peak_RSS_bytes':int(m[3])})
assert len(measurements)==6
averages={label:{'mean_host_wall_ms':statistics.mean(r['host_wall_ms'] for r in measurements if r['variant']==label),
 'mean_host_peak_RSS_bytes':statistics.mean(r['host_peak_RSS_bytes'] for r in measurements if r['variant']==label)} for label in ['original','candidate']}
assert sha(ROOT/'content/catalog.json')==manifest['source_master_sha256']
assert sha(ROOT/'build/runtime-preview/content/catalog.json')==manifest['original_runtime_sha256']
report={
 'status':'CANDIDATE_PASS_ACTUAL_NATIVE_READER_AND_COMPOSITION_AWAITING_ROOT_PEER_NOT_ADMITTED',
 'master_sha256':manifest['source_master_sha256'],
 'baseline':{'path':(P/'original-runtime.json').relative_to(ROOT).as_posix(),'sha256':sha(P/'original-runtime.json'),'bytes':(P/'original-runtime.json').stat().st_size},
 'candidate':{'path':(P/'candidate-runtime.json').relative_to(ROOT).as_posix(),'sha256':sha(P/'candidate-runtime.json'),'bytes':(P/'candidate-runtime.json').stat().st_size},
 'saved_JSON_bytes':manifest['saved_bytes'],
 'native_Catalog_comparison':'PASS every parsed field/array/order, media URLs, image captions, video posters, soundtrack cue bounds, credits/source/licences, dates, models, editorial features, eras and23alias resolutions. Uses actual C++ Catalog::parse/load; no Python whitelist simulation as acceptance.',
 'actual_Screen_composition':{'entries':1395,'cards':cards,'byte_identical_complete_snapshot_sha256':sha(P/'candidate-composition.json'),
  'fields':'kind/title/lead/paragraph+continuations/feature/imageindex+URL+contentidentity/video/study/musicroom/preferredimage/explicitmediapolicy',
  'unillustrated_scenes':389,'Maze_Auto_Kinect_noncover_associations':13,'cover_only_and_SHA_alias_regressions':'PASS identical'},
 'native_fresh_process_load_measurements':measurements,'native_load_averages':averages,
 'mean_host_load_saving_ms':averages['original']['mean_host_wall_ms']-averages['candidate']['mean_host_wall_ms'],
 'mean_host_peak_RSS_saving_bytes':averages['original']['mean_host_peak_RSS_bytes']-averages['candidate']['mean_host_peak_RSS_bytes'],
 'room_and_game_counts':{'rooms':561,'distinct_game_entries_with_music':559,'tracks':6888},
 'source_transform_manifest':manifest,'product_projection_tool_modified':False,'production_CPP_modified':False,
 'source_master_runtime_or_full_credits_inventory_modified':False,'global_parser_limit_increased':False,
 'evidence':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in list(P.glob('*.log'))+[P/'original-composition.json',P/'candidate-composition.json',P/'original-gap-profile.json',P/'candidate-gap-profile.json']},
 'limits':['Host process RSS includes nativeJSON/strings and process overhead; it is not physical PS5 memory.',
 'Source authoring, complete credit/source inventory and visible native selections remain unchanged. Only serialized runtime fields not read by the current parser are removed.',
 'Existing boolean policy is made explicit before its research object payload is omitted. The actual native composer confirms unchanged paragraph/media grouping.',
 'Compaction creates headroom, but a future100kcuecollection still needs bounded per-room loading rather than a higher globalJSONcap.',
 'The candidate is isolated and not in package/runtimeprojection. Root peer and coherent next-group regeneration are required before adoption.']}
out=P/'verification.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(out.relative_to(ROOT),sha(out));print(cards,'cards, bytes saved',manifest['saved_bytes']);print(averages)
