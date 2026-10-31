"""Resumable public metadata-only batch; failed native attempts remain explicit holds."""
import importlib.util
import json
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'build/research/soundtrack-broad/modern-public-albums'
mods={}
for name,filename in [('p','content/expansion/soundtrack-broad-pipeline.py'),('v','tools/discover-museum-videos.py')]:
    spec=importlib.util.spec_from_file_location(name,ROOT/filename)
    mods[name]=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mods[name])
for video_id in sys.argv[1:]:
    target=OUT/(video_id+'-actual-publication-research.json')
    if target.exists():
        record=json.loads(target.read_text(encoding='utf8'))
    else:
        record={'youtube_id':video_id,'publication_status':'research_hold'}
        try:
            pub=mods['p'].watch(video_id)
            record['publication']=pub
            native=mods['v'].metadata(video_id,{'title':pub['title'],'channel':pub['author']})
            record.update(publication_status='metadata_candidate',native_avc_aac=native.get('native_compatible_avc_aac'),
                native_codec_receipt='build/research/video-discovery/video-'+video_id+'.json')
        except Exception as error:
            record['error']=str(error)
            native_path=ROOT/('build/research/video-discovery/video-'+video_id+'.json')
            if native_path.exists():
                native=json.loads(native_path.read_text(encoding='utf8'))
                record['native_avc_aac']=native.get('native_compatible_avc_aac')
                record['native_codec_receipt']=native_path.relative_to(ROOT).as_posix()
        mods['p'].write(target,record)
    pub=record.get('publication',{})
    print(json.dumps({'id':video_id,'title':pub.get('title'),'author':pub.get('author'),
        'duration':pub.get('lengthSeconds'),'native':record.get('native_avc_aac'),'error':record.get('error'),
        'description_excerpt':pub.get('shortDescription','')[:900]},ensure_ascii=False),flush=True)
