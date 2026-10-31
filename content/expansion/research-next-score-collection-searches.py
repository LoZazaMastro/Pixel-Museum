"""Bounded discovery, not admission, of readily public modern/Switch score collections."""
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
spec = importlib.util.spec_from_file_location('v', ROOT / 'tools/discover-museum-videos.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
queries = {
    'arceus': 'Pokemon Legends Arceus full soundtrack timestamps',
    'scarletviolet': 'Pokemon Scarlet Violet full soundtrack timestamps original',
    'bayonetta3': 'Bayonetta 3 original soundtrack full album timestamps',
    'starfield': 'Starfield original soundtrack Inon Zur full album Bethesda',
    'residentevil4-2023': 'Resident Evil 4 2023 official soundtrack Capcom full album',
    'metaphor': 'Metaphor ReFantazio original soundtrack full album timestamps',
    'ff7rebirth': 'Final Fantasy VII Rebirth original soundtrack full album timestamps',
    'eldenring-base': 'Elden Ring original soundtrack full album 67 tracks timestamps',
    'acvalhalla': 'Assassins Creed Valhalla original soundtrack full album Ubisoft',
    'hifirush': 'Hi Fi Rush original soundtrack full album Bethesda',
    'cyberpunk2077': 'Cyberpunk 2077 original score full soundtrack CD Projekt Red',
    'control': 'Control original soundtrack Petri Alanko Martin Stig Andersen full album',
    'bioshock': 'BioShock 2007 I Chose Rapture original score Garry Schyman full soundtrack',
    'cuphead': 'Cuphead original soundtrack Kristofer Maddigan full album official',
    'masseffect': 'Mass Effect original soundtrack 2007 full album Jack Wall Sam Hulick',
    'ff16': 'Final Fantasy XVI original soundtrack Square Enix full album',
    'horizonforbiddenwest': 'Horizon Forbidden West original soundtrack full album Sony Music',
    'kirbystarallies': 'Kirby Star Allies original soundtrack full album timestamps',
    'splatoon3': 'Splatoon 3 Splatune 3 original soundtrack full album timestamps',
    'mario3dworldbowser': 'Super Mario 3D World Bowsers Fury original soundtrack full album timestamps',
    'metroidprime4': 'Metroid Prime 4 Beyond original soundtrack full OST timestamps',
    'smashultimate': 'Super Smash Bros Ultimate original soundtrack new remixes full album timestamps',
}
for name, query in queries.items():
    if len(sys.argv)>1 and name not in sys.argv[1:]:
        continue
    path = OUT / (name + '-available-score-search.json')
    if path.exists():
        result = json.loads(path.read_text(encoding='utf-8'))
    else:
        result = v.search(query)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(name, [(item['id'], item['title'], item['channel'], item.get('duration')) for item in result['entries'][:8]], flush=True)
