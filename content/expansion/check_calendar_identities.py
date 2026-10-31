#!/usr/bin/env python3
"""Read-only identity-migration tests; no master assembly or package writes."""
import copy
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest

CONTENT=Path(__file__).resolve().parents[1]
JOIN=runpy.run_path(str(CONTENT/'expansion/integrate_calendar_identities.py'))
CALENDAR=runpy.run_path(str(CONTENT/'expansion/integrate_calendar.py'))
LOCALES=runpy.run_path(str(CONTENT/'expansion/reuse_playhub_locales.py'))
def read(path): return json.loads(path.read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


class IdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document=read(CONTENT/'expansion/calendar-identity-corrections-02.json')
        baseline={e['id']:copy.deepcopy(e) for e in read(CONTENT/'catalog.json')['entries']}
        for filename,field in [('calendar-canonical-narratives-audit-07.json','original_records'),
                               ('calendar-canonical-narratives-audit-06.json','original_records'),
                               ('calendar-prose-restoration-audit-05.json','original_records'),
                               ('calendar-identity-integration-audit-03.json','original_records_before_migration')]:
            path=CONTENT/filename
            if not path.exists():continue
            for row in read(path)[field]:
                daily=row.get('original_daily',row.get('daily'))
                old=row.get('original_canonical',row.get('opaque_destination'))
                baseline[daily['id']]=copy.deepcopy(daily)
                if old is not None:baseline[old['id']]=copy.deepcopy(old)
        baseline.pop('wikipedia-292874',None)
        # Reconstruct the frozen inherited records so this regression remains
        # useful after the real master has already adopted the migration.
        inherited={c['edition_id']:c['archived_published_edition'] for c in cls.document['cases']}
        inherited.update({c['original_canonical_id']:c['archived_mislabeled_master_snapshot'] for c in cls.document['cases']})
        inherited['wikipedia-2829113']=cls.document['archived_street_fighter_reference']
        cls.original=[copy.deepcopy(inherited.get(e['id'],e)) for e in baseline.values() if e['id']!='never-alone']
        cls.paths=[CONTENT/'catalog.json',*(CONTENT/'locales').glob('*.json')]
        cls.before={str(p):sha(p) for p in cls.paths}

    def migrated(self):
        entries=copy.deepcopy(self.original)
        JOIN['integrate'](entries,self.document)
        CALENDAR['integrate'](entries,read(CONTENT/'expansion/date-corrections.json'))
        return entries,{e['id']:e for e in entries}

    def test_exact_published_copy_all_editions_and_destinations(self):
        entries,lookup=self.migrated()
        original={e['id']:e for e in self.original}
        days=[e for e in entries if e.get('calendar_only')]
        self.assertEqual(len(days),365)
        self.assertEqual(sum(len(e['body']) for e in days),1656)
        destinations=set()
        aliases=0
        for daily in days:
            before=original[daily['id']]
            self.assertEqual((daily['body'],daily['story_headings'],daily['calendar']),
                             (before['body'],before['story_headings'],before['calendar']))
            canonical=lookup.get(daily.get('linked_exhibit_id',''))
            if canonical and canonical['year']==daily['year']:
                aliases+=1
                self.assertEqual((canonical['body'],canonical['story_headings']),(daily['body'],daily['story_headings']))
            destinations.add(canonical['id'] if canonical else daily['id'])
        self.assertEqual((aliases,len(destinations)),(333,365))
        self.assertEqual({e['id'] for e in entries}-{e['id'] for e in self.original},{'never-alone'})

    def test_subjects_exact_references_and_separate_date_semantics(self):
        _,lookup=self.migrated()
        for case in self.document['cases']:
            daily=lookup[case['edition_id']]
            self.assertEqual((daily['title'],daily['year'],daily['linked_exhibit_id']),
                             (case['corrected_title'],case['corrected_year'],case['corrected_canonical_id']))
            self.assertEqual(daily['date']['precision'],'year')
            old=lookup[case['original_canonical_id']]
            self.assertEqual(old['body'],case['restored_original_destination']['body'])
            self.assertEqual(old['attribution']['license'],'CC BY-SA 4.0')
            self.assertFalse(old.get('calendar_editorial'))
        self.assertEqual(lookup['never-alone']['date']['month'],11)
        self.assertEqual(lookup['never-alone']['date']['day'],18)
        self.assertEqual(lookup['wikipedia-2829113']['date']['precision'],'year')
        self.assertNotIn('attribution',lookup['wikipedia-2829113'])
        hell=lookup['workbook-05-21-senua-s-saga-hellblade-ii']
        self.assertNotIn('9th century',' '.join(hell['body']))
        self.assertEqual(len(hell['body']),2)

    def test_stale_or_unreviewed_change_rejected_atomically(self):
        for case_id,field in [('daily-05-21','body'),('daily-08-30','story_headings')]:
            entries=copy.deepcopy(self.original)
            row=next(e for e in entries if e['id']==case_id)
            row[field][0]+=' changed'
            before=copy.deepcopy(entries)
            with self.assertRaisesRegex(ValueError,'published narrative changed'):
                JOIN['integrate'](entries,self.document)
            self.assertEqual(entries,before)
        doc=copy.deepcopy(self.document)
        doc['cases'][0]['corrected_canonical_id']='unreviewed-new-game'
        with self.assertRaisesRegex(ValueError,'unreviewed identity'):
            JOIN['integrate'](copy.deepcopy(self.original),doc)

    def test_eight_generated_locales_preserve_every_original_string(self):
        entries,lookup=self.migrated()
        with tempfile.TemporaryDirectory(prefix='identity-locales-') as folder:
            target=Path(folder)
            (target/'expansion').mkdir()
            (target/'expansion/calendar-template-review.json').write_bytes((CONTENT/'expansion/calendar-template-review.json').read_bytes())
            LOCALES['integrate'](entries,target)
            mapping={c['original_canonical_id']:c['corrected_canonical_id'] for c in self.document['cases']}
            titles={c['edition_id']:c['corrected_title'] for c in self.document['cases']}
            titles.update({c['corrected_canonical_id']:c['corrected_title'] for c in self.document['cases']})
            for language in LOCALES['COMPLETE']:
                old=read(CONTENT/'locales'/f'{language}.json')
                # This tests the earlier two-case migration in isolation.
                # Reconstruct aliases removed by subsequent reviewed repairs.
                narrative06=CONTENT/'calendar-canonical-narratives-audit-06.json'
                if narrative06.exists():
                    for record in read(narrative06)['removed_canonical_locale_overlays']:
                        if record['locale']==language:
                            old['entries'][record['entry_id']]=copy.deepcopy(record['record'])
                narrative07=CONTENT/'calendar-canonical-narratives-audit-07.json'
                if narrative07.exists():
                    for record in read(narrative07)['removed_canonical_locale_overlays']:
                        if record['locale']==language:
                            old['entries'][record['entry_id']]=copy.deepcopy(record['record'])
                later=read(CONTENT/'calendar-identity-locale-audit-03.json')
                for record in later['removed_wrong_opaque_overlays']:
                    if record['locale']==language:
                        old['entries'][record['old_key']]=copy.deepcopy(record['archived_removed_record'])
                for record in later['original_daily_records_before_migration']:
                    if record['locale']==language:
                        old['entries'][record['key']]=copy.deepcopy(record['record'])
                for record in read(CONTENT/'calendar-prose-restoration-audit-05.json')['removed_canonical_locale_overlays']:
                    if record['locale']==language:
                        old['entries'][record['entry_id']]=copy.deepcopy(record['record'])
                new=read(target/'locales'/f'{language}.json')
                self.assertEqual({k:v for k,v in old.items() if k!='entries'}, {k:v for k,v in new.items() if k!='entries'})
                expected={}
                for identifier,row in old['entries'].items():
                    destination=mapping.get(identifier,identifier)
                    value=copy.deepcopy(row)
                    if destination in titles:
                        value['title']=titles[destination]
                    expected[destination]=value
                self.assertEqual(new['entries'],expected,language)
                for case in self.document['cases']:
                    source_row=new['entries'].get(case['edition_id'])
                    canonical_row=new['entries'].get(case['corrected_canonical_id'])
                    if source_row:
                        self.assertEqual(source_row['body'],canonical_row['body'])
                        self.assertEqual(source_row['story_headings'],canonical_row['story_headings'])

    def test_media_jobs_and_source_briefs_preserved_with_one_addition(self):
        _,lookup=self.migrated()
        backlog=read(CONTENT/'editorial/media-backlog.json')
        backlog['entries']=[r for r in backlog['entries'] if r['entry_id']!='never-alone']
        backlog['batches']=[b for b in backlog['batches'] if b['id']!='P6-reviewed-source-identities']
        for row in backlog['entries']:
            history=row.pop('source_identity_migrations',[])
            if history:
                old=history[0]
                row['sections']=copy.deepcopy(old['previous_sections'])
                row['body_sections']=len(row['sections'])
                row['minimum_distinct_contextual_sections']=len(row['sections'])//2+1
                row['existing_article_source_urls']=copy.deepcopy(old['previous_article_source_urls'])
                # The original two-case receipt captured hero state; later
                # prose-only migrations need not have changed or archived it.
                if 'previous_hero_task' in old:
                    row['hero_task']=copy.deepcopy(old['previous_hero_task'])
        previous={r['entry_id']:copy.deepcopy(r) for r in backlog['entries']}
        result=JOIN['migrate_media_backlog'](backlog,lookup,self.document)
        self.assertEqual(result['added_entry_ids'],['never-alone'])
        current={r['entry_id']:r for r in backlog['entries']}
        self.assertEqual(set(current),set(previous)|{'never-alone'})
        for case in self.document['cases']:
            identifier=case['original_canonical_id']
            self.assertEqual(current[identifier]['source_identity_migrations'][0]['previous_sections'],previous[identifier]['sections'])
            target=current[case['corrected_canonical_id']]
            self.assertEqual([s['brief'] for s in target['sections']],[s['brief'] for s in previous[identifier]['sections']])
        for identifier in set(previous)-set(result['migrated_existing_job_ids']):
            self.assertEqual(current[identifier],previous[identifier])
        units=[i for b in backlog['batches'] for u in b['work_units'] for i in u['entry_ids']]
        self.assertEqual(len(units),len(set(units)))
        self.assertEqual(set(units),set(current))
        repeated=JOIN['migrate_media_backlog'](backlog,lookup,self.document)
        self.assertEqual(repeated,{'added_entry_ids':[],'migrated_existing_job_ids':[]})

    @classmethod
    def tearDownClass(cls):
        if cls.before!={str(p):sha(p) for p in cls.paths}:
            raise AssertionError('Tests modified actual source/master files')


if __name__=='__main__': unittest.main(verbosity=2)
