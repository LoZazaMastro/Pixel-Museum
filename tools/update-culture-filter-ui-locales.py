from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
keys=['All','History','Science','Technology','Cinema & TV','Music','Literature','Arts','Sport']
values={
'en':keys,
'it':['Tutto','Storia','Scienza','Tecnologia','Cinema e TV','Musica','Letteratura','Arte','Sport'],
'es':['Todo','Historia','Ciencia','Tecnología','Cine y TV','Música','Literatura','Arte','Deporte'],
'fr':['Tout','Histoire','Sciences','Technologie','Cinéma et TV','Musique','Littérature','Arts','Sport'],
'de':['Alles','Geschichte','Wissenschaft','Technik','Film und Fernsehen','Musik','Literatur','Kunst','Sport']}
for locale,translated in values.items():
 p=ROOT/'content/ui-locales'/f'{locale}.json';d=json.loads(p.read_text(encoding='utf8'));d['strings'].update(dict(zip(keys,translated)));p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
