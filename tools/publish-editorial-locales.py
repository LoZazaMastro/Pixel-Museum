"""Publish exact-source reuse and reviewed translation batches as partial overlays."""
from pathlib import Path
from collections import defaultdict, Counter
import hashlib, json, runpy

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('title', 'subtitle', 'summary', 'body', 'story_headings')
LANGUAGES = ('it', 'es', 'fr', 'de')
_quarantine = runpy.run_path(str(ROOT / 'tools/editorial_translation_quarantine.py'))
QUARANTINED = _quarantine['load_quarantine']()
is_quarantined = _quarantine['quarantined']
CHANGE_NOTICES = {
 'it':'Testo localizzato dai brani inglesi corrispondenti. Attribuzioni e licenze delle fonti originali conservate; i brani non ancora tradotti restano in inglese.',
 'es':'Texto localizado a partir de los pasajes ingleses correspondientes. Se conservan las atribuciones y licencias originales; los pasajes pendientes siguen en inglés.',
 'fr':'Texte localisé à partir des passages anglais correspondants. Les attributions et licences originales sont conservées ; les passages non encore traduits restent en anglais.',
 'de':'Aus den entsprechenden englischen Textpassagen lokalisiert. Ursprüngliche Quellenangaben und Lizenzen bleiben erhalten; noch nicht übersetzte Passagen bleiben auf Englisch.'
}


def read(path):
    return json.loads(path.read_text(encoding='utf8'))

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf8')
    temporary.replace(path)

runpy.run_path(str(ROOT / 'tools/map-editorial-translation-gaps.py'))
planning = read(ROOT / 'build/research/translation-planning/source-units.json')['units']
summary = read(ROOT / 'build/research/translation-planning/summary.json')
units = defaultdict(list)
for row in planning:
    units[row['owner_id']].append(row)
owners = {}
original_credits = {}
for collection in ('catalog', 'human-history'):
    for exhibit in read(ROOT / 'content' / (collection + '.json'))['entries']:
        for owner in [exhibit] + exhibit.get('editorial_features', []):
            fields = {field: owner.get(field, [] if field in ('body', 'story_headings') else '') for field in FIELDS}
            identifier = owner.get('id', exhibit['id'])
            if identifier in owners and owners[identifier] != fields:
                raise ValueError('Conflicting English owners for locale ID ' + identifier)
            owners[identifier] = fields
            original_credits[identifier] = owner.get('editorial_credit', '')

overlays = {lang: {'schema_version': 2, 'locale': lang, 'default_locale': 'en', 'source_language': 'en', 'publication_status': 'partial', 'source_catalog_sha256': summary['catalog_sha256'], 'source_history_sha256': summary['history_sha256'], 'hash_encoding': 'sha256 of compact UTF-8 JSON; ensure_ascii=false, sort_keys=true, no trailing newline', 'entries': {}} for lang in LANGUAGES}
person_event_locales = runpy.run_path(str(ROOT / 'content/expansion/reviewed_person_event_locales.py'))['load'](ROOT, owners)
for identifier, fields in owners.items():
    for lang in LANGUAGES:
        selected = [row for row in units.get(identifier, [])
                    if row['languages'][lang]['status'] == 'exact_source_reuse'
                    and not is_quarantined(row['english'], row['languages'][lang]['translated'], lang, row['field'], QUARANTINED)]
        if not selected:
            continue
        row = {}
        provenance = {'source_fields_sha256': digest(fields), 'source_field_hashes': {field: digest(value) for field, value in fields.items()}, 'source_units': [], 'english_fallback_units': []}
        for unit in selected:
            field, index = unit['field'], unit['index']
            if field not in row:
                row[field] = list(fields[field]) if isinstance(fields[field], list) else fields[field]
            if isinstance(row[field], list):
                row[field][index] = unit['languages'][lang]['translated']
            else:
                row[field] = unit['languages'][lang]['translated']
            provenance['source_units'].append({'field': field, 'index': index, 'english_sha256': unit['english_sha256'], 'mode': 'exact_source_reuse', 'references': unit['languages'][lang]['provenance']})
        for unit in units.get(identifier, []):
            if unit['languages'][lang]['status'] not in ('exact_source_reuse', 'canonical_name_preserved'):
                provenance['english_fallback_units'].append({'field': unit['field'], 'index': unit['index'], 'english_sha256': unit['english_sha256']})
        row['editorial_credit'] = (original_credits.get(identifier, '') + '\n' + CHANGE_NOTICES[lang]).strip()
        row['provenance'] = provenance
        overlays[lang]['entries'][identifier] = row

