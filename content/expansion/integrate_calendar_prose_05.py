"""Apply four source-bound corrections after published-locale restoration.

The original daily text is an archival edition. Canonical biographies and the
single disclosed studio-ownership correction have separate, honest credits.
This module is pure: the assembler alone persists outputs and their archives.
"""
import copy
import hashlib
import json

DECLARATION = 'content/expansion/calendar-prose-restorations-05.json'
DECLARATION_SHA256 = '7ff63f12f41a159a5e465a94bc8af497d5b20eb503f96e1443869f86a56d020b'
BIOGRAPHIES = {'daily-02-22', 'daily-02-24', 'daily-03-08'}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_document(path):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == DECLARATION_SHA256, 'Prose05 declaration changed since review')
    document = json.loads(raw)
    require({case['edition_id'] for case in document['biography_cases']} == BIOGRAPHIES, 'Unexpected biography set')
    require(len(document['english_correction_cases']) == 1 and document['english_correction_cases'][0]['edition_id'] == 'daily-11-08', 'Unexpected clause set')
    return document


def integrate(entries, locales, document):
    # Bind the parsed declaration too, so callers cannot pass a modified copy.
    require(digest(document) == REVIEWED_DOCUMENT_DIGEST, 'Unreviewed prose05 proposal')
    working = copy.deepcopy(entries)
    languages = copy.deepcopy(locales)
    lookup = {row['id']: row for row in working}
    require(len(lookup) == len(working), 'Duplicate records before prose05')
    archives, removed, actions = [], [], []
    cases = document['biography_cases'] + document['english_correction_cases']
    for case in cases:
        daily = lookup[case['edition_id']]
        target_id = case['target_canonical_id']
        old = lookup.get(target_id)
        require(digest(daily['body']) == case['published_english_body_sha256'] and digest(daily['story_headings']) == case['published_english_headings_sha256'], daily['id'] + ': original daily prose changed')
        require(daily.get('calendar_only'), daily['id'] + ': not a calendar edition')
        if case.get('calendar_slot_unchanged'):
            require(daily.get('calendar') == case['calendar_slot_unchanged'], daily['id'] + ': schedule changed')
        expected = case['expected_canonical_body_sha256']
        require((old is None and expected is None) or (old is not None and digest(old['body']) == expected), target_id + ': canonical prose drift')
        archives.append({'edition_id': daily['id'], 'original_daily': copy.deepcopy(daily), 'original_canonical': copy.deepcopy(old)})
        for language in ('en', 'it', 'es', 'fr', 'de', 'pt', 'ru', 'uk'):
            rows = languages[language]['entries']
            source = case['source_locale_archives'][language]
            if daily['id'] in rows:
                require(rows[daily['id']]['body'] == source['body'] and rows[daily['id']]['story_headings'] == source['story_headings'], daily['id'] + '/' + language + ': source translation changed')
            else:
                require(language == 'en', daily['id'] + '/' + language + ': missing daily source')
            overlay = rows.get(target_id)
            expected_overlay = case['canonical_locale_overlay_policy']['old_canonical_overlays_archived'][language]
            require(overlay == expected_overlay, target_id + '/' + language + ': stale canonical overlay changed')
            if overlay is not None:
                removed.append({'locale': language, 'entry_id': target_id, 'record': copy.deepcopy(overlay)})
                del rows[target_id]
        if case['case_kind'] == 'canonical_biography_reference_restoration':
            replacement = copy.deepcopy(case['proposed_canonical'])
            replacement['canonical_reference_restoration'] = {'review_file': DECLARATION, 'reviewed_declaration_sha256': DECLARATION_SHA256, 'source_daily_id': daily['id'], 'daily_source_prose_preserved': True}
            if old is None:
                replacement['calendar_only'] = False
                working.append(replacement)
                lookup[target_id] = replacement
            else:
                old.clear()
                old.update(replacement)
                old['calendar_only'] = False
            daily.update(copy.deepcopy(case['proposed_daily_metadata']))
            for credit in case['proposed_daily_source_credit_corrections']:
                source = daily['sources'][credit['source_index']]
                require(source.get('attribution') == credit['expected'], daily['id'] + ': changed source credit')
                source['attribution'] = credit['replacement']
            if 'editorial_revision' in daily:
                daily['editorial_revision']['displayed_source_status'] = case['proposed_daily_revision_note_status']
            daily['canonical_reference_restoration'] = copy.deepcopy(replacement['canonical_reference_restoration'])
        else:
            require(old is not None and digest(old['story_headings']) == case['expected_canonical_headings_sha256'], target_id + ': heading drift')
            index = case['paragraph_index']
            require(old['body'][index] == case['source_paragraph'], target_id + ': original clause drift')
            change = case['mechanical_replacement']
            require(old['body'][index].count(change['old']) == change['occurrences'] and old['body'][index].replace(change['old'], change['new']) == case['replacement_paragraph'], target_id + ': nonminimal correction')
            old['body'][index] = case['replacement_paragraph']
            require(digest(old['body']) == case['corrected_body_sha256'], target_id + ': corrected body hash mismatch')
            old['editorial_mode'] = case['proposed_canonical_editorial_mode']
            old['editorial_credit'] = case['proposed_canonical_editorial_credit']
            old['disclosed_english_correction'] = {'review_file': DECLARATION, 'reviewed_declaration_sha256': DECLARATION_SHA256, 'paragraph_index': index, 'original_body_sha256': expected, 'corrected_body_sha256': case['corrected_body_sha256'], 'change': copy.deepcopy(change)}
            for source in old.get('sources', []):
                if source.get('publisher') == 'Playhub / LoZazaMastro':
                    source['attribution'] = case['source_citation_update']['existing_playhub_source_attribution']
            selected = set(case['source_citation_update']['add_evidence_source_ids'])
            for source in document['primary_evidence']:
                if source['id'] in selected and source['url'] not in {row['url'] for row in old['sources']}:
                    old['sources'].append({key: copy.deepcopy(source[key]) for key in ('title', 'url', 'publisher')})
        actions.append({'daily_id': daily['id'], 'canonical_id': target_id, 'new_id_for_existing_subject': old is None, 'daily_body_unchanged': True, 'daily_headings_unchanged': True})
    entries[:] = working
    locales.clear()
    locales.update(languages)
    return {'schema_version': 1, 'review_file': DECLARATION, 'reviewed_declaration_sha256': DECLARATION_SHA256, 'actions': actions, 'original_records': archives, 'removed_canonical_locale_overlays': removed, 'new_subjects_claimed': 0, 'original_daily_prose_and_translations_changed': False, 'media_automatically_transferred': False}


REVIEWED_DOCUMENT_DIGEST = '08d5a8b9c26e1ed0287a8f66a2e92a5a34683cfceb382488b4ad780c2ebdd8dc'
