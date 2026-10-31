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
    policy=json.loads((root/'content/expansion/museum-reviewed-precutoff-fiftythree-display-policy.json').read_bytes())
    if policy.get('publication_status')!='independently_reviewed':raise ValueError('Unreviewed music policy')
    candidate=pinned(policy['candidate_path'],policy['candidate_sha256'])
    peer=pinned(policy['peer_path'],policy['peer_sha256'])
    if peer.get('status')!='ROOT_PRE2012_FINITE_DISPLAY_REVIEW_53_PASS_ONE_HOLD' or peer.get('proposal_sha256')!=candidate.get('proposal_sha256') or peer.get('rows')!=candidate.get('reviewed_display_rows') or peer.get('reviewed_count')!=53:raise ValueError('Exact independent Root53 display peer required')
    proposal=pinned(candidate['proposal_path'],candidate['proposal_sha256'])
    selected=[r for r in proposal['proposals']if r['year']<=2012 and r['youtube_id']!='4mXebVTGu_k']
    if selected!=candidate['display_proposals']:raise ValueError('Selected display proposals differ from reviewed source')
    normalized=[{'game':r['game'],'before':r['before'],'after':r['after'],'receipt_sha256':r['source']['sha256']}for r in selected]
    if normalized!=peer['rows']or len(selected)!=53:raise ValueError('Display proposals differ from Root actual-source peer')
    covered=[]
    for row in candidate['entries']:
        expected=copy.deepcopy(row['before_soundtrack'])
        for change in selected:
            if change['entry_id']!=row['entry_id']:continue
            track=expected['tracks'][change['track_index']]
            if track['title']!=change['before']or track['youtube_id']!=change['youtube_id']:raise ValueError('Display before-label or recording changed')
            track['title']=change['after'];covered.append(change)
        if expected!=row['after_soundtrack']:raise ValueError('Fields beyond approved display titles changed')
    if len(covered)!=53:raise ValueError('Missing or repeated display change')
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
