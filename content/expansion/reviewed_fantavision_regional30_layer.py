"""Exact, reviewed Fantavision three-region music layer; no other owner edits."""
from pathlib import Path
import copy, hashlib, json

def packed(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def validated(root, candidate):
    root = Path(root).resolve()
    def pin(path, digest):
        p = (root / path).resolve()
        if not p.is_relative_to(root): raise ValueError('Input escapes project')
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest: raise ValueError('Immutable input changed: ' + path)
        return json.loads(raw)
    if len(candidate['components']) != 1: raise ValueError('Exactly one reviewed component required')
    component = candidate['components'][0]
    original = pin(component['candidate_path'], component['candidate_sha256'])
    peer = pin(component['peer_path'], component['peer_sha256'])
    independent = pin(component['independent_peer_path'], component['independent_peer_sha256'])
    if peer['status'] != 'ROOT_APPROVED_FANTAVISION_THREE_REGIONAL_ROOMS_PRIVATE_ONLY': raise ValueError('Root peer status changed')
    if peer['candidate_sha256'] != component['candidate_sha256']: raise ValueError('Root candidate binding changed')
    for key in ('independent_peer_path', 'independent_peer_sha256', 'additional_immutable_inputs'):
        if peer[key] != component[key]: raise ValueError('Root evidence binding changed')
    if independent['status'] != 'PASS_FINITE_NATURAL_PAL_DISPLAY_INVERSE_PEER': raise ValueError('Finite peer status changed')
    if independent['candidate'] != {'path': component['candidate_path'], 'sha256': component['candidate_sha256']}:
        raise ValueError('Finite peer candidate changed')
    for item in component['additional_immutable_inputs']: pin(item['path'], item['sha256'])
    if candidate['entries'] != original['entries']: raise ValueError('Original reviewed entry changed')
    for receipt in candidate['source_receipts']:
        path = (root / receipt['path']).resolve()
        if not path.is_relative_to(root) or hashlib.sha256(path.read_bytes()).hexdigest() != receipt['sha256']:
            raise ValueError('Original evidence receipt changed')
    if len(candidate['entries']) != 1: raise ValueError('Exactly one owner required')
    row = candidate['entries'][0]
    rooms = row['after_soundtrack_rooms']
    if row['entry_id'] != 'wikipedia-2386098' or len(rooms) != 3 or [len(r['tracks']) for r in rooms] != [2,14,14]:
        raise ValueError('Exact PAL/JP/USA room scope changed')
    if row['after_soundtrack'] != rooms[0]: raise ValueError('Main-room compatibility alias changed')
    if row['before_soundtrack_rooms'] is not None: raise ValueError('Unexpected prior regional rooms')
    return row

def apply(entries, root):
    root = Path(root).resolve()
    policy = json.loads((root / 'content/expansion/museum-reviewed-fantavision-regional30-policy.json').read_bytes())
    path = (root / policy['candidate_path']).resolve()
    if not path.is_relative_to(root): raise ValueError('Candidate escapes project')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != policy['candidate_sha256']: raise ValueError('Candidate changed')
    row = validated(root, json.loads(raw))
    found = [e for e in entries if e['id'] == row['entry_id']]
    if len(found) != 1: raise ValueError('Missing or duplicate Fantavision owner')
    entry = found[0]
    before = (row['before_soundtrack'], row['before_soundtrack_rooms'])
    after = (row['after_soundtrack'], row['after_soundtrack_rooms'])
    current = (entry.get('soundtrack'), entry.get('soundtrack_rooms'))
    if current not in (before, after): raise ValueError('Unreviewed or partially applied regional music')
    restored = copy.deepcopy(entry)
    for field in ('soundtrack', 'soundtrack_rooms'):
        value = row['before_' + field]
        if value is None: restored.pop(field, None)
        else: restored[field] = copy.deepcopy(value)
    if hashlib.sha256(packed(restored)).hexdigest() != row['source_entry_sha256']:
        raise ValueError('Fantavision non-music source changed')
    if current == after: return {'status':'PASS','changed':[], 'available_tracks':30, 'regional_rooms':3}
    # Every binding and both complete field states were validated before mutation.
    entry['soundtrack'] = copy.deepcopy(row['after_soundtrack'])
    entry['soundtrack_rooms'] = copy.deepcopy(row['after_soundtrack_rooms'])
    return {'status':'PASS','changed':[entry['id']], 'available_tracks':30, 'regional_rooms':3}
