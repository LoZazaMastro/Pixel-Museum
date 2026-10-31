"""Bounded artist presentation reconciliation, with both actual public identities retained."""
import concurrent.futures
import importlib.util
import json
import pathlib
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
DEST = OUT / 'discoelysium-artist-presentation'
DEST.mkdir(exist_ok=True)
spec = importlib.util.spec_from_file_location('v', ROOT / 'tools/discover-museum-videos.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
load = lambda p: json.loads(p.read_text(encoding='utf8'))
data = load(OUT / 'discoelysium-public-public-oembed-fallback-research.json')

def acquire(original):
    row = dict(original)
    source = row['source']
    video_id = source['id']
    target = DEST / (video_id + '.json')
    if target.exists():
        return load(target)
    try:
        assert source['channel'] == 'Sea Power'
        native_path = ROOT / ('build/research/video-discovery/video-' + video_id + '.json')
        if native_path.exists():
            assert load(native_path).get('native_compatible_avc_aac') is not False, 'Cached native failure retained without retry'
        url = 'https://www.youtube.com/oembed?format=json&url=' + urllib.parse.quote('https://www.youtube.com/watch?v=' + video_id, safe='')
        with urllib.request.urlopen(url, timeout=20) as response:
            raw = json.load(response)
        identity = {k: raw.get(k) for k in ['title', 'author_name', 'author_url', 'provider_name', 'provider_url']}
        assert identity['title'] == source['title']
        assert identity['author_name'] == 'Sea Power - Topic'
        meta = v.metadata(video_id, {'title': identity['title'], 'channel': identity['author_name']})
        assert meta['native_compatible_avc_aac']
        duration = float(meta['duration'])
        assert duration > 0 and abs(duration-float(source['duration'])) <= 3
        identity_path = DEST / (video_id + '-actual-public-oembed.json')
        identity_path.write_text(json.dumps(identity, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
        row.update(status='metadata_candidate', publication={'title': identity['title'],
            'author': identity['author_name'], 'channelId': '', 'shortDescription': '',
            'lengthSeconds': str(duration), 'metadata_source': 'Current public oEmbed artist-Topic presentation, not a recovered original description.'},
            current_public_channel_url=identity['author_url'],
            publication_metadata_receipt=identity_path.relative_to(ROOT).as_posix(),
            native_codec_receipt=native_path.relative_to(ROOT).as_posix(), native_compatible_avc_aac=True,
            public_channel_reading_scope='Exact artist-upload ID/title/duration from the public Sea Power playlist presentation, with current oEmbed explicitly Sea Power - Topic. Original artist Bandcamp independently identifies the album and Sea Power/British Sea Power alias. Both channel presentations are retained; no missing description, verified uploader badge or recording-role field is invented.')
        row.pop('error', None)
    except Exception as error:
        row.update(status='hold', error=str(error))
    target.write_text(json.dumps(row, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    return row

rows = []
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    for row in pool.map(acquire, data['tracks']):
        rows.append(row)
        (OUT / 'discoelysium-artist-presentation-research.json').write_text(json.dumps({'publication_status': 'research_only', 'tracks': rows}, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
        print(row['source']['id'], row['status'], row.get('error', ''), flush=True)
