"""Compare reviewed card values with actual authoring and runtime catalogues."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'build/research/playhub-semantic-coverage/wiki-clarity'
sources = [FOLDER / relative for relative in [
    'strong-first17/candidate.json', 'pass6-root/candidate.json',
    'experience-fourteen-article-template-repair-provenance-corrected-candidate.json',
    'additional-three/candidate.json', 'repeated-final23/candidate.json',
    'secret-world-final/candidate.json', 'army-final/candidate.json',
    'final-five-root/candidate.json', 'final-seven-editorial/candidate.json',
    'remaining-semantic-three/five-additional-concrete-cards-candidate.json',
]]
sources.append(ROOT / 'build/research/nobuyoshi-sano-primary-portrait/three-concrete-career-cards-candidate.json')
sources.append(ROOT / 'build/research/gba-sp-launch-and-concrete-article/four-wikipedia-cards-launch-without-regional-prose-candidate.json')
sources.append(FOLDER / 'new-bounded-current-audit/sayonara-three/three-concrete-sayonara-cards-clarity-edited-candidate.json')
sources.append(ROOT / 'build/research/mega-drive-three-concrete-cards/three-concrete-wikipedia-mega-drive-cards-clear-identities-candidate.json')
sources.append(ROOT / 'build/research/gta2-three-concrete-cards/three-concrete-gta2-cards-multiplier-claim-omitted-candidate.json')
sources.append(FOLDER / 'sakaguchi-bounded-two/two-concrete-sakaguchi-cards-standalone-fantasian-candidate.json')
expected = {}
for path in sources:
    candidate = json.loads(path.read_text(encoding='utf8'))
    for row in candidate.get('replacements', candidate.get('changes', [])):
        if 'body' not in row:
            continue
        key = row['entry_id'], row['source_chapter_index']
        assert key not in expected, ('Overlapping reviewed replacement', key)
        expected[key] = row['body'], row['heading']
    for identifier, article in candidate.get('entries', {}).items():
        for index in article['replacement_paragraphs']:
            key = identifier, int(index)
            assert key not in expected, ('Overlapping reviewed replacement', key)
            expected[key] = article['body'][int(index)], article['story_headings'][int(index)]
assert len(expected) == 201
catalogues = {}
for relative in ['content/catalog.json', 'build/runtime-preview/content/catalog.json']:
    data = (ROOT / relative).read_bytes()
    entries = {e['id']: e for e in json.loads(data)['entries']}
    for (identifier, index), (body, heading) in expected.items():
        actual = entries[identifier]
        assert actual['body'][index] == body, (relative, identifier, index, 'body')
        assert actual['story_headings'][index] == heading, (relative, identifier, index, 'heading')
    catalogues[relative] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
proof = {'status': 'PASS', 'cards': len(expected), 'source_candidate_files': len(sources),
         'actual_catalogues': catalogues,
         'method': 'Independent reconstruction of every approved body and heading pair from reviewed candidates, compared with both actual catalogues. Count is not inferred from provenance.'}
output = FOLDER / 'root-actual201-master-runtime-proof.json'
output.write_text(json.dumps(proof, indent=2) + '\n', encoding='utf8')
print(json.dumps(proof))
