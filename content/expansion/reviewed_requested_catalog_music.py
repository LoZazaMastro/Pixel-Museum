"""Late user-requested exclusions and publisher-sourced music presentation fixes.

Run after all exact-body/media source guards; does not edit source recordings.
"""
import hashlib
import json


def apply(catalog, root):
    plan_path = root / 'build/research/requested-catalog-music-corrections/candidate.json'
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    for rel, expected in plan['source_files'].items():
        assert hashlib.sha256((root / rel).read_bytes()).hexdigest() == expected, rel
    entries = catalog['entries']
    removed = {row['id'] for row in plan['excluded_entries']}
    actual = {e['id'] for e in entries if e['title'].lower().startswith('9-nine')}
    assert actual in (removed, set()), ('9-nine source identity drift', actual)
    entries[:] = [e for e in entries if e['id'] not in removed]
    reference_changes = []

    def prune(value, path):
        if isinstance(value, list):
            original = list(value)
            value[:] = [v for v in value if not isinstance(v, str) or v not in removed]
            if value != original:
                reference_changes.append(path)
            for i, child in enumerate(value):
                prune(child, path + '/' + str(i))
        elif isinstance(value, dict):
            for key, child in list(value.items()):
                if key in removed or isinstance(child, str) and child in removed:
                    del value[key]
                    reference_changes.append(path + '/' + str(key))
                else:
                    prune(child, path + '/' + str(key))

    prune(catalog, '')
    by_id = {e['id']: e for e in entries}
    rebirth = by_id['wikipedia-71040722']['soundtrack']['tracks']
    by_video = {t['youtube_id']: t for t in rebirth}
    title_changes = 0
    for patch in plan['rebirth_title_patches']:
        track = by_video[patch['youtube_id']]
        assert track['title'] in (patch['before'], patch['after']), patch
        if track['title'] == patch['before']:
            track['title'] = patch['after']
            track['display_title_source'] = plan['rebirth_title_source']
            title_changes += 1
    gow = plan['god_of_war']
    tracks = by_id[gow['entry_id']]['soundtrack']['tracks']
    rejected = [t for t in tracks if t['youtube_id'] == gow['remove_recording']]
    main = [t for t in tracks if t['youtube_id'] == gow['first_recording']]
    assert len(main) == 1 and len(rejected) <= 1
    tracks[:] = main + [t for t in tracks if t['youtube_id'] not in (gow['remove_recording'], gow['first_recording'])]
    return {'excluded_entries': sorted(actual), 'references_pruned': reference_changes,
            'rebirth_english_titles_changed': title_changes,
            'god_of_war_first_recording': main[0]['youtube_id'],
            'god_of_war_rejected_alternate_removed': bool(rejected),
            'policy': 'Official English publisher track names, original recording IDs retained. Other untranslated albums remain separately audited, not silently machine-translated.'}
