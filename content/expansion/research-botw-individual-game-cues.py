"""Acquire identity and codec receipts for actual individual BOTW game cues.

This does not declare the archive complete, map it to the CD, or publish it.
Descriptions remain empty when the public upload has no description.
"""
import concurrent.futures
import importlib.util
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
spec = importlib.util.spec_from_file_location('pipeline', ROOT / 'content/expansion/soundtrack-broad-pipeline.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)
spec = importlib.util.spec_from_file_location('videos', ROOT / 'tools/discover-museum-videos.py')
videos = importlib.util.module_from_spec(spec)
spec.loader.exec_module(videos)
playlist = json.loads((OUT / 'botw-arnheim-public-flat-playlist.json').read_text(encoding='utf-8'))
cache_dir = OUT / 'botw-individuals'
cache_dir.mkdir(exist_ok=True)


def read(source):
    video_id = source['id']
    destination = cache_dir / (video_id + '.json')
    if destination.exists():
        return json.loads(destination.read_text(encoding='utf-8'))
    row = {'youtube_id': video_id, 'source': source}
    try:
        watch_path = ROOT / f'build/research/soundtrack-broad/watch/{video_id}.json'
        if watch_path.exists():
            watch = json.loads(watch_path.read_text(encoding='utf-8'))
        else:
            process = subprocess.run([
                str(pipeline.YTDLP), '--skip-download', '--dump-single-json', '--no-warnings',
                '--ignore-no-formats-error', '--no-check-formats', '--socket-timeout', '12',
                '--retries', '1', '--extractor-args',
                'youtube:player_skip=webpage,configs;player_client=android',
                'https://www.youtube.com/watch?v=' + video_id,
            ], capture_output=True, text=True, encoding='utf-8', timeout=45)
            raw = json.loads(process.stdout)
            watch = {
                'title': raw.get('title'), 'author': raw.get('channel'),
                'channelId': raw.get('channel_id'), 'shortDescription': raw.get('description') or '',
                'lengthSeconds': str(raw.get('duration') or 0),
                'metadata_source': 'Actual public Android player identity metadata; absent descriptions remain empty.',
            }
            assert watch['title'] and watch['channelId']
            pipeline.write(watch_path, watch)
        assert watch['channelId'] == 'UCRgbtEYQ6dxbcjG6KHj1qaA'
        assert watch['title'] == source['title']
        assert abs(float(watch['lengthSeconds']) - float(source['duration'])) <= 3
        native = videos.metadata(video_id, {'title': watch['title'], 'channel': watch['author']})
        row.update(
            status='metadata_candidate' if native.get('native_compatible_avc_aac') else 'codec_hold',
            publication=watch,
            native_codec_receipt=f'build/research/video-discovery/video-{video_id}.json',
            native_compatible_avc_aac=bool(native.get('native_compatible_avc_aac')),
        )
    except Exception as error:
        row.update(status='hold', error=str(error))
    pipeline.write(destination, row)
    return row


if __name__ == '__main__':
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(read, playlist['entries']):
            rows.append(row)
            pipeline.write(OUT / 'botw338-individual-publication-research.json', {
                'publication_status': 'research_only', 'expected_archive_entries': len(playlist['entries']),
                'scope': 'Actual individual archive metadata only; no complete-CD or whole-game claim.',
                'tracks': rows,
            })
            print(len(rows), row['youtube_id'], row['status'], flush=True)
