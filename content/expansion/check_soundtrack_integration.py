"""Adversarial metadata checks; no network or media playback is performed."""
import copy
from pathlib import Path
import runpy

join = runpy.run_path(str(Path(__file__).with_name('integrate_soundtracks.py')))['integrate']
track = dict(youtube_id='AbCdEfGhI12', url='https://www.youtube.com/watch?v=AbCdEfGhI12',
             title='Official track', creator='Composer / official artist channel',
             source_page='https://www.youtube.com/watch?v=AbCdEfGhI12',
             channel_url='https://www.youtube.com/channel/official-test-fixture',
             official_uploader_verified=True)
entries = [dict(id='game', year=2012, sources=[], videos=[{'youtube_id':'Documentary'}]),
           dict(id='daily', year=2012, calendar_only=True, linked_exhibit_id='game', sources=[]),
           dict(id='regional', year=2013, calendar_only=True, linked_exhibit_id='game', sources=[])]
selection = dict(entry_id='game', title='Listening room', composer='Composer',
                 curator_note='A selected official publication.', tracks=[track])
report = join(entries, {'entries':[selection]})
assert report['unique_tracks'] == 1 and report['same_event_calendar_copies'] == ['daily']
assert entries[0]['videos'] == [{'youtube_id':'Documentary'}]
assert entries[0]['soundtrack'] == entries[1]['soundtrack'] and 'soundtrack' not in entries[2]
assert entries[0]['sources'] and entries[1]['sources']
for mutation in ('id', 'url', 'uploader', 'duplicate'):
    bad = copy.deepcopy(selection)
    if mutation == 'id': bad['tracks'][0]['youtube_id'] = 'short'
    if mutation == 'url': bad['tracks'][0]['url'] = 'https://www.youtube.com/watch?v=Different12'
    if mutation == 'uploader': bad['tracks'][0]['official_uploader_verified'] = False
    if mutation == 'duplicate': bad['tracks'].append(copy.deepcopy(bad['tracks'][0]))
    try:
        join(copy.deepcopy(entries), {'entries':[bad]})
        raise AssertionError('Invalid soundtrack metadata was accepted: '+mutation)
    except ValueError:
        pass
print('Soundtrack metadata checks passed: exact IDs/URLs, verified official uploader required, duplicates rejected, documentary films preserved, sources retained, playlist copied only to the same historical event.')
