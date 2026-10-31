"""Explicit native 480px fallback applies only to reviewed linked-film posters."""
import json,runpy
from pathlib import Path

def apply(entries, root):
    root=Path(root);path=root/'content/expansion/museum-native-hq-film-posters-reviewed.json'
    if not path.exists():return {'status':'not_admitted'}
    core=runpy.run_path(str(root/'content/expansion/reviewed_original_video_posters.py'))
    results=[]
    for batch in json.loads(path.read_text(encoding='utf8'))['batches']:
        cp=root/batch['candidate_path'];pp=root/batch['peer_path']
        assert core['digest_file'](cp)==batch['candidate_sha256'] and core['digest_file'](pp)==batch['peer_sha256']
        candidate=json.loads(cp.read_text(encoding='utf8'));peer=json.loads(pp.read_text(encoding='utf8'))
        assert peer['status'].startswith('PASS') and peer['candidate_sha256']==batch['candidate_sha256']
        assert candidate['native_thumbnail_minimum_width']==480
        assert core['digest_file'](root/candidate['source_report_path'])==candidate['source_report_sha256']
        for row in candidate['rows']:
            image=row['new_poster'];assert image['kind']=='video-poster' and image['story_paragraph']==-1
            assert image['url']==f"https://i.ytimg.com/vi/{row['youtube_id']}/hqdefault.jpg"
        results.append(core['apply_candidate'](entries,root,candidate,minimum_width=480))
    return {'status':'PASS_REVIEWED_NATIVE_FILM_PREVIEWS_ONLY','batches':results}
