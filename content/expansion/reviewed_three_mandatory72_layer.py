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
    policy=json.loads((root/'content/expansion/museum-reviewed-three-mandatory72-policy.json').read_bytes())
    if policy.get('publication_status')!='independently_reviewed':raise ValueError('Unreviewed music policy')
    candidate=pinned(policy['candidate_path'],policy['candidate_sha256'])
    if candidate['components']!=policy['components']:raise ValueError('Component policy drift')
    combined=[]
    allowed={'ROOT_APPROVED_MANDATORY_ORIGINAL_SOUNDTRACK_PEER_PASS_PRIVATE_ONLY'}
    for component in policy['components']:
        original=pinned(component['candidate_path'],component['candidate_sha256']);peer=pinned(component['peer_path'],component['peer_sha256'])
        independent=pinned(component['independent_peer_path'],component['independent_peer_sha256'])
        if peer.get('independent_peer_path')!=component['independent_peer_path'] or peer.get('independent_peer_sha256')!=component['independent_peer_sha256']:raise ValueError('Root independent peer binding changed')
        if component['independent_peer_status'] not in ('INDEPENDENT_FULL_ORIGINAL_BASE_ALBUM_PEER_PASS_PRIVATE_ONLY', 'INDEPENDENT_FULL_FALLOUT3_TWENTYNINE_ORIGINAL_SCORE_PEER_PASS_PRIVATE_ONLY'):raise ValueError('Unknown independent review schema')
        if independent.get('status')!=component['independent_peer_status'] or peer.get('independent_peer_status')!=component['independent_peer_status']:raise ValueError('Independent status drift')
        if peer.get('independent_peer_entry_candidate_sha256')!=component['independent_peer_entry_candidate_sha256'] or component['independent_peer_entry_candidate_sha256']!=component['candidate_sha256']:raise ValueError('Independent candidate binding drift')
        if component['independent_peer_schema'] not in ('single_candidate_top_level','exact_candidate_in_reviews_array') or peer.get('independent_peer_schema')!=component['independent_peer_schema']:raise ValueError('Independent schema drift')
        if peer.get('additional_immutable_inputs')!=component['additional_immutable_inputs']:raise ValueError('Additional immutable binding drift')
        for pin in component['additional_immutable_inputs']:pinned(pin['path'],pin['sha256'])
        candidates=independent['reviews'] if component['independent_peer_schema']=='exact_candidate_in_reviews_array' else [independent]
        selected=[r for r in candidates if r.get('candidate_sha256')==component['candidate_sha256']]
        if len(selected)!=1:raise ValueError('Independent candidate missing or repeated')
        if component['peer_status'] not in allowed or peer['status']!=component['peer_status'] or peer['candidate_sha256']!=component['candidate_sha256']:raise ValueError('Wrong exact component Root peer')
        combined.extend(original['entries'])
    if combined!=candidate['entries'] or len(combined)!=3 or sum(len(r['after_soundtrack']['tracks'])for r in combined)!=72:raise ValueError('Combined music differs from reviewed components')
    if not (sum(r['before_soundtrack'] is None for r in combined)==0 and sum(isinstance(r['before_soundtrack'],dict) for r in combined)==3):raise ValueError('Exact reviewed scope: zero new rooms and three existing replacements')
    owners={e['id']:e for e in entries};changes=[]
    for row in candidate['entries']:
        e=owners.get(row['entry_id'])
        if not e or (e['title'],e['year'])!=(row['match_title'],row['match_year']):raise ValueError('Music source owner missing or changed')
        fields={k:e[k] for k in ('title','subtitle','summary','body','story_headings')}
        if 'english_five_fields_sha256' in row and hashlib.sha256(packed(fields)).hexdigest()!=row['english_five_fields_sha256']:raise ValueError('Music source prose changed')
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
