import json, importlib.util
from pathlib import Path
R = Path(__file__).resolve().parents[2]
s = importlib.util.spec_from_file_location('p', R/'content/expansion/soundtrack-broad-pipeline.py')
p = importlib.util.module_from_spec(s); s.loader.exec_module(p)
D = p.RESEARCH/'final-user-score-priorities/simpsons'; D.mkdir(exist_ok=True)
queries = ['Simpsons Hit Run Professor Frink theme OST Jeff Tymoschuk', 'Simpsons Hit Run Dr Nick Monkey See Monkey Doh soundtrack', 'Simpsons Hit Run Kang Kodos Halloween Havoc soundtrack']
for i, query in enumerate(queries, 1):
    out = []
    for result in p.search(query)[:4]:
        try: out.append({'youtube_id': result['id'], 'actual_publication': p.watch(result['id'])})
        except Exception as ex: out.append({'youtube_id': result['id'], 'error': str(ex)})
    p.write(D/f'{i}-discover.json', {'query': query, 'candidates': out})
    print(i, [(x['youtube_id'], x.get('actual_publication',{}).get('title')) for x in out], flush=True)
