"""Preserve the reviewed event behind each cultural person's timeline date."""
import copy
import json
from pathlib import Path

def apply(entries,root):
    policy=json.loads((Path(root)/'content/expansion/human-history-person-events-reviewed.json').read_text(encoding='utf-8'))
    if policy.get('status')!='ROOT_REVIEWED_PERSON_EVENT_TEXT':raise ValueError('Unreviewed person-event policy')
    owners={e['id']:e for e in entries};changed=[]
    for row in policy['entries']:
        e=owners[row['id']]
        if e['year']!=row['year'] or e['date']!=row['date']:raise ValueError('Person event date drift: '+row['id'])
        current={field:e.get(field,[] if field in ['body','story_headings'] else '') for field in row['after_text']}
        if current not in [row['before_text'],row['after_text']]:raise ValueError('Person event text drift: '+row['id'])
        if current!=row['after_text']:changed.append(row['id'])
        e.update(copy.deepcopy(row['after_text']))
        existing={source.get('url')for source in e.get('sources',[])}
        e.setdefault('sources',[]).extend(copy.deepcopy(source)for source in row['verified_sources']if source.get('url')not in existing)
        e.setdefault('provenance',{})['person_event_clarification']=copy.deepcopy(row['event_provenance'])
    return {'status':'PASS','reviewed_owners':len(policy['entries']),'changed':changed,'date_and_media_untouched':True}
