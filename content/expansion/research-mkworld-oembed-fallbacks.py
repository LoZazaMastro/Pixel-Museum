"""Recover missing presentation fields through ordinary public oEmbed only.

Cached native failures remain holds. This never downloads media, signs in,
changes a failed client's authentication or fabricates missing descriptions.
"""
import concurrent.futures
import importlib.util
import json
import pathlib
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
spec = importlib.util.spec_from_file_location('reader', ROOT / 'content/expansion/research-botw-cd-individuals.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
NAME = sys.argv[1] if len(sys.argv) > 1 else 'mkworld-clean-freeroam'
if NAME in ['ff7rebirth-public', 'bayonetta3-public', 'acvalhalla-public', 'discoelysium-public']:
    OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
INPUT = {'mkworld-clean-freeroam': 'mkworld-clean-freeroam-archive-publication-research.json',
         'mkworld-inventory-exact-gaps': 'mkworld-inventory-exact-gaps-publication-research.json',
         'mkworld-koopasaurus-core': 'mkworld-koopasaurus-core-archive-publication-research.json',
         'next-switch-public': 'next-switch-public-collections-research.json',
         'kirby-forgotten-public': 'kirby-forgotten-public-research.json',
         'xenoblade2-public': 'xenoblade2-available-publication-research.json',
         'luigi3-public': 'luigi3-available-publication-research.json',
         'ff7rebirth-public': 'ff7rebirth-available-publication-research.json',
         'acvalhalla-public': 'acvalhalla-available-publication-research.json',
         'discoelysium-public': 'discoelysium-available-publication-research.json',
         'bayonetta3-public': 'bayonetta3-available-publication-research.json'}[NAME]
DEST = OUT / (NAME + '-oembed-fallbacks')
DEST.mkdir(exist_ok=True)


def acquire(original):
    row = dict(original)
    source = row['source']
    video_id = source['id']
    dest = DEST / (video_id + '.json')
    if dest.exists():
        return json.loads(dest.read_text(encoding='utf-8'))
    try:
        native_path = ROOT / f'build/research/video-discovery/video-{video_id}.json'
        if native_path.exists():
            existing = json.loads(native_path.read_text(encoding='utf-8'))
            if existing.get('native_compatible_avc_aac') is False:
                raise ValueError('Existing native failure retained; no retry: ' + str(existing.get('error')))
        endpoint = 'https://www.youtube.com/oembed?format=json&url=' + urllib.parse.quote('https://www.youtube.com/watch?v=' + video_id, safe='')
        with urllib.request.urlopen(urllib.request.Request(endpoint, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20) as response:
            raw = json.load(response)
        # Keep actual source identity, never the HTML iframe or media URLs.
        identity = {key: raw.get(key) for key in ('title', 'author_name', 'author_url', 'provider_name', 'provider_url')}
        assert identity['title'] == source['title'], 'Actual oEmbed title differs from playlist'
        assert identity['author_name'] == source['channel'], 'Actual oEmbed author differs from playlist'
        reader.pipeline.write(DEST / (video_id + '-public-oembed.json'), identity)
        native = reader.videos.metadata(video_id, {'title': identity['title'], 'channel': identity['author_name']})
        assert native.get('native_compatible_avc_aac'), 'Native AVC/AAC not verified'
        duration = float(native.get('duration') or 0)
        assert duration > 0 and abs(duration - source['duration']) <= 3, 'Native duration differs from actual playlist'
        row.update(status='metadata_candidate', publication={
            'title': identity['title'], 'author': identity['author_name'],
            'channelId': source['channel_id'], 'shortDescription': '',
            'lengthSeconds': str(duration),
            'metadata_source': 'Actual public YouTube oEmbed title/author plus independently native-resolved duration. Description unavailable and left empty.',
        }, publication_metadata_receipt=str((DEST / (video_id + '-public-oembed.json')).relative_to(ROOT)).replace('\\', '/'),
            native_codec_receipt=f'build/research/video-discovery/video-{video_id}.json', native_compatible_avc_aac=True)
        row.pop('error', None)
    except Exception as error:
        row.update(status='hold', error=str(error))
    reader.pipeline.write(dest, row)
    return row


if __name__ == '__main__':
    original = json.loads((OUT / INPUT).read_text(encoding='utf-8'))
    selected = [row for row in original['tracks'] if row['status'] != 'metadata_candidate' and not row.get('error')]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(acquire, selected):
            results.append(result)
            reader.pipeline.write(OUT / (NAME + '-public-oembed-fallback-research.json'), {
                'publication_status': 'research_only', 'scope': 'Ordinary public presentation fallback. No authentication or failed native-request retries.', 'tracks': results,
            })
            print(result['source']['id'], result['status'], result.get('error', ''), flush=True)
