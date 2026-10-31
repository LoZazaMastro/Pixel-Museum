"""Apply only the independently reviewed public music replacements after backfills."""
import copy,hashlib,json
from pathlib import Path

def apply(entries,root):
    root=Path(root).resolve()
    def packed(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')
    def pinned(relative,expected):
        p=(root/relative).resolve()
        if not p.is_relative_to(root):raise ValueError('Music path outside project')
        raw=p.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Reviewed music input changed')
        return json.loads(raw)
    policy=json.loads((root/'content/expansion/museum-reviewed-five-2010-217-public-music-policy.json').read_bytes())
    if policy.get('publication_status')!='independently_reviewed':raise ValueError('Unreviewed music policy')
    candidate=pinned(policy['candidate_path'],policy['candidate_sha256'])
    peer=pinned(policy['peer_path'],policy['peer_sha256'])
    if peer.get('status')!='ROOT_FULL_217_MUSIC_METADATA_AND_FINITE_CREDIT_PEER_PASS_PRIVATE_ONLY' or peer.get('candidate_sha256')!=policy['candidate_sha256']:raise ValueError('Exact independent Root music peer required')
    owners={e['id']:e for e in entries};changes=[]
    for row in candidate['entries']:
        e=owners.get(row['entry_id'])
        if not e or (e['title'],e['year'])!=(row['match_title'],row['match_year']):raise ValueError('Music source owner missing or changed')
        fields={k:e[k] for k in ('title','subtitle','summary','body','story_headings')}
        if hashlib.sha256(packed(fields)).hexdigest()!=row['english_five_fields_sha256']:raise ValueError('Music source prose changed')
        current=e.get('soundtrack')
        if current not in (row['before_soundtrack'],row['after_soundtrack']):raise ValueError('Music layer would overwrite an unreviewed room')
        restored=copy.deepcopy(e)
        if row['before_soundtrack'] is None:restored.pop('soundtrack',None)
        else:restored['soundtrack']=copy.deepcopy(row['before_soundtrack'])
        if hashlib.sha256(packed(restored)).hexdigest()!=row['source_entry_sha256']:raise ValueError('Music source media or metadata changed')
        if current!=row['after_soundtrack']:changes.append((e,copy.deepcopy(row['after_soundtrack'])))
    # Reject every conflict before changing any room. Existing prose/media stay intact.
    for e,room in changes:e['soundtrack']=room
    return {'status':'PASS','changed':[e['id'] for e,_ in changes],'available_tracks':sum(len(r['after_soundtrack']['tracks'])for r in candidate['entries'])}
