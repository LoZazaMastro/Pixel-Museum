"""Real 45-canonical migration: exact archives, ownership and atomic failure."""
import copy
import json
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / 'content'
MODULE = runpy.run_path(str(CONTENT / 'expansion/integrate_calendar_narratives_06.py'))
DOCUMENT = MODULE['checked_document'](ROOT)


def baseline():
    entries = json.loads((CONTENT / 'catalog.json').read_text(encoding='utf-8'))['entries']
    locales = {p.stem:json.loads(p.read_text(encoding='utf-8')) for p in (CONTENT / 'locales').glob('*.json')}
    audit = CONTENT / 'calendar-canonical-narratives-audit-06.json'
    if audit.exists():
        receipt = json.loads(audit.read_text(encoding='utf-8'))
        lookup = {e['id']:e for e in entries}
        for row in receipt['original_records']:
            for key in ('original_daily', 'original_canonical'):
                original = row[key]
                lookup[original['id']].clear()
                lookup[original['id']].update(copy.deepcopy(original))
        for row in receipt['removed_canonical_locale_overlays']:
            locales[row['locale']]['entries'][row['entry_id']] = copy.deepcopy(row['record'])
    return entries, locales


class Narratives06Tests(unittest.TestCase):
    def test_media_jobs_archive_all_reviewed_briefs_and_preserve_nested_features(self):
        refresh=runpy.run_path(str(ROOT/'tools/refresh-media-backlog.py'))
        backlog=json.loads((CONTENT/'editorial/media-backlog.json').read_text(encoding='utf-8'))
        entries=json.loads((CONTENT/'catalog.json').read_text(encoding='utf-8'))['entries']
        lookup={e['id']:e for e in entries}
        targets={c['target_canonical_id'] for c in DOCUMENT['cases']}
        for row in backlog['entries']:
            if row['entry_id'] not in targets:continue
            migrations=row['source_identity_migrations']
            index=next(i for i,m in enumerate(migrations) if m['source']==MODULE['DECLARATION'])
            previous=migrations.pop(index)
            row['sections']=copy.deepcopy(previous['previous_sections'])
            row['existing_article_source_urls']=copy.deepcopy(previous['previous_article_source_urls'])
            row['hero_task']=copy.deepcopy(previous['previous_hero_task'])
            row['existing_media']=copy.deepcopy(previous['previous_existing_media'])
        before=copy.deepcopy(backlog)
        changed=refresh['migrate_reviewed_narrative_jobs'](backlog,lookup)
        self.assertEqual(set(changed),targets)
        old={r['entry_id']:r for r in before['entries']}
        self.assertEqual(len(backlog['entries']),len(before['entries']))
        for row in backlog['entries']:
            identifier=row['entry_id']
            if identifier not in targets:
                self.assertEqual(row,old[identifier]);continue
            archive=row['source_identity_migrations'][-1]
            self.assertEqual(archive['previous_sections'],old[identifier]['sections'])
            self.assertEqual(archive['previous_existing_media'],old[identifier]['existing_media'])
            self.assertEqual(row.get('editorial_features'),old[identifier].get('editorial_features'))
            self.assertEqual([s['body_sha256'] for s in row['sections']],
                [__import__('hashlib').sha256(b.encode()).hexdigest() for b in lookup[identifier]['body']])
        repeated=copy.deepcopy(backlog)
        self.assertEqual(refresh['migrate_reviewed_narrative_jobs'](backlog,lookup),[])
        self.assertEqual(backlog,repeated)
        broken=copy.deepcopy(before)
        next(r for r in broken['entries'] if r['entry_id']==DOCUMENT['cases'][-1]['target_canonical_id'])['sections'][-1]['body_sha256']='unreviewed'
        snapshot=copy.deepcopy(broken)
        with self.assertRaises(AssertionError):refresh['migrate_reviewed_narrative_jobs'](broken,lookup)
        self.assertEqual(broken,snapshot)

    def test_actual_45_targets_preserve_all_archival_languages_and_media_rights(self):
        entries, locales = baseline()
        before = copy.deepcopy(entries)
        old_locales = copy.deepcopy(locales)
        old = {e['id']:e for e in before}
        receipt = MODULE['integrate'](entries, locales, DOCUMENT)
        after = {e['id']:e for e in entries}
        self.assertEqual(len(receipt['actions']), 45)
        self.assertEqual([e['id'] for e in entries], [e['id'] for e in before])
        self.assertEqual(receipt['new_subjects_claimed'], 0)
        affected = set()
        for case in DOCUMENT['cases']:
            daily, target = case['edition_id'], case['target_canonical_id']
            affected.update((daily, target))
            parent = after[target]
            for key in ('body', 'story_headings', 'summary'):
                self.assertEqual(parent[key], case['proposed_canonical'][key])
                self.assertEqual(after[daily][key], old[daily][key])
            for key in ('year', 'date', 'kind', 'related_ids'):
                self.assertEqual(parent.get(key), old[target].get(key))
            self.assertEqual(parent.get('editorial_features'), old[target].get('editorial_features'))
            for field in ('images', 'videos', 'models'):
                expected = copy.deepcopy(old[target].get(field, []))
                for media in expected:
                    media.pop('story_paragraph', None)
                self.assertEqual(parent.get(field, []), expected, (target, field))
            expected_daily = copy.deepcopy(old[daily])
            for correction in case['daily_source_credit_corrections']:
                expected_daily['sources'][correction['source_index']]['attribution'] = correction['replacement']
            self.assertEqual(after[daily], expected_daily)
            for language in old_locales:
                self.assertEqual(locales[language]['entries'].get(daily), old_locales[language]['entries'].get(daily))
                self.assertNotIn(target, locales[language]['entries'])
        for e in before:
            if e['id'] not in affected:
                self.assertEqual(e, after[e['id']])
        for language, document in locales.items():
            for eid, row in document['entries'].items():
                self.assertEqual(row, old_locales[language]['entries'][eid])
        self.assertTrue(any(row['record']['body'] for row in receipt['removed_canonical_locale_overlays']))
        self.assertEqual(len(receipt['original_records']), 45)

    def test_supplemental_sources_and_corrected_authorship_reach_canonicals(self):
        entries, locales = baseline()
        MODULE['integrate'](entries, locales, DOCUMENT)
        by_id = {e['id']:e for e in entries}
        sources = by_id['workbook-02-10-vagrant-story']['sources']
        self.assertIn('https://www.rpgfan.com/review/vagrant-story-2/', {s['url'] for s in sources})
        sources = by_id['workbook-02-27-pokemon-red-e-pokemon-green']['sources']
        self.assertTrue(any('469662408' in s['url'] for s in sources))
        sources = by_id['workbook-03-24-bloodborne']['sources']
        tips = next(s for s in sources if '24-tips' in s['url'])
        self.assertIn('Sid Shuman', tips['author'])
        self.assertNotIn('FromSoftware', tips['publisher'])
        sources = by_id['workbook-03-26-pillars-of-eternity']['sources']
        self.assertTrue(any('kickstarter.com' in s['url'] for s in sources))

    def test_only_parent_paragraph_bindings_and_briefs_are_retired(self):
        entries, locales = baseline()
        e = next(e for e in entries if e['id']=='workbook-02-11-final-fantasy-viii')
        e['media_briefs'] = [{'body_index':3, 'caption':'Original archived brief'}]
        e['cards'] = [{'body_index':3, 'heading':'Original bound card'}]
        e['editorial_features'] = [{'id':'separate-work', 'body':['one','two','three','four'],
                                   'images':[{'url':'https://example.org/feature.jpg', 'story_paragraph':3}]}]
        before = copy.deepcopy(e)
        receipt = MODULE['integrate'](entries, locales, DOCUMENT)
        actual = next(e for e in entries if e['id']==before['id'])
        self.assertNotIn('media_briefs', actual)
        self.assertNotIn('cards', actual)
        self.assertEqual(actual['editorial_features'], before['editorial_features'])
        archive = next(r for r in receipt['original_records'] if r['original_canonical']['id']==before['id'])
        self.assertEqual(archive['original_canonical'], before)

    def test_late_daily_drift_and_last_locale_drift_are_atomic(self):
        for error in ('daily', 'locale'):
            entries, locales = baseline()
            last = DOCUMENT['cases'][-1]
            if error=='daily':
                next(e for e in entries if e['id']==last['edition_id'])['body'][-1] += ' changed'
            else:
                locales['uk']['entries'][last['target_canonical_id']]['body'][-1] += ' changed'
            before = copy.deepcopy((entries, locales))
            with self.assertRaises(ValueError):
                MODULE['integrate'](entries, locales, DOCUMENT)
            self.assertEqual((entries, locales), before)

    def test_unreviewed_narrative_subject_drift_and_duplicates_are_rejected(self):
        for error in ('document', 'subject', 'duplicate'):
            entries, locales = baseline()
            document = copy.deepcopy(DOCUMENT)
            if error=='document':
                document['cases'][0]['proposed_canonical']['body'][0] += ' unsupported'
            elif error=='subject':
                next(e for e in entries if e['id']==DOCUMENT['cases'][0]['target_canonical_id'])['year'] += 1
            else:
                entries.append(copy.deepcopy(entries[0]))
            before = copy.deepcopy((entries, locales))
            with self.assertRaises(ValueError):
                MODULE['integrate'](entries, locales, document)
            self.assertEqual((entries, locales), before)

    def test_immediate_second_pass_checks_full_receipt_and_output(self):
        entries, locales = baseline()
        receipt = MODULE['integrate'](entries, locales, DOCUMENT)
        before = copy.deepcopy((entries, locales))
        self.assertEqual(MODULE['integrate'](entries, locales, DOCUMENT, receipt), receipt)
        self.assertEqual((entries, locales), before)
        changed = copy.deepcopy(receipt)
        changed['actions'][0]['daily_prose_unchanged'] = False
        with self.assertRaises(ValueError):
            MODULE['integrate'](entries, locales, DOCUMENT, changed)
        self.assertEqual((entries, locales), before)
        next(e for e in entries if e['id']==DOCUMENT['cases'][0]['target_canonical_id'])['images'].append({'url':'https://example.org/new.jpg'})
        changed_before = copy.deepcopy((entries, locales))
        with self.assertRaises(ValueError):
            MODULE['integrate'](entries, locales, DOCUMENT, receipt)
        self.assertEqual((entries, locales), changed_before)


if __name__=='__main__':
    unittest.main(verbosity=2)
