#!/usr/bin/env python3
"""Enumerate every published edition without pretending keyword scans review it."""
from pathlib import Path
import copy
import datetime
import hashlib
import json
import math

CONTENT=Path(__file__).resolve().parents[1]/'content'
def read(path): return json.loads(path.read_text(encoding='utf-8'))
def file_hash(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def main():
    source=read(CONTENT/'expansion/calendar-features.json')
    review=read(CONTENT/'expansion/calendar-identity-corrections-02.json')
    current={e['id']:e for e in read(CONTENT/'catalog.json')['entries']}
    cases={r['edition_id']:r for r in review['cases']}
    path=CONTENT/'editorial/playhub-identity-review-queue.json'
    previous=read(path) if path.exists() else {}
    previous_rows={r['edition_id']:r for r in previous.get('editions',[])}
    locales={p.stem:read(p) for p in (CONTENT/'locales').glob('*.json')}
    rows=[]
    ordered=sorted(source['entries'],key=lambda e:(e['id'] not in cases,e['calendar']['month'],e['calendar']['day']))
    for e in ordered:
        locale_rows={}
        for language,document in locales.items():
            translated=document['entries'].get(e['id'])
            english=language=='en'
            locale_rows[language]={
                'status':'existing_exact_published_locale' if translated else 'English_master_base_no_override' if english else 'missing',
                'body_sha256':digest(translated['body'] if translated else e['body']) if translated or english else None,
                'headings_sha256':digest(translated['story_headings'] if translated else e['story_headings']) if translated or english else None}
        case=cases.get(e['id'])
        observed=current[e['id']]
        row={'edition_id':e['id'],'source_record_id':e['provenance']['source_record_id'],
            'scheduled_month_day':e['id'].removeprefix('daily-'),
            'published_metadata_title':e['title'],'published_metadata_year':e['year'],
            'published_canonical_id':e.get('linked_exhibit_id'),
            'source_anniversary_metadata':copy.deepcopy(e['provenance'].get('source_anniversary_metadata')),
            'body_sections':len(e['body']),'published_english_body_sha256':digest(e['body']),
            'published_english_headings_sha256':digest(e['story_headings']),
            'locale_reference_rows':locale_rows,'work_unit':'identity-'+str(len(rows)//15+1).zfill(2),
            'review_status':'mismatch_confirmed_reviewed_migration_prepared' if case else 'unreviewed',
            'checked_subject':case['corrected_title'] if case else None,
            'proposed_canonical_id':case['corrected_canonical_id'] if case else None,
            'subject_identity_review':'complete_exact_narrative_and_external_identity_evidence' if case else 'pending_read_every_paragraph_and_heading',
            'date_semantics_review':case['historical_date_review'] if case else 'pending_release_regional_launch_announcement_commemoration_or_editorial_slot',
            'media_identity_review':'pending_exact_subject_version_rights_quality_and_caption_review',
            'full_historical_factual_signoff':False,'source_prose_rewrite_authorized':False}
        row['current_master_observation']={'title':observed['title'],'year':observed['year'],
            'canonical_id':observed.get('linked_exhibit_id'),
            'published_prose_and_headings_exact':observed['body']==e['body'] and observed['story_headings']==e['story_headings']}
        if case:
            row['approved_migration_state']=('applied_in_observed_master' if
                (observed['title'],observed['year'],observed.get('linked_exhibit_id')) ==
                (case['corrected_title'],case['corrected_year'],case['corrected_canonical_id'])
                else 'prepared_not_yet_observed_in_master')
        prior=previous_rows.get(e['id'])
        if prior:
            if all(prior[k]==row[k] for k in ('published_english_body_sha256','published_english_headings_sha256')):
                for key in ('review_status','checked_subject','proposed_canonical_id','subject_identity_review',
                            'date_semantics_review','media_identity_review','full_historical_factual_signoff',
                            'findings','evidence','reviewed_by','reviewed_utc','prior_review_history'):
                    if key in prior:row[key]=copy.deepcopy(prior[key])
            else:
                row['review_status']='source_changed_requires_review'
                row['prior_review_history']=copy.deepcopy(prior.get('prior_review_history',[]))+[prior]
        rows.append(row)
    units=[]
    for index in range(math.ceil(len(rows)/15)):
        identifier='identity-'+str(index+1).zfill(2)
        chosen=[r for r in rows if r['work_unit']==identifier]
        units.append({'id':identifier,'edition_ids':[r['edition_id'] for r in chosen],
            'status':'incomplete' if any(r['review_status'] in ('unreviewed','source_changed_requires_review') for r in chosen) else 'subject_review_recorded_remaining_gates_separate',
            'definition_of_done':'Read every introduction/chapter/heading; identify subject/event type; compare title, canonical link, year/date and imagery; cite specific evidence for corrections; preserve every published source-language string; record per-edition findings.'})
    queue={'schema_version':1,'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status':'enumerated_review_queue_not_editorial_readiness',
        'source_import_sha256_snapshot':file_hash(CONTENT/'expansion/calendar-features.json'),
        'original_playhub_source_sha256':review['source_original_playhub_sha256'],
        'catalog_sha256_snapshot':file_hash(CONTENT/'catalog.json'),
        'source_locale_file_sha256_snapshot':{p.stem:file_hash(p) for p in (CONTENT/'locales').glob('*.json')},
        'counts':{'editions':len(rows),'source_sections':sum(r['body_sections'] for r in rows),
            'confirmed_subject_mismatches':sum(r['review_status'].startswith('mismatch_confirmed') for r in rows),
            'unreviewed_editions':sum(r['review_status'] in ('unreviewed','source_changed_requires_review') for r in rows),
            'work_units':len(units),'maximum_editions_per_unit':15,
            'full_historical_signoffs':sum(r['full_historical_factual_signoff'] for r in rows)},
        'policy':['Title/keyword agreement alone is not semantic review. Read every paragraph and heading.',
            'Calendar scheduling is not evidence of an exact release date.',
            'Original Playhub source is immutable. Reviewed metadata/key migrations preserve all source-language body/headings.',
            'Preserve opaque IDs or explicit aliases, wrongly attached narratives and previous media briefs in archives.',
            'Images require exact subject/version and rights/quality checks; URL counts do not confer readiness.',
            'Snapshot hashes describe observed inputs. Refresh observations without resetting recorded reviews.'],
        'work_units':units,'editions':rows}
    assert len({r['edition_id'] for r in rows})==365 and queue['counts']['source_sections']==1656
    assert {i for unit in units for i in unit['edition_ids']}=={r['edition_id'] for r in rows}
    path.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(queue['counts'],indent=2))


if __name__=='__main__':main()
