"""Join verified, remotely played soundtrack selections to exact exhibit IDs."""
import copy
import re
from urllib.parse import parse_qs, urlparse


def video_id(url):
    parsed = urlparse(url)
    if parsed.scheme != 'https':
        return ''
    if parsed.netloc in ('youtube.com', 'www.youtube.com', 'music.youtube.com'):
        return parse_qs(parsed.query).get('v', [''])[0]
    if parsed.netloc == 'youtu.be':
        return parsed.path.lstrip('/').split('/')[0]
    return ''


def integrate(entries, document):
    by_id = {entry['id']: entry for entry in entries}
    seen_exhibits, seen_videos = set(), set()
    playlists, mirrors = [], []
    tracks_count = 0
    for selection in document.get('entries', []):
        identifier = selection['entry_id']
        if identifier in seen_exhibits or identifier not in by_id:
            raise ValueError('Duplicate or unknown soundtrack exhibit: ' + identifier)
        seen_exhibits.add(identifier)
        entry = by_id[identifier]
        if entry.get('calendar_only'):
            raise ValueError('Soundtrack selection must name the canonical exhibit: ' + identifier)
        tracks = selection.get('tracks', [])
        if not 1 <= len(tracks) <= (256 if selection.get('full_album_collection') else 32):
            raise ValueError('Soundtrack track count is empty or excessive: ' + identifier)
        playlist_video_ids = set()
        for track in tracks:
            youtube_id = track.get('youtube_id', '')
            if not re.fullmatch(r'[A-Za-z0-9_-]{11}', youtube_id) or youtube_id in playlist_video_ids:
                raise ValueError('Invalid or duplicate soundtrack YouTube ID: ' + youtube_id)
            if video_id(track.get('url', '')) != youtube_id:
                raise ValueError('Soundtrack URL does not identify the declared video: ' + youtube_id)
            if (track.get('official_uploader_verified') is not True or not track.get('creator')
                    or not track.get('title') or not track.get('source_page')
                    or not track.get('channel_url')):
                raise ValueError('Soundtrack lacks verified official-uploader provenance: ' + youtube_id)
            playlist_video_ids.add(youtube_id)
            seen_videos.add(youtube_id)
        playlist = {field: copy.deepcopy(selection.get(field, ''))
                    for field in ('title', 'composer', 'curator_note')}
        playlist['tracks'] = copy.deepcopy(tracks)
        entry['soundtrack'] = playlist
        source_urls = {source['url'] for source in entry.get('sources', [])}
        for track in tracks:
            for url, label in ((track['source_page'], 'Official soundtrack: ' + track['title']),
                               (track.get('verification_url', ''), 'Official soundtrack publishing provenance')):
                if url and url not in source_urls:
                    entry.setdefault('sources', []).append(dict(title=label, url=url,
                        publisher=track['creator'], attribution='Music remains on its original official YouTube publication. No audio file is bundled or redistributed.'))
                    source_urls.add(url)
        playlists.append(identifier)
        tracks_count += len(tracks)
    for feature in entries:
        linked_id = feature.get('linked_exhibit_id', '')
        canonical = by_id.get(linked_id)
        if (feature.get('calendar_only') and canonical and canonical['year'] == feature['year']
                and 'soundtrack' in canonical):
            feature['soundtrack'] = copy.deepcopy(canonical['soundtrack'])
            mirrors.append(feature['id'])
            existing = {source['url'] for source in feature.get('sources', [])}
            for source in canonical.get('sources', []):
                if source.get('attribution', '').startswith('Music remains on its original official YouTube publication.') and source['url'] not in existing:
                    feature.setdefault('sources', []).append(copy.deepcopy(source))
                    existing.add(source['url'])
    return dict(canonical_exhibits=playlists, unique_tracks=tracks_count,
                same_event_calendar_copies=mirrors,
                policy='Official remote YouTube publications only. Existing documentary films, chronology and media are unchanged.')
