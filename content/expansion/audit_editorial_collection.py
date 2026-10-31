"""Measure real import completeness, editorial depth and illustration coverage."""
from pathlib import Path
import collections, hashlib, json
from datetime import datetime,timezone
from publication_readiness import evaluate
ROOT=Path(__file__).resolve().parents[1]
PLAYHUB=Path('F:/Playhub/Plugin/Playhub/catalog/on-this-day.json')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    source=read(PLAYHUB);published=[x for x in source['editions']['entries'] if x.get('published')]
    original=read(ROOT/'expansion/calendar-features.json');imported={x['id']:x for x in original['entries']}
    revisions={x['id']:x for agent in ('soundtrack','curation','native') for x in read(ROOT/f'expansion/calendar-template-revisions-{agent}.json')['entries']}
    catalog=read(ROOT/'catalog.json');lookup={x['id']:x for x in catalog['entries']};sections=chapters=0;edition_rows=[]
    for edition in published:
        slot=edition['anniversary']['date'];theme=edition['theme'];eid='daily-'+slot
        body=[theme['intro']['en']]+[x['body']['en'] for x in theme.get('chapters',[]) if x.get('body',{}).get('en')]
        headings=[theme['title']['en']]+[x['title']['en'] for x in theme.get('chapters',[]) if x.get('body',{}).get('en')]
        retained=imported[eid]['body']==body and imported[eid]['story_headings']==headings
        assert retained,f'Original English content changed in immutable import: {eid}'
        assert eid in lookup,f'Missing runtime calendar edition: {eid}'
        expected=imported[eid];assert lookup[eid]['body']==expected['body'],f'Original published writing lost at runtime: {eid}'
        canonical=lookup.get(lookup[eid].get('linked_exhibit_id',''))
        if canonical and canonical['year']==lookup[eid]['year']:assert canonical['body']==lookup[eid]['body'],f'Canonical story lost sections: {eid}'
        sections+=len(body);chapters+=len(body)-1
        edition_rows.append({'edition_id':eid,'subject':theme['subject'],'original_intro':1,'original_chapters':len(body)-1,'original_sections_sha256':hashlib.sha256(json.dumps(body,ensure_ascii=False).encode()).hexdigest(),'original_verbatim_import_retained':retained,'original_verbatim_runtime_retained':lookup[eid]['body']==body,'reviewed_research_retained_separately':eid in revisions,'published_body_sections':len(lookup[eid]['body']),'canonical_destination':canonical['id'] if canonical and canonical['year']==lookup[eid]['year'] else eid})
    readiness=evaluate(catalog['entries'])
    audit={'schema_version':1,'audit_utc':datetime.now(timezone.utc).isoformat(),'catalog_sha256':hashlib.sha256((ROOT/'catalog.json').read_bytes()).hexdigest(),'counts_are_not_interchangeable':'365 daily editions are not1291 distinct articles. Original chapters, calendar slots, distinct subjects, imported reference introductions and editorial signoff are measured separately.','playhub_import':{'published_editions':len(published),'english_introductions':len(published),'english_chapters':chapters,'original_sections_preserved_verbatim':sections,'runtime_calendar_editions':len(edition_rows),'reviewed_research_alternatives_preserved':len(revisions),'published_calendar_sections':sum(x['published_body_sections'] for x in edition_rows)},'readiness':{k:v for k,v in readiness.items() if k!='entries'},'edition_records':edition_rows}
    (ROOT/'editorial-collection-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='edition_records'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
