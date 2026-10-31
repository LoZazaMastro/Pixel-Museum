"""Admit source-bound article repairs after earlier paragraph-level copy edits."""
from pathlib import Path
import copy
import hashlib
import json


def body_hash(body):
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, separators=(',', ':')).encode('utf8')).hexdigest()


def apply(entries, root):
    root = Path(root)
    path = root / 'content/expansion/museum-fourteen-article-clarity-reviewed.json'
    if not path.is_file():
        return {'status': 'not_available'}
    doc = json.loads(path.read_text(encoding='utf8'))
    if doc.get('publication_status') != 'independently_reviewed':
        return {'status': 'not_admitted'}
    candidate = root / doc['reviewed_candidate']['local_path']
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if digest != doc['reviewed_candidate']['sha256']:
        raise ValueError('Reviewed article candidate changed')
    original = json.loads(candidate.read_text(encoding='utf8'))
    if original['entries'] != doc['entries']:
        raise ValueError('Article fields changed after peer review')
    review = json.loads((root / doc['independent_review_receipt']).read_text(encoding='utf8'))
    if review.get('status') != 'PASS' or review.get('candidate_sha256') != digest:
        raise ValueError('Article peer receipt does not match candidate')
    owners = {e['id']: e for e in entries}
    result = []
    for identifier, change in doc['entries'].items():
        entry = owners.get(identifier)
        if entry is None:
            raise ValueError('Reviewed article absent: ' + identifier)
        if entry.get('body') == change['body']:
            continue
        if entry.get('body') != change['old_body'] or body_hash(entry['body']) != change['old_body_sha256']:
            raise ValueError('Reviewed old article changed: ' + identifier)
        if len(change['body']) != len(change['old_body']) or len(change['story_headings']) != len(change['body']):
            raise ValueError('Reviewed article paragraph structure changed')
        sources = entry.setdefault('sources', [])
        known = {s.get('url') for s in sources}
        for card in change['replacement_paragraphs'].values():
            source = card['source']
            source_path = root / source['local_path']
            if hashlib.sha256(source_path.read_bytes()).hexdigest() != source['sha256']:
                raise ValueError('Frozen article source changed')
            page = json.loads(source_path.read_text(encoding='utf8'))['query']['pages'][0]
            if page['pageid'] != source['page_id'] or page['revisions'][0] != source['revision']:
                raise ValueError('Frozen article identity/revision changed')
            lines = page['extract'].split('\n')
            if any(lines[p['extract_line']] != p['text'] for p in card['source_paragraphs']):
                raise ValueError('Reviewed source comparison differs')
            if source['revision_url'] not in known:
                sources.append({'title': source['article_title'] + ': English Wikipedia revision',
                                'url': source['revision_url'], 'publisher': 'English Wikipedia contributors',
                                'attribution': 'Adapted and abridged under Creative Commons Attribution-ShareAlike 4.0.'})
                known.add(source['revision_url'])
        licence = doc['source_license']['url']
        if licence not in known:
            sources.append({'title': 'Text licence: Creative Commons Attribution-ShareAlike 4.0',
                            'url': licence, 'publisher': 'Creative Commons'})
        provenance = entry.setdefault('provenance', {})
        if not isinstance(provenance, dict):
            entry['provenance'] = {'original_record': provenance}
            provenance = entry['provenance']
        provenance['reviewed_article_clarity'] = {
            'original_body': copy.deepcopy(entry['body']),
            'original_headings': copy.deepcopy(entry.get('story_headings', [])),
            'old_body_sha256': change['old_body_sha256'],
            'reviewed_candidate_sha256': digest,
            'independent_review_receipt': doc['independent_review_receipt'],
            'paragraph_source_records': copy.deepcopy(change['replacement_paragraphs']),
            'reason': 'Replace repeated template tails with concrete, independently read English Wikipedia material.'}
        entry['body'] = copy.deepcopy(change['body'])
        entry['story_headings'] = copy.deepcopy(change['story_headings'])
        entry['editorial_credit'] = entry.get('editorial_credit', '').rstrip() + ' ' + change['attribution']
        result.append({'entry_id': identifier, 'replaced_paragraphs': len(change['replacement_paragraphs'])})
    return {'status': 'PASS', 'articles': result, 'candidate_sha256': digest,
            'wording_counts': copy.deepcopy(doc['wording_counts'])}
