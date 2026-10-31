"""Exact paragraph bindings for individually reviewed historical photographs."""
import copy,json
from pathlib import Path

def apply(entries,root):
    path=Path(root)/'content/expansion/museum-story-illustrations-editorial-reviewed.json'
    if not path.is_file():return {'status':'not_available'}
    doc=json.loads(path.read_text(encoding='utf8'))
    if doc.get('publication_status')!='independently_visually_reviewed':return {'status':'not_admitted'}
    owners={}
    for entry in entries:
        owners[entry['id']]=entry
        for feature in entry.get('editorial_features',[]):owners[feature['id']]=feature
    admitted=[]
    for identifier,records in doc.get('entries',{}).items():
        owner=owners.get(identifier)
        if owner is None:continue
        photos=owner.setdefault('images',[])
        for image in photos:
            if image.get('url')in doc.get('clear_story_associations',{}).get(identifier,[]):image['story_paragraph']=-1
        preferred_url=photos[min(owner.get('preferred_image',0),len(photos)-1)]['url']if photos else None
        for record in records:
            index=record['story_paragraph']
            if not isinstance(index,int)or not 0<=index<len(owner.get('body',[])):raise ValueError('Reviewed image paragraph is invalid: '+identifier)
            if record['url']==preferred_url and owner.get('kind')=='person':raise ValueError('Person cover must not be repeated as story image: '+identifier)
            old=next((image for image in photos if image['url']==record['url']),None)
            if old is None:photos.append(copy.deepcopy(record))
            else:old.update(copy.deepcopy(record))
            admitted.append({'entry_id':identifier,'story_paragraph':index,'url':record['url']})
        owner['explicit_story_media_only']=True
        if preferred_url:owner['preferred_image']=next(n for n,image in enumerate(photos)if image['url']==preferred_url)
        elif photos:owner['preferred_image']=0
    return {'status':'PASS','associations':admitted}
