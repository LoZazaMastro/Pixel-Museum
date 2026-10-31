"""Independently compare available original MHW publications with both label inventories."""
from pathlib import Path
import hashlib,json,re,html
ROOT=Path(__file__).resolve().parents[1];BASE='build/research/soundtrack-broad/modern-following/'
PATH=BASE+'monster-hunter-world-eighty-two-original-recordings-candidate.json'
EXPECTED='1f972ebb04972ff77fe2298cc464fd212def4bcdb44d77c62a37bbc8c6a2f2ae'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert sha(PATH)==EXPECTED
d=load(PATH);e=d['entries'][0];tracks=e['tracks'];assert len(tracks)==82 and not e['full_album_collection']
owner=next(x for x in load('content/catalog.json')['entries'] if x['id']==e['entry_id'])
assert (owner['title'],owner['year'])==(e['match_title'],2018)
for r in d['source_receipts']:assert sha(r['path'])==r['sha256'],r['path']
steam=(ROOT/(BASE+'mhw-original-steam-store.html')).read_text(encoding='utf8')
titles=[html.unescape(x).strip() for x in re.findall(r'<div class="music_album_track_name">(.*?)</div>',steam,re.S)]
assert len(titles)==83
label=[x for x in load(BASE+'mhw-original-label-album.json')['results'] if x.get('kind')=='song']
assert len(label)==83
playlist=load(BASE+'mhw-original-archive-playlist.json')['entries'];assert len(playlist)==84
seen=set();rows=[]
for t in tracks:
    ordinal=t['published_album_ordinal'];a=label[ordinal-1];p=playlist[ordinal]
    assert t['youtube_id']==p['id'] and t['source_actual_publication_title']==p['title']
    assert t['title']==titles[ordinal-1] and t['published_original_language_title']==a['trackName']
    assert t['creator']==t['label_artist_credit']==a['artistName']
    assert (t['published_album_disc'],t['published_album_track_number'],t['published_duration_ms'])==(a['discNumber'],a['trackNumber'],a['trackTimeMillis'])
    w=load(t['publication_metadata_receipt']);v=load(t['native_codec_metadata_receipt'])
    assert v['id']==t['youtube_id'] and v['title']==w['title']==t['source_actual_publication_title']
    assert int(w['lengthSeconds'])==v['duration']==t['duration_seconds']
    assert v['channel_id']==w['channelId'] and t['channel_url'].endswith(v['channel_id'])
    assert v['native_compatible_avc_aac'] and v['avc_format_count']>0 and v['aac_format_count']>0
    assert not t['official_uploader_verified'] and not t['playback_verified_on_ps5']
    assert 'start_seconds' not in t and 'end_seconds' not in t
    assert t['youtube_id'] not in seen;seen.add(t['youtube_id'])
    rows.append(dict(ordinal=ordinal,title=t['title'],label_title=a['trackName'],artist=a['artistName'],actual_publication_title=w['title'],seconds=v['duration']))
assert {t['published_album_ordinal'] for t in tracks}==set(range(1,84))-{75}
assert d['held_recordings']==[dict(album_ordinal=75,youtube_id='IRrgmitUMB8',title=titles[74],reason='Unsigned app player: login_required')]
receipt=dict(status='PASS',candidate_path=PATH,candidate_sha256=EXPECTED,available_recordings=82,published_inventory=83,held_ordinals=[75],rows=rows,source_hashes_verified=len(d['source_receipts']),observations=['All82 display titles read and independently matched in order to literal English publisher Steam titles; Japanese label titles and individual artists remain exact, without invented translation or exclusive composer roles.','The six available research flags are punctuation or version abbreviations:6 Astera tilde,17 Quest Clear version/ver.,30 Proof of a Hero MH:W abbreviation,59 colon spacing,63 Nergigante tilde,81 extended Proof of a Hero abbreviation. The held75 also differs only spacing; it remains held. Distinct Chase and extended variants remain separate.','All82 actual publications match their original-album ordinal and title context, have positive AVC/AAC metadata, and retain differing public versus retail durations honestly. No audio fingerprint or exact retail-master claim.','One login-required ordinal75 is excluded without another fetch. The13203second whole album has no usable chapters and supplies no invented boundaries. Scope is original2018base-game published album, not Iceborne or the film. Partial coverage retained.'],master_modified=False)
out=BASE+'independent-eighty-two-original-mhw-recordings-review.json';(ROOT/out).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(out,sha(out))
