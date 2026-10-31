"""Atomic reviewed identity repair for22 complete-subject cases only.

No command-line action or filesystem mutation. The root assembler chooses the
hook position. Apply after exact Playhub English restoration, and migrate locale
overlays after their normal generation so stale aliases cannot be reintroduced.
The two mixed editions remain untouched pending a separate editorial decision.
"""
import copy
import hashlib
import json

REVIEW_FILE='content/expansion/calendar-identity-corrections-03.json'
REVIEWED_DECLARATION_SHA256='7eedf0930c06601d5fe7fd9fbdc3f4d819539313f2c99befded1dd223de0ba76'
REVIEWED_CANONICAL_DIGEST='455eca22a9303da217eebf16e13837f95d6e07915340f2e182395d45a9e30042'
MIXED_HOLDS={'daily-03-15','daily-04-06'}

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def require(condition,message):
    if not condition: raise ValueError(message)

def era(year):
    if year<1970:return 'origins'
    if year<1980:return 'public-play'
    if year<1990:return 'personal'
    if year<2000:return 'dimensions'
    if year<2010:return 'connected'
    if year<2020:return 'everywhere'
    return 'living-history'

def whole_cases(document):
    require(digest(document)==REVIEWED_CANONICAL_DIGEST,'Identity03 declaration differs from the independently reviewed snapshot')
    require(document.get('schema_version')==1,'Unknown identity03 schema')
    require(len(document.get('cases',[]))==24,'Expected24 reviewed declaration cases')
    require({c['edition_id'] for c in document['cases'] if c['correction_kind']=='mixed_original_sections'}==MIXED_HOLDS,'Mixed holds changed')
    cases=[c for c in document['cases'] if c['correction_kind']=='whole_subject_mapping']
    require(len(cases)==22 and len({c['edition_id'] for c in cases})==22,'Expected22 unique whole-subject cases')
    for case in cases:
        require(len(case['proposed_partitions'])==1,case['edition_id']+': whole case has multiple partitions')
        original=case['archived_published_edition'];part=case['proposed_partitions'][0]
        require(case['source_body_sha256']==digest(original['body']) and case['source_headings_sha256']==digest(original['story_headings']),case['edition_id']+': archived source hash changed')
        require(part['source_body_indices']==list(range(len(original['body']))),case['edition_id']+': incomplete source partition')
        require(case.get('wrong_canonical_id') and case['restored_original_destination']['id']==case['wrong_canonical_id'],case['edition_id']+': opaque original destination missing')
        require(part['exact_source_locales']['en']['body']==original['body'] and part['exact_source_locales']['en']['story_headings']==original['story_headings'],case['edition_id']+': English projection changed')
    return cases

