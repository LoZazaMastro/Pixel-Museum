"""Resume public metadata for original Wii U recordings; never downloads media."""
import importlib.util, json, re, time, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
F=ROOT/'build/research/soundtrack-broad/splatoon-original-2015'
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
music=module('splatoon_music','content/expansion/soundtrack-broad-pipeline.py')
video=module('splatoon_video','tools/discover-museum-videos.py')
playlist=json.loads((F/'playlist-original-flat.json').read_text('utf-8'))
file=F/'individual-publication-research.json'
old=json.loads(file.read_text('utf-8')) if file.exists() else {'records':[]}
records={r['youtube_id']:r for r in old['records']}
excluded=[]
for row in playlist['entries']:
    title=row.get('title','');id=row.get('id','')
    if re.search(r'\bLIVE\b|\bExtended\b',title,re.I):
        excluded.append({'youtube_id':id,'title':title,'reason':'Live performance or extended version excluded from original game collection.'});continue
    if id in records:continue
    result={'youtube_id':id,'playlist_title':title,'status':'held'}
    try:
        watch=music.watch(id)
        if re.search(r'\b(?:remix|cover|remaster|Splatoon\s*[23])\b',watch['title'],re.I):
            raise ValueError('Different version or game in actual publication title')
        if not re.search(r'Splatoon',watch['title'],re.I):raise ValueError('Original game not named by actual publication')
        native=video.metadata(id,row)
        result.update(status='metadata_verified_pending_semantic_peer',title=watch['title'],uploader=watch['author'],channel_id=watch['channelId'],duration_seconds=float(watch['lengthSeconds']),
            watch_receipt='build/research/soundtrack-broad/watch/'+id+'.json',
            native_metadata_receipt='build/research/video-discovery/video-'+id+'.json',
            native_avc_aac=native.get('native_compatible_avc_aac'),
            watch_sha256=hashlib.sha256((music.RESEARCH/'watch'/f'{id}.json').read_bytes()).hexdigest())
    except Exception as error:result['reason']=str(error)
    records[id]=result
    out={'status':'research_only_not_admitted','scope':'Original2015 Wii U game collection; public archive metadata, not official label publication or audio fingerprint verification. Playlist differs from61-track retail Splatune; no completeness claim.',
         'playlist_id':playlist.get('id'),'records':list(records.values()),'excluded':excluded}
    music.write(file,out)
    print(result['status'],title,result.get('duration_seconds',''),flush=True)
    time.sleep(.9)
print('FINISHED',len(records),'EXCLUDED',len(excluded),flush=True)
