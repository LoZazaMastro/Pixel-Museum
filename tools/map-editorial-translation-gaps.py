"""Read-only, source-bound translation inventory. Does not generate translations."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib, json, re, runpy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/research/translation-planning'
OUT.mkdir(parents=True, exist_ok=True)
LANGUAGES = ('it', 'es', 'fr', 'de')
_quarantine = runpy.run_path(str(ROOT / 'tools/editorial_translation_quarantine.py'))
QUARANTINED = _quarantine['load_quarantine']()
is_quarantined = _quarantine['quarantined']

def read(path):
    return json.loads(path.read_text(encoding='utf8'))

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def normalize(text):
    return ' '.join(text.split())

def first_sentence(text):
    """Extract a sentence without treating an ordinal date as its ending.

    Keep the original substring byte-for-byte. Only known date/abbreviation
    contexts suppress a boundary; a year followed by a period still ends one.
    """
    months = r'(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember|Jan|Feb|Mär|Mrz|Apr|Aug|Sep|Sept|Okt|Nov|Dez)'
    titles = {'dr', 'dra', 'prof', 'mr', 'mrs', 'ms', 'sr', 'sra', 'srta', 'mme', 'mlle', 'st'}
    connectors = {'bzw', 'ca', 'vgl', 'bspw', 'ggf', 'inkl', 'zzgl', 'env', 'aprox'}
    month_abbreviations = {'jan', 'feb', 'mär', 'mrz', 'apr', 'aug', 'sep', 'sept', 'okt', 'nov', 'dez',
                           'janv', 'févr', 'avr', 'juil', 'oct', 'déc', 'ene', 'mar', 'abr', 'jun', 'jul', 'ago', 'dic'}
    for boundary in re.finditer(r'''(?P<stop>[.!?]+)["'”’»)\]]*\s+''', text):
        end = boundary.start() + len(boundary.group(0).rstrip())
        prefix = text[:boundary.end('stop')]
        following = text[boundary.end():]
        if boundary.group('stop') == '.':
            if (re.search(r'(?<!\w)(?:[1-9]|[12]\d|3[01])\.$', prefix)
                    and re.match(months + r'\b', following, re.IGNORECASE)):
                continue
            word = re.search(r'([^\W\d_]+)\.$', prefix)
            token = word.group(1).lower() if word else ''
            if token in titles or token in connectors:
                continue
            compact = re.sub(r'\s+', '', prefix[-12:]).lower()
            if any(compact.endswith(abbreviation) for abbreviation in ('e.g.', 'i.e.', 'z.b.', 'd.h.', 'p.ex.', 'p.ej.')):
                continue
            # Spaced forms such as "z. B." have a possible boundary inside
            # the abbreviation too; neither period terminates the sentence.
            pairs = {'z': r'B\.', 'd': r'h\.', 'p': r'(?:ex|ej)\.', 'i': r'e\.', 'e': r'g\.'}
            if token in pairs and re.match(pairs[token] + r'(?:\s|$)', following, re.IGNORECASE):
                continue
            if token in month_abbreviations and (re.match(r'\d', following)
                    or re.search(r'(?<!\w)\d{1,2}\.\s+[^\s.]+\.$', prefix)):
                continue
            if token in {'etc', 'inc', 'ltd', 'corp', 'co'} and following[:1].islower():
                continue
            if re.search(r'(?:\b[A-Z]\.){2,}$', prefix) and (following[:1].islower()
                    or re.match(r'(?:Army|Navy|Air Force)\b', following)):
                continue
        return text[:end]
    return text

catalog = read(ROOT / 'content/catalog.json')
history = read(ROOT / 'content/human-history.json')
aliases = read(ROOT / 'content/museum-revision-audit.json').get('aliases', {})
playhub_path = Path('F:/Playhub/Plugin/Playhub/catalog/on-this-day.json')
playhub = read(playhub_path)
source_hash = hashlib.sha256(playhub_path.read_bytes()).hexdigest()
reusable = defaultdict(list)

def offer(english, kind, translations, provenance):
    if not english or not all(isinstance(translations.get(lang), str) and translations[lang].strip() for lang in LANGUAGES):
        return
    reusable[(kind, normalize(english))].append({'translations': translations, 'provenance': provenance})

# Only an individual unchanged English unit may be reused. Never map a whole
# multi-topic date edition onto one newly separated game article.
for edition in playhub['editions']['entries']:
    if not edition.get('published'):
        continue
    theme = edition['theme']
    parts = [(theme['intro'], theme['title'], 'intro')]
    parts += [(chapter['body'], chapter['title'], 'chapter-' + str(n)) for n, chapter in enumerate(theme.get('chapters', []))]
    for body, title, part in parts:
        provenance = {'source': 'published_playhub', 'source_record_id': theme['id'], 'part': part, 'source_sha256': source_hash}
        offer(body.get('en'), 'body', body, provenance)
        offer(title.get('en'), 'story_headings', title, provenance)
        if body.get('en'):
            offer(first_sentence(body['en']), 'summary', {lang: first_sentence(body.get(lang, '')) for lang in LANGUAGES}, provenance)

# Historical reference translations are usable only at their reviewed English
# source snapshot. Partial exact-text matches remain explicit partial reuse.
locale_module = runpy.run_path(str(ROOT / 'content/expansion/integrate_wikipedia_locales.py'))
old_snapshots = defaultdict(list)
for filename in locale_module['BATCH_IDS']:
    batch = read(ROOT / 'content/expansion' / filename)
    for record in batch['entries']:
        entry_id = record.get('entry_id', record.get('id'))
        current_id = aliases.get(entry_id, entry_id)
        source = record.get('source', {})
        translations = record.get('translations', record.get('locales', {}))
        old_snapshots[current_id].append({'batch': filename, 'source': source})
        if not source or not all(lang in translations for lang in LANGUAGES):
            continue
        for field in ('subtitle', 'summary', 'body', 'story_headings'):
            units = source.get(field, []) if field in ('body', 'story_headings') else [source.get(field, '')]
            for n, english in enumerate(units):
                localized = {}
                for lang in LANGUAGES:
                    value = translations[lang].get(field, []) if field in ('body', 'story_headings') else [translations[lang].get(field, '')]
                    localized[lang] = value[n] if n < len(value) else ''
                offer(english, field, localized, {'source': 'reviewed_wikipedia_translation', 'entry_id': current_id, 'batch': filename, 'field': field, 'index': n, 'revision_id': source.get('revision_id')})

direct_translations = {}
for path in sorted((ROOT / 'content/expansion').glob('museum-translations-*.json')):
    batch = read(path)
    if batch.get('publication_status') != 'validated':
        continue
    review = read(ROOT / batch['independent_review'])
    assert review.get('status') == 'PASS'
    reviewed = {row['entry_id']: row for row in review.get('entries', [])}
    for row in batch['entries']:
        assert reviewed[row['entry_id']]['translation_sha256'] == digest(row['translation'])
        direct_translations[(batch['locale'], row['entry_id'])] = {**row, 'batch_file': path.relative_to(ROOT).as_posix(), 'review_receipt': batch['independent_review']}
rows = []
entry_inventory = []
for collection, document in [('museum', catalog), ('culture', history)]:
    for exhibit in document['entries']:
        for owner in [exhibit] + exhibit.get('editorial_features', []):
            owner_id = owner.get('id', exhibit['id'])
            before = len(rows)
            for field in ('title', 'subtitle', 'summary', 'body', 'story_headings'):
                values = owner.get(field, []) if field in ('body', 'story_headings') else [owner.get(field, '')]
                for n, english in enumerate(values):
                    if not isinstance(english, str) or not english.strip():
                        continue
                    row = {'entry_id': exhibit['id'], 'owner_id': owner_id, 'collection': collection, 'field': field, 'index': n, 'english': english, 'english_sha256': digest(english), 'source_words': len(english.split())}
                    # Canonical proper names are not automatically translated.
                    preserve = field == 'title' and collection == 'museum' and owner is exhibit and exhibit.get('kind') in ('game', 'console', 'hardware', 'person', 'company', 'organization')
                    options = reusable.get((field, normalize(english)), [])
                    if field == 'title':
                        options = []
                    accepted = []
                    for option in options:
                        provenance = option['provenance']
                        if provenance['source'] == 'reviewed_wikipedia_translation' and provenance['entry_id'] != exhibit['id']:
                            continue
                        accepted.append(option)
                    # Conflicting historic translations are a review item, not
                    # an arbitrary first-match selection.
                    row['languages'] = {}
                    for lang in LANGUAGES:
                        safe_options = [option for option in accepted if not is_quarantined(
                            english, option['translations'][lang], lang, field, QUARANTINED)]
                        translated = {option['translations'][lang] for option in safe_options}
                        direct = direct_translations.get((lang, owner_id))
                        source_field = direct.get('source', {}).get(field) if direct else None
                        source_unit = source_field[n] if isinstance(source_field, list) and n < len(source_field) else source_field
                        direct_text = None
                        if direct and source_unit == english:
                            localized_field = direct['translation'][field]
                            direct_text = localized_field[n] if isinstance(localized_field, list) else localized_field
                        if direct_text is not None and not is_quarantined(english, direct_text, lang, field, QUARANTINED):
                            state = {'status': 'reviewed_direct_translation', 'translated': direct_text, 'provenance': [{'batch_file': direct['batch_file'], 'independent_review': direct['review_receipt']}]}
                        elif preserve:
                            state = {'status': 'canonical_name_preserved', 'translated': english}
                        elif len(translated) == 1:
                            state = {'status': 'exact_source_reuse', 'translated': next(iter(translated)), 'provenance': [option['provenance'] for option in safe_options]}
                        elif len(translated) > 1:
                            state = {'status': 'conflicting_existing_translations', 'candidates': sorted(translated)}
                        else:
                            state = {'status': 'translation_required'}
                        if len(safe_options) != len(accepted) or (direct_text is not None and is_quarantined(english, direct_text, lang, field, QUARANTINED)):
                            state['quarantined_known_template'] = True
                        row['languages'][lang] = state
                    rows.append(row)
            units = rows[before:]
            prior = old_snapshots.get(exhibit['id'], [])
            source_fields = {field: owner.get(field, [] if field in ('body', 'story_headings') else '') for field in ('title', 'subtitle', 'summary', 'body', 'story_headings')}
            entry_inventory.append({'entry_id': exhibit['id'], 'owner_id': owner_id, 'collection': collection, 'title': owner.get('title', exhibit['title']), 'kind': exhibit['kind'], 'english_fields_sha256': digest(source_fields), 'source_words': sum(row['source_words'] for row in units), 'older_reference_snapshots': [{'batch': old['batch'], 'status': 'exact_current_fields' if all(old['source'].get(field) == value for field, value in source_fields.items()) else 'stale_or_partial'} for old in prior], 'languages': {lang: {'complete': all(row['languages'][lang]['status'] in ('canonical_name_preserved', 'exact_source_reuse', 'reviewed_direct_translation') for row in units), 'status_units': dict(Counter(row['languages'][lang]['status'] for row in units)), 'words_requiring_translation_or_review': sum(row['source_words'] for row in units if row['languages'][lang]['status'] in ('translation_required', 'conflicting_existing_translations'))} for lang in LANGUAGES}})

summary = {'schema_version': 1, 'policy': 'Planning only; no translations generated or runtime overlays published. Exact English unit matching only; never reuse an entire multi-game Playhub date edition for one game. Canonical game/person/hardware names preserved by default. English field hashes bind every future translation to this source checkpoint.', 'catalog_sha256': hashlib.sha256((ROOT / 'content/catalog.json').read_bytes()).hexdigest(), 'history_sha256': hashlib.sha256((ROOT / 'content/human-history.json').read_bytes()).hexdigest(), 'playhub_source_sha256': source_hash, 'museum_entries': len(catalog['entries']), 'culture_entries': len(history['entries']), 'article_and_feature_owners': len(entry_inventory), 'source_units': len(rows), 'source_words_including_headings_summaries': sum(row['source_words'] for row in rows), 'languages': {}}
for lang in LANGUAGES:
    summary['languages'][lang] = {'complete_owners_from_existing_sources': sum(owner['languages'][lang]['complete'] for owner in entry_inventory), 'partial_or_untranslated_owners': sum(not owner['languages'][lang]['complete'] for owner in entry_inventory), 'status_units': dict(Counter(row['languages'][lang]['status'] for row in rows)), 'words_requiring_translation_or_review': sum(row['source_words'] for row in rows if row['languages'][lang]['status'] in ('translation_required', 'conflicting_existing_translations')), 'exact_source_reuse_words': sum(row['source_words'] for row in rows if row['languages'][lang]['status'] == 'exact_source_reuse')}
for name, document in [('summary.json', summary), ('entry-gaps.json', {'entries': entry_inventory}), ('source-units.json', {'units': rows})]:
    path = OUT / name
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(document, ensure_ascii=True, indent=2) + '\n', encoding='utf8')
    temporary.replace(path)
print(json.dumps(summary, indent=2))
