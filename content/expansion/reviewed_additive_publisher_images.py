"""Append independently reviewed original publisher images; never edit prose."""
import copy,hashlib,json
import runpy
from pathlib import Path
from PIL import Image

def apply(entries, root):
    root=Path(root);manifest=root/'content/expansion/museum-additive-publisher-images-reviewed.json'
    if not manifest.exists():return {'status':'not_admitted'}
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    owners={entry['id']:entry for entry in entries};added=[]
    excluded=runpy.run_path(str(root/'content/expansion/user_sports_policy.py'))['excluded_ids'](root)
    for batch in json.loads(manifest.read_text(encoding='utf8'))['batches']:
        cp=root/batch['candidate_path'];pp=root/batch['peer_path']
        assert sha(cp)==batch['candidate_sha256'] and sha(pp)==batch['peer_sha256']
        candidate=json.loads(cp.read_text(encoding='utf8'));peer=json.loads(pp.read_text(encoding='utf8'))
        assert candidate['status']=='ADDITIVE_IMAGE_ONLY_REVIEW_PLAN'
        assert peer['status'].startswith('PASS') and peer['candidate_sha256']==batch['candidate_sha256']
        for source in candidate['source_files']:assert sha(root/source['path'])==source['sha256']
        for binding in candidate['bindings']:
            if binding['entry_id'] not in owners and binding['entry_id'] in excluded:continue
            entry=owners[binding['entry_id']];body_bytes=json.dumps(entry['body'],ensure_ascii=False,separators=(',',':')).encode('utf8')
            assert hashlib.sha256(body_bytes).hexdigest()==binding['body_sha256']
            image=binding['image'];assert 0<=image['story_paragraph']<len(entry['body'])
            assert image['kind'] in {'gameplay','publisher-game-image'} and sha(root/image['recovery_local_source'])==image['verification']['sha256']
            with Image.open(root/image['recovery_local_source']) as picture:assert picture.size==(image['width'],image['height'])
            existing=[old for old in entry['images'] if old['url']==image['url']]
            if existing:
                assert len(existing)==1
                old=existing[0]
                assert old.get('story_paragraph')==image['story_paragraph']
                assert (old['width'],old['height'])==(image['width'],image['height'])
                assert old.get('verification',{}).get('sha256')==image['verification']['sha256']
                assert old is not entry['images'][entry.get('preferred_image',0)]
                assert old.get('kind')!='video-poster'
                continue
            entry['images'].append(copy.deepcopy(image))
            added.append({'entry_id':entry['id'],'image_url':image['url'],'story_paragraph':image['story_paragraph']})
    return {'status':'PASS_ADDITIVE_IMAGES_ONLY_ALL_PROSE_PRESERVED','added':added}
