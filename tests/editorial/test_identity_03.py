"""Real-data regression tests; no catalogue, locale or console writes."""
from pathlib import Path
import copy
import hashlib
import json
import runpy
import unittest

ROOT=Path(__file__).resolve().parents[2]
CONTENT=ROOT/'content'
HELPER=runpy.run_path(str(CONTENT/'expansion/integrate_calendar_identities_03.py'))
DOCUMENT=json.loads((CONTENT/'expansion/calendar-identity-corrections-03.json').read_text(encoding='utf-8'))
BASE=json.loads((CONTENT/'catalog.json').read_text(encoding='utf-8'))['entries']
LOCALES={f.stem:json.loads(f.read_text(encoding='utf-8')) for f in (CONTENT/'locales').glob('*.json')}
DIGEST=HELPER['digest']

# The assembler may already have run. Reconstruct only the44 affected original
# records from its receipt; leave every unrelated current catalogue row intact.
audit_path=CONTENT/'calendar-identity-integration-audit-03.json'
if audit_path.exists():
    audit=json.loads(audit_path.read_text(encoding='utf-8'))
    lookup={e['id']:e for e in BASE}
    for row in audit['original_records_before_migration']:
        for key in ('daily','opaque_destination'):
            original=row[key]
            lookup[original['id']].clear();lookup[original['id']].update(copy.deepcopy(original))

locale_audit_path=CONTENT/'calendar-identity-locale-audit-03.json'
if locale_audit_path.exists():
    audit=json.loads(locale_audit_path.read_text(encoding='utf-8'))
    for row in audit['removed_wrong_opaque_overlays']:
        LOCALES[row['locale']]['entries'][row['old_key']]=copy.deepcopy(row['archived_removed_record'])
    for row in audit.get('original_daily_records_before_migration',[]):
        LOCALES[row['locale']]['entries'][row['key']]=copy.deepcopy(row['record'])

