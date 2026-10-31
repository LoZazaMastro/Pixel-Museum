"""Restore the reviewed event photograph, independently of the rejected pre-event skyline."""
from pathlib import Path
import copy
import hashlib
import json


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def apply(entries, root):
    root = Path(root)
    plan = json.loads((root / 'content/expansion/human-history-september11-reviewed.json').read_text(encoding='utf8'))
    entry = plan['entry']
    provenance = entry['provenance']
    archived = json.loads((root / provenance['source_receipt']).read_text(encoding='utf8'))['September 11 attacks']
    if (plan.get('status') != 'reviewed_historic_milestone' or
            archived['revisions'][0]['revid'] != provenance['revision'] or
            hashlib.sha256(archived['extract'].encode()).hexdigest() != plan['archived_source_sha256'] or
            not all(fragment in archived['extract'] for fragment in plan['text_fragments'])):
        raise ValueError('September11 archived text or revision drift')
    if digest(root / plan['commons_page_path']) != plan['commons_page_sha256']:
        raise ValueError('September11 image-rights receipt drift')
    image = entry['images'][0]
    if digest(root / image['recovery_local_source']) != image['verification']['sha256']:
        raise ValueError('September11 original event photograph drift')
    if digest(root / plan['peer_path']) != plan['peer_sha256']:
        raise ValueError('September11 independent review changed')
    peer = json.loads((root / plan['peer_path']).read_text(encoding='utf8'))
    if (peer.get('status') != 'PASS' or peer.get('image_sha256') != image['verification']['sha256'] or
            peer.get('source_revision') != provenance['revision'] or peer.get('date') != '2001-09-11'):
        raise ValueError('September11 independent source/date review mismatch')
    matches = [current for current in entries if current.get('id') == entry['id']]
    if len(matches) > 1:
        raise ValueError('Duplicate September11 milestone')
    if matches:
        if matches[0] != entry:
            raise ValueError('September11 milestone already differs; review before replacing it')
        changed = False
    else:
        entries.append(copy.deepcopy(entry))
        changed = True
    entries.sort(key=lambda row: (row['year'], row.get('date', {}).get('month', 0),
                                  row.get('date', {}).get('day', 0), row['id']))
    return {'status': 'PASS', 'entry_id': entry['id'], 'added': changed,
            'date': '2001-09-11', 'source_revision': provenance['revision']}
