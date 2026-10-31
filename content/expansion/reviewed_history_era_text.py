"""Keep the 2006 milestone on Twitter's founding, with its archived sources intact."""
import copy
import hashlib
import json
from pathlib import Path


def apply(entries, root):
    path = Path(root) / 'content/expansion/human-history-twitter-2006-era-text.json'
    selection = json.loads(path.read_text(encoding='utf8'))
    if selection.get('status') != 'reviewed_historic_source_selection':
        raise ValueError('Unreviewed historic Twitter text selection')
    matches = [entry for entry in entries if entry.get('id') == selection['entry_id']]
    if len(matches) != 1:
        raise ValueError('Expected exactly one historic Twitter milestone')
    entry = matches[0]
    provenance = entry.get('provenance', {})
    source = provenance.get('full_source_extract', '')
    if (entry.get('year') != selection['year'] or
            provenance.get('revision') != selection['revision'] or
            provenance.get('seed_title') != 'Twitter' or
            hashlib.sha256(source.encode()).hexdigest() != selection['full_source_extract_sha256'] or
            not all(fragment in source for fragment in selection['source_fragments'])):
        raise ValueError('Historic Twitter archived source drift; review the new source first')
    for field, previous in selection['old_display_fields'].items():
        if entry.get(field) not in (previous, selection['new_display_fields'][field]):
            raise ValueError('Historic Twitter display drift: ' + field)
    changed = any(entry.get(field) != value for field, value in selection['new_display_fields'].items())
    entry.update(copy.deepcopy(selection['new_display_fields']))
    return {'status': 'PASS', 'entry_id': entry['id'], 'changed': changed,
            'source_revision': selection['revision'], 'images_sources_and_provenance_preserved': True}
