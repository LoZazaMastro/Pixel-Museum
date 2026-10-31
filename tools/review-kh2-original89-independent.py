"""Independent metadata/printed-credit review of the original KHII album."""
from pathlib import Path
import copy,hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/soundtrack-broad/kingdom-hearts-complete'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
path=BASE/'kh2-original89-plus5-original2006-primary-candidate.json'
digest=hashlib.sha256(path.read_bytes()).hexdigest()
assert digest=='88a202f3d0087f5479c1523a835234835118ebc77ddfd935465ef1f10d145845'
entry=read(path)['entries'][0];album=entry['tracks'][:89];extras=entry['tracks'][89:]
inventory=read(BASE/'kh2-original89-secondary-inventory.json')['tracks']
assert len(album)==len(inventory)==89 and len(extras)==5
assert [t['album_track_number']for t in album]==list(range(1,90))
assert [t['disc_track_number']for t in album]==list(range(1,52))+list(range(1,39))
assert len({t['youtube_id']for t in entry['tracks']})==94
aliases={2:'KH2 OST 02- Passion Orchrestrated version',7:'KH2 OST 07- Dive Into the Heart',
 20:'KH2 OST 20- Reviving Hallow Bastion',26:"KH2 OST 26- Shipmeister' Shanty",
 31:'KH2 OST 31- Dance of the Darling',35:'KH2 OST 35-The Home of the Dragons',
 45:'KH2 OST 45- Micky Mouse Club March',51:'KH2 OST 51- Bounce-O-Rama',
 59:'KH2 OST 59- Night of the Cursed',64:'KH2 OST 64- Agrabian Dream',
 72:'KH2 OST 72- Sinister Shadow',74:'KH2 OST 74-Showdown at Hallow Bastion',
 75:'KH2 OST 75- One-Winged Angel',85:'KH2 OST 85-Fantasia all marcia'}
normal=lambda s:re.sub('[^a-z0-9]','',s.casefold())
checks=[]
for t,inv in zip(album,inventory):
    n=t['album_track_number'];assert t['title']==inv['title']
    assert t['album_disc']==inv['disc'] and t['disc_track_number']==inv['disc_track']
    raw=read(ROOT/t['publication_metadata_receipt']);watch=raw.get('publication',raw)
    native=read(ROOT/t['native_codec_metadata_receipt'])
    assert native['id']==t['youtube_id'] and native['native_compatible_avc_aac']
    assert native['avc_format_count']>0 and native['aac_format_count']>0
    assert abs(float(native['duration'])-t['duration_seconds'])<.1
    assert abs(t['duration_seconds']-inv['duration_seconds'])<=4
    assert watch['title']==t['primary_published_title']
    if n in aliases:assert watch['title']==aliases[n]
    else:assert normal(t['title'])in normal(watch['title'])
    if n<89:
        expected_channel='UCMTW0vOUQi-X8hz4tyXIteQ' if n in [3,84] else 'UCwinJ-Pa4aveXWg2IA-aAow'
        assert watch['channelId']==expected_channel==t['channel_url'].rsplit('/',1)[-1]
        assert int(watch['lengthSeconds'])==int(t['duration_seconds'])
        if n in [3,84]:assert 'From Kingdom Hearts' in watch['shortDescription'] and 'Soundtrack.' in watch['shortDescription']
        else:assert str(n).zfill(2) in watch['title']
    else:
        assert watch['provider_name']=='YouTube'and watch['author_name']=='Kaiyo'
        assert t['duration_seconds']==88 and 'oEmbed' in t['publication_metadata_scope']
    assert not t['official_uploader_verified'] and not t['playback_verified_on_ps5']
    assert 'start_seconds'not in t and 'end_seconds'not in t
    checks.append(dict(number=n,title=t['title'],source_title=watch['title'],
        seconds=t['duration_seconds'],reference_seconds=inv['duration_seconds'],
        title_alias_reviewed=n in aliases))
checkpoint=ROOT/'build/research/soundtrack-broad/checkpoints/incremental-517-912-reviewed-eight-2026-10-21.json'
assert hashlib.sha256(checkpoint.read_bytes()).hexdigest()=='9bab3955ca22796d6d47326d3648c8863e71523ac3276f01108d76c11fb9cd1d'
prior=next(e for e in read(checkpoint)['entries']if e['entry_id']==entry['entry_id'])['tracks']
stripped=copy.deepcopy(extras)
for t in stripped:t.pop('collection_section',None)
assert stripped==prior
roles={2:'Hikaru Utada',3:'Hikaru Utada',34:'Alan Menken',45:'Jimmie Dodd',
 50:'Richard M. Sherman, Robert B. Sherman',55:'Alan Menken',56:'Alan Menken',
 60:'Klaus Badelt, Geoffrey Zanelli, Hans Zimmer',65:'Danny Elfman',75:'Nobuo Uematsu',84:'Hikaru Utada'}
for n,t in enumerate(album,1):assert t['creator']==roles.get(n,'Yoko Shimomura')
for n in [2,85]:assert album[n-1]['additional_recording_roles']['orchestra']==['Tokyo Philharmonic']
for n in [1,2,74,85,86,87,88]:assert album[n-1]['additional_recording_roles']['orchestral_arrangement']==['Kaoru Wada']
assert album[88]['additional_recording_roles']=={'piano_arrangement':['Kaoru Wada'],'piano':['Shinko Ogata']}
for n in [3,84]:
    assert album[n-1]['additional_recording_roles']['vocals']==['Hikaru Utada']
    assert album[n-1]['additional_recording_roles']['arrangement']==['Hikaru Utada']
for image in read(BASE/'kh2-original2006-printed-primary-roles-receipt.json')['original_images']:
    assert hashlib.sha256((ROOT/image['path']).read_bytes()).hexdigest()==image['sha256']
receipt=dict(status='PASS',candidate_sha256=digest,album_tracks=89,prior_supplements_preserved=5,
    independent_visual_review='Read actual original2006 booklet credit spreads, printed51+38 track order and Passion production pages. Not the expanded2007 compilation.',
    checks=checks,source_typographical_aliases_reviewed=aliases,
    limitations='All89 public identity/codec receipts checked;14 uploader spelling/short-title variants explicitly reviewed against numbered sequence and near CD durations. One final reprise uses declared public oEmbed. Original-album association follows metadata/order/durations, not audio fingerprinting or listening. No physical PS5 playback certification; later FinalMix/HD versions are separate preserved supplements, not counted in the89 original tracks.')
(BASE/'root-independent-kh2-original89-review.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PASS:89 original-album publications +5 unchanged supplements, printed roles and all native metadata checked.')
