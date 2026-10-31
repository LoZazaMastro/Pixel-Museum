"""Keep birth dates distinct from the project dates in reviewed person entries."""
import copy,json
from pathlib import Path

def apply(entries,root):
    policy=json.loads((Path(root)/'content/expansion/catalog-person-event-labels-reviewed.json').read_text(encoding='utf-8'))
    if policy.get('status')!='ROOT_REVIEWED_PERSON_EVENT_LABELS':raise ValueError('Unreviewed person labels')
    owners={e['id']:e for e in entries};changed=[]
    for row in policy['entries']:
        e=owners[row['id']]
        if e['year']!=row['year']or e['date']!=row['date']:raise ValueError('Person date drift: '+row['id'])
        current={f:e.get(f,[]if f in ['body','story_headings']else'')for f in row['after_text']}
        if current not in [row['before_text'],row['after_text']]:raise ValueError('Person label text drift: '+row['id'])
        if current!=row['after_text']:changed.append(row['id'])
        e.update(copy.deepcopy(row['after_text']))
    return dict(status='PASS',owners=len(policy['entries']),changed=changed,dates_media_and_other_fields_untouched=True)
