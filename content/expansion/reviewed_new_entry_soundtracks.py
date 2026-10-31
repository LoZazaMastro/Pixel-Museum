"""Attach reviewed soundtrack overrides after independently admitted new entries exist."""
import copy,json,re,unicodedata
from pathlib import Path

def apply(entries, root):
    root=Path(root)
    plan=json.loads((root/'content/expansion/museum-complete-new-entries-reviewed.json').read_text(encoding='utf8'))
    allowed={identifier for batch in plan['batches'] for identifier in batch['approved_entry_ids']}
    source=json.loads((root/'content/expansion/soundtrack-multitrack-priority-overrides.json').read_text(encoding='utf8'))
    if source.get('publication_status')!='validated':return {'status':'not_admitted'}
    key=lambda value:re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',value).encode('ascii','ignore').decode().lower())
    by_id={entry['id']:entry for entry in entries};attached=[]
    for selection in source['entries']:
        identifier=selection.get('entry_id')
        if identifier not in allowed:continue
        target=by_id[identifier]
        assert target['year']==selection['match_year'] and key(target['title'])==key(selection['match_title'])
        assert not target.get('soundtrack_rooms'), 'Multiple listening rooms require their own reviewed join'
        assert not selection.get('append_existing_tracks'), 'New-entry append collections require explicit review'
        room={name:copy.deepcopy(selection[name]) for name in ['title','composer','curator_note','tracks']}
        for name in ['full_album_collection','coverage_status','completeness','album_completeness','recording_collection_scope','independent_review_receipt','music_kind']:
            if name in selection:room[name]=copy.deepcopy(selection[name])
        target['soundtrack']=room
        sources=target.setdefault('sources',[]);known={item['url'] for item in sources}
        for item in selection.get('sources',[]):
            if item['url'] not in known:sources.append(copy.deepcopy(item));known.add(item['url'])
        for track in selection['tracks']:
            if track['source_page'] not in known:
                sources.append({'title':'Soundtrack publication: '+track['title'],'url':track['source_page'],'publisher':track['uploader'],'attribution':'Original recording rights retained; streamed from its original publication.'});known.add(track['source_page'])
        attached.append({'entry_id':identifier,'tracks':len(room['tracks']),'coverage_status':room.get('coverage_status')})
    return {'status':'PASS_SOUNDTRACKS_ONLY_ON_REVIEWED_NEW_ENTRIES','attached':attached}
