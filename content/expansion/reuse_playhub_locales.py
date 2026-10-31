"""Reuse published Playhub writing and translations, with no new translation."""
from pathlib import Path
import copy, hashlib, json, re
COMPLETE=('en','it','es','fr','de','pt','ru','uk')
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def first_sentence(text):
    parts=re.split(r'(?<=[.!?。！？])\s+',text,maxsplit=1)
    return parts[0]
def integrate(entries,root):
    source_path=Path('F:/Playhub/Plugin/Playhub/catalog/on-this-day.json')
    raw=source_path.read_bytes();source_digest=hashlib.sha256(raw).hexdigest();source=json.loads(raw);lookup={x['id']:x for x in entries}
    review=json.loads((root/'expansion/calendar-template-review.json').read_text(encoding='utf-8'))
    reviewed={x['id'] for x in review['entries']}
    locales={locale:{'schema_version':1,'locale':locale,'default_locale':'en','source':'Playhub published historical editions','entries':{}} for locale in COMPLETE}
    restored=[];editions=sections=0;coverage={locale:0 for locale in COMPLETE}
    for edition in source['editions']['entries']:
        if not edition.get('published'):continue
        editions+=1;theme=edition['theme'];daily_id='daily-'+edition['anniversary']['date'];daily=lookup[daily_id]
        linked=lookup.get(daily.get('linked_exhibit_id',''));canonical=linked if linked and linked['year']==daily['year'] else daily
        targets=[daily] if canonical is daily else [daily,canonical]
        source_sections=[theme['intro']]+[x['body'] for x in theme.get('chapters',[]) if x.get('body',{}).get('en')]
        source_headings=[theme['title']]+[x['title'] for x in theme.get('chapters',[]) if x.get('body',{}).get('en')]
        sections+=len(source_sections)
        if daily_id in reviewed:
            for entry in targets:
                entry['body']=[x['en'] for x in source_sections];entry['story_headings']=[x['en'] for x in source_headings]
                entry['summary']=first_sentence(entry['body'][0]);entry['editorial_mode']='playhub_published_story'
                entry['editorial_credit']='Playhub historical collection / LoZazaMastro. Original published text and chapter headings retained. Researched alternatives remain in separate authoring records.'
                entry['source_edition_restoration']={'reason':'Reuse the same published editorial version across existing source translations.','source_record_id':theme['id'],'reviewed_research_retained':'content/expansion/calendar-template-revisions-*.json'}
            restored.append(daily_id)
        for locale in COMPLETE:
            assert all(x.get(locale) for x in source_sections+source_headings),(daily_id,locale)
            coverage[locale]+=len(source_sections)
            if locale=='en' and daily_id not in reviewed:continue
            body=[x[locale] for x in source_sections];headings=[x[locale] for x in source_headings]
            for entry in targets:
                value={'title':entry['title'],'subtitle':theme['title'][locale],'summary':first_sentence(body[0]),'body':body,'story_headings':headings,'source_locale':locale,'provenance':{'source_record_id':theme['id'],'source_file':'catalog/on-this-day.json','source_repository':'https://github.com/LoZazaMastro/Playhub','source_sha256':source_digest,'mode':'Existing published source text; no new translation.'}}
                assert len(body)==len(entry['body']),(entry['id'],locale,len(body),len(entry['body']))
                locales[locale]['entries'][entry['id']]=value
    assert editions==365 and sections==1656 and len(restored)==53
    for locale,document in locales.items():write(root/'locales'/f'{locale}.json',document)
    audit={'source_path':str(source_path),'source_sha256':source_digest,'published_editions':editions,'original_english_sections':sections,'restored_source_english_editions':restored,'reused_locales':{locale:{'original_sections':coverage[locale],'runtime_records':len(locales[locale]['entries'])} for locale in COMPLETE},'partial_source_locales_not_exported':{'ja':245,'ko':245,'zh':245,'hi':245},'new_translations_created':0,'note':'Runtime localized records include both published daily identities and their same-event canonical destinations; this is not a distinct-article count.'}
    write(root/'playhub-localization-audit.json',audit)
    runtime=[entry for entry in entries if not(entry.get('calendar_only') and (base:=lookup.get(entry.get('linked_exhibit_id',''))) and base['year']==entry['year'])]
    localization={'schema_version':1,'policy':'Only existing Playhub translations have been reused. Missing museum reference translations fall back to English explicitly and are not marked complete.','runtime_distinct_articles':len(runtime),'requested_locales':{},'pending_reference_ids':[entry['id'] for entry in runtime if entry.get('editorial_mode')=='reference']}
    for locale in ('it','es','fr','de'):
        mapped=locales[locale]['entries'];missing=[entry['id'] for entry in runtime if entry['id'] not in mapped]
        localization['requested_locales'][locale]={'existing_source_translations_ready':len(runtime)-len(missing),'english_fallback_pending':len(missing),'missing_ids':missing}
    write(root/'localization-readiness.json',localization)
    return audit