def integrate(entries,document,previous_receipt=None):
    """Mutate the caller list only after the complete cloned transaction passes."""
    cases=whole_cases(document)
    if previous_receipt is not None:
        # Idempotence is checked against the immediate, complete result. A
        # later editorial/media enrichment must run as its own transaction.
        require(previous_receipt.get('review_file')==REVIEW_FILE,'Identity03 receipt belongs to another review')
        archived=previous_receipt.get('original_records_before_migration',[])
        require(len(archived)==22,'Identity03 receipt needs all22 original record pairs')
        require(previous_receipt.get('original_records_sha256')==digest(archived),'Identity03 original receipt records changed')
        baseline=copy.deepcopy(entries)
        lookup={e['id']:e for e in baseline}
        require(len(lookup)==len(baseline),'Duplicate IDs before identity03 replay')
        expected_ids={c['edition_id'] for c in cases}
        require({r.get('edition_id') for r in archived}==expected_ids,'Identity03 receipt case set changed')
        for row in archived:
            for key in ('daily','opaque_destination'):
                original=row[key]
                require(original['id'] in lookup,original['id']+': receipt destination missing')
                lookup[original['id']].clear();lookup[original['id']].update(copy.deepcopy(original))
        expected_receipt=integrate(baseline,document)
        require(previous_receipt==expected_receipt,'Identity03 receipt differs from a complete replay')
        expected={e['id']:e for e in baseline}
        actual={e['id']:e for e in entries}
        for identifier in expected_receipt['result_record_sha256']:
            require(actual[identifier]==expected[identifier],identifier+': migrated record differs from immediate reviewed result')
        return copy.deepcopy(expected_receipt)
    working=copy.deepcopy(entries)
    lookup={e['id']:e for e in working}
    require(len(lookup)==len(working),'Duplicate IDs before identity03')
    original_records=[];actions=[]
    for case in cases:
        identifier=case['edition_id'];old_id=case['wrong_canonical_id']
        daily=lookup.get(identifier);old=lookup.get(old_id);part=case['proposed_partitions'][0]
        require(daily is not None and old is not None,identifier+': required source destinations missing')
        require(daily.get('calendar_only') and daily.get('calendar')==case['calendar_slot_unchanged'],identifier+': calendar source changed')
        require(daily['title']==case['wrong_metadata_title'] and daily['year']==case['wrong_metadata_year'],identifier+': inherited daily identity changed')
        require(digest(daily['body'])==case['source_body_sha256'] and digest(daily['story_headings'])==case['source_headings_sha256'],identifier+': published daily narrative changed')
        require(old['title']==case['wrong_metadata_title'] and old['year']==case['wrong_metadata_year'],old_id+': original game identity changed')
        require(digest(old['body'])==case['source_body_sha256'],old_id+': old canonical no longer contains reviewed unrelated narrative')
        reference=case['restored_original_destination']
        require(reference['id']==old_id and reference['title']==old['title'] and reference['year']==old['year'],old_id+': restored reference changes opaque identity')
        require(reference.get('attribution',{}).get('revision_id')==case['restored_reference_source']['revision_id'],old_id+': reference revision differs')
        original_records.append(dict(edition_id=identifier,daily=copy.deepcopy(daily),opaque_destination=copy.deepcopy(old)))
        review=dict(review_file=REVIEW_FILE,reviewed_declaration_sha256=REVIEWED_DECLARATION_SHA256,
            edition_id=identifier,old_canonical_id=old_id,actual_subject_title=part['title'],
            published_body_sha256=case['source_body_sha256'],published_headings_sha256=case['source_headings_sha256'],
            source_sections_preserved=True,original_bibliography=copy.deepcopy(daily.get('sources',[])),
            original_media=dict(images=copy.deepcopy(daily.get('images',[])),videos=copy.deepcopy(daily.get('videos',[])),models=copy.deepcopy(daily.get('models',[]))))
        year=case['proposed_calendar_historical_year']
        require(isinstance(year,int),identifier+': whole story needs explicit historical anchor')
        # A distinct original story stays on the daily ID. It does not replace
        # another canonical edition and receives no inherited wrong-game media.
        daily.update(title=part['title'],year=year,kind=part['kind'],era_id=era(year),
            calendar_only=True,images=[],videos=[],models=[],
            date=dict(month=0,day=0,precision='year',region='Editorial calendar scheduling; exact historical event date remains separately reviewed.'),
            event_semantics=part['calendar_event_semantics'],
            source_identity_correction=copy.deepcopy(review))
        daily.pop('linked_exhibit_id',None)
        daily.pop('date_provenance',None)
        daily.pop('soundtrack',None)
        daily.pop('editorial_features',None)
        target=part['target_id']
        daily['related_ids']=[target] if target in lookup and target!=old_id and target!=identifier else []
        # Bibliography is preserved exactly, rather than silently relabelled as
        # actual-subject evidence. The note makes its inherited status explicit.
        daily['factual_note']=(daily.get('factual_note','')+' '+
            'Reviewed subject correction: the original published narrative and bibliography are preserved. Some inherited bibliography/media labels described the wrong game and remain unverified for this story. The calendar day does not establish an exact release date.').strip()
        evidence=part['subject_evidence']
        url=evidence.get('immutable_url') or evidence.get('url')
        if url and all(s.get('url')!=url for s in daily.get('sources',[])):
            daily.setdefault('sources',[]).append(dict(title=evidence['title']+' — reviewed subject identity',url=url,publisher='English Wikipedia contributors' if evidence.get('revision_id') else evidence.get('publisher','')))
        # Owner media remains only with its real original-game destination.
        owner_media={key:copy.deepcopy(old.get(key,[])) for key in ('images','videos','models')}
        old.update(copy.deepcopy(reference))
        old.update(owner_media)
        old['source_identity_correction']=copy.deepcopy(review)
        for key in ('calendar_editorial','source_edition_restoration','publication_readiness','linked_exhibit_id','calendar',
                    'source_subject','source_topic','source_feature_title','research_media_refs','date_provenance'):
            old.pop(key,None)
        old['calendar_only']=False
        actions.append(dict(edition_id=identifier,corrected_story_title=daily['title'],story_historical_year=year,
            canonical_original_year=part['canonical_original_year'],restored_opaque_id=old_id,
            existing_correct_related_id=target if target in daily['related_ids'] else None,
            published_sections=len(daily['body']),wrong_subject_media_transferred=0))
    # A failed case above leaves the caller completely untouched.
    entries[:]=working
    return dict(schema_version=1,review_file=REVIEW_FILE,
        corrected_distinct_daily_stories=actions,restored_opaque_destination_ids=[a['restored_opaque_id'] for a in actions],
        original_records_before_migration=original_records,
        original_records_sha256=digest(original_records),
        result_record_sha256={identifier:digest(lookup[identifier]) for action in actions
            for identifier in (action['edition_id'],action['restored_opaque_id'])},
        held_mixed_edition_ids=sorted(MIXED_HOLDS),
        new_ids_added=[],ids_removed=[],calendar_slots_unchanged=True,
        original_published_sections_preserved=sum(a['published_sections'] for a in actions),
        note='22 whole-subject corrections only. This is not admission of media or complete historical correctness.')

