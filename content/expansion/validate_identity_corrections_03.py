"""Validate the proposed identity migration without applying it anywhere."""
from pathlib import Path
import copy
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[1]

def read(path): return json.loads(path.read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def require(condition,message):
    if not condition: raise ValueError(message)

def validate(document):
    require(document['schema_version']==1,'Unknown declaration schema')
    require(document['status'].startswith('prepared_'),'A proposal must not claim application')
    original_path=Path(r'F:\Playhub\Plugin\Playhub\catalog\on-this-day.json')
    require(sha(original_path)==document['source_original_playhub_sha256'],'Original Playhub source changed')
    imported={e['id']:e for e in read(ROOT/'expansion/calendar-features.json')['entries']}
    source={e['theme']['id']:e for e in read(original_path)['editions']['entries']}
    queue={e['edition_id']:e for e in read(ROOT/'editorial/playhub-identity-review-queue.json')['editions']}
    require(len(document['cases'])==24,'Wrong number of new reviewed conflicts')
    require(len({c['edition_id'] for c in document['cases']})==24,'Duplicate conflict')
    sections=0
    for case in document['cases']:
        identifier=case['edition_id'];old=imported[identifier];q=queue[identifier]
        archive=case['archived_published_edition']
        require(archive==old,identifier+': imported archive changed')
        require(case['source_body_sha256']==digest(old['body'])==q['published_english_body_sha256'],identifier+': body hash differs')
        require(case['source_headings_sha256']==digest(old['story_headings'])==q['published_english_headings_sha256'],identifier+': heading hash differs')
        theme=source[case['source_record_id']]['theme']
        require(case['archived_original_theme']==theme,identifier+': multilingual source theme differs')
        require(case['calendar_slot_unchanged']==old['calendar'],identifier+': scheduled day changed')
        locales=case['source_locale_archives']
        require(set(locales)=={'en','it','es','fr','de','pt','ru','uk'},identifier+': missing original language')
        used=[]
        for language,localized in locales.items():
            body=[theme['intro'][language]]+[c['body'][language] for c in theme['chapters']]
            headings=[theme['title'][language]]+[c['title'][language] for c in theme['chapters']]
            require(localized['body']==body and localized['story_headings']==headings,identifier+': source-language strings changed')
            require(localized['body_sha256']==digest(body) and localized['headings_sha256']==digest(headings),identifier+': bad locale hash')
        for part in case['proposed_partitions']:
            indices=part['source_body_indices'];used+=indices
            require(part['source_heading_indices']==indices,identifier+': heading/body partition differs')
            for language,localized in locales.items():
                projected=part['exact_source_locales'][language]
                require(projected['body']==[localized['body'][i] for i in indices],identifier+': projected source body differs')
                require(projected['story_headings']==[localized['story_headings'][i] for i in indices],identifier+': projected source heading differs')
                require(projected['body_sha256']==digest(projected['body']) and projected['headings_sha256']==digest(projected['story_headings']),identifier+': projected locale hash differs')
            require(part['proposed_media']==dict(images=[],videos=[],models=[]),identifier+': wrong-subject media transfer')
        require(sorted(used)==list(range(len(old['body']))) and len(set(used))==len(used),identifier+': omitted or repeated source section')
        reference=case['restored_original_destination'];evidence=case['restored_reference_source']
        path=ROOT/evidence['cache_file'];require(sha(path)==evidence['cache_sha256'],identifier+': source snapshot hash differs')
        cache=read(path);pages=cache.get('pages') or cache['response']['query']['pages'];page=next(p for p in pages if p.get('pageid')==evidence['page_id'])
        require(page['revisions'][0]['revid']==evidence['revision_id']==reference['attribution']['revision_id'],identifier+': revision differs')
        require(hashlib.sha256(page['extract'].encode()).hexdigest()==evidence['extract_sha256'],identifier+': extract differs')
        paragraphs=[p.strip() for p in page['extract'].split('\n') if p.strip()]
        if 'selected_intro_sentence_indices' in reference['provenance']:
            expected=[]
            for index,selected in reference['provenance']['selected_intro_sentence_indices'].items():
                sentences=re.split(r'(?<=[.!?])\s+',paragraphs[int(index)])
                expected.append(' '.join(sentences[i] for i in selected))
        else:
            expected=[paragraphs[i] for i in reference['provenance']['selected_intro_paragraph_indices']]
        replacements=reference['provenance'].get('mechanical_replacements',[])
        if replacements:
            require(reference['provenance']['selected_source_body_before_mechanical_correction']==expected,identifier+': original selection archive differs')
            require(reference['provenance']['selected_source_body_sha256']==digest(expected),identifier+': pre-correction hash differs')
            for replacement in replacements:
                require(sum(b.count(replacement['old']) for b in expected)==replacement['occurrences'],identifier+': correction occurrence count differs')
                expected=[b.replace(replacement['old'],replacement['new']) for b in expected]
            require(reference['provenance']['corrected_body_sha256']==digest(expected),identifier+': corrected hash differs')
            require('grammatical correction' in reference['editorial_credit'],identifier+': mechanical correction not disclosed')
        require(reference['body']==expected,identifier+': restored reference text differs from attributed selection')
        require(len(reference['body'])==len(reference['story_headings']) and all(reference['story_headings']),identifier+': missing reference heading')
        require(reference['attribution']['source_url']==f"https://en.wikipedia.org/w/index.php?oldid={evidence['revision_id']}",identifier+': mutable revision link')
        require(reference['attribution']['license']=='CC BY-SA 4.0' and 'action=history' in reference['attribution']['contributors_url'],identifier+': missing attribution')
        require(not any(reference[k] for k in ('images','videos','models')),identifier+': inherited media in restored reference')
        if identifier=='daily-09-05':
            require(case['proposed_calendar_historical_year']==2006 and case['proposed_partitions'][0]['canonical_original_year']==2005,identifier+': original and regional edition years flattened')
        if identifier=='daily-04-22':
            require(reference['summary'].startswith('A remaster of the Replicant version called') and reference['summary'].endswith('in 2021.'),identifier+': truncated remake summary')
        if identifier=='daily-09-01':
            require(reference['summary'].endswith('Warner Bros. Interactive Entertainment.'),identifier+': publisher abbreviation truncated sentence')
        sections+=len(old['body'])
    require(sections==105,'Original section total differs')
    return dict(cases=24,sections=sections,languages=8,localized_sections=840,
        exact_partitions=26,restored_reference_selections=24,source_preservation='PASS',
        all_original_sections_accounted_once='PASS',reference_revision_license_and_selection='PASS',
        media_transfer='NONE',assembly='NOT PERFORMED')

if __name__=='__main__':
    document=read(ROOT/'expansion/calendar-identity-corrections-03.json')
    result=validate(document)
    broken=copy.deepcopy(document)
    broken['cases'][0]['proposed_partitions'][0]['exact_source_locales']['it']['body'][0]+=' changed'
    try: validate(broken)
    except ValueError: result['changed_translation_rejected']='PASS'
    else: raise AssertionError('Changed source translation was accepted')
    broken=copy.deepcopy(document)
    broken['cases'][0]['restored_original_destination']['body'][0]+=' changed'
    try: validate(broken)
    except ValueError: result['changed_reference_selection_rejected']='PASS'
    else: raise AssertionError('Changed reference selection was accepted')
    print(json.dumps(result,indent=2))
