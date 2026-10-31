"""Persist ordinary public identity and codec receipts, never transport URLs."""
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
mods = {}
for name, filename in [('p', 'content/expansion/soundtrack-broad-pipeline.py'), ('v', 'tools/discover-museum-videos.py')]:
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    mods[name] = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mods[name])
for video_id in sys.argv[1:]:
    target = OUT / (video_id + '-actual-publication-research.json')
    if target.exists():
        record = json.loads(target.read_text(encoding='utf-8'))
    else:
        publication = mods['p'].watch(video_id)
        native = mods['v'].metadata(video_id, {'title': publication['title'], 'channel': publication['author']})
        record = {'youtube_id': video_id, 'publication': publication,
                  'native_avc_aac': native.get('native_compatible_avc_aac'),
                  'native_codec_receipt': 'build/research/video-discovery/video-' + video_id + '.json'}
        mods['p'].write(target, record)
    publication = record['publication']
    print(json.dumps({'id': video_id, 'title': publication['title'], 'author': publication['author'],
                      'duration': publication['lengthSeconds'], 'native': record['native_avc_aac'],
                      'description': publication['shortDescription'][:2400]}, ensure_ascii=False), flush=True)