class Identity03Tests(unittest.TestCase):
    def test_actual22_case_transaction(self):
        entries=copy.deepcopy(BASE);before={e['id']:e for e in BASE}
        receipt=HELPER['integrate'](entries,DOCUMENT);after={e['id']:e for e in entries}
        self.assertEqual(set(before),set(after))
        self.assertEqual(receipt['new_ids_added'],[])
        self.assertEqual(receipt['original_published_sections_preserved'],88)
        self.assertEqual(len(receipt['corrected_distinct_daily_stories']),22)
        for case in HELPER['whole_cases'](DOCUMENT):
            key=case['edition_id'];opaque=case['wrong_canonical_id']
            self.assertEqual(after[key]['body'],before[key]['body'])
            self.assertEqual(after[key]['story_headings'],before[key]['story_headings'])
            self.assertEqual(after[key]['calendar'],before[key]['calendar'])
            self.assertTrue(after[key]['calendar_only'])
            self.assertNotIn('linked_exhibit_id',after[key])
            self.assertEqual(after[key]['title'],case['proposed_partitions'][0]['title'])
            for media in ('images','videos','models'):
                self.assertEqual(after[key][media],[])
                self.assertEqual(after[opaque][media],before[opaque].get(media,[]))
            self.assertEqual(after[key]['sources'][:len(before[key]['sources'])],before[key]['sources'])
            self.assertEqual(after[opaque]['body'],case['restored_original_destination']['body'])
            self.assertEqual(after[opaque]['title'],before[opaque]['title'])
            self.assertEqual(after[opaque]['date']['precision'],'year')
        for key in ('daily-03-15','daily-04-06','never-alone','workbook-12-08-yakuza'):
            self.assertEqual(after[key],before[key],key+' must remain unchanged')
        self.assertEqual(after['daily-09-05']['year'],2006)
        self.assertEqual(after['workbook-12-08-yakuza']['year'],2005)
        self.assertEqual(after['daily-08-22']['body'],before['daily-08-22']['body'])

    def test_changed_final_case_is_atomic(self):
        entries=copy.deepcopy(BASE)
        final=HELPER['whole_cases'](DOCUMENT)[-1]
        next(e for e in entries if e['id']==final['edition_id'])['body'][0]+=' invalid'
        snapshot=DIGEST(entries)
        with self.assertRaises(ValueError):HELPER['integrate'](entries,DOCUMENT)
        self.assertEqual(DIGEST(entries),snapshot)

    def test_complete_second_pass_is_idempotent(self):
        entries=copy.deepcopy(BASE)
        receipt=HELPER['integrate'](entries,DOCUMENT)
        snapshot=copy.deepcopy(entries)
        replay=HELPER['integrate'](entries,DOCUMENT,receipt)
        self.assertEqual(entries,snapshot)
        self.assertEqual(replay,receipt)
        self.assertEqual(len(receipt['result_record_sha256']),44)

    def test_second_pass_rejects_any_record_or_receipt_change(self):
        entries=copy.deepcopy(BASE)
        receipt=HELPER['integrate'](entries,DOCUMENT)
        for key in (HELPER['whole_cases'](DOCUMENT)[0]['edition_id'],
                    HELPER['whole_cases'](DOCUMENT)[-1]['wrong_canonical_id']):
            changed=copy.deepcopy(entries)
            next(e for e in changed if e['id']==key)['factual_note']='changed after migration'
            snapshot=copy.deepcopy(changed)
            with self.assertRaises(ValueError):HELPER['integrate'](changed,DOCUMENT,receipt)
            self.assertEqual(changed,snapshot)
        changed_receipt=copy.deepcopy(receipt)
        changed_receipt['corrected_distinct_daily_stories'][0]['story_historical_year']+=1
        snapshot=copy.deepcopy(entries)
        with self.assertRaises(ValueError):HELPER['integrate'](entries,DOCUMENT,changed_receipt)
        self.assertEqual(entries,snapshot)

    def test_unreviewed_reference_change_rejected(self):
        document=copy.deepcopy(DOCUMENT)
        document['cases'][0]['restored_original_destination']['body'][0]+=' unreviewed'
        entries=copy.deepcopy(BASE);snapshot=DIGEST(entries)
        with self.assertRaises(ValueError):HELPER['integrate'](entries,document)
        self.assertEqual(DIGEST(entries),snapshot)

    def test_eight_locale_alias_migration(self):
        documents=copy.deepcopy(LOCALES)
        receipt=HELPER['migrate_locale_overlays'](documents,DOCUMENT)
        self.assertEqual(len(receipt['removed_wrong_opaque_overlays']),157)
        for case in HELPER['whole_cases'](DOCUMENT):
            for language,document in documents.items():
                if language not in case['source_locale_archives']:continue
                rows=document['entries'];key=case['edition_id']
                self.assertNotIn(case['wrong_canonical_id'],rows)
                if key in rows:
                    self.assertEqual(rows[key]['body'],LOCALES[language]['entries'][key]['body'])
                    self.assertEqual(rows[key]['story_headings'],LOCALES[language]['entries'][key]['story_headings'])
                    self.assertEqual(rows[key]['title'],case['proposed_partitions'][0]['title'])
        for language in documents:
            for key in ('daily-03-15','daily-04-06'):
                self.assertEqual(documents[language]['entries'].get(key),LOCALES[language]['entries'].get(key))

    def test_changed_locale_is_atomic(self):
        documents=copy.deepcopy(LOCALES)
        old=HELPER['whole_cases'](DOCUMENT)[-1]['wrong_canonical_id']
        documents['uk']['entries'][old]['body'][0]+=' invalid'
        snapshot=DIGEST(documents)
        with self.assertRaises(ValueError):HELPER['migrate_locale_overlays'](documents,DOCUMENT)
        self.assertEqual(DIGEST(documents),snapshot)

if __name__=='__main__':unittest.main(verbosity=2)
