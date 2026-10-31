"""Freeze the completely reconciled136-cue original-game album selection."""
import copy,hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'build/research/soundtrack-broad/nintendo-full'
research=json.loads((OUT/'odyssey136-individual-publication-research.json').read_text())['tracks'];assert len(research)==136
alternatives={r['track_number']:r for r in json.loads((OUT/'odyssey-five-alternate-publications.json').read_text())}
expected=json.loads((OUT/'odyssey-nintendo-music-inventory.json').read_text())['media'][0]['tracks'];assert len(expected)==136
booklet_index=json.loads((OUT/'odyssey-original-booklet-image-index.json').read_text())
credits_image=next(i for i in booklet_index['images']if i['id']==21038808833)['image']
team_image=next(i for i in booklet_index['images']if i['id']==21038806949)['image']
sources=[]
for name in ['odyssey-label-actual.html','odyssey-cd-english-inventory.json','odyssey-nintendo-music-inventory.json','odyssey-booklet-21038808833.jpg','odyssey-booklet-21038806949.jpg']:
 path=OUT/name;sources.append({'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'actually_read':True})
tracks=[];audit=[]
for r,inventory in zip(research,expected):
 n=r['album_track_number'];assert n==inventory['position']
 if r['status']=='hold':
  alt=alternatives[n];assert alt['ok'];w=alt['publication'];id=alt['id'];codec=alt['native_receipt']
 else:w=r['publication'];id=r['candidate_id'];codec=r['native_codec_receipt'];assert r['native_compatible_avc_aac']
 meta=json.loads((ROOT/codec).read_text());assert meta['native_compatible_avc_aac']
 assert abs(float(w['lengthSeconds'])-inventory['length']/1000)<=4,(n,w['lengthSeconds'],inventory['length'])
 t={'youtube_id':id,'url':'https://www.youtube.com/watch?v='+id,'source_page':'https://www.youtube.com/watch?v='+id,'title':inventory['title'],'creator':'Nintendo sound team','composer_source':team_image,'album_track_number':n,'recording_album':'Super Mario Odyssey — complete original-game136-track collection','album_inventory_source':'https://bzone.co.jp/site/mario_ost/','localized_inventory_source':'https://musicbrainz.org/release/0cae19d6-3b6b-46a3-a9fd-78da0297be14','recording_version':'Archival original-game score recording, individually matched to the136-cue Nintendo Music inventory. Original2017game; actual capture hardware/mastering identity not independently established.','uploader':w['author'],'channel_url':'https://www.youtube.com/channel/'+w['channelId'],'official_uploader_verified':False,'publishing_kind':'archival_game_recording','duration_seconds':float(w['lengthSeconds']),'artist_credit_scope':'Nintendo sound team is an honest collective game/album-level credit. Individual cue authorship is not separately documented here; the full composer roster is not assigned to each cue.','game_score_composers':['Naoto Kubo','Shiho Fujii','Koji Kondo'],'rights':'Original music and recording rights retained by Nintendo and credited authors; the archival upload is not an official Nintendo publication.','primary_published_title':w['title'],'native_codec_metadata_verified':True,'native_codec_metadata_receipt':codec,'publication_metadata_receipt':f'build/research/soundtrack-broad/watch/{id}.json','playback_verified_on_ps5':False}
 if n in [122,130,132,135]:
  japanese=n in [132,135]
  t.update(creator='Naoto Kubo',composer_source=credits_image,artist_credit_scope='Individual song composition and vocal/lyric roles read directly from the original publisher-printed CD booklet. The English credit names Kate Davis; no unverified alias is substituted.')
  t['additional_recording_roles']={'vocals':['Aimi Mukohara'if japanese else'Kate Davis'],'lyrics':['Nobuyoshi Suzuki']if japanese else['Rob Tunstall','Nobuyoshi Suzuki']}
  if n in [130,132]:t['additional_recording_roles']['arrangement']=['Yoichi Murata'];t['arrangement_source']=team_image
 tracks.append(t)
 audit.append({'track':n,'title':inventory['title'],'youtube_id':id,'actual_watch_metadata_read':True,'description_was_available':bool(w['shortDescription']),'archive_expected_seconds':inventory['length']/1000,'actual_video_seconds':float(w['lengthSeconds']),'title_match':'Exact localized title after punctuation and numbering normalization, or explicitly reviewed same-cue CD-name alias for five alternatives.','native_avc_aac':True,'alternate_original_upload':r['status']=='hold'})
assert len({t['youtube_id']for t in tracks})==136
out={'schema_version':1,'publication_status':'awaiting_independent_review','entries':[{'entry_id':'workbook-10-27-super-mario-odyssey','match_title':'Super Mario Odyssey','match_year':2017,'title':'Listen to Super Mario Odyssey','composer':'Nintendo sound team','curator_note':'Listen to the music of Nintendo sound team\nSuper Mario Odyssey','replace_existing_tracks':True,'full_album_collection':True,'album_completeness':{'expected_tracks':136,'source':'Publisher original136-track album plus Nintendo Music localized inventory; actual public individual recordings, no whole-album shortcut.','inventory_receipt':'build/research/soundtrack-broad/nintendo-full/odyssey136-complete-editorial-review.json'},'tracks':tracks}],'validation_scope':'Metadata identity, exact136-cue inventory mapping, original printed booklet song roles, and136positive nativeAVC/AAC receipts. Archival uploads retain uploader credit; no listening/audio-fingerprint/physicalPS5playback claim.'}
dest=OUT/'odyssey-complete136-candidate.json';dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
review={'status':'awaiting_independent_review','candidate':dest.relative_to(ROOT).as_posix(),'candidate_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'expected_tracks':136,'verified_metadata_tracks':136,'missing_tracks':0,'primary_sources':sources,'printed_booklet_observations':{'team_commentary':'Composer Naoto Kubo states music creation together with Koji Kondo and Shiho Fujii.','song_credits':'Left red credit spread: JumpUp/BreakFree composerNaotoKubo; EnglishKateDavis/JapaneseAimiMukohara vocals; EnglishRobTunstall+NobuyoshiSuzuki/JapaneseSuzuki lyrics. Kubo commentary explicitly calls YoichiMurata arrangements of CD3tracks26/27.'},'tracks':audit}
(OUT/'odyssey136-complete-editorial-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('FREEZE136',review['candidate_sha256'])
