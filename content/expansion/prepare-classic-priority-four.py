"""Research-only curated original game recordings; never assembles runtime content."""
import json, hashlib, importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
B=R/'build/research/soundtrack-broad'
D=B/'user-priority/classic-extra'
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
p=module('pipeline',R/'content/expansion/soundtrack-broad-pipeline.py')
v=module('discovery',R/'tools/discover-museum-videos.py')
catalog=json.loads((R/'content/catalog.json').read_text(encoding='utf-8'))
catalog=catalog if isinstance(catalog,list) else catalog['entries']
add=json.loads((R/'content/expansion/user-requested-game-additions.json').read_text(encoding='utf-8'))['entries']
ids={(p.norm(e['title']),e['year']):e['id'] for e in catalog+add}
booklet='https://www.squareenixmusic.com/albums/v/viewtifuljoe.shtml'
groups=[
 ('Ape Escape',1999,'Soichi Terada','https://en.wikipedia.org/wiki/Ape_Escape_(video_game)',
  'https://daily.redbullmusicacademy.com/2017/10/soichi-terada-interview/',
  'Original 1999 PS1 game score; credited archival recording.',
  [('K7_JMWnC64g','Hot Spring'),('kP48ndIylv4','Sushi Temple'),('tz9J1yyU8XQ','Snowy Mammoth')]),
 ('Fantavision',2000,'Ashif Hakik','https://en.wikipedia.org/wiki/Fantavision_(video_game)',
  'https://www.mobygames.com/game/3827/fantavision/credits/ps2/',
  'Original North American 2000 PS2 soundtrack; credited archival recording. Other regions use different scores.',
  [('iFisJiUAd8c','Into Space — Stage 3'),('GWExQ7szPaM','Snow on the Moon — Stage 6')]),
 ('Viewtiful Joe',2003,'Masakazu Sugimori','https://en.wikipedia.org/wiki/Viewtiful_Joe_(video_game)',booklet,
  'Original first-game score; archival game-length cue. Not claimed identical to the longer soundtrack-album master.',
  [('uoz_QiZQpsQ','Joe the Hero'),('erbcvbwrST8','Some Like It Red Hot')]),
 ('Viewtiful Joe 2',2004,'Sayaka Morita','https://en.wikipedia.org/wiki/Viewtiful_Joe_2',booklet,
  'Original 2004 game score; credited archival recording. Cue authorship follows the original two-game album credit transcription.',
  [('OuNPduAfsHg','Ice Edge — Polar Movie Land'),('0vNVOGKgMZI','Ten Million Years B.C.')]),
]
entries=[];audit=[]
for game,year,composer,wiki,credit,version,rows in groups:
    eid=ids.get((p.norm(game),year))
    if not eid:
        print('ARTICLE_HOLD',game,flush=True);continue
    tracks=[]
    for vid,title in rows:
        actual=p.watch(vid)
        row={'game':game,'youtube_id':vid,'title':title,'creator':composer,
             'actual_title':actual['title'],'uploader':actual['author']}
        try:
            codec=v.metadata(vid,{'title':actual['title'],'channel':actual['author']})
            assert codec.get('native_compatible_avc_aac')
        except Exception as ex:
            row.update(status='CODEC_HOLD',reason=str(ex));audit.append(row);continue
        tracks.append({'youtube_id':vid,'url':'https://www.youtube.com/watch?v='+vid,
            'title':title,'creator':composer,'composer_source':wiki,
            'additional_role_credit_source':credit,'recording_context_source':wiki,
            'recording_version':version,'uploader':actual['author'],
            'channel_url':'https://www.youtube.com/channel/'+actual['channelId'],
            'source_page':'https://www.youtube.com/watch?v='+vid,
            'official_uploader_verified':False,'publishing_kind':'credited_archival_game_recording',
            'duration_seconds':int(actual['lengthSeconds']),
            'rights':'Composition and recording rights remain with the original game publishers, named composers and relevant recording owners.',
            'verification_receipt':'build/research/soundtrack-broad/watch/'+vid+'.json',
            'native_codec_metadata_receipt':'build/research/video-discovery/video-'+vid+'.json',
            'native_codec_metadata_verified':True,'playback_verified_on_ps5':False})
        row['status']='CANDIDATE_PENDING_INDEPENDENT_REVIEW';audit.append(row)
        print(game,title,'AVC_AAC',flush=True)
    if tracks:
        entries.append({'entry_id':eid,'match_title':game,'match_year':year,
            'title':'Listen to '+game,'composer':composer,
            'curator_note':'Listen to music from '+game+'.','tracks':tracks})
f=D/'classic-four-games9-candidate.json'
f.write_text(json.dumps({'publication_status':'awaiting_independent_exact_role_review',
    'scope':'Four original games, distinct regional Fantavision score, individually mapped Viewtiful Joe album credits. Metadata/source review, not audio fingerprint or PS5 playback.',
    'entries':entries},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(D/'classic-nine-editorial-review.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('FINAL',len(entries),sum(len(e['tracks']) for e in entries),hashlib.sha256(f.read_bytes()).hexdigest(),flush=True)
