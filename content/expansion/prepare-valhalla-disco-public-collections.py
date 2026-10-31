"""Available published recordings; literal label chapters and transparent artist presentations."""
import hashlib
import json
import pathlib
import re
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
load = lambda p: json.loads(p.read_text(encoding='utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
norm = lambda s: re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower())
base_source = 'https://news.ubisoft.com/en-us/article/12nFvpgMd9CPBeRopB21aY/assassins-creed-valhalla-composers-and-songwriter-revealed'
wrath_source = 'https://assassinscreedvalhalla.bandcamp.com/album/assassin-s-creed-valhalla-wrath-of-the-druids-original-game-soundtrack'
disco_source = 'https://seapower.bandcamp.com/album/disco-elysium'
source_paths = [OUT/'acvalhalla-available-publication-research.json', OUT/'discoelysium-available-publication-research.json', OUT/'discoelysium-artist-presentation-research.json']

def track(row, title, creator, composer_source, version, year):
    pub = row['publication']
    assert row['native_compatible_avc_aac'] and load(ROOT/row['native_codec_receipt'])['native_compatible_avc_aac']
    assert float(pub['lengthSeconds']) > 0 and abs(float(pub['lengthSeconds'])-float(row['source']['duration'])) <= 3
    video_id = row['source']['id']
    meta_path = row.get('publication_metadata_receipt') or (OUT/('acvalhalla-public-individuals' if 'Valhalla' in version else 'discoelysium-public-individuals')/(video_id+'.json')).relative_to(ROOT).as_posix()
    desc = pub.get('shortDescription') or ''
    return {'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v='+video_id,
        'source_page': 'https://www.youtube.com/watch?v='+video_id, 'title': title, 'creator': creator,
        'composer_source': composer_source, 'duration_seconds': float(pub['lengthSeconds']),
        'uploader': pub['author'], 'channel_url': row.get('current_public_channel_url') or 'https://www.youtube.com/channel/'+pub['channelId'],
        'source_flat_channel': row['source']['channel'], 'source_flat_channel_id': row['source']['channel_id'],
        'public_channel_reading_scope': row.get('public_channel_reading_scope', ''),
        'public_presentation_fallback': 'oEmbed only; no original description claimed' if not desc else '',
        'primary_published_title': pub['title'], 'official_uploader_verified': bool(desc),
        'publishing_kind': 'official_game_recording' if desc else 'artist_attributed_game_recording',
        'artist_credit_scope': 'Primary original artist/publisher album context, not an inferred composer role from producer-only fields. Additional raw distributor roles are retained without changing their meaning.',
        'publisher_music_role_lines': [s for s in desc.splitlines() if ' · ' in s or re.match(r'^(Producer|Mastering Engineer|Mixer|Composer|Lyricist):',s)],
        'recording_version': version, 'recording_year': year,
        'rights': 'Ubisoft Music / Lakeshore Records and original credited authors and performers.' if 'Valhalla' in version else 'Sea Power / Golden Chariot Records and original credited authors and recording contributors.',
        'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': row['native_codec_receipt'],
        'publication_metadata_receipt': meta_path, 'playback_verified_on_ps5': False}

ac_data = load(source_paths[0])
ac_tracks, excluded, seen = [], [], set()
full = None
for row in sorted(ac_data['tracks'], key=lambda r:r['source_playlist_position']):
    video_id = row['source']['id']
    if row['status'] != 'metadata_candidate':
        continue
    pub, desc = row['publication'], row['publication'].get('shortDescription','')
    if video_id == 'wTAvdXlUcwc':
        full = row
        continue
    if 'Wrath of the Druids' in desc:
        excluded.append({'youtube_id':video_id,'reason':'Same DLC selections included once through actual complete label chapter publication.'})
        continue
    if 'Preview (Official Video)' in pub['title']:
        excluded.append({'youtube_id':video_id,'reason':'Album preview montage, not a full individual recording.'})
        continue
    assert 'Ubisoft Music' in desc
    title = pub['title']
    creator = 'Assassin\'s Creed Valhalla music team'
    source = base_source
    if pub['author'] == 'Sarah Schachner':
        creator = 'Sarah Schachner'
    elif pub['author'] == 'JesperKyd':
        creator = 'Jesper Kyd'
    elif pub['author'] == 'Einar Selvik - Topic':
        creator = 'Einar Selvik'
    elif video_id == 'hsONr02KZS8':
        title, creator = "Helreið Oðins - Odin's Ride to Hel", 'Einar Selvik'
    elif video_id == 'nfhV2EyGNB4':
        title, creator = 'Hrafnsmál - The Words of the Raven', 'Einar Selvik'
    if video_id == 'UgKr2c2ZebM':
        creator = 'Sarah Schachner, Jesper Kyd'
        source = 'https://news.ubisoft.com/en-us/article/6YhFPGYjNKgOBr3SnFVBfP/assassins-creed-valhalla-composers-reveal-how-they-created-the-main-theme'
    key = norm(title)
    if key in seen:
        excluded.append({'youtube_id':video_id,'reason':'Duplicate named selection from another official EP/expanded album.'})
        continue
    seen.add(key)
    released = re.search(r'Released on: (\d{4})',desc)
    year = int(released[1]) if released else 2020
    album = next((s for s in desc.splitlines() if s.startswith("Assassin's Creed Valhalla:") and 'Soundtrack)' in s), None)
    version = 'Assassin\'s Creed Valhalla original score publication: '+(album or 'original 2020 label music video')+'. This named release is distinct from Dawn of Ragnarök or another game.'
    item = track(row,title,creator,source,version,year)
    if '(feat. Einar Selvik)' in title:
        item['additional_recording_roles'] = {'featured_artist':['Einar Selvik']}
    ac_tracks.append(item)
assert full
pub = full['publication']
markers=[]
for line in pub['shortDescription'].splitlines():
    m=re.match(r'^\d+\.\s+(.+?) - (Max Aruj|Einar Selvik) (\d+:\d{2})$',line)
    if m:
        minutes,seconds=map(int,m[3].split(':'))
        markers.append({'title':m[1],'composer':m[2],'start':minutes*60+seconds,'line':line})
assert len(markers)==18
for index,marker in enumerate(markers):
    end=markers[index+1]['start'] if index+1<len(markers) else float(pub['lengthSeconds'])
    assert 0<=marker['start']<end<=float(pub['lengthSeconds'])
    item=track(full,marker['title'],marker['composer'],wrath_source,
        "Assassin's Creed Valhalla: Wrath of the Druids, official 2021 expansion album. Label's actual individually indexed album passage, not attributed to the 2020 base score.",2021)
    item.update(start_seconds=marker['start'],end_seconds=end,duration_seconds=end-marker['start'],
        source_actual_chapter_line=marker['line'],source_publication_duration_seconds=float(pub['lengthSeconds']))
    if 'Julie Fowlis' in marker['title'] and 'Instrumental' not in marker['title']:
        item['additional_recording_roles']={'featured_vocals':['Julie Fowlis']}
    ac_tracks.append(item)

disco_original=load(source_paths[1])
disco_recovered={r['source']['id']:r for r in load(source_paths[2])['tracks'] if r['status']=='metadata_candidate'}
disco_tracks=[]
for original in sorted(disco_original['tracks'],key=lambda r:r['source_playlist_position']):
    row=original if original['status']=='metadata_candidate' else disco_recovered.get(original['source']['id'])
    if not row:
        continue
    pub=row['publication']
    assert pub['author'] in ['Sea Power','Sea Power - Topic']
    assert 'Remix' not in pub['title'] and pub['title']!='Unreleased'
    item=track(row,pub['title'],'Sea Power',disco_source,
        'Original Disco Elysium soundtrack, artist-issued 2020 album publication. British Sea Power is the group now named Sea Power; no inferred new performer or recreated score.',2020)
    item['artist_credit_scope']='Original artist Bandcamp credits the band collectively and explicitly documents British Sea Power now trading as Sea Power. Individual band-member cue authorship is not separately inferred.'
    disco_tracks.append(item)
assert len(disco_tracks)==27

entries=[]
for entry_id,name,year,composer,tracks,scope in [
    ('wikipedia-63809881',"Assassin's Creed Valhalla",2020,"Assassin's Creed Valhalla music team",ac_tracks,'Available original official base-score/EP/expanded-score recordings plus the 18-track official Wrath of the Druids expansion album. Repeated named selections omitted; not every later DLC or complete base game master inventory.'),
    ('workbook-10-15-disco-elysium','Disco Elysium',2019,'Sea Power',disco_tracks,'27 available original artist album publications; one currently unresolved native recording and later added Bandcamp bonus selections are not declared absent from the score.')]:
    entries.append({'entry_id':entry_id,'match_title':name,'match_year':year,'title':'Listen to '+name,
        'composer':composer,'curator_note':'Listen to the music of '+composer+'\n'+name,
        'replace_existing_tracks':True,'full_album_collection':False,'coverage_status':'partial',
        'recording_collection_scope':scope,'album_completeness':{'verified_available_tracks':len(tracks),'scope':scope},'tracks':tracks})
primary=OUT/'valhalla-disco-primary-web-read-receipt.json'
primary.write_text(json.dumps({'actual_web_pages_read':[
    {'url':base_source,'context':'Ubisoft distinguishes composers Kyd/Schachner and original songwriter Selvik.'},
    {'url':wrath_source,'context':'Lakeshore-hosted artist album labels all18 individual selections by Max Aruj or Einar Selvik and identifies the2021 expansion.'},
    {'url':'https://assassinscreedvalhalla.bandcamp.com/album/assassins-creed-valhalla-twilight-of-the-gods','context':'Original expanded score by Sarah Schachner, not the later Dawn of Ragnarok expansion.'},
    {'url':'https://assassinscreedvalhalla.bandcamp.com/album/assassin-s-creed-valhalla-sons-of-the-great-north','context':'Original expanded score by Jesper Kyd.'},
    {'url':disco_source,'context':'Original artist album and British Sea Power/Sea Power identity explicitly stated; collective group credit, not a cue-by-cue individual roster.'}],
    'local_fetch_rejected':'acvalhalla-wrath-rejected-client-challenge.html is a challenge body, not claimed actual primary HTML. Actual web-rendered page was read instead.',
    'scope':'Public metadata/source editorial verification only; no listening, audio fingerprinting or physical PS5 playback.'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
source_paths.append(primary)
target=OUT/'valhalla-disco-available-public-candidate.json'
assert not target.exists()
target.write_text(json.dumps({'schema_version':1,'publication_status':'awaiting_independent_peer','entries':entries,
    'excluded_duplicate_or_montage_records':excluded,'source_receipts':[{'local_path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in source_paths]},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'candidate':target.relative_to(ROOT).as_posix(),'sha256':sha(target),'tracks_per_game':[len(e['tracks']) for e in entries]}))
