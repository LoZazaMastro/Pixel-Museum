"""Apply the 45 independently reviewed canonical narratives, without file writes.

Run after original-body-bound collection media and before final readiness. Daily
editions remain archival; nested features are separate works and are untouched.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

DECLARATION = 'content/expansion/calendar-canonical-narratives-06.json'
DECLARATION_SHA256 = 'f0a477b0cacda3ed917d7ace328db6e5eb58f80e6c6aaf241473c48257d21dab'
REVIEWED_DOCUMENT_DIGEST = 'ff0520f73d3c788c37bb065dd88f0f83776cf142b3c8dd1857cc147459dab915'
ARCHIVE_FIELDS = ('media_briefs', 'cards', 'story_cards', 'heading_provenance',
                  'source_edition_restoration', 'publication_readiness')


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_document(root):
    root = Path(root)
    path = root if root.suffix == '.json' else root / DECLARATION
    project = path.parents[2]
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == DECLARATION_SHA256,
            'Narratives06 declaration changed since review')
    document = json.loads(raw)
    require(digest(document) == REVIEWED_DOCUMENT_DIGEST, 'Unreviewed narratives06 declaration')
    require(len(document.get('cases', [])) == 45, 'Unexpected narratives06 case set')
    for relative, expected in {**document['review_files'], **document['source_file_hashes']}.items():
        require(hashlib.sha256((project / relative).read_bytes()).hexdigest() == expected,
                'Narratives06 reviewed source changed: ' + relative)
    return document


def _replay(entries, locales, document, receipt):
    """Verify an immediate second pass against complete before/after evidence."""
    require(receipt.get('reviewed_declaration_sha256') == DECLARATION_SHA256,
            'Narratives06 receipt belongs to a different declaration')
    restored_entries = copy.deepcopy(entries)
    restored_locales = copy.deepcopy(locales)
    lookup = {row['id']: row for row in restored_entries}
    require(len(lookup) == len(restored_entries), 'Duplicate article before narratives06 replay')
    expected_ids = {case['edition_id'] for case in document['cases']}
    originals = receipt.get('original_records', [])
    require({row.get('edition_id') for row in originals} == expected_ids
            and len(originals) == len(expected_ids), 'Incomplete narratives06 replay archive')
    for row in originals:
        for field in ('original_daily', 'original_canonical'):
            original = row[field]
            require(original['id'] in lookup, 'Missing narratives06 replay article')
            lookup[original['id']].clear()
            lookup[original['id']].update(copy.deepcopy(original))
    for row in receipt.get('removed_canonical_locale_overlays', []):
        restored_locales[row['locale']]['entries'][row['entry_id']] = copy.deepcopy(row['record'])
    expected_receipt = integrate(restored_entries, restored_locales, document)
    require(expected_receipt == receipt, 'Narratives06 replay receipt changed')
    current_lookup = {row['id']: row for row in entries}
    result_lookup = {row['id']: row for row in restored_entries}
    affected = expected_ids | {case['target_canonical_id'] for case in document['cases']}
    require(all(current_lookup[eid] == result_lookup[eid] for eid in affected),
            'Narratives06 immediate replay output changed')
    for language in document['cases'][0]['expected_locales']:
        require(all(locales[language]['entries'].get(eid) ==
                    restored_locales[language]['entries'].get(eid) for eid in affected),
                'Narratives06 immediate replay locale changed: ' + language)
    return copy.deepcopy(receipt)


def integrate(entries, locales, document, previous_receipt=None):
    """Atomically mutate parsed authoring data; return complete archival evidence.

    No filesystem or network calls occur here. The caller persists the catalogue,
    locale documents and returned receipt only after this operation succeeds.
    """
    require(digest(document) == REVIEWED_DOCUMENT_DIGEST, 'Unreviewed narratives06 proposal')
    if previous_receipt is not None:
        return _replay(entries, locales, document, previous_receipt)
    working = copy.deepcopy(entries)
    languages = copy.deepcopy(locales)
    lookup = {row['id']: row for row in working}
    require(len(lookup) == len(working), 'Duplicate article before narratives06')
    archives, removed, actions = [], [], []
    for case in document['cases']:
        eid, target = case['edition_id'], case['target_canonical_id']
        daily, canonical = lookup.get(eid), lookup.get(target)
        require(daily is not None and canonical is not None, eid + ': missing source or canonical')
        require(daily.get('calendar_only') is True and not canonical.get('calendar_only', False),
                eid + ': incorrect archival/canonical ownership')
        require(daily.get('linked_exhibit_id') == target, eid + ': canonical link changed')
        for label, row, expected in [('daily', daily, case['expected_daily']),
                                     ('canonical', canonical, case['expected_canonical'])]:
            for key, value in expected.items():
                require(row.get(key) == value, eid + ': ' + label + ' ' + key + ' changed')
        require(daily.get('calendar') == case['expected_calendar'], eid + ': calendar changed')
        proposal = case['proposed_canonical']
        require(len(proposal['body']) == len(proposal['story_headings']) == 3,
                eid + ': unexpected researched card count')
        require(all(isinstance(text, str) and text.strip() for text in
                    proposal['body'] + proposal['story_headings']), eid + ': empty researched card')
        archives.append({'edition_id':eid, 'original_daily':copy.deepcopy(daily),
                         'original_canonical':copy.deepcopy(canonical)})
        for language, expected in case['expected_locales'].items():
            require(language in languages and isinstance(languages[language].get('entries'), dict),
                    language + ': missing locale document')
            rows = languages[language]['entries']
            require((eid in rows) == expected['daily_present']
                    and digest(rows.get(eid)) == expected['daily_sha256'],
                    eid + '/' + language + ': archival translation changed')
            require((target in rows) == expected['canonical_present']
                    and digest(rows.get(target)) == expected['canonical_sha256'],
                    target + '/' + language + ': old canonical overlay changed')
            if target in rows:
                removed.append({'locale':language, 'entry_id':target,
                                'record':copy.deepcopy(rows.pop(target))})
        stripped = []
        for field in ('images', 'videos', 'models'):
            for index, media in enumerate(canonical.get(field, [])):
                if 'story_paragraph' in media:
                    stripped.append({'field':field, 'index':index,
                                     'value':copy.deepcopy(media.pop('story_paragraph')),
                                     'url':media.get('url', media.get('source_url', ''))})
        cleared = []
        for field in ARCHIVE_FIELDS:
            if field in canonical:
                canonical.pop(field)
                cleared.append(field)
        # Preserve original source references and all unrelated metadata/media.
        sources = canonical.setdefault('sources', [])
        for incoming in proposal['sources']:
            matching = next((source for source in sources if source.get('url') == incoming['url']), None)
            if matching is None:
                sources.append(copy.deepcopy(incoming))
            else:
                matching.update(copy.deepcopy(incoming))
        for field in ('title', 'summary', 'body', 'story_headings', 'editorial_mode',
                      'editorial_credit', 'editorial_revision'):
            if field in proposal:
                canonical[field] = copy.deepcopy(proposal[field])
        canonical['canonical_narrative_enrichment'] = {
            'review_file':DECLARATION, 'reviewed_declaration_sha256':DECLARATION_SHA256,
            'source_daily_id':eid, 'original_daily_prose_preserved':True,
            'original_canonical_body_sha256':digest(case['expected_canonical']['body']),
            'new_canonical_body_sha256':digest(canonical['body']),
            'unreviewed_translation_policy':'Fall back to the researched English narrative.',
            'media_paragraph_bindings_cleared':len(stripped), 'new_subjects_claimed':0}
        credits = []
        for correction in case['daily_source_credit_corrections']:
            index = correction['source_index']
            require(index < len(daily.get('sources', [])), eid + ': missing original source credit')
            source = daily['sources'][index]
            require(source.get('attribution') == correction['expected'], eid + ': daily credit changed')
            source['attribution'] = correction['replacement']
            credits.append(copy.deepcopy(correction))
        # The only daily mutations above are explicitly declared source credits.
        actions.append({'edition_id':eid, 'canonical_id':target,
                        'new_canonical_body_sha256':digest(canonical['body']),
                        'daily_source_credit_corrections':credits,
                        'stripped_media_paragraph_bindings':stripped,
                        'archived_and_cleared_source_bound_fields':cleared,
                        'daily_prose_unchanged':True, 'attached_features_unchanged':True})
    result = {'schema_version':1, 'review_file':DECLARATION,
              'reviewed_declaration_sha256':DECLARATION_SHA256,
              'actions':actions, 'original_records':archives,
              'removed_canonical_locale_overlays':removed,
              'original_daily_prose_or_translations_changed':False,
              'new_subjects_claimed':0, 'new_records_created':0,
              'media_deleted_or_transferred':False}
    entries[:] = working
    locales.clear()
    locales.update(languages)
    return result