def migrate_locale_overlays(documents,document):
    """Remove wrong opaque aliases, retaining exact daily source strings.

    documents maps locale codes to parsed locale JSON. The returned audit keeps
    every removed record. The caller owns persistence after all other locale
    generators finish; this function never writes any file.
    """
    cases=whole_cases(document);working=copy.deepcopy(documents);removed=[];original_daily=[]
    for language,locale in working.items():
        if language not in {'en','it','es','fr','de','pt','ru','uk'}:continue
        rows=locale.get('entries',{})
        require(isinstance(rows,dict),language+': invalid locale entry map')
        for case in cases:
            identifier=case['edition_id'];old_id=case['wrong_canonical_id'];expected=case['source_locale_archives'][language]
            daily=rows.get(identifier)
            if daily is not None:
                require(daily.get('body')==expected['body'] and daily.get('story_headings')==expected['story_headings'],identifier+'/'+language+': original daily translation differs')
                original_daily.append(dict(locale=language,key=identifier,record=copy.deepcopy(daily)))
                daily['title']=case['proposed_partitions'][0]['title']
            else:
                # English normally uses the master baseline. Other languages
                # must not disappear merely because an old alias was removed.
                require(language=='en',identifier+'/'+language+': original daily locale missing')
            old=rows.get(old_id)
            if old is not None:
                require(old.get('body')==expected['body'] and old.get('story_headings')==expected['story_headings'],old_id+'/'+language+': opaque override is not reviewed unrelated source text')
                removed.append(dict(locale=language,old_key=old_id,actual_daily_key=identifier,
                    archived_removed_record=copy.deepcopy(old),body_sha256=digest(old['body']),headings_sha256=digest(old['story_headings'])))
                del rows[old_id]
    documents.clear();documents.update(working)
    return dict(schema_version=1,review_file=REVIEW_FILE,removed_wrong_opaque_overlays=removed,
        original_daily_records_before_migration=original_daily,
        daily_source_prose_changed=False,reference_translations_added=False,
        note='Original daily strings remain exact; removed aliases are archived in this returned audit. Mixed editions untouched.')
