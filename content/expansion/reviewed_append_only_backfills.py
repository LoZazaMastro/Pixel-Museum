"""Reconstruct approved missing articles, preserving every existing owner."""
import copy, hashlib, json
from pathlib import Path

def apply(entries,root):
    root=Path(root).resolve()
    def pinned(relative,expected):
        path=(root/relative).resolve()
        if not path.is_relative_to(root):raise ValueError('Backfill path outside project')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Backfill source changed: '+relative)
        return json.loads(raw)
    manifest=json.loads((root/'content/expansion/museum-reviewed-append-only-backfills.json').read_bytes())
    if manifest.get('publication_status')!='independently_reviewed':raise ValueError('Unreviewed backfill manifest')
    owners={entry['id']:entry for entry in entries}
    if len(owners)!=len(entries):raise ValueError('Duplicate owner before backfill')
    reserved={o['id'] for e in entries for o in [e]+e.get('editorial_features',[])}
    additions=[]
    for batch in manifest['batches']:
        candidate=pinned(batch['candidate_path'],batch['candidate_sha256'])
        peer=pinned(batch['peer_path'],batch['peer_sha256'])
        approval=pinned(batch['approval_path'],batch['approval_sha256'])
        field=batch['peer_source_hash_field']
        if field not in ('candidate_sha256','source_sha256'):raise ValueError('Unsupported source-peer contract')
        approval_ok=approval.get('status') in ('ROOT_APPROVED_2010_BACKFILL_ATOMIC_INTEGRATION','ROOT_APPROVED_EARLIEST_TWO_BACKFILL_INTEGRATION')
        peer_status=batch.get('peer_status')
        if peer_status is None:
            peer_ok=peer.get('status','').startswith('PASS')
        elif peer_status=='ROOT_FULL_ENGLISH_SOURCE_AND_SELECTED_MEDIA_PEER_PASS' and field=='candidate_sha256':
            peer_ok=peer.get('status')==peer_status
        elif peer_status=='INDEPENDENT_FULL_SOURCE_MEDIA_AND_FOUR_LANGUAGE_PEER_PASS_PRIVATE_ONLY' and field=='source_sha256':
            peer_ok=peer.get('status')==peer_status
            approval_ok=(approval.get('status')=='ROOT_APPROVED_2011_TEN_OWNER_BACKFILL_INTEGRATION'
                and approval.get('apply_writer_sha256')==batch.get('apply_writer_sha256')=='4f7321f284aa6f6ee2bebb10cc2f0df313703a29747e56050818706a434e62a0'
                and approval.get('writer_sha256')==batch.get('preparer_sha256')=='b2c46874f5aa4b4a6b31ea2d02f184ca04a0f1193fe810eb40d0394afd0cc312')
        else:raise ValueError('Unsupported exact source-peer status contract')
        if (not peer_ok or peer.get(field)!=batch['candidate_sha256']
                or not approval_ok
                or approval.get('plan_sha256')!=batch['boundary_plan_sha256']):
            raise ValueError('Backfill lacks exact source peer and Root boundary approval')
        boundary=pinned(batch['boundary_plan_path'],batch['boundary_plan_sha256'])
        if peer_status=='INDEPENDENT_FULL_SOURCE_MEDIA_AND_FOUR_LANGUAGE_PEER_PASS_PRIVATE_ONLY':
            if (boundary.get('batch_number')!=225 or boundary.get('new_owners')!=10
                    or boundary.get('source_candidate_sha256')!=batch['candidate_sha256']
                    or boundary.get('translation_candidate_sha256')!=peer.get('translation_sha256')
                    or len(candidate['entries'])!=10 or any(e.get('year')!=2011 for e in candidate['entries'])):
                raise ValueError('2011 source/media/language boundary differs')
        if batch['owner_ids']!=[e['id'] for e in candidate['entries']]:raise ValueError('Backfill owner set changed')
        for entry in candidate['entries']:
            identifier=entry['id']
            if identifier in owners:
                if owners[identifier]!=entry:raise ValueError('Backfill would replace an existing owner: '+identifier)
                continue
            if identifier in reserved:raise ValueError('Backfill feature ID collision')
            if any(e['title']==entry['title'] and e['year']==entry['year'] for e in owners.values()):raise ValueError('Backfill title/year collision')
            if not entry['body'] or len(entry['body'])!=len(entry['story_headings']):raise ValueError('Incomplete backfill article')
            for image in entry['images']:
                original=(root/image['recovery_local_source']).resolve()
                if not original.is_relative_to(root):raise ValueError('Backfill image outside project')
                if hashlib.sha256(original.read_bytes()).hexdigest()!=image['verification']['sha256']:raise ValueError('Backfill original image changed')
            proposed=copy.deepcopy(entry);additions.append(proposed);owners[identifier]=proposed;reserved.add(identifier)
    # Validate every batch before appending anything to the caller's list.
    entries.extend(additions)
    return {'status':'PASS','added':[e['id'] for e in additions]}
