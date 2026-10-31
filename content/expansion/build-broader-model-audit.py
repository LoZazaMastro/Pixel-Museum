"""Record bounded source research without silently selecting approximate assets."""
from pathlib import Path
import json
import struct

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / 'build/research/model-validation'
downloads = json.loads((RESEARCH / 'broader-source-downloaded.json').read_text())
decisions = {
    '08d4fd565ae64e6bbcda044c9195a639': {
        'target': 'xbox-series-x', 'status': 'not_selected_fidelity',
        'native_proof': {'resolution': [3840, 2160], 'triangles': 22833, 'draws': 1, 'gl_errors': 0},
        'observations': ['Post-launch December 2020 publication; original black retail form, disc slot, front USB/pair control and rear ports are represented.',
            'Rear label explicitly reads 3D MODEL - MADE WITH BLENDER rather than the physical console markings.',
            'Native top ventilation lacks the retail subsurface green appearance. Do not replace the selected model without correcting and reviewing these differences.'],
    },
    'df5cc09db250476fb02843c5ae063eb0': {
        'target': 'xbox-series-s', 'status': 'not_selected_fidelity',
        'native_proof': {'resolution': [3840, 2160], 'triangles': 255312, 'draws': 6, 'gl_errors': 0},
        'observations': ['White original Series S form; actual perforations, rear ports and front Xbox mark are modelled.',
            'Large circular black exhaust has an obviously faceted polygonal boundary in the native 4K capture; surface materials and missing small print also require review.',
            'High triangle count alone does not establish accurate geometry. Not accepted as a finished museum replacement.'],
    },
    'c2de422f22234b209aaae7a377846995': {
        'target': 'master-system', 'status': 'not_selected_renderer_and_fidelity',
        'native_proof': {'error': 'This GLB requires an unsupported extension'},
        'observations': ['Recognisable original black/red Master System Power Base body in publisher preview.',
            'Publisher preview has a blank red wordmark stripe and lacks physical top control labels. Not a finished fidelity replacement.',
            'Native loader correctly rejects its unsupported material extension; original source is retained for research only.'],
    },
}
records = []
for download in downloads:
    uid = download['uid']
    meta = json.loads((RESEARCH / f'candidate-{uid}.json').read_text())
    raw = Path(download['path']).read_bytes()
    n = struct.unpack_from('<I', raw, 12)[0]
    gltf = json.loads(raw[20:20+n])
    record = dict(download)
    record['path'] = str(Path(record['path']).relative_to(ROOT))
    record.update({'source_page': f'https://sketchfab.com/models/{uid}', 'title': meta['name'],
        'creator': meta['user']['displayName'], 'creator_username': meta['user']['username'],
        'current_license': meta['license'], 'is_downloadable': meta['isDownloadable'],
        'published_at': meta['publishedAt'], 'metadata_evidence': str((RESEARCH / f'candidate-{uid}.json').relative_to(ROOT)),
        'extensions_required': gltf.get('extensionsRequired', []),
        'download_route': 'Independently published Allen Institute Objaverse asset matched by exact Sketchfab UID; no viewer extraction or authenticated quota bypass.'})
    record.update(decisions[uid])
    if 'error' not in record['native_proof']:
        record['native_proof']['captures'] = [record['path'] + '-0.png', record['path'] + '-1.png']
        record['native_proof']['current_capture_yaw'] = 2.6
        record['native_proof']['other_angles_also_reviewed'] = [-0.4, -1.3, 1.7]
    records.append(record)

report = {'checked_date': '2026-10-20', 'scope': 'Focused public, licensed hardware source search beyond current selections; no runtime catalogue or model-index edits.',
    'selected_count': 0, 'downloaded_candidates': records,
    'non_sketchfab_leads': [
        {'target': 'original-ds', 'source_page': 'https://bitbuilt.net/forums/threads/original-ds-console-rescan.6790/',
         'creator': 'Wesk', 'kind': 'physical hardware scan reference', 'status': 'reference_only_no_redistribution_grant',
         'notes': 'Author provides six original DS shell/hinge/trigger scans, about 2.5M triangles each, explicitly as reference only. Useful for accurate modelling; not an open licensed finished bundled asset.'},
        {'target': 'atari-jaguar', 'source_page': 'https://bitbuilt.net/forums/threads/atari-jaguar-console.6252/',
         'creator': 'Wesk', 'kind': 'physical hardware scan reference', 'status': 'reference_only_no_redistribution_grant',
         'notes': 'Author provides top and bottom shell scans, about 20M triangles per mesh, explicitly as reference only. No author contact or download performed.'},
        {'target': 'ps-vita', 'source_page': 'https://blendswap.com/blend/5780', 'creator': 'EricWalker',
         'license': 'CC-BY as displayed by author download page', 'status': 'account_required_not_downloaded',
         'notes': 'Blender 2.6 asset, 580KB. Official download requires sign-in. Quality and complete rear geometry have not been verified; not a selected replacement.'},
        {'target': 'ps-vita', 'source_page': 'https://blendswap.com/blend/6105', 'creator': 'omorenof',
         'license': 'CC-BY as displayed by author download page', 'status': 'account_required_not_downloaded',
         'notes': 'Blender 2.6 asset, 1.24MB. Official download requires sign-in. Comments report invisible rear geometry; not a verified complete asset.'},
        {'target': 'neo-geo-aes', 'source_page': 'https://www.printables.com/model/1639087-neogeo-aes-replacement-shell',
         'status': 'unverified_lead_only', 'notes': 'Replacement shell lead; source page could not be inspected. No licence, geometry completeness or download claim is made.'},
    ],
    'remaining_gaps': ['Accurate original DS/DSi', 'Faithful Vita', 'Atari Jaguar', 'Faithful complete Series X retail / Series S',
        'Detailed PS5 replacement', 'Master System', 'Game Gear', 'Neo Geo AES', 'PC Engine', 'ColecoVision', 'Vectrex'],
    'conclusion': 'No newly checked candidate meets the full fidelity requirement unchanged. Preserve honest gaps rather than substitute an approximate body, wrong revision or fictional labels.'}
(ROOT / 'content/broader-model-search-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'downloaded': len(records), 'selected': 0, 'report': 'content/broader-model-search-audit.json'}))
