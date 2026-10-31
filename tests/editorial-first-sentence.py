"""Run the real pure extractor without executing the inventory's file writes."""
import ast
import copy
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
module = ast.parse((ROOT / 'tools/map-editorial-translation-gaps.py').read_text(encoding='utf8'))
function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'first_sentence')
namespace = {'re': re}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(ROOT / 'tools/map-editorial-translation-gaps.py'), 'exec'), namespace)
extract = namespace['first_sentence']

cases = [
    ('Am 12. September 1998 erschien das Spiel. Es folgte eine Fortsetzung.', 'Am 12. September 1998 erschien das Spiel.'),
    ('Am 1. März 1999 erschien es. Danach folgte mehr.', 'Am 1. März 1999 erschien es.'),
    ('Am 31. Dez. 1999 erschien es. Danach folgte mehr.', 'Am 31. Dez. 1999 erschien es.'),
    ('Released in 1999. December brought a sequel.', 'Released in 1999.'),
    ('Released on 12. It returned later.', 'Released on 12.'),
    ('Dr. Mario uses falling capsules. Another game followed.', 'Dr. Mario uses falling capsules.'),
    ('Prof. Müller worked with Dr. Smith. They built it.', 'Prof. Müller worked with Dr. Smith.'),
    ('It uses e.g. maps and logs. Another system follows.', 'It uses e.g. maps and logs.'),
    ('Das gilt z. B. für Karten. Danach geht es weiter.', 'Das gilt z. B. für Karten.'),
    ('Il utilise p. ex. des cartes. Une suite arrive.', 'Il utilise p. ex. des cartes.'),
    ('Incluye p. ej. mapas. Después cambia.', 'Incluye p. ej. mapas.'),
    ('The U.S. Army appears. It is fictional.', 'The U.S. Army appears.'),
    ('It launched in the U.S. It later reached Europe.', 'It launched in the U.S.'),
    ('This is it! Another follows.', 'This is it!'),
    ('He said "go." Then left.', 'He said "go."'),
    ('No terminal period', 'No terminal period'),
    ('', ''),
]
for source, expected in cases:
    assert extract(source) == expected, (source, extract(source), expected)

# Causal regression: all four requested languages and English from the actual
# published source whose German date was reduced to "Am 12.". Source prose is
# never normalized or rewritten, only an exact prefix is selected.
published = Path('F:/Playhub/Plugin/Playhub/catalog/on-this-day.json')
document = json.loads(published.read_text(encoding='utf8'))
theme = next(row['theme'] for row in document['editions']['entries'] if row['theme']['id'] == 'workbook-09-12-pokemon-giallo')
before = copy.deepcopy(theme)
for lang in ('en', 'it', 'es', 'fr', 'de'):
    source = theme['intro'][lang]
    selected = extract(source)
    assert source.startswith(selected) and len(selected) > 100, (lang, selected)
    assert '1998' in selected and 'Pikachu' in selected, (lang, selected)
    assert not re.fullmatch(r'Am\s+\d{1,2}\.', selected)
    print(lang, selected)
assert theme == before, 'Translation extraction changed the original paragraph'
print('PASS real extractor: ordinal dates, abbreviations, genuine year/sentence endings, five published source languages and untouched prose')
