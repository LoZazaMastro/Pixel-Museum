"""Build the museum's curated English catalog from its maintained records."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ERAS = [
    ("origins", "Before the arcade", 1950, 1969, "Laboratories, public demonstrations and the idea of playing through a screen.", ["#EEE9DD", "#8C5844", "#272E2D"]),
    ("public-play", "Play goes public", 1970, 1979, "Coin-operated rooms, living-room televisions and the first shared computer worlds.", ["#F3E9D4", "#B05F36", "#38312B"]),
    ("personal", "A personal medium", 1980, 1989, "Home computers, portable machines and designers finding a language of their own.", ["#E8E5DD", "#587F83", "#252D32"]),
    ("dimensions", "New dimensions", 1990, 1999, "Polygons, optical discs, competitive communities and worlds connected by telephone lines.", ["#E6E7EB", "#746881", "#292B35"]),
    ("connected", "Connected lives", 2000, 2009, "Online services, everyday stories and an expanding idea of who games can reach.", ["#E5EBE4", "#668470", "#24352D"]),
    ("everywhere", "Games everywhere", 2010, 2019, "Independent voices, smartphones and new ways to share a place.", ["#EAE5DF", "#A65E60", "#342B30"]),
    ("living-history", "A living history", 2020, 2029, "Portable libraries, remote togetherness and the work of keeping play accessible.", ["#E8E8DD", "#8B8659", "#2D302B"]),
]
entries = []

def add(id, year, kind, title, subtitle, summary, paragraphs, source, *, date=(0,0,"year",""), tags=(), related=(), featured=False, layout=None, caveat=""):
    era = next(e[0] for e in ERAS if e[2] <= year <= e[3])
    publisher, source_title, url = source
    entries.append(dict(id=id,year=year,date=dict(month=date[0],day=date[1],precision=date[2],region=date[3]),kind=kind,title=title,subtitle=subtitle,summary=summary,body=paragraphs,era_id=era,tags=list(tags),related_ids=list(related),layout=layout or ("portrait" if kind=="person" else "editorial" if featured else "object"),images=[],videos=[],models=[],sources=[dict(title=source_title,url=url,publisher=publisher)],featured=featured,factual_note=caveat))

add("nimrod",1951,"technology","Nimrod","A computer explains itself through a game",
    "At the Festival of Britain, a wall of lights invited visitors to play Nim against a machine.",[
    "Ferranti built Nimrod for the 1951 Festival of Britain. Suggested by engineer John Bennett, the machine played Nim, a game of removing objects from piles. Its illuminated panels made a calculation visible, letting a public audience follow decisions that would otherwise remain hidden inside circuitry.",
    "Entertainment and demonstration overlapped from the beginning. Nimrod was not a commercial video-game cabinet, and its display used lamps rather than a video screen. It belongs here because it shows how play helped people approach an unfamiliar technology."],
    ("Computer History Museum","Nimrod at the Festival of Britain","https://www.computerhistory.org/timeline/1951/"),tags=("United Kingdom","demonstration","computing"),related=("tennis-for-two","spacewar"))

add("tennis-for-two",1958,"game","Tennis for Two","A laboratory becomes a playground",
    "William Higinbotham and Robert Dvorak turned an oscilloscope into a shared tennis court.",[
    "On 18 October 1958, visitors to Brookhaven National Laboratory could try an electronic tennis game. Physicist William Higinbotham designed it, and technician Robert Dvorak built the circuitry. An analog computer calculated the ball's path while an oscilloscope displayed the court from the side.",
    "Two hand controllers let visitors send the ball over a net. The important feature was a simple social one: people could participate together instead of watching another static scientific display.",
    "Calling any single invention the first video game hides the different experiments that led to the medium. Tennis for Two is a well-documented early example of an electronic screen used specifically to entertain a public audience."],
    ("Brookhaven National Laboratory","The First Video Game?","https://www.bnl.gov/about/history/firstvideo.php"),date=(10,18,"day","United States: public demonstration"),tags=("United States","laboratory","multiplayer"),related=("nimrod","spacewar","pong"),featured=True)

add("spacewar",1962,"game","Spacewar!","A shared experiment, not a solitary invention",
    "A community around MIT's PDP-1 made spacecraft, gravity and competition fit on one luminous screen.",[
    "Steve Russell wrote the first version of Spacewar!, after discussions with Martin Graetz and Wayne Wiitanen. Peter Samson, Dan Edwards and others helped improve it in 1962. Players steered two ships around a gravitational hazard, trying to line up a shot without destroying themselves.",
    "Its movement depended on a computer continually updating a world and responding to two people. Custom controllers made the exchange more comfortable than reaching for the computer's own switches.",
    "Spacewar! travelled through a small network of institutions with compatible machines. This was a culture of adaptation and shared code, long before a mass market for game software. The surviving PDP-1 restoration also reminds us that preserving a game can mean preserving its display, controls and timing."],
    ("Computer History Museum","Spacewar! — PDP-1 Restoration Project","https://www.computerhistory.org/pdp-1/spacewar/"),tags=("United States","computing","multiplayer"),related=("tennis-for-two","pong","preserving-play"),featured=True)

add("brown-box",1968,"person","Ralph Baer, Bill Harrison and Bill Rusch","Making television answer back",
    "The Brown Box prototypes imagined a television as something a household could play with.",[
    "Working at Sanders Associates, Ralph Baer and colleagues Bill Harrison and Bill Rusch developed a sequence of television-game prototypes. The wood-grain-covered Brown Box could support several games rather than one fixed activity. A light gun was among the team's experimental accessories.",
    "Magnavox licensed the technology and released the Odyssey in 1972. Baer's surviving notebooks, prototypes and workshop make this more than a story about one successful object: they preserve decisions, failed paths and the collaboration behind it."],
    ("Smithsonian Institution","The Ralph Baer Prototypes and Electronic Games","https://www.si.edu/spotlight/the-father-of-the-video-game-the-ralph-baer-prototypes-and-electronic-games"),tags=("engineering","television","United States"),related=("odyssey","pong"),caveat="The Brown Box was developed during 1967–1968; 1968 is used as an exhibition anchor, not an exact release date.")

add("oregon-trail",1971,"game","The Oregon Trail","The classroom as a game space",
    "A teaching experiment made decisions, resources and consequences part of a history lesson.",[
    "Don Rawitsch, Bill Heinemann and Paul Dillenberger created an early Oregon Trail for a Minnesota classroom in 1971. Later versions, associated with the Minnesota Educational Computing Consortium, reached generations of schoolchildren through shared computers.",
    "Food, money, travel and illness became linked systems. Playing could make a lesson memorable, but a simulation also chooses whose experiences to represent. The familiar settler viewpoint is a useful starting point for asking what a historical game leaves outside its frame."],
    ("The Strong National Museum of Play","The Oregon Trail","https://www.museumofplay.org/games/the-oregon-trail/"),tags=("education","United States","simulation"),related=("simcity","papers-please"))

add("odyssey",1972,"console","Magnavox Odyssey","The living room becomes interactive",
    "A home television, translucent overlays and physical pieces shared the work of making a game.",[
    "Magnavox brought the Odyssey to the US market in 1972, building on the Sanders team's prototypes. Its austere electronic shapes were only part of the experience. Plastic screen overlays, cards and other physical accessories supplied colour, settings and rules.",
    "The console did not contain a modern stored-program game computer. Looking at the complete set makes that distinction tangible: early home video games developed alongside board games and toys, rather than replacing them overnight."],
    ("Computer History Museum","Games on Your TV?","https://www.computerhistory.org/revolution/computer-games/16/190"),tags=("United States","television","hardware"),related=("brown-box","channel-f","atari-vcs"))

add("pong",1972,"game","Pong","A rule you could understand from across a room",
    "Two paddles and one moving square helped turn electronic play into a public business.",[
    "Allan Alcorn engineered Atari's Pong as a two-player electronic table-tennis game. Its immediate feedback made the rules legible: move the paddle, return the ball, watch the score. The cabinet asked strangers to stand side by side and learn through play.",
    "Pong was not the first electronic game, nor the first commercial arcade video game. Its lasting importance lies in how convincingly it demonstrated an audience for coin-operated screen entertainment."],
    ("Computer History Museum","Atari Announces Pong Game","https://www.computerhistory.org/tdih/november/29/"),date=(11,29,"day","United States: announcement"),tags=("arcade","United States","multiplayer"),related=("tennis-for-two","odyssey","space-invaders"))

add("channel-f",1976,"person","Jerry Lawson and the Channel F team","A machine with a future beyond its first games",
    "Removable program cartridges separated the hardware you owned from the games you could buy next.",[
    "Gerald 'Jerry' Lawson led the engineering team behind Fairchild's Channel F. Introduced in 1976, it brought interchangeable ROM game cartridges to the home-console market. The platform could grow through new software without each game requiring another complete machine.",
    "Lawson's career also included founding Video Soft. His place in this history is both technical and entrepreneurial: a Black engineer leading important consumer-electronics work in an industry where access and recognition were far from equal."],
    ("The Strong National Museum of Play","Jerry Lawson: The Black Engineer and Entrepreneur Who Changed Video Games","https://www.museumofplay.org/exhibits/online-exhibits/"),tags=("hardware","United States","engineering"),related=("odyssey","atari-vcs"),featured=True)

add("atari-vcs",1977,"console","Atari Video Computer System","A library in cartridges",
    "The console later called the Atari 2600 made a changing software collection part of home life.",[
    "Atari released its Video Computer System in 1977. Its cartridge library eventually ranged from arcade conversions to original adventures and experiments. Distinctive controllers, a wood-grain front and game boxes turned computer entertainment into a recognisable household product.",
    "Creating for the machine demanded precise control of limited memory and display timing. Its constraints helped produce a visual vocabulary of strong silhouettes, flat colour and repeated patterns that remains readable decades later."],
    ("Atari","Atari 2600+ — original hardware heritage","https://atari.com/products/atari-2600-plus"),tags=("United States","hardware","cartridges"),related=("channel-f","carol-shaw","adventure"))

add("space-invaders",1978,"game","Space Invaders","Pressure becomes a rhythm",
    "Tomohiro Nishikado's descending formation made an entire screen feel like a threat.",[
    "Taito first presented Space Invaders at a trade exhibition on 16 June 1978. Its alien formation, protective shelters and accelerating pressure gave each attempt a clear dramatic shape. The booming popularity that followed reached beyond dedicated arcades into spaces such as Japanese coffee shops.",
    "Nishikado's game shows how recognisable characters can emerge from tiny groups of pixels. The aliens are a repeating system and individual visual identities at the same time."],
    ("Taito","Taito 70th Anniversary — history, 1978","https://www.taito.co.jp/70th/history"),date=(6,16,"day","Japan: exhibition debut"),tags=("Japan","arcade","sound"),related=("pong","pac-man","dona-bailey"),caveat="16 June marks Taito's product presentation, not a claim that every arcade received the game that day.")

add("mud",1978,"technology","MUD","A world made of words, inhabited together",
    "Roy Trubshaw and Richard Bartle helped make the computer terminal a meeting place.",[
    "Roy Trubshaw began MUD at the University of Essex in 1978; Richard Bartle became a central collaborator as the project evolved. The name stood for Multi-User Dungeon. Instead of merely reading a description, participants could act in a shared textual space and encounter one another.",
    "MUDs linked adventure-game commands to persistent social worlds. Their descendants include online role-playing games, but their significance is broader: a world can feel inhabited through language and other people, even without a moving image."],
    ("Richard A. Bartle","Richard Bartle: Biography","https://mud.co.uk/richard/biog.htm"),tags=("United Kingdom","online","text"),related=("adventure","world-of-warcraft"))

add("adventure",1979,"game","Adventure","A small kingdom and a hidden signature",
    "Warren Robinett translated exploration into rooms, coloured shapes and a secret author credit.",[
    "Atari's Adventure adapted ideas from text adventures to a joystick-controlled world. A square hero could carry objects between rooms, unlock passages and encounter dragons. Its economical shapes asked the player to remember connections across a larger space.",
    "Robinett also concealed a room bearing his name, making a now-famous argument for recognising the people who create games. The secret is a reminder that authorship was not always visible on a box or title screen."],
    ("Warren Robinett / Good Deal Games","Interview with Warren Robinett","https://www.gooddealgames.com/interviews/int_Warren_Robinett.html"),tags=("United States","authorship","exploration"),related=("atari-vcs","zelda"),caveat="The designer dates completion/publication to 1979; some catalogues use 1980 for the retail release. Do not treat this entry as an exact anniversary.")

add("pac-man",1980,"game","Pac-Man","A character you could meet outside the cabinet",
    "Toru Iwatani and Namco gave maze-chasing a cast, a personality and a bright visual identity.",[
    "Pac-Man replaced an invading enemy fleet with a maze full of food and pursuit. The ghosts' differing behaviour and the sudden reversal offered by a power pellet made a small space rich with decisions.",
    "Namco's 1980 game also became a cultural character: toys, television and music carried its image beyond people who played arcades. The history of games is partly a history of how recognisable faces travel between media."],
    ("The Strong National Museum of Play","Pac-Man","https://www.worldvideogamehalloffame.org/games/pac-man/"),tags=("Japan","arcade","character design"),related=("space-invaders","super-mario-bros"))

add("roberta-williams",1980,"person","Roberta Williams","Putting a picture inside the adventure",
    "Mystery House brought line-drawn locations to the computer mystery, opening another route into storytelling.",[
    "Roberta Williams designed Mystery House, released with Ken Williams through On-Line Systems in 1980. Its Apple II images were sparse line drawings, but they changed the relationship between text, place and player: a room could now be examined visually as well as described.",
    "Her later King's Quest designs continued to explore character and story within graphical worlds. The evolution was collaborative, involving artists, programmers and changing hardware, rather than a simple replacement of words by pictures."],
    ("Roberta Williams","Roberta Williams — Her Games","https://robertawilliams.com/her-games/"),tags=("United States","storytelling","Apple II"),related=("adventure","myst","karateka"),featured=True)

add("dona-bailey",1981,"person","Dona Bailey and Centipede","A different kind of arcade garden",
    "A trackball, a field of mushrooms and a moving insect turned fast reactions into unusually tactile play.",[
    "Dona Bailey programmed Centipede with Ed Logg at Atari. Released in 1981, the game let players sweep the shooter using a trackball while the insect formation threaded through a changing mushroom field.",
    "Its colour and accessible control helped distinguish it in the arcade. Bailey's work belongs alongside the familiar company histories: individual programmers made decisive choices about how an electronic game felt under a player's hands."],
    ("Museum of the Moving Image","Arcade Classics","https://movingimage.org/event/arcade-classics/"),tags=("United States","arcade","controls"),related=("space-invaders","carol-shaw"))

add("carol-shaw",1982,"person","Carol Shaw and River Raid","A river that fits in a cartridge",
    "Clever generation turned limited storage into a long, changing flight.",[
    "Carol Shaw designed and programmed River Raid for Activision's Atari 2600 library. Its scrolling river challenged players to steer, refuel and judge the narrow space between hazards. Repeated structures and calculated variation made the landscape feel more extensive than the cartridge's small memory might suggest.",
    "Shaw's papers preserve code listings, notes and design documentation. Such material makes it possible to study a finished game as engineering and creative work, rather than treating its author as a footnote."],
    ("The Strong National Museum of Play","Carol Shaw Papers, 1960–2017","https://www.museumofplay.org/app/uploads/2022/01/Finding-Aid-to-the-Carol-Shaw-papers_013122.pdf"),tags=("United States","programming","Atari 2600"),related=("dona-bailey","atari-vcs"))

add("zx-spectrum",1982,"computer","ZX Spectrum","A keyboard, a cassette and a new possibility",
    "An affordable British microcomputer helped make playing and programming neighbours.",[
    "Sinclair's ZX Spectrum arrived in 1982. Its compact keyboard and cassette-based software placed a programmable computer within reach of many British households. Games could come from a shop, a magazine listing or someone experimenting at home.",
    "Its characteristic colour attributes became part of a recognisable graphic style. The wider home-computer scene also supported small publishers and designers whose work did not need to begin inside a console manufacturer."],
    ("Centre for Computing History","Sinclair ZX Spectrum 48K","https://www.computinghistory.org.uk/det/424/Sinclair-ZX-Spectrum-48k/"),date=(4,23,"day","United Kingdom: announcement"),tags=("United Kingdom","home computing","programming"),related=("commodore-64","mud"))

add("commodore-64",1982,"computer","Commodore 64","A computer with a voice",
    "The SID sound chip helped turn a mass-market home computer into a musical instrument.",[
    "Introduced in 1982, the Commodore 64 brought games, programming and music-making into the same beige case. Its SID audio chip gave composers control over distinctive waveforms and filters, producing a sound that musicians still explore.",
    "The machine's history includes commercial games, copied magazine programs and the demoscene: communities building audiovisual works to test what the hardware could do. Creative use continued long after the computer ceased being new."],
    ("Computer History Museum","Commodore introduces the Commodore 64","https://www.computerhistory.org/timeline/1982/"),tags=("home computing","sound","demoscene"),related=("zx-spectrum","mule","game-boy"))

add("famicom",1983,"console","Family Computer","A platform built to stay in the home",
    "Nintendo's red-and-white Famicom began a hardware family whose overseas form would look very different.",[
    "Nintendo launched the Family Computer in Japan in 1983. Under development leader Masayuki Uemura, the system joined cartridge software with controllers attached to the console. Its Japanese design and its later overseas NES identity should not be collapsed into a single worldwide launch.",
    "The platform's long life depended on software, manufacturing and a network of developers as much as on chips. It became the home of games that taught players how to navigate, jump and explore through increasingly carefully designed worlds."],
    ("Nintendo","Nintendo History — 1983","https://www.nintendo.com/en-gb/Hardware/Nintendo-History/Nintendo-History-625945.html"),tags=("Japan","hardware","cartridges"),related=("super-mario-bros","zelda","dragon-quest"))

add("mule",1983,"person","Dani Bunten Berry and M.U.L.E.","An economy with people in the room",
    "Cooperation and competition share the same small colony in Ozark Softscape's multiplayer design.",[
    "Dani Bunten Berry and the Ozark Softscape team made M.U.L.E. in 1983. Players develop land, produce resources and trade. A successful personal strategy depends on an economy that other participants are also shaping.",
    "Its auctions turn numbers into negotiation and anticipation. Bunten's wider career repeatedly explored social play, including connecting people through modems. Her surviving design and business papers offer evidence of multiplayer thinking that predates today's constant online connections."],
    ("The Strong National Museum of Play","Dani Bunten Berry papers — Ozark Softscape materials","https://archives.museumofplay.org/repositories/3/archival_objects/13766"),tags=("United States","multiplayer","simulation"),related=("commodore-64","mud","simcity"),featured=True)

add("tetris",1984,"game","Tetris","A puzzle crosses borders",
    "Alexey Pajitnov's falling blocks became a common language across computers, handhelds and cultures.",[
    "Alexey Pajitnov devised Tetris in the Soviet Union on an Electronika 60. The puzzle turns placement into a repeated negotiation: every completed line creates room, while every awkward gap leaves a problem for the future.",
    "Its journey abroad involved ports, competing licensing claims and publishers with very different ideas about where a game belonged. On Game Boy it helped make a handheld attractive to people beyond an established console audience.",
    "A contemporary anniversary is not necessarily a securely documented development date. This catalog follows the rights holder's 1984 year while leaving the exact original day unspecified. That small distinction matters when a cultural memory becomes a historical record."],
    ("The Tetris Company","About Tetris","https://www.tetris.com/about"),tags=("Soviet Union","puzzle","portable"),related=("game-boy","preserving-play"),featured=True,caveat="1984 follows the current official chronology. June 6 is an official celebration date; it is not used here as a verified original release day.")

add("karateka",1984,"game","Karateka","Learning to stage a moving body",
    "Jordan Mechner used film reference and carefully paced scenes to give an Apple II game a cinematic rhythm.",[
    "Karateka made fighting part of a staged journey. Jordan Mechner's animation experiments used filmed movement as reference, while changing viewpoints and pauses linked the action to a larger rescue story.",
    "Surviving journals, prototypes and footage reveal the trial and revision behind the game. Digital Eclipse's later documentary makes that process explorable. The evidence helps distinguish a finished style from the many experiments that made it possible."],
    ("Digital Eclipse","The Making of Karateka","https://www.digitaleclipse.com/games/karateka"),tags=("United States","animation","Apple II"),related=("roberta-williams","preserving-play"),layout="screening")

add("super-mario-bros",1985,"game","Super Mario Bros.","A world that teaches through movement",
    "Shigeru Miyamoto and Takashi Tezuka's team built a readable landscape around the pleasure of a jump.",[
    "Super Mario Bros. arrived for Japan's Famicom in 1985. The first obstacles introduce a vocabulary: moving enemies, breakable blocks, growth and height. Players learn what the world permits by touching it, trying again and finding a different route.",
    "Its scrolling spaces are not simply bigger screens. Distances, running speed and the shape of a jump work together. Koji Kondo's music gives that movement another layer of timing and recognition."],
    ("Nintendo","Super Mario Bros. 35th Anniversary history","https://mario.nintendo.com/history/"),tags=("Japan","design","platformer"),related=("famicom","zelda","super-mario-64"))

add("zelda",1986,"game","The Legend of Zelda","The value of getting a little lost",
    "Exploration, memory and curiosity turn a map into something personal.",[
    "The Legend of Zelda first appeared in Japan on the Famicom Disk System in 1986, before its cartridge releases overseas. A broad overhead view made routes, secrets and landmarks part of the player's working memory.",
    "The series pairs direction with the pleasure of choosing a detour. Shigeru Miyamoto, Takashi Tezuka, Koji Kondo and their colleagues developed a world whose objects and sounds could become familiar through repeated visits."],
    ("Nintendo","The Legend of Zelda — official series history","https://zelda.nintendo.com/about/"),tags=("Japan","exploration","sound"),related=("adventure","famicom","switch"))

add("dragon-quest",1986,"game","Dragon Quest","A role-playing invitation",
    "Yuji Horii, Akira Toriyama and Koichi Sugiyama helped make computer role-playing approachable on a console.",[
    "Released for Japan's Famicom in 1986, Dragon Quest combined menu-driven battles, a journey through towns and countryside, distinctive character art and memorable music. Its team adapted role-playing ideas to a gamepad and a broad home audience.",
    "The collaboration of scenario writer Yuji Horii, artist Akira Toriyama and composer Koichi Sugiyama shows how an interface, a visual world and a musical identity can work together. Later international releases also remind us that familiarity with a series depends strongly on where a player grew up."],
    ("The Strong National Museum of Play","Dragon Quest","https://www.museumofplay.org/games/dragon-quest/"),tags=("Japan","role-playing","collaboration"),related=("famicom","final-fantasy-vii","pokemon"))

add("game-boy",1989,"console","Game Boy","Designing for the journey between places",
    "Gunpei Yokoi and Nintendo's teams chose practical portability over a race for the brightest screen.",[
    "Nintendo launched Game Boy in Japan in 1989. Its monochrome display, familiar controls and interchangeable cartridges made a personal library portable. The machine's durability and battery use mattered as much as what it could draw.",
    "Gunpei Yokoi played a central role in Nintendo's portable products. Game Boy illustrates a lasting design question: the most capable technology is not always the technology that best fits everyday use. Games such as Tetris found an unusually welcoming home in this balance."],
    ("Nintendo","Iwata Asks — Gunpei Yokoi and portable hardware","https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-Nintendo-3DS/Vol-1-And-That-s-How-the-Nintendo-3DS-Was-Made/2-Shigeru-Miyamoto-Talks-Virtual-Boy/2-Shigeru-Miyamoto-Talks-Virtual-Boy-229419.html"),tags=("Japan","portable","hardware"),related=("tetris","pokemon","steam-deck"))

add("simcity",1989,"game","SimCity","The city is the toy",
    "Will Wright's design made building and watching a system respond an activity worth doing for its own sake.",[
    "Will Wright found that making maps could be as engaging as playing across them. SimCity grew from that discovery into an open-ended urban simulation. Roads, land use, services and money form a network of consequences rather than a fixed path to a final level.",
    "Its city is an interpretation, not a neutral model of urban life. What a simulation counts becomes visible; what it omits can disappear. Playing with the system is also an opportunity to ask which assumptions hold it together."],
    ("The Strong National Museum of Play","SimCity","https://www.museumofplay.org/games/simcity/"),tags=("United States","simulation","cities"),related=("mule","the-sims","papers-please"),featured=True)

add("sonic",1991,"game","Sonic the Hedgehog","Momentum as an identity",
    "Curves, speed and a blue silhouette made the Mega Drive feel different in motion.",[
    "Sonic the Hedgehog launched on Genesis in North America in June 1991; Japan's Mega Drive release followed in July. Yuji Naka's programming, Naoto Ohshima's character design and Hirokazu Yasuhara's levels helped turn acceleration into a recognisable style.",
    "The stages reward reading slopes and carrying speed, but also hide slower routes and secrets. Masato Nakamura's music strengthens an identity that can be recognised even before the character appears."],
    ("Sega","Sonic Channel — 1991 chronology","https://sonic.sega.jp/SonicChannelOld/chara/history/1991/index.html"),date=(6,23,"day","North America: Genesis release"),tags=("Japan","platformer","sound"),related=("super-mario-bros","dreamcast"))

add("street-fighter-ii",1991,"game","Street Fighter II","A conversation in six buttons",
    "Capcom's fighting game made differences between characters the foundation of competitive play.",[
    "Street Fighter II gave arcade opponents a varied cast with distinct reach, movement and special attacks. Learning a character meant learning possibilities; facing another person meant adapting to someone who was learning too.",
    "Its competition depended on meeting places, repeated encounters and the exchange of techniques. The sound and music of composers including Yoko Shimomura helped give each contest a place and a memorable identity."],
    ("The Strong National Museum of Play","Street Fighter II","https://www.museumofplay.org/games/street-fighter-ii/"),tags=("Japan","arcade","competition","sound"),related=("starcraft","dance-dance-revolution"))

add("doom",1993,"game","DOOM","A game that spread through a network",
    "Fast movement, shareware distribution and tools for modification made players part of its continuing life.",[
    "id Software's DOOM brought a forceful sense of space and speed to personal computers. Its first-person view connected looking, moving and shooting into a rapid rhythm, supported by recognisable sound and bold environmental design.",
    "The shareware model helped the first episode circulate. Network play and user-made levels created further reasons to return. Its cultural history therefore includes server administrators, map makers and people passing files between machines, as well as the original development team."],
    ("The Strong National Museum of Play","DOOM","https://www.museumofplay.org/games/doom/"),tags=("United States","PC","modding","online"),related=("spacewar","steam","starcraft"),featured=True)

add("myst",1993,"game","Myst","An island made for looking closely",
    "Cyan's CD-ROM adventure used stillness, sound and detail to make a place feel worth investigating.",[
    "Rand and Robyn Miller's Myst placed the player on an unfamiliar island with little explanation. Moving between carefully composed views, listening and noticing recurring details became the main tools of discovery.",
    "CD-ROM storage helped support its rendered images and recorded audio. The result offered a different account of immersion from the speed of DOOM in the same year: a world can pull someone in by asking them to slow down."],
    ("Cyan","Myst","https://cyan.com/games/myst/"),tags=("United States","PC","sound","exploration"),related=("roberta-williams","doom","journey"))

add("playstation",1994,"console","PlayStation","A new material for worlds",
    "Optical discs and real-time polygons changed the look, scale and audience of console games.",[
    "Sony launched PlayStation in Japan on 3 December 1994. North American and European launches followed in September 1995. Its CD-ROM format supported large quantities of art, music and video, while real-time 3D made perspective itself part of play.",
    "The platform housed very different visual languages, from racing circuits to pre-rendered role-playing scenes. Memory cards and audio discs also placed the console among the everyday media objects of a household."],
    ("Sony Interactive Entertainment","PlayStation 1994 — history timeline","https://www.playstation.com/en-us/playstation-history/1994-ps-one/"),date=(12,3,"day","Japan: launch"),tags=("Japan","hardware","3D","optical discs"),related=("final-fantasy-vii","tomb-raider","playstation-2"),featured=True)

add("pokemon",1996,"game","Pokémon Red and Green","A collection designed to leave the screen",
    "A link cable turned different copies of a portable game into a reason to meet.",[
    "Game Freak's Pokémon Red and Green launched in Japan in 1996. Capturing and developing creatures created a personal collection, while differences between versions encouraged players to trade through Game Boy's link cable.",
    "Satoshi Tajiri's concept grew through a team whose work included Ken Sugimori's designs and Junichi Masuda's music and programming. The social exchange was not an extra attached to the adventure; it helped give the collection its meaning."],
    ("The Pokémon Company","Pokémon Red Version and Pokémon Blue Version","https://www.pokemon.com/us/pokemon-video-games/pokemon-red-version-and-pokemon-blue-version"),tags=("Japan","portable","collecting","multiplayer"),related=("game-boy","pokemon-go"),caveat="The 1996 anchor is the Japanese Red/Green release. Overseas Red/Blue arrived later; names and dates should not be substituted between regions.")

add("super-mario-64",1996,"game","Super Mario 64","Learning how to move all over again",
    "An analog stick and an adjustable viewpoint made running in three dimensions a subject of its own.",[
    "Super Mario 64 accompanied the Nintendo 64's Japanese launch in 1996. Its spaces gave players room to practise movement, judge depth and discover different objectives within the same landscape.",
    "A 3D world also created a new design problem: the camera. Positioning a viewpoint could help or obstruct a jump, so seeing became part of controlling. The game helped establish a widely influential vocabulary, while leaving a problem that later designers would continue to revisit."],
    ("Nintendo","Iwata Asks — Super Mario 64 and 3D design","https://iwataasks.nintendo.com/interviews/wii/mario25th/0/0/"),tags=("Japan","3D","controls"),related=("super-mario-bros","playstation","switch"))

add("tomb-raider",1996,"game","Tomb Raider","Archaeology by movement",
    "Core Design turned the reading of a room into a sequence of measured jumps, climbs and discoveries.",[
    "Tomb Raider's three-dimensional ruins asked players to look for a route before moving. Lara Croft's actions and the architecture shared a consistent scale, making a ledge or gap something the player could learn to judge.",
    "The character also became a widely circulated media image. Keeping those histories together matters: the movement system, the work of the development team and the marketing of its heroine all shaped what the game meant outside the screen."],
    ("The Strong National Museum of Play","Tomb Raider","https://www.museumofplay.org/games/tomb-raider/"),tags=("United Kingdom","3D","character design"),related=("playstation","super-mario-64"))

add("final-fantasy-vii",1997,"game","Final Fantasy VII","An industrial city, a planet and a memory",
    "Square brought a long-form role-playing story to the optical-disc generation.",[
    "Final Fantasy VII paired polygonal characters with pre-rendered locations and filmed sequences. Its 1997 PlayStation release made shifts between different visual forms part of the experience of travelling through a large narrative world.",
    "The work of a broad team, including director Yoshinori Kitase and composer Nobuo Uematsu, gave an industrial landscape emotional scale. The relationship between energy, exploitation and ordinary lives remains a useful way into its story."],
    ("The Strong National Museum of Play","Final Fantasy VII","https://www.museumofplay.org/games/final-fantasy-vii/"),tags=("Japan","role-playing","sound","optical discs"),related=("dragon-quest","playstation","journey"))

add("starcraft",1998,"game","StarCraft","From a strategy game to a spectator culture",
    "Blizzard's asymmetrical armies became part of a much larger competitive ecosystem, particularly in South Korea.",[
    "StarCraft set three distinct forces against one another, requiring players to manage production, information and movement at once. Its multiplayer depth made learning an ongoing activity rather than something completed by finishing a campaign.",
    "In South Korea, PC rooms, organised competition and broadcasts helped make the game a public spectacle. That development cannot be explained by software alone: places to play, network infrastructure, commentators and audiences built the culture around it."],
    ("The Strong National Museum of Play","StarCraft","https://www.museumofplay.org/games/starcraft/"),tags=("South Korea","United States","PC","competition","online"),related=("street-fighter-ii","world-of-warcraft","steam"))

add("dance-dance-revolution",1998,"game","Dance Dance Revolution","The body becomes the controller",
    "Konami made rhythm visible on a floor of arrows, with performance spilling into the surrounding room.",[
    "Dance Dance Revolution arrived in Japanese arcades in 1998. Players matched foot movements to music and scrolling cues, learning patterns through their whole body rather than only through a joystick.",
    "The cabinet made skill visible to spectators. Players could rehearse, improvise and perform together, turning an arcade into a temporary stage. Its popularity is a reminder that videogame history includes physical exertion and shared public space."],
    ("The Strong National Museum of Play","Dance Dance Revolution","https://www.museumofplay.org/games/dance-dance-revolution/"),tags=("Japan","arcade","rhythm","controls"),related=("street-fighter-ii","wii"))

add("dreamcast",1998,"console","Dreamcast","A modem beside the television",
    "Sega put network communication inside the console and made connected play part of its identity.",[
    "Dreamcast launched in Japan on 27 November 1998. Its built-in modem supported a vision of browsing, communication and online games from the living room. The Visual Memory unit added a tiny display to the familiar memory card.",
    "Its library joined arcade traditions to experiments such as Shenmue, Seaman and Phantasy Star Online. Sega ended production and withdrew from making home consoles, but the system's ideas travelled beyond its commercial life."],
    ("Sega","Sega Hardware Encyclopedia — Dreamcast","https://www.sega.jp/history/hard/dreamcast/"),date=(11,27,"day","Japan: launch"),tags=("Japan","online","hardware"),related=("sonic","xbox-halo","world-of-warcraft"))

add("playstation-2",2000,"console","PlayStation 2","A games machine inside a changing media home",
    "DVD playback and a vast software library connected the console to more than one kind of screen entertainment.",[
    "PlayStation 2 launched in Japan on 4 March 2000. Its ability to play DVDs gave it another role during a transition in home video, while compatibility with original PlayStation software carried existing collections forward.",
    "The library ranged from expansive commercial productions to unusual visual and musical experiments. Treating the console as a cultural object means looking at what households used it for, not only comparing its technical specifications."],
    ("Sony Interactive Entertainment","PlayStation 2 — history timeline","https://www.playstation.com/en-us/playstation-history/2000-ps2-psp/"),date=(3,4,"day","Japan: launch"),tags=("Japan","hardware","optical discs"),related=("playstation","xbox-halo","preserving-play"))

add("the-sims",2000,"game","The Sims","Everyday life becomes the story",
    "Maxis found play in relationships, rooms and the small disruptions of a household.",[
    "The Sims brought the scale of simulation down from a city to people and their homes. Players arranged spaces, watched needs interact and helped generate domestic stories without a single required ending.",
    "Will Wright and the Maxis team made a structure that invited individual interpretation. Building, customisation and sharing gave players ways to become authors within it. The game's audience challenged narrow assumptions about who computer games were for."],
    ("The Strong National Museum of Play","The Sims","https://www.museumofplay.org/games/the-sims/"),tags=("United States","simulation","customisation"),related=("simcity","animal-crossing"))

add("xbox-halo",2001,"console","Xbox and Halo","The ring world and the connected living room",
    "Microsoft's first console arrived with a shooter that helped define its controls and social life.",[
    "Xbox launched in North America on 15 November 2001, with Bungie's Halo: Combat Evolved among its games. Halo moved between open combat spaces and enclosed interiors while building a readable control scheme around the console gamepad.",
    "Split-screen and linked consoles made groups of people part of the experience. Xbox Live followed later, in 2002, extending the platform's social ambitions through an online service. The original launch should not be confused with that subsequent step."],
    ("Microsoft","Microsoft Announces Games for the North American Xbox Launch","https://news.microsoft.com/source/2001/11/08/microsoft-announces-powerhouse-games-portfolio-for-north-american-xbox-launch/"),date=(11,15,"day","North America: launch"),tags=("United States","hardware","multiplayer"),related=("doom","dreamcast","world-of-warcraft"))

add("steam",2003,"technology","Steam","The library becomes a service",
    "Valve's platform helped reshape how PC games are distributed, updated and kept together.",[
    "Steam began in 2003 and developed from a way of delivering updates into a large PC storefront and social platform. A game library increasingly became an account linked to downloads, automatic updates and online features.",
    "Convenience also changed the responsibilities of preservation. Installers, dependencies and particular versions can matter as much as a boxed disc. A service-based library raises new questions about continuity when software and infrastructure keep changing."],
    ("Valve","Steam — 20th Anniversary","https://store.steampowered.com/sale/steam20"),tags=("PC","distribution","online"),related=("doom","steam-deck","preserving-play"))

add("world-of-warcraft",2004,"game","World of Warcraft","A place that keeps going after you leave",
    "Blizzard's shared world made routine, cooperation and long-term relationships part of an adventure.",[
    "World of Warcraft launched in North America in November 2004, followed by releases in other regions. It connected exploration, character development and group activities within an online world that continued between visits.",
    "Guilds, scheduled gatherings and player-made knowledge became part of the experience. Preserving such a game requires more than a copy of its client: communities, server behaviour and changes over time are also historical evidence."],
    ("Blizzard Entertainment","World of Warcraft — timeline chapter 6","https://worldofwarcraft.blizzard.com/en-gb/story/timeline/chapter-06"),date=(11,0,"month","North America: launch"),tags=("United States","online","role-playing"),related=("mud","starcraft","preserving-play"))

add("wii",2006,"console","Wii","A familiar gesture opens a door",
    "Nintendo made swinging, pointing and sharing the room central to a console's design.",[
    "Wii's motion-sensitive remote offered a different invitation from an increasingly complicated gamepad. Its design asked how a wider range of people could understand an action by performing a familiar gesture.",
    "President Satoru Iwata's interviews documented the collaborative decisions behind the machine and its software. The ambition was not only new hardware: it was a broader place for play in everyday family life."],
    ("Nintendo","Iwata Asks — Wii closing statement, 7 December 2006","https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-Wii/Iwata-Asks-WarioWare-Smooth-Moves/Closing-statement/Closing-statement-228732.html"),tags=("Japan","hardware","controls"),related=("dance-dance-revolution","game-boy","switch"))

add("braid",2008,"game","Braid","A mistake can become a tool",
    "Jonathan Blow's puzzle-platformer makes reversing time something to think with.",[
    "Braid lets the player rewind actions, but its puzzles give that power different rules and consequences. An apparent failure can expose a useful relationship between moving objects, timing and memory.",
    "Released in 2008, it became a prominent part of a period in which smaller independent teams gained visibility through digital distribution. Its significance lies in how directly its central mechanic carries an idea, not simply in the size of its production."],
    ("Microsoft / Number None","Braid — Xbox release record","https://www.xbox.com/en-US/games/store/braid/bzgpbrq3lz7g"),date=(8,6,"day","Xbox Live Arcade release"),tags=("independent","puzzle","time"),related=("steam","papers-please","celeste"))

add("minecraft",2011,"game","Minecraft","A world becomes a set of materials",
    "Mining, making and sharing turn a landscape into an ongoing collective project.",[
    "Minecraft was available in public development before the release of version 1.0 in 2011. Its blocks give terrain a consistent grammar: an object can be removed, carried and placed somewhere else.",
    "The game grew from Markus Persson's early work into a wider Mojang production and a vast player culture. Buildings, servers, technical contraptions, lessons and videos extend its history far beyond one official set of objectives."],
    ("Mojang Studios","Minecraft 15th Anniversary — timeline","https://www.minecraft.net/en-us/15th-anniversary"),tags=("Sweden","building","online","PC"),related=("simcity","steam","preserving-play"),caveat="2011 marks version 1.0, not the first public builds, which appeared in 2009.")

add("journey",2012,"game","Journey","A stranger becomes a companion",
    "A few sounds, shared movement and an anonymous meeting can carry a story between players.",[
    "Journey follows a robed figure across a desert towards a distant mountain. Its online encounters remove voice chat and familiar player labels, asking two strangers to communicate through movement and a small musical call.",
    "Creative director Jenova Chen and the thatgamecompany team shaped an experience around emotional pacing. Art, animation and Austin Wintory's score carry meaning that does not depend on spoken dialogue.",
    "This form of connection is deliberately limited. Without a conventional conversation, offering help or waiting becomes unusually expressive. The 2012 PlayStation 3 release showed how multiplayer design could cultivate care as well as competition."],
    ("Sony Interactive Entertainment / Jenova Chen","Journey Takes Its First Steps This March","https://blog.playstation.com/2012/02/16/journey-takes-its-first-steps-this-march/"),date=(3,13,"day","North America: general PSN release"),tags=("United States","online","sound","art"),related=("myst","world-of-warcraft","celeste"),featured=True,layout="screening",caveat="The date is the announced general North American release. Early-access promotions and other regional dates differ.")

add("papers-please",2013,"game","Papers, Please","The desk is the difficult part",
    "Lucas Pope turns paperwork into a system of observation, pressure and moral decisions.",[
    "Papers, Please puts the player at a fictional border checkpoint. Documents must be compared under changing rules while time, wages and a household's needs apply pressure from outside the desk.",
    "The interface does much of the storytelling. Moving a passport, discovering a mismatch or deciding to make an exception makes an abstract policy personal. A deliberately small work space can expose a large system."],
    ("3909 / Lucas Pope","Papers, Please — press kit","https://papersplea.se/presskit/"),date=(8,8,"day","Windows, macOS and Linux release"),tags=("independent","PC","interface","storytelling"),related=("oregon-trail","simcity","braid"),layout="diptych")

add("pokemon-go",2016,"game","Pokémon GO","The map becomes a meeting place",
    "A smartphone game connected a familiar collection to streets, parks and routines.",[
    "Pokémon GO brought catching and collecting into a location-based mobile game in 2016. Walking through the physical world changed what could appear on the screen, linking play to places players already used or newly discovered.",
    "Its gatherings also made questions of access visible: not every neighbourhood has equal places to play, and not every player can move in the same way. Location-aware design ties virtual systems to the opportunities and limits of real environments."],
    ("Niantic / The Pokémon Company","Pokémon GO official site","https://pokemongo.com/"),tags=("mobile","location","Japan","United States"),related=("pokemon","animal-crossing"))

add("switch",2017,"console","Nintendo Switch","One game, different places",
    "A portable screen and a television dock let the same session move between private and shared space.",[
    "Nintendo Switch launched on 3 March 2017. Its detachable Joy-Con controllers and television dock combined portable and home-console arrangements in one system.",
    "The Legend of Zelda: Breath of the Wild accompanied the launch, offering a landscape built around observation, experimentation and routes chosen by the player. Hardware flexibility and open-ended software made different forms of personal exploration part of the same invitation."],
    ("Nintendo","Nintendo Switch launch announcement, 13 January 2017","https://www.nintendo.co.jp/corporate/release/en/2017/170113.html"),date=(3,3,"day","Initial launch markets"),tags=("Japan","portable","hardware"),related=("wii","game-boy","zelda","steam-deck"))

add("celeste",2018,"game","Celeste","Trying again is part of the story",
    "Precise platforming and an intimate journey put difficulty, support and self-understanding in the same frame.",[
    "Celeste asks players to guide Madeline through tightly composed platforming rooms. Short retries make failure an immediate part of learning, while the mountain journey gives that repeated effort an emotional context.",
    "The work of Maddy Thorson, Noel Berry, the art team, composer Lena Raine and collaborators joins precision with warmth. Assist options let players change the challenge, making access to the story a considered part of the design."],
    ("Extremely OK Games / Celeste team","Celeste official site and credits","https://www.celestegame.com/?lang=en"),tags=("Canada","independent","accessibility","sound"),related=("super-mario-bros","braid","journey"))

add("animal-crossing",2020,"game","Animal Crossing: New Horizons","A small routine in an unsettled year",
    "An island's daily tasks became part of how many people spent time together at a distance.",[
    "Animal Crossing: New Horizons released for Nintendo Switch in March 2020. Fishing, arranging rooms, meeting neighbours and visiting other islands gave players a gentle structure without a single required pace.",
    "Its launch coincided with the early months of the COVID-19 pandemic. Players used the game for gatherings and creative projects, but no one game represents everyone's experience of that period. Its history connects software design to the very different circumstances in which people played."],
    ("Nintendo","Animal Crossing: New Horizons","https://www.nintendo.com/us/store/products/animal-crossing-new-horizons-switch/"),tags=("Japan","online","everyday life"),related=("the-sims","switch","pokemon-go"))

add("steam-deck",2022,"console","Steam Deck","A PC library in your hands",
    "Valve's portable computer connects a console-like form to the changing software world of the PC.",[
    "Steam Deck brought the Steam library to a handheld PC running SteamOS. Its controls combine sticks, buttons, trackpads and a touch display, reflecting the many different interfaces PC games expect.",
    "Compatibility is ongoing work rather than a single hardware feature. The system shows how operating systems, translation tools and community knowledge help older and newer software move between environments. Portability can change not only where a game is played, but which parts of a library are revisited."],
    ("Valve","Steam Deck official booklet","https://media.steampowered.com/apps/valve/2022/steamDeck_booklet_EN.pdf"),tags=("PC","portable","compatibility"),related=("steam","game-boy","switch","preserving-play"))

add("preserving-play",2023,"feature","Preserving play","Keeping the decisions, not only the executable",
    "A playable game, a prototype and a remembered development story preserve different kinds of evidence.",[
    "A game is more than its final image. Controls, timing, hardware, distribution and the people around it shape the experience. Preserving one version is valuable, but it does not automatically preserve every way the game was played.",
    "Digital Eclipse's Gold Master Series places games beside documents, prototypes and interviews. Its 2023 opening title, The Making of Karateka, lets the audience trace a creation rather than only receive a verdict about its importance.",
    "Museums and community projects also preserve source code, packaging and oral histories. Emulation and restoration help maintain access to software as original equipment ages. Each approach answers a different question, and the most useful collections explain what survives and what remains uncertain.",
    "Pixel Museum is a curated starting collection, not an exhaustive history. Follow the sources, look at the objects closely and make connections between rooms. The medium's history is still being written by the people who make, play and preserve it."],
    ("Digital Eclipse","Introducing the Gold Master Series","https://www.digitaleclipse.com/media/goldmasterseries"),tags=("preservation","archives","design"),related=("spacewar","karateka","world-of-warcraft","steam"),featured=True)

add("tectoy",1989,"technology","Tectoy and the Master System","A platform's history changes with its geography",
    "Sega's Brazilian partner helped give familiar hardware a different cultural life.",[
    "Tectoy brought its first videogame console to Brazil in 1989, following an earlier partnership with Sega in electronic toys. Local manufacturing, distribution and communication shaped how Sega's machines reached Brazilian households.",
    "Hardware generations do not begin and end everywhere at once. A console that had become an older product in one market could remain current somewhere else. Brazil's experience makes a single global succession of machines an inadequate way to tell the story."],
    ("Tectoy","Tectoy — our history","https://www.loja.tectoy.com.br/quem-somos/"),tags=("Brazil","manufacturing","localisation"),related=("sonic","famicom","dandara"))

add("dandara",2018,"game","Dandara","A Brazilian voice changes the rules of movement",
    "Long Hat House made a world in which the heroine travels by leaping between surfaces.",[
    "Brazilian studio Long Hat House built Dandara around an unusual movement rule: the player moves between marked surfaces instead of freely walking. Rooms are read as networks of possible jumps, making familiar platform-game spaces feel different.",
    "The heroine draws inspiration from Dandara dos Palmares, associated with resistance to slavery in colonial Brazil. The game transforms that reference into a fictional world rather than claiming to reconstruct a documented biography. Its place in this collection links independent design to histories and perspectives outside the industry's most familiar centres."],
    ("Apple App Store editorial / Long Hat House","A warrior from Brazil","https://apps.apple.com/br/iphone/story/id1450220912"),tags=("Brazil","independent","movement"),related=("tectoy","celeste","raji"))

add("raji",2020,"game","Raji: An Ancient Epic","Building from a local visual tradition",
    "A studio in Pune brought Indian architectural and mythological references into an action adventure.",[
    "Nodding Heads Games developed Raji: An Ancient Epic in Pune, India. The team's art direction draws on Indian architecture, storytelling and visual traditions, placing a young protagonist within an adventure shaped by those references.",
    "The production's history includes the challenges faced by a small studio seeking an audience beyond its home market. It belongs here as one route through a much larger Indian games culture, rather than a claim that a country's game development began with a single title."],
    ("Epic Games / Nodding Heads Games","Raji: An Ancient Epic — developer interview","https://www.unrealengine.com/developer-interviews/raji-an-ancient-epic-represents-one-of-this-year-s-biggest-underdog-stories"),tags=("India","independent","art"),related=("dandara","journey"))

entries.sort(key=lambda e:(e["year"],e["id"]))
catalog = dict(schema_version=1,title="Pixel Museum",subtitle="People, machines and the worlds we made together.",language="en",edition="First collection",updated="2026-10-20",remote_catalog_url=None,eras=[dict(id=e[0],title=e[1],start_year=e[2],end_year=e[3],summary=e[4],palette=e[5]) for e in ERAS],entries=entries)
if __name__ == "__main__":
    media_path=ROOT/"media.json"
    if media_path.exists():
        media=json.loads(media_path.read_text(encoding="utf-8"))
        for entry in entries:
            for key in ("images","videos","models"):
                entry[key]=media.get(entry["id"],{}).get(key,[])
    (ROOT/"catalog.json").write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    credit_records=[]
    for entry in entries:
        for kind in ("images","videos","models"):
            for item in entry[kind]:
                credit_records.append(dict(exhibit_id=entry["id"],media_kind=kind[:-1],title=item.get("title",""),creator=item.get("creator",""),credit=item.get("credit",""),license=item.get("license","Copyright retained by the video creator and other respective rights holders"),license_url=item.get("license_url",""),source_page=item.get("source_page",""),url=item["url"]))
    credits=dict(title="Pixel Museum — collection credits",updated="2026-10-20",editorial="Original exhibition text written for Pixel Museum. This collection is an introduction to selected histories, not an exhaustive archive.",media_policy="Photographs and approved models are packaged locally with their source and licence records. Videos and music stream from their original publications. Third-party works retain their individual copyrights and licences.",design_references=[dict(name="Digital Eclipse — Gold Master Series",url="https://www.digitaleclipse.com/media/goldmasterseries"),dict(name="Gran Turismo — Brand Central museum",url="https://www.gran-turismo.com/au/news/00_1796083.html"),dict(name="SMK OPEN",url="https://collection.smk.dk/"),dict(name="Nasjonalmuseet",url="https://www.nasjonalmuseet.no/en/collection/")],sources=[dict(exhibit_id=e["id"],references=e["sources"]) for e in entries],media=credit_records)
    (ROOT/"credits.json").write_text(json.dumps(credits,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Wrote {len(entries)} exhibits across {len(ERAS)} eras")
