"""User-approved photograph presentation, including the complete console withdrawal."""
import json
from pathlib import Path


def photograph_only_console_ids(root):
    root = Path(root)
    index_path = root / 'models/index.json'
    if index_path.is_file() and json.loads(index_path.read_text(encoding='utf8')).get('catalog_console_models_withdrawn') is True:
        catalog = json.loads((root / 'content/catalog.json').read_text(encoding='utf8'))
        return frozenset(entry['id'] for entry in catalog['entries']
                         if entry.get('kind') in ('console', 'hardware') and entry.get('images'))
    path = root / 'content/expansion/hardware-identity-corrections.json'
    if not path.is_file():
        return frozenset()
    # This is an explicit preference for the original GBA, not a generic model-hold bypass.
    original_gba_ids = {'workbook-03-21-game-boy-advance', 'daily-03-21'}
    rows = json.loads(path.read_text(encoding='utf8')).get('overrides', [])
    return frozenset(row['id'] for row in rows
        if row.get('id') in original_gba_ids
        and row.get('kind') == 'console'
        and row.get('approved_model_id') is None
        and row.get('presentation') == 'photograph'
        and row.get('explicit_user_exception') is True)
