"""Exact source-identity exclusions requested by the user; retain local archives."""
import json,hashlib
from pathlib import Path
def apply(entries, root):
    policy = json.loads((Path(root) / 'content/expansion/user-selected-game-exclusions.json').read_text(encoding='utf8'))
    for archive in policy.get('confirmed_archives',[]):
        assert hashlib.sha256((Path(root)/archive['path']).read_bytes()).hexdigest()==archive['sha256'],'Confirmed removal archive changed'
    rows = policy['rows']
    guards = {row['id']: row for row in rows}
    removed = []
    for entry in entries:
        guard = guards.get(entry['id'])
        if guard:
            if any(entry.get(key) != guard[key] for key in ('title', 'year', 'date')):
                raise ValueError('Requested exclusion identity drift: ' + entry['id'])
            removed.append(guard)
    entries[:] = [entry for entry in entries if entry['id'] not in guards]
    return {'status': 'PASS', 'removed': removed, 'assets_deleted': False}