# New translations never silently migrate to a changed English article.
skipped_display_cleanup_translations = []
reviewed_english_fallbacks = read(ROOT / "content/expansion/reviewed-locale-english-fallbacks.json")["rows"]
for path in sorted((ROOT / 'content/expansion').glob('museum-translations-*.json')):
    batch = read(path)
    if batch.get('publication_status') != 'validated':
        continue
    lang = batch['locale']
    review_path = batch.get('independent_review')
    if not review_path:
        raise ValueError('Reviewed translation batch has no review receipt: ' + path.name)
    review = read(ROOT / review_path)
    if review.get('status') != 'PASS':
        raise ValueError('Translation review is not PASS: ' + path.name)
    reviewed = {row['entry_id']: row for row in review.get('entries', [])}
    if lang not in overlays:
        raise ValueError('Unsupported translation locale ' + lang)
    for addition in batch.get('entries', []):
        identifier = addition['entry_id']
        if identifier in person_event_locales[lang]:
            # These explicitly reviewed replacements have already passed exact
            # current-English binding checks. Older source batches stay archived.
            continue
        if identifier not in owners:
            # The user removed this standalone machine entry while retaining
            # Josef Kates. Keep the reviewed source translation in its archive,
            # but never publish an overlay that resurrects the removed owner.
            if identifier == 'bertie-the-brain':
                exclusions = read(ROOT / 'content/expansion/user-selected-game-exclusions.json')
                if any(row['id'] == identifier for row in exclusions['rows']):
                    overlays[lang]['entries'].pop(identifier, None)
                    skipped_display_cleanup_translations.append({'entry_id': identifier, 'locale': lang, 'reason': 'Exact standalone Bertie entry removed by the user; archived translation retained'})
                    continue
            retired = next((row for row in reviewed_english_fallbacks if row['entry_id'] == identifier and row.get('removed_owner') and row['old_fields_sha256'] == addition['source_fields_sha256']), None)
            if retired and hashlib.sha256((ROOT / retired['candidate_path']).read_bytes()).hexdigest() == retired['candidate_sha256']:
                skipped_display_cleanup_translations.append({'entry_id': identifier, 'locale': lang, 'reason': retired['reason']})
                continue
            raise ValueError('Reviewed translation owner absent: ' + identifier)
        fields = owners[identifier]
        if addition['source_fields_sha256'] != digest(fields):
            # Omit stale translated labels instead of migrating reviewed prose.
            # Only this exact display-only cleanup is tolerated; all other drift fails.
            frozen = addition.get('source')
            cleaned = dict(frozen) if frozen else None
            if cleaned is not None:
                if cleaned.get('subtitle') == 'From the reference collection':
                    cleaned['subtitle'] = ''
                cleaned['story_headings'] = ['' if value == 'From the reference collection' else value for value in cleaned.get('story_headings', [])]
            if frozen and digest(frozen) == addition['source_fields_sha256'] and cleaned == fields:
                skipped_display_cleanup_translations.append({'entry_id': identifier, 'locale': lang, 'reason': 'Exact generic display-label removal; current English fallback retained'})
                overlays[lang]['entries'].pop(identifier, None)
                continue
            fallback = next((row for row in reviewed_english_fallbacks if row['entry_id'] == identifier and row['old_fields_sha256'] == addition['source_fields_sha256'] and row['new_fields_sha256'] == digest(fields)), None)
            if fallback and hashlib.sha256((ROOT / fallback['candidate_path']).read_bytes()).hexdigest() == fallback['candidate_sha256']:
                skipped_display_cleanup_translations.append({'entry_id': identifier, 'locale': lang, 'reason': fallback['reason']})
                overlays[lang]['entries'].pop(identifier, None)
                continue
            raise ValueError('Translation source fields changed: ' + identifier)
        translated = addition['translation']
        for field in FIELDS:
            english_units = fields[field] if isinstance(fields[field], list) else [fields[field]]
            localized_units = translated.get(field, []) if isinstance(fields[field], list) else [translated.get(field, '')]
            if any(is_quarantined(english, localized, lang, field, QUARANTINED)
                   for english, localized in zip(english_units, localized_units)):
                raise ValueError('Known non-translation template in reviewed batch: ' + path.name + ' / ' + identifier)
        if reviewed.get(identifier, {}).get('translation_sha256') != digest(translated):
            raise ValueError('Translation changed after its independent review: ' + identifier)
        if addition.get('source') is not None and addition['source'] != fields:
            raise ValueError('Frozen English snapshot changed: ' + identifier)
        for field in FIELDS:
            if field not in translated:
                raise ValueError('Incomplete reviewed translation: ' + identifier + '/' + field)
            if isinstance(fields[field], list) and len(fields[field]) != len(translated[field]):
                raise ValueError('Translation paragraph alignment changed: ' + identifier + '/' + field)
        translated = dict(translated)
        translated['editorial_credit'] = (original_credits.get(identifier, '') + '\n' + CHANGE_NOTICES[lang]).strip()
        translated['provenance'] = {'source_fields_sha256': digest(fields), 'source_field_hashes': {field: digest(value) for field, value in fields.items()}, 'mode': 'direct_translation_from_current_english', 'translation_method': batch.get('translation_method'), 'review_receipt': batch.get('independent_review'), 'batch_file': path.relative_to(ROOT).as_posix(), 'source_units': [{'field': field, 'index': n, 'english_sha256': digest(english), 'mode': 'reviewed_direct_translation'} for field in FIELDS for n, english in enumerate(fields[field] if isinstance(fields[field], list) else [fields[field]])], 'english_fallback_units': []}
        overlays[lang]['entries'][identifier] = translated

for lang, rows in person_event_locales.items():
    overlays[lang]['entries'].update(rows)

audit = {'schema_version': 1, 'policy': 'Partial overlays; omitted fields and recorded units intentionally retain English. No complete-language claim.', 'source_catalog_sha256': summary['catalog_sha256'], 'source_history_sha256': summary['history_sha256'], 'languages': {}, 'skipped_display_cleanup_translations': skipped_display_cleanup_translations}
for lang, document in overlays.items():
    path = ROOT / 'content/museum-locales' / (lang + '.json')
    write(path, document)
    audit['languages'][lang] = {'overlay_owners': len(document['entries']), 'complete_owners': sum(not row['provenance']['english_fallback_units'] for row in document['entries'].values()), 'source_bound_translated_units': sum(len(row['provenance']['source_units']) for row in document['entries'].values()), 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
write(ROOT / 'build/research/translation-planning/published-overlay-audit.json', audit)
print(json.dumps(audit, indent=2))
