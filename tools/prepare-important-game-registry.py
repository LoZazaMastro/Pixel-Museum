"""Record the landmark series and named games subject to the five-card minimum."""
from pathlib import Path
import json, re, unicodedata

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/editorial-resume-20261030'

SERIES = '''mario|zelda|metroid|pokemon|donkey kong|kirby|fire emblem|f zero|star fox|animal crossing|smash bros|xenoblade|pikmin|splatoon|wario|warioware|luigi|kid icarus|wave race|bayonetta|sonic|phantasy star|streets of rage|golden axe|shenmue|jet set|panzer dragoon|virtua fighter|virtua tennis|daytona|out run|outrun|after burner|nights into dreams|space harrier|skies of arcadia|grandia|guardian heroes|dragon force|alex kidd|wonder boy|jak and daxter|jak 2|jak ii|jak 3|ratchet|sly cooper|crash bandicoot|crash twinsanity|crash team|spyro|god of war|the last of us|uncharted|shadow of the colossus|the last guardian|gran turismo|wipeout|littlebigplanet|ape escape|medievil|gravity rush|patapon|locoroco|killzone|resistance|socom|pursuit force|twisted metal|parappa|jumping flash|tearaway|infamous|returnal|helldivers|ghost of tsushima|ghost of yotei|forza|halo|gears of war|fable|crackdown|perfect dark|banjo|conker|kameo|project gotham|sea of thieves|flight simulator|amped|metal gear|castlevania|contra|mega man|megaman|street fighter|mortal kombat|tekken|soulcalibur|soul calibur|dead or alive|ninja gaiden|devil may cry|onimusha|dino crisis|resident evil|silent hill|final fantasy|dragon quest|chrono trigger|chrono cross|kingdom hearts|tales of|bioshock|doom|quake|half life|portal|counter strike|team fortress|unreal|crysis|far cry|deus ex|system shock|dishonored|wolfenstein|call of duty|battlefield|medal of honor|rainbow six|splinter cell|ghost recon|hitman|max payne|mafia|grand theft auto|red dead|assassin s creed|assassins creed|prince of persia|tomb raider|indiana jones|warcraft|starcraft|diablo|civilization|age of empires|command conquer|command and conquer|dungeon keeper|theme hospital|simcity|the sims|populous|rollercoaster tycoon|heroes of might|total war|xcom|x com|company of heroes|homeworld|crusader kings|europa universalis|hearts of iron|stellaris|the settlers|anno|fallout|the elder scrolls|the witcher|mass effect|dragon age|baldur s gate|baldurs gate|planescape|icewind dale|neverwinter nights|disco elysium|pillars of eternity|divinity|ultima|wizardry|kingdom come|the outer worlds|knights of the old republic|jade empire|lost odyssey|blue dragon|golden sun|suikoden|xenogears|xenosaga|tenchu|persona|shin megami|nier|drakengard|ni no kuni|dark souls|demon s souls|demons souls|bloodborne|elden ring|sekiro|world of goo|super meat boy|cave story|undertale|deltarune|stardew valley|hollow knight|cuphead|shovel knight|hades|dead cells|subnautica|outer wilds|return of the obra dinn|papers please|hotline miami|five nights at freddy|firewatch|the stanley parable|what remains of edith finch|amnesia|little nightmares|no man s sky|minecraft|terraria|baba is you|vampire survivors|dave the diver|animal well|guitar hero|rock band|rocksmith|ridge racer|need for speed|burnout|tony hawk|ssx|colin mcrae|dirt rally|dance dance revolution|katamari|star wars|lego|claire obscur|clair obscur|death stranding|marvel s spider man|marvel s wolverine|marvels spider man|marvels wolverine'''.split('|')
EXACT = '''Pong|Space Invaders|Pac-Man|Ms. Pac-Man|Tetris|Breakout|Asteroids|Tempest|Galaga|Defender|Elite|R-Type|Gradius|Darius|Ikaruga|Radiant Silvergun|Another World|Flashback|Lemmings|Lode Runner|Bubble Bobble|Bomberman|Lunar: The Silver Star|EarthBound|Mother 3|F-Zero Climax|Lumines|Ico|Rez|Braid|Limbo|Inside|Journey|Flower|Fez|Spelunky|Celeste|Tunic|Balatro|Dredge|Soma|Okami|Viewtiful Joe|God Hand|Psychonauts|Psychonauts 2|Bully|The Darkness|The Darkness II|L.A. Noire|Sleeping Dogs|Watch Dogs|Watch Dogs 2|Mercenaries: Playground of Destruction|The Saboteur|Black|Beyond Good & Evil|Rayman|Rayman 2: The Great Escape|Rayman Origins|Rayman Legends|Aladdin|The Lion King|DuckTales|QuackShot|Goof Troop|The Magical Quest|Disney Epic Mickey|Disney's Hercules|Toy Story 2: Buzz Lightyear to the Rescue|Tarzan|Donald in Maui Mallard|Castle of Illusion Starring Mickey Mouse|World of Illusion Starring Mickey Mouse and Donald Duck|Bugs Bunny: Lost in Time|Sheep Raider|Taz Wanted|Saros|Lost Planet|Lost Planet 2'''.split('|')
EXCEPTIONS = {'Battles of Prince of Persia'}

def key(s):
    return re.sub('[^a-z0-9]+', ' ', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()).strip()

def main():
    catalog = json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf-8'))
    exact = {key(x) for x in EXACT}
    series = [key(x) for x in SERIES]
    important = []
    for e in catalog['entries']:
        name = key(e['title'])
        if e.get('kind') == 'game' and e['title'] not in EXCEPTIONS and (name in exact or any(re.search(r'\b' + re.escape(s) + r'\b', name) for s in series)):
            important.append({'entry_id': e['id'], 'title': e['title'], 'year': e['year'], 'cards': len(e.get('body', [])), 'minimum': 5})
    data = {'scope': 'Flagship series, landmark games and titles explicitly emphasised by the user; other games retain the two-card minimum.',
            'entries': important, 'below_minimum': [r for r in important if r['cards'] < 5]}
    (BASE / 'important-game-registry.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'important_games': len(important), 'below_five': len(data['below_minimum'])}))

if __name__ == '__main__':
    main()
