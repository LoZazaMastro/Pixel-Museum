"""Keep each dated Game Awards exhibit focused on its own ceremony."""
from pathlib import Path
import copy, json, re, unicodedata

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/editorial-resume-20261030'
LANGS = ('en', 'it', 'fr', 'de', 'es')

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def normal(s):
    return re.sub('[^a-z0-9]', '', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower())

def preferred(entry):
    choice = entry.get('preferred_image', 0)
    if isinstance(choice, str):
        choice = next((i for i, image in enumerate(entry['images']) if image.get('url') == choice), 0)
    return entry['images'][choice]

def main():
    catalog = read(ROOT / 'content/catalog.json')
    locales = {lang: read(ROOT / f'content/museum-locales/{lang}.json')['entries'] for lang in LANGS[1:]}
    opening = {
      'en': 'The Game Awards is an annual ceremony created by Geoff Keighley in 2014. It brings developers, performers and players together to recognise the year’s games and the work behind them, with awards for direction, performance, music and independent productions. The show also features announcements, trailers and live performances.',
      'it': 'Geoff Keighley ha creato The Game Awards nel 2014. La cerimonia annuale riunisce sviluppatori, interpreti e giocatori per premiare i giochi dell’anno e il lavoro di chi li realizza. Le categorie comprendono regia, interpretazione, musica e produzioni indipendenti. La serata ospita anche annunci, trailer ed esibizioni dal vivo.',
      'fr': 'Créée en 2014 par Geoff Keighley, la cérémonie des Game Awards réunit développeurs, artistes et joueurs pour récompenser les jeux de l’année et le travail de leurs créateurs. Les prix distinguent notamment la réalisation, l’interprétation, la musique et les productions indépendantes. Annonces, bandes-annonces et concerts ponctuent aussi la soirée.',
      'de': 'The Game Awards wurden 2014 von Geoff Keighley ins Leben gerufen. Bei der jährlichen Preisverleihung kommen Entwickler, Künstler und Spieler zusammen, um die Spiele des Jahres und die Arbeit ihrer Teams zu würdigen. Auszeichnungen gibt es unter anderem für Regie, Schauspiel, Musik und unabhängige Produktionen. Zur Show gehören auch Ankündigungen, Trailer und Liveauftritte.',
      'es': 'The Game Awards es una ceremonia anual creada por Geoff Keighley en 2014. Reúne a desarrolladores, intérpretes y jugadores para premiar los juegos del año y el trabajo de quienes los crean. Las categorías reconocen, entre otros aspectos, la dirección, la interpretación, la música y las producciones independientes. La gala también incluye anuncios, tráileres y actuaciones en directo.'
    }
    headings = {'en': 'The Game Awards', 'it': 'I Game Awards', 'fr': 'Les Game Awards', 'de': 'The Game Awards', 'es': 'The Game Awards'}
    patches = []
    for e in catalog['entries']:
        if not re.fullmatch(r'the-game-awards-20\d\d', e['id']):
            continue
        year = int(e['id'][-4:])
        old_index = next(i for i, h in enumerate(e['story_headings']) if h.startswith(str(year)) and 'Winner' in h)
        winner_lines = [s.strip() for s in e['body'][old_index].splitlines() if s.strip()]
        assert winner_lines[0] == 'Game of the Year', e['id']
        game = winner_lines[1].split(' – ')[0].split(' — ')[0]
        candidates = [g for g in catalog['entries'] if g.get('kind') == 'game' and normal(g['title']) == normal(game)]
        assert candidates, (e['id'], game, 'winner missing from catalog')
        g = next((g for g in candidates if g['year'] == year), candidates[0])
        cover = copy.deepcopy(preferred(e))
        cover['story_paragraph'] = -1
        winner = copy.deepcopy(preferred(g))
        winner['story_paragraph'] = 1
        winner['caption'] = f'{game} — Game of the Year, The Game Awards {year}'
        video = copy.deepcopy(next(v for v in e['videos'] if v.get('story_paragraph') == old_index))
        video['story_paragraph'] = 0
        video['poster_url'] = cover['url']
        summaries = {
          'en': f'The {year} edition of The Game Awards named {game} Game of the Year. The ceremony recognises achievements across game development, performance and music.',
          'it': f'Ai The Game Awards {year}, il premio al gioco dell’anno è andato a {game}. La cerimonia premia anche il lavoro di sviluppo, le interpretazioni e la musica dei videogiochi.',
          'fr': f'Lors des Game Awards {year}, {game} a été élu jeu de l’année. La cérémonie récompense également la création, les interprétations et la musique des jeux vidéo.',
          'de': f'Bei der Verleihung der Game Awards {year} wurde {game} zum Spiel des Jahres gewählt. Auch Entwicklung, Schauspiel und Musik wurden ausgezeichnet.',
          'es': f'En The Game Awards {year}, {game} recibió el premio al juego del año. La ceremonia también reconoce el trabajo de desarrollo, las interpretaciones y la música de los videojuegos.'
        }
        labels = {'en': f'{year} winners', 'it': f'I vincitori del {year}', 'fr': f'Les lauréats de {year}',
                  'de': f'Die Gewinner {year}', 'es': f'Los ganadores de {year}'}
        languages = {}
        for lang in LANGS:
            row = e if lang == 'en' else locales[lang][e['id']]
            assert len(row['body']) == len(e['body']), (e['id'], lang, 'unaligned source')
            languages[lang] = {'title': f'The Game Awards {year}', 'subtitle': '', 'summary': summaries[lang],
                'body': [opening[lang], row['body'][old_index]], 'story_headings': [headings[lang], labels[lang]]}
        keys = ('title', 'subtitle', 'summary', 'body', 'story_headings', 'images', 'videos', 'preferred_image')
        patches.append({'collection': 'catalog', 'entry_id': e['id'],
            'before': {k: copy.deepcopy(e.get(k)) for k in keys},
            'set': {'images': [cover, winner], 'videos': [video], 'preferred_image': 0,
                    'annual_awards_scope': {'year': year, 'winner_source_card': old_index,
                                            'other_editions_removed_from_this_stop': True}},
            'languages': languages})
    output = BASE / 'annual-game-awards-focused.json'
    output.write_text(json.dumps({'patches': patches}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'annual_entries': len(patches), 'text_cards_per_edition': 2, 'videos_per_edition': 1}))

if __name__ == '__main__':
    main()
