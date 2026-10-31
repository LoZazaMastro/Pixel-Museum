"""Bounded independent review of available original-game archive publications."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/soundtrack-broad/nintendo-full'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
specs=[('echoes-mk8booster-calamity-available-public-v4-supplement-candidate.json','9357d1a3b9292a5372ef1fa07449d92ee4b8003f1f0854f438f45a23a34fa981',264),('kirby-forgotten92-public-candidate.json','db673cd8c29f131d3db81f8e6706d409c4dbcd71db8b23edb6c5f7abde9d38c6',92)]
for filename,digest,count in specs:
    path=BASE/filename;assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    d=read(path);checks=[];oembed=0
    for e in d['entries']:
        assert e['coverage_status']=='partial' and not e['full_album_collection']
        if e['match_title']=='Mario Kart 8':
            assert e['append_existing_tracks'] and not e['replace_existing_tracks']
        assert len({t['youtube_id']for t in e['tracks']})==len(e['tracks'])
        for t in e['tracks']:
            assert t['creator']==e['composer'] and 'team' in t['creator']
            assert not t['official_uploader_verified'] and t['publishing_kind']=='archival_game_recording'
            assert t['rights'] and not t['playback_verified_on_ps5']
            assert not any(s in t['title'].lower()for s in ['dspadpcm','.brstm','.bfstm'])
            n=read(ROOT/t['native_codec_metadata_receipt']);assert n['native_compatible_avc_aac'] and n['id']==t['youtube_id']
            assert abs(float(n['duration'])-t['duration_seconds'])<1
            raw=read(ROOT/t['publication_metadata_receipt']);pub=raw.get('publication',raw)
            assert pub['title']==t['primary_published_title']
            if pub.get('channelId'):assert pub['channelId'] in t['channel_url']
            else:
                assert pub.get('provider_name')=='YouTube' and pub.get('author_url');oembed+=1
            if e['match_title']=='Mario Kart 8':assert '2022' in t['recording_release_scope'] and '2023' in t['recording_release_scope']
            if e['match_title']=='Kirby and the Forgotten Land':assert t['recording_year']==2022 and '2025' in t['recording_version']
            checks.append(dict(game=e['match_title'],title=t['title'],youtube_id=t['youtube_id'],year=t.get('recording_year'),version=t['recording_version']))
    assert len(checks)==count
    out=BASE/('root-independent-'+('switch264'if count==264 else'kirby92')+'-review.json')
    out.write_text(json.dumps(dict(status='PASS',candidate_sha256=digest,tracks=count,oembed_publications=oembed,checks=checks,
        scope='Actual public recording titles, native AVC/AAC availability, declared original-game/platform versions and honest collective music-team credits. MK8 Booster recordings supplement existing base-game music. Unavailable publications remain excluded.',
        limitations='No audio fingerprints, exact edited-CD identity, all-game completeness or physical PS5 playback assertion. Collective game credits do not assign individual cue authorship.'),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(out.name,count,'PASS')
