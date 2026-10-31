"""Separate already translated paragraphs into meaningful authored chapters."""
from pathlib import Path
from collections import defaultdict
import argparse, copy, hashlib, json

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/editorial-resume-20261030'
FIELDS = ('title', 'subtitle', 'summary', 'body', 'story_headings')
LANGS = ('en', 'it', 'fr', 'de', 'es')
parser = argparse.ArgumentParser()
parser.add_argument('--input', default='repartition-headings.json')
parser.add_argument('--output', default='TEXT-reviewed-pro-repartition.json')
args = parser.parse_args()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

catalog = read(ROOT / 'content/catalog.json')
owners = {e['id']: e for e in catalog['entries']}
locales = {lang: read(ROOT / f'content/museum-locales/{lang}.json')['entries'] for lang in LANGS[1:]}
grouped = defaultdict(list)
specification = read(BASE / args.input)
target_paragraph_count = specification.get('target_paragraph_count', 5)
for proposal in specification['patches']:
    grouped[proposal['entry_id']].append(proposal)
patches, requirements = [], []
for eid, proposals in grouped.items():
    owner = owners[eid]
    assert all(p['before_body_sha256'] == hashlib.sha256(owner['body'][p['split']['old_index']].encode('utf-8')).hexdigest() for p in proposals), (eid, 'baseline changed')
    splits = {p['split']['old_index']: p['split']['languages'] for p in proposals}
    assert len(splits) == len(proposals)
    mapping, next_index = {}, 0
    for old_index in range(len(owner['body'])):
        mapping[old_index] = [next_index, next_index + 1] if old_index in splits else [next_index]
        next_index += len(mapping[old_index])
    assert next_index == target_paragraph_count
    patch = {'collection': 'catalog', 'entry_id': eid, 'before': {k: copy.deepcopy(owner.get(k)) for k in FIELDS}, 'languages': {}, 'set': {}}
    for lang in LANGS:
        row = owner if lang == 'en' else locales[lang][eid]
        result = {k: copy.deepcopy(row.get(k, '')) for k in FIELDS}
        body, headings = [], []
        for old_index, paragraph in enumerate(row['body']):
            if old_index in splits:
                anchor = splits[old_index][lang].get('anchor')
                if anchor:
                    cut = paragraph.index(anchor)
                    parts = [paragraph[:cut].rstrip(), paragraph[cut:].lstrip()]
                else:
                    parts = paragraph.split('\n\n')
                assert len(parts) == 2
                body.extend(parts)
                headings.extend([splits[old_index][lang]['first'], splits[old_index][lang]['second']])
            else:
                body.append(paragraph)
                headings.append(row['story_headings'][old_index])
        assert ' '.join(' '.join(body).split()) == ' '.join(' '.join(row['body']).split())
        assert len(body) == len(headings) == target_paragraph_count and all(headings)
        result.update(body=body, story_headings=headings)
        patch['languages'][lang] = result
    for field in ('images', 'videos', 'models', 'soundtrack_rooms'):
        if not isinstance(owner.get(field), list):
            continue
        updated = copy.deepcopy(owner[field])
        for item in updated:
            index = item.get('story_paragraph')
            if index in mapping:
                item['story_paragraph'] = mapping[index][0]
        if updated != owner[field]:
            patch['before'][field] = copy.deepcopy(owner[field])
            patch['set'][field] = updated
    if isinstance(owner.get('sources'), list):
        sources = copy.deepcopy(owner['sources'])
        for source in sources:
            if not isinstance(source, dict):
                continue
            if 'story_paragraphs' in source:
                source['story_paragraphs'] = [new for old in source['story_paragraphs'] for new in mapping.get(old, [old])]
            if isinstance(source.get('paragraph_locators'), dict):
                source['paragraph_locators'] = {str(new): value for old, value in source['paragraph_locators'].items() for new in mapping.get(int(old), [int(old)])}
        if sources != owner['sources']:
            patch['before']['sources'] = copy.deepcopy(owner['sources'])
            patch['set']['sources'] = sources
    for old_index in splits:
        new_index = mapping[old_index][1]
        requirements.append({'entry_id': eid, 'story_paragraph': new_index,
                             'heading': patch['languages']['en']['story_headings'][new_index],
                             'media_subject': patch['languages']['en']['body'][new_index],
                             'reuse_existing_relevant_gallery_first': True})
    patches.append(patch)
out = {'batch_id': Path(args.output).stem.removeprefix('TEXT-'), 'completed': True, 'scope': 'Existing prose and all five translations preserved; only paragraph boundaries, their whitespace and headings change.', 'patches': patches, 'media_requirements': requirements}
(BASE / args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'games': len(patches), 'new_chapters_per_language': len(requirements)}))
