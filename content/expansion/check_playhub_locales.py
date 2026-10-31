"""Exact source-copy assertions; no translation service or network is involved."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
source_path=Path('F:/Playhub/Plugin/Playhub/catalog/on-this-day.json')
source_bytes=source_path.read_bytes();source_digest=hashlib.sha256(source_bytes).hexdigest();source=json.loads(source_bytes)
entries={x['id']:x for x in json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))['entries']}
locales={locale:json.loads((ROOT/'locales'/f'{locale}.json').read_text(encoding='utf-8')) for locale in ('en','it','es','fr','de','pt','ru','uk')}
restorations=json.loads((ROOT/'expansion/calendar-prose-restorations-05.json').read_text(encoding='utf-8'))
exceptions={case['target_canonical_id']:case for case in restorations['biography_cases']+restorations['english_correction_cases']}
import runpy
narrative_cases={};narrative_modules={};narrative_declarations={}
for batch,count in [('06',45),('07',12)]:
    module=runpy.run_path(str(ROOT/f'expansion/integrate_calendar_narratives_{batch}.py'))
    document=module['checked_document'](ROOT.parent)
    cases={case['target_canonical_id']:case for case in document['cases']}
    assert len(cases)==count and not ((set(exceptions)|set(narrative_cases))&set(cases))
    receipt=json.loads((ROOT/f'calendar-canonical-narratives-audit-{batch}.json').read_text(encoding='utf-8'))
    assert receipt['reviewed_declaration_sha256']==module['DECLARATION_SHA256']
    assert {row['canonical_id'] for row in receipt['actions']}==set(cases)
    narrative_cases.update(cases)
    narrative_modules.update({target:module for target in cases})
    narrative_declarations[batch]=module['DECLARATION_SHA256']
identity03=json.loads((ROOT/'expansion/calendar-identity-corrections-03.json').read_text(encoding='utf-8'))
unlinked={case['edition_id'] for case in identity03['cases'] if case['correction_kind']=='whole_subject_mapping'}
assert len(unlinked)==22
editions=sections=canonical_count=0;destinations=set();coverage={locale:0 for locale in locales}
for edition in source['editions']['entries']:
    if not edition.get('published'):continue
    editions+=1;theme=edition['theme'];eid='daily-'+edition['anniversary']['date'];daily=entries[eid]
    source_sections=[theme['intro']]+[x['body'] for x in theme.get('chapters',[]) if x.get('body',{}).get('en')]
    source_headings=[theme['title']]+[x['title'] for x in theme.get('chapters',[]) if x.get('body',{}).get('en')]
    assert daily['body']==[x['en'] for x in source_sections],eid
    assert daily['story_headings']==[x['en'] for x in source_headings],eid
    sections+=len(source_sections)
    canonical=entries.get(daily.get('linked_exhibit_id',''));targets=[daily]
    if canonical and canonical['year']==daily['year']:
        canonical_count+=1
        if canonical['id'] in narrative_cases:
            case=narrative_cases[canonical['id']]
            assert eid==case['edition_id'],eid
            for field in ('body','story_headings','summary'):
                assert canonical[field]==case['proposed_canonical'][field],(eid,field)
            marker=canonical['canonical_narrative_enrichment']
            assert marker['source_daily_id']==eid and marker['reviewed_declaration_sha256']==narrative_modules[canonical['id']]['DECLARATION_SHA256'],eid
            assert all(canonical['id'] not in document['entries'] for document in locales.values()),eid
        elif canonical['id'] in exceptions:
            case=exceptions[canonical['id']]
            if case['case_kind']=='canonical_biography_reference_restoration':
                assert canonical['body']==case['proposed_canonical']['body'] and canonical['attribution']==case['proposed_canonical']['attribution'],eid
            else:
                body=list(daily['body']);body[case['paragraph_index']]=case['replacement_paragraph']
                assert canonical['body']==body and canonical['story_headings']==daily['story_headings'],eid
            assert all(canonical['id'] not in document['entries'] for document in locales.values()),eid
        else:
            targets.append(canonical)
            assert canonical['body']==daily['body'] and canonical['story_headings']==daily['story_headings'],eid
    if eid in unlinked:assert not daily.get('linked_exhibit_id'),eid
    destination=canonical['id'] if canonical and canonical['year']==daily['year'] else daily['id'];assert destination not in destinations,('Unexpected duplicate destination',eid);destinations.add(destination)
    for locale,document in locales.items():
        expected_body=[x[locale] for x in source_sections];expected_headings=[x[locale] for x in source_headings]
        for entry in targets:
            row=document['entries'].get(entry['id'])
            if locale=='en' and not row:assert entry['body']==expected_body;continue
            assert row and row['body']==expected_body and row['story_headings']==expected_headings,(entry['id'],locale)
            assert row['source_locale']==locale and row['provenance']['source_sha256']==source_digest
            assert len(row['body'])==len(entry['body']) and all(len(x.encode('utf-8'))<=16384 for x in row['body']),entry['id']
        coverage[locale]+=len(expected_body)
assert editions==365 and sections==1656 and canonical_count==333-len(unlinked)+1
receipt={'schema_version':1,'source_path':str(source_path),'source_sha256':source_digest,'source_published_editions':editions,'source_english_introductions':365,'source_english_chapters':1291,'original_english_sections_in_runtime':sections,'same_event_canonical_destinations':canonical_count,'independent_edition_destinations':editions-canonical_count,'missing_editions':[],'missing_complete_locale_sections':{locale:1656-count for locale,count in coverage.items()},'reused_complete_locales':list(locales),'partial_locales':{'ja':{'complete_editions':245,'missing_editions':120},'ko':{'complete_editions':245,'missing_editions':120},'zh':{'complete_editions':245,'missing_editions':120},'hi':{'complete_editions':245,'missing_editions':120}},'new_translations_created':0,'reviewed_canonical_prose_exception_ids':sorted(set(exceptions)|set(narrative_cases)),'canonical_narratives_declaration_sha256':narrative_declarations,'no_model_console_articles_retained':[{ 'id':entry['id'],'title':entry['title']} for entry in entries.values() if entry.get('kind')=='console' and not entry.get('models')],'checks':'Every published daily body and heading exactly matches its original source, with all eight source-language editions retained. Explicit reviewed canonical prose exceptions preserve archived originals and use English fallback instead of misapplying source translations. No dates, models or media are substituted by localization.'}
(ROOT/'playhub-import-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Playhub source import PASS:365 editions,1291 chapters+365 introductions,1656 exact English archival sections,{canonical_count} canonical+{365-canonical_count} independent destinations,{len(exceptions)+len(narrative_cases)} explicitly reviewed canonical prose exceptions,8 original locales preserved.')
