"""Mechanical integrity only; independent source/credit peer remains required."""
from pathlib import Path
import hashlib,json,re
P=Path(__file__).resolve().parents[1]/'build/research/soundtrack-broad/yakuza-zero-public-collection'
ROOT=P.parents[3]
def load(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=P/'yakuza-zero-88-public-chapters-candidate.json'
new=P/'yakuza-zero-91-public-passages-vocal-extended-candidate.json'
assert sha(old)=='1d1080ae01a1cf660af4f1e27305c597d1845fe8ad20086fed2b9869cb3e6021'
a,b=load(old),load(new)
before=a['entries'][0]['tracks'];after=b['entries'][0]['tracks']
changes=[]
for i,(o,n) in enumerate(zip(before,after)):
 delta={k:[o.get(k),n.get(k)] for k in set(o)|set(n) if o.get(k)!=n.get(k)}
 if delta:changes.append({'index':i,'changed':delta})
assert len(changes)==1 and changes[0]['changed']=={'title':['Fatal Confrict','Fatal Conflict']}
watch=load(ROOT/'build/research/soundtrack-broad/watch/p025z6l57Z0.json')
description=watch['shortDescription']
for t in after[-3:]:
 assert t['source_actual_chapter_line'] in description
 assert 0<=t['start_seconds']<t['end_seconds']<=int(watch['lengthSeconds'])
 assert t['duration_seconds']==t['end_seconds']-t['start_seconds']
 assert t['youtube_id']=='p025z6l57Z0' and t['native_codec_metadata_verified'] and not t['playback_verified_on_ps5']
 assert '  ' not in t['recording_version'] and re.search(r'\b2015\b',t['recording_version'])
assert len(after)==91 and len({(t['youtube_id'],t['start_seconds'],t['end_seconds']) for t in after})==91
report={'status':'PASS_MECHANICAL_ONLY_SOURCE_PEER_PENDING','candidate_sha256':sha(new),'parent_88_sha256':sha(old),
 'preserved_old_tracks':88,'old_track_changes':changes,'new_vocal_passages':after[-3:],
 'identical_native_source_and_exact_actual_description_chapter_lines':True,
 'no_master_or_source71_mutation':True,'no_audio_video_download':True,
 'limits':['This verifies mechanical preservation/bounds only. Independent reading of the three source/credit decisions is still required.']}
out=P/'vocal-extension-mechanical-integrity.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(out,sha(out))
