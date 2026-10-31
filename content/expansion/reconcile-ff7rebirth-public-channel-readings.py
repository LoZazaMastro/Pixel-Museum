"""Reconcile only mutually corroborated public readings of exact publisher album IDs."""
import concurrent.futures
import importlib.util
import json
import pathlib
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
DEST = OUT / 'ff7rebirth-public-channel-reconciliation'
DEST.mkdir(exist_ok=True)
spec = importlib.util.spec_from_file_location('v', ROOT / 'tools/discover-museum-videos.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
research = load(OUT / 'ff7rebirth-public-public-oembed-fallback-research.json')
selected = [row for row in research['tracks'] if row.get('error') == 'Actual oEmbed author differs from playlist']


def check(original):
    row = dict(original)
    source, video_id = row['source'], row['source']['id']
    path = DEST / (video_id + '.json')
    if path.exists():
        return load(path)
    try:
        cached = load(ROOT / 'build/research/soundtrack-broad/watch' / (video_id + '.json'))
        assert cached['title'] == source['title']
        assert 'Provided to YouTube by NexTone Inc.' in cached['shortDescription']
        assert 'FINAL FANTASY VII REBIRTH Original Soundtrack' in cached['shortDescription']
        assert abs(float(cached['lengthSeconds'])-float(source['duration'])) <= 3
        native_path = ROOT / 'build/research/video-discovery' / ('video-' + video_id + '.json')
        if native_path.exists() and load(native_path).get('native_compatible_avc_aac') is False:
            raise ValueError('Cached native failure retained; no retry')
        url = 'https://www.youtube.com/oembed?format=json&url=' + urllib.parse.quote('https://www.youtube.com/watch?v=' + video_id, safe='')
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20) as response:
            raw = json.load(response)
        identity = {key: raw.get(key) for key in ['title', 'author_name', 'author_url', 'provider_name', 'provider_url']}
        assert identity['title'] == source['title']
        assert identity['author_name'] == cached['author'], 'Current public reading does not corroborate cached publication author'
        identity_path = DEST / (video_id + '-actual-public-oembed.json')
        identity_path.write_text(json.dumps(identity, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        native = v.metadata(video_id, {'title': cached['title'], 'channel': cached['author']})
        assert native.get('native_compatible_avc_aac') is True
        assert abs(float(native['duration'])-float(source['duration'])) <= 3
        row.update(status='metadata_candidate', publication=cached,
                   publication_metadata_receipt=identity_path.relative_to(ROOT).as_posix(),
                   native_codec_receipt=native_path.relative_to(ROOT).as_posix(), native_compatible_avc_aac=True,
                   public_channel_reading_scope='The exact same publisher-album video ID, title and duration are corroborated by cached original NexTone publication and current public oEmbed, whose authors agree. Flat album presentation names a consolidated artist channel; that differing presentation is preserved, not silently equated or used as a writer credit.',
                   source_flat_channel=source['channel'], source_flat_channel_id=source['channel_id'],
                   corroborated_public_author=cached['author'], corroborated_public_channel_id=cached['channelId'],
                   original_android_metadata_receipt='build/research/soundtrack-broad/watch/' + video_id + '.json')
        row.pop('error', None)
    except Exception as error:
        row.update(status='hold', error=str(error))
    path.write_text(json.dumps(row, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return row


if __name__ == '__main__':
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(check, selected):
            rows.append(row)
            (OUT / 'ff7rebirth-channel-reconciled-public-research.json').write_text(json.dumps({
                'publication_status': 'research_only', 'tracks': rows,
                'scope': 'Strict corroborated source readings within the exact original publisher album. No generic channel-name bypass, title-only approval, failed native retry or authentication.'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(row['source']['id'], row['status'], row.get('error', ''), flush=True)
