"""Publish human-reviewed person labels only against their exact English fields."""
import copy,hashlib,json
from pathlib import Path

def load(root,owners):
    result={lang:{}for lang in ['it','fr','de','es']}
    for name in ['human-history-person-events-reviewed-locales.json','catalog-person-event-labels-reviewed-locales.json']:
        path=Path(root)/'content/expansion'/name
        if not path.exists():continue
        policy=json.loads(path.read_text(encoding='utf-8'))
        if policy.get('status')not in ['ROOT_REVIEWED_FOUR_LANGUAGE_PERSON_EVENT_TEXT','ROOT_REVIEWED_FOUR_LANGUAGE_PERSON_EVENT_LABELS']:raise ValueError('Unreviewed person-event locales')
        for lang,rows in policy['entries'].items():
            for identity,row in rows.items():
                fields=owners[identity]
                binding=hashlib.sha256(json.dumps(fields,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
                if row['provenance']['source_fields_sha256']!=binding:raise ValueError('Person-event locale source drift: '+identity)
                tr=copy.deepcopy(row)
                for f in ['title','subtitle','summary','body','story_headings']:
                    if f not in tr:tr[f]=copy.deepcopy(fields[f])
                    if isinstance(fields[f],list)and len(fields[f])!=len(tr[f]):raise ValueError('Person-event locale paragraph drift: '+identity)
                tr['provenance'].setdefault('english_fallback_units',[])
                tr['provenance'].setdefault('source_units',[dict(field=f,index=i,mode='root_reviewed_person_event_text')for f in fields for i,_ in enumerate(fields[f]if isinstance(fields[f],list)else[fields[f]])])
                result[lang][identity]=tr
    return result
