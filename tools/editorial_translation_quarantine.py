"""Exact, source-bound quarantine of observed non-translations.

This is a finite evidence list, not a vocabulary/language detector. A legitimate
translation can contain every word of a known template without matching its
exact English/translated pair. Reviewed corrections have a different digest.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'content/editorial/playhub-template-quarantine-v4.json'


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def quarantine_key(english, translated, locale, field):
    return locale, field, digest(english), digest(translated)


def load_quarantine(path=REGISTRY):
    document = json.loads(Path(path).read_text(encoding='utf-8'))
    result = {}
    for row in document['units']:
        assert digest(row['english']) == row['english_sha256']
        assert digest(row['translated']) == row['translated_sha256']
        result[quarantine_key(row['english'], row['translated'], row['locale'], row['field'])] = row['reason']
    return result


def quarantined(english, translated, locale, field, registry):
    return quarantine_key(english, translated, locale, field) in registry
