"""Admit complete five-language batches while keeping unrelated app data intact."""
from pathlib import Path
import argparse, hashlib, json, re, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/editorial-resume-20261030'
LANGS = ('en', 'it', 'fr', 'de', 'es')
FIELDS = {'title', 'subtitle', 'summary', 'body', 'story_headings'}

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def write(p, value):
    tmp = p.with_suffix('.progress.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(p)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('batches', nargs='+')
    args = parser.parse_args()
    jobs = {j['batch_id']: j for j in read(BASE / 'jobs.json')['jobs']}
    registry_path = BASE / 'important-game-registry.json'
    registered_important = {r['entry_id'] for r in read(registry_path)['entries']} if registry_path.exists() else set()
    docs = {name: read(ROOT / f'content/{name}.json') for name in ('catalog', 'human-history')}
    owners = {}
    for collection, doc in docs.items():
        for entry in doc['entries']:
            owners[collection, entry['id']] = entry
            for feature in entry.get('editorial_features', []):
                owners[collection, feature['id']] = feature
    progress_path = BASE / 'progress.json'
    progress = read(progress_path) if progress_path.exists() else {'completed': {}, 'important_entry_ids': []}
    paths = []
    admitted = []
    for batch in args.batches:
        job = jobs[batch]
        path = BASE / f'TEXT-{batch}.json'
        output = read(path)
        assert output.get('batch_id') == batch and output.get('completed') is True, (batch, 'incomplete')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if progress['completed'].get(batch, {}).get('sha256') == digest:
            continue
        patches = output['patches']
        expected = set(job['entry_ids'])
        for eid in job['entry_ids']:
            expected.update(f['id'] for f in owners[job['collection'], eid].get('editorial_features', []))
        assert {p['entry_id'] for p in patches} == expected, (batch, 'owner IDs differ')
        important = set(output.get('important_entry_ids', [])) | (expected & registered_important)
        for patch in patches:
            eid = patch['entry_id']
            owner = owners[job['collection'], eid]
            assert patch.get('collection', 'catalog') == job['collection']
            assert set(patch.get('set', {})) <= FIELDS | {'sources'}, (eid, 'protected field')
            assert set(patch['languages']) == set(LANGS), (eid, 'missing language')
            english = patch['languages']['en']
            count = len(english['body'])
            minimum = 6 if owner.get('kind') in ('console', 'computer') else 5 if eid in important else 2 if owner.get('kind') == 'game' else 1
            assert count >= minimum, (eid, 'minimum cards', minimum)
            assert len(english['summary'].split()) <= 55, (eid, 'timeline summary too long')
            assert english['summary'].strip() != english['body'][0].strip(), (eid, 'summary duplicates introduction')
            for lang in LANGS:
                row = patch['languages'][lang]
                assert set(row) == FIELDS, (eid, lang, 'unexpected text fields')
                assert len(row['body']) == len(row['story_headings']) == count
                assert all(isinstance(s, str) and s.strip() for s in row['body'] + row['story_headings'])
                assert all(isinstance(row[k], str) for k in ('title', 'subtitle', 'summary'))
                assert not re.search('[\u3040-\u30ff\u3400-\u9fff]', '\n'.join([row['title'], row['subtitle'], row['summary'], *row['story_headings'], *row['body']])), (eid, lang, 'non-romanized name')
                if lang != 'en':
                    assert row['body'] != english['body'], (eid, lang, 'English fallback')
        paths.append(path)
        admitted.append((batch, digest, patches, sorted(important)))
    if paths:
        subprocess.run([sys.executable, str(ROOT / 'tools/apply-editorial-recovery-patches.py'),
                        *[str(p.relative_to(ROOT)) for p in paths]], cwd=ROOT, check=True)
    for batch, digest, patches, important in admitted:
        progress['completed'][batch] = {'sha256': digest, 'owners': len(patches),
                                       'cards_per_language': sum(len(p['languages']['en']['body']) for p in patches)}
        progress['important_entry_ids'] = sorted(set(progress['important_entry_ids']) | set(important))
    progress['completed_pro_batches'] = 144
    progress['completed_total'] = 144 + len(progress['completed'])
    progress['remaining'] = 319 - progress['completed_total']
    write(progress_path, progress)
    print(json.dumps({k: progress[k] for k in ('completed_total', 'remaining')}))

if __name__ == '__main__':
    main()
