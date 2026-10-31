"""Original object stories for five exact, officially downloaded user selections.

The runtime assembler attaches actual licensed model files separately. Regional
dates are deliberately no more precise than the evidence recorded here.
"""


def source(title, url, publisher):
    return {"title": title, "url": url, "publisher": publisher}


NEW_BATCH_STORIES = [
    {
        "id": "gamecube", "title": "Nintendo GameCube", "year": 2001, "era_id": "connected",
        "date": {"month": 9, "day": 14, "precision": "day", "region": "Japan: original launch"},
        "release_dates": [{"year": 2001, "month": 9, "day": 14, "region": "Japan"}, {"year": 2001, "month": 11, "day": 18, "region": "North America"}, {"year": 2002, "month": 5, "day": 3, "region": "Europe"}],
        "subtitle": "A small box with room for four",
        "summary": "A compact console, small optical discs and a distinctive controller gave Nintendo's next generation a recognisable physical character.",
        "body": [
            "The indigo GameCube reached Japan on 14 September 2001. Its name described an unusually direct piece of industrial design: a compact body, a lid on top and a handle at the back. North America followed that November; Europe arrived in May 2002. A familiar object in one region could still be a new arrival somewhere else.",
            "Inside the lid was an eight-centimetre optical disc. Across the front were four controller ports, keeping shared play visible in the hardware itself. The controller gave its buttons different shapes and sizes around a large green A button. Rather than presenting every action as an identical mark, it made the arrangement something a thumb could learn by touch.",
            "The object also grew connections beyond its own discs. A cable linked compatible games to Game Boy Advance, while the later Game Boy Player fitted underneath and brought Game Boy, Game Boy Color and Game Boy Advance cartridges to a television. These accessories offered different ways to connect a portable library with the living room. The model shown here represents the original indigo case and its controller, rather than the later Panasonic Q or a special edition."
        ],
        "tags": ["Japan", "hardware", "Nintendo", "optical discs", "local multiplayer"], "related_ids": ["nintendo-64", "game-boy-advance", "wii"],
        "image_file": "GameCube-Console-Set.png", "image_title": "Indigo GameCube and its controller", "image_creator": "Evan-Amos",
        "sources": [
            source("Original GameCube hardware page - Japanese launch, disc format and ports", "https://www.nintendo.co.jp/ngc/thisis/index.html", "Nintendo"),
            source("GameCube accessories - Game Boy Advance cable and Game Boy Player", "https://www.nintendo.co.jp/ngc/acce/index.html", "Nintendo"),
            source("Nintendo history - North American and European GameCube launches", "https://www.nintendo.com/es-es/Hardware/La-historia-de-Nintendo/La-historia-de-Nintendo-625945.html", "Nintendo"),
        ],
        "factual_note": "The main date is the Japanese indigo hardware launch, not a global release. Game Boy Player was a later accessory, released in Japan on 21 March 2003; it was not part of the original console. GBA link functions depended on compatible software. Model creator LuisAR describes this as a low-poly reconstruction; the native renderer review decides whether its visual detail meets the exhibition standard.",
        "requested_model_uid": "34ca13c57463417b825cf72604eda75d", "requested_model_url": "https://sketchfab.com/models/34ca13c57463417b825cf72604eda75d", "ready_for_assembly_when_model_attached": True,
    },
    {
        "id": "game-boy-color", "title": "Game Boy Color", "year": 1998, "era_id": "dimensions",
        "date": {"month": 10, "day": 21, "precision": "day", "region": "Japan: original launch"},
        "release_dates": [{"year": 1998, "month": 10, "day": 21, "region": "Japan"}],
        "subtitle": "A new screen, an old library",
        "summary": "Colour changed the picture without asking players to leave their existing Game Boy cartridges behind.",
        "body": [
            "By 1998, a Game Boy could already carry years of someone's playing life. Nintendo's next handheld had to offer a visible change without making that collection feel disposable. Game Boy Color launched in Japan on 21 October, combining a colour screen with support for original Game Boy cartridges. Continuity was part of the attraction, not simply a technical footnote.",
            "Its appearance made the new direction easy to recognise. The case came in bright colours, including green, yellow and clear purple. The screen still relied on available light rather than a backlight, and two AA batteries powered the machine. The new experience remained attached to familiar habits: choosing a cartridge, finding a comfortable place to see the screen and carrying a small collection along.",
            "The library crossed the boundary in more than one way. Some cartridges worked on older Game Boys as well as the Color, while others required the new machine's capabilities. An existing game and a newly designed colour game could therefore sit beside each other in the same player's bag. The green model displayed here is an artist's reconstruction of that original form, with a game image on its screen; the screen image is not a claim that every cartridge was exclusive to Game Boy Color."
        ],
        "tags": ["Japan", "hardware", "handhelds", "colour", "backward compatibility"], "related_ids": ["game-boy", "pokemon", "game-boy-advance"],
        "image_file": "Nintendo-Game-Boy-Color-FL.jpg", "image_title": "Original Game Boy Color", "image_creator": "Evan-Amos",
        "sources": [
            source("Original Japanese Game Boy Color product page - launch and display", "https://www.nintendo.co.jp/n02/dmg/hardware/color/index.html", "Nintendo"),
            source("Game Boy Color - colours, battery power and cartridge library", "https://www.nintendo.com/en-gb/Hardware/Nintendo-History/Game-Boy-Color/Game-Boy-Color-627137.html", "Nintendo"),
            source("Game Boy cartridge compatibility - original, Color and Advance formats", "https://www.nintendo.com/de-ch/Support/Fruhere-Konsolen/Konnen-die-verschiedenen-Arten-an-Game-Boy-Game-Boy-Color-und-Game-Boy-Advance-Spielen-auf-allen-Game-Boy-Modellen-abgespielt-werden-619413.html", "Nintendo Support"),
        ],
        "factual_note": "The date is the Japanese hardware launch only. Later regional days are not inferred. This was a reflective colour display, not a backlit screen. The selected green artist model shows Pokemon Yellow; that game originated for Game Boy and must not be labelled a Game Boy Color exclusive.",
        "requested_model_uid": "277998bca398436faaece92470d93372", "requested_model_url": "https://sketchfab.com/models/277998bca398436faaece92470d93372", "ready_for_assembly_when_model_attached": True,
    },
    {
        "id": "intellivision", "title": "Intellivision", "year": 1980, "era_id": "personal",
        "date": {"month": 0, "day": 0, "precision": "year", "region": "United States: national introduction; test market in 1979"},
        "release_dates": [{"year": 1979, "month": 0, "day": 0, "precision": "year", "region": "Fresno area, California: test market"}, {"year": 1980, "month": 0, "day": 0, "precision": "year", "region": "United States: national introduction"}],
        "subtitle": "Putting a team on the television",
        "summary": "Mattel used sports, detailed animation and a different kind of controller to argue that its console could offer something beyond another game of Pong.",
        "body": [
            "Before its national American introduction in 1980, Intellivision was tested in and around Fresno, California, during 1979. That distinction matters: the first local sale and the wider arrival were different events. The brown and woodgrain console belonged to Mattel's attempt to give the home television a more ambitious role in play.",
            "Its controllers asked players to learn a different vocabulary. A disc registered sixteen directions, while a twelve-key pad and side buttons offered more inputs than a simple paddle. Sports helped make the argument for the hardware. Mattel's advertising compared its baseball with Atari's, while programmers worked around a less visible problem: the display hardware could draw only eight moving objects at once.",
            "The solution depended on decisions about what needed to move and what could temporarily become part of the background. A busy playing field was an effect constructed within limits, not an unlimited canvas. The Blue Sky Rangers' retrospective describes these techniques and the people behind them. Looking at the original console alongside that account brings the commercial promise and the programming work into the same frame: a machine sold through the picture, and games made through careful compromises."
        ],
        "tags": ["United States", "hardware", "sports", "controllers", "Mattel"], "related_ids": ["atari-vcs", "carol-shaw", "nes"],
        "image_file": "Intellivision-Console-Set.png", "image_title": "Original brown Intellivision and keypad controllers", "image_creator": "Evan-Amos",
        "sources": [
            source("Intellivision history - 1979 Fresno test and 1980 national introduction", "https://history.blueskyrangers.com/", "Blue Sky Rangers / former Mattel Electronics developers"),
            source("Intellivision Master Component - contemporary technical document and controllers", "https://history.blueskyrangers.com/hardware/2609.html", "Blue Sky Rangers / Mattel Electronics technical documentation"),
            source("Sports Network - baseball advertising and eight-object programming limit", "https://history.blueskyrangers.com/mattelelectronics/sportsnetwork.html", "Blue Sky Rangers"),
            source("Intellivision physical collection record 119195", "https://api.acmi.net.au/works/119195/", "ACMI"),
        ],
        "factual_note": "The timeline uses 1980 for the national US introduction, retaining 1979 as a separate Fresno test-market event. The artist source labels its specimen 1979 and says the model was developed with ACMI; that does not establish a worldwide launch date. The represented case is the original brown/woodgrain design, not the light-grey Intellivision II.",
        "requested_model_uid": "28b8c481499244f7a6259893bb29e077", "requested_model_url": "https://sketchfab.com/models/28b8c481499244f7a6259893bb29e077", "ready_for_assembly_when_model_attached": True,
    },
    {
        "id": "atari-lynx", "title": "Atari Lynx", "year": 1989, "era_id": "personal",
        "date": {"month": 0, "day": 0, "precision": "year", "region": "United States: original model; limited initial availability"},
        "release_dates": [{"year": 1989, "month": 0, "day": 0, "precision": "year", "region": "United States: original model"}],
        "subtitle": "Turn the screen around",
        "summary": "A colour handheld could change its orientation to suit the player's hands and link with other machines for shared games.",
        "body": [
            "The first Lynx arrived in 1989, bringing a colour screen into a handheld whose broad body was very different from a Game Boy. The comparison is useful, but the Lynx deserves a closer look than a contest between two specification sheets. It proposed its own relationship between the player's hands, the display and the people nearby.",
            "Atari's original manual explains a revealing feature: players could turn the machine around and flip its image, moving the directional pad from the left hand to the right. Games designed for a vertical screen could be held another way again. The arrangement treated orientation as a choice rather than a fixed assumption. Duplicated action buttons made that choice practical in the physical case.",
            "A ComLynx cable connected compatible games across separate handhelds. Each player could hold a screen while taking part in the same session. Colour, orientation and linked play all had to fit inside an object powered by batteries or an adaptor. The wide original model displayed here predates the smaller Lynx II. Its unusual proportions preserve a particular answer to portable play, rather than a failed attempt to become the same object as its better-known competitor."
        ],
        "tags": ["United States", "hardware", "handhelds", "colour", "multiplayer", "accessibility"], "related_ids": ["game-boy", "game-boy-color"],
        "image_file": "Atari-Lynx-I-Handheld.jpg", "image_title": "Original wide-body Atari Lynx", "image_creator": "Evan-Amos",
        "sources": [
            source("Lynx Portable Color Entertainment System Owner's Manual, C301139-001 Rev. B, 1989", "https://manuals.plus/m/708b76a2cbce86a01e73826d96f89017ca6e69cb7c0678f562e5be5cabb53a39", "Atari Corporation; scan hosted by Manuals+"),
            source("Atari Lynx physical collection object 113.6216 - 1989", "https://artsandculture.google.com/asset/handheld-video-game-console-atari-lynx-handheld-console-with-case-atari-inc/NQFD_BUY2NexDw?hl=en", "The Strong National Museum of Play / Google Arts & Culture"),
        ],
        "factual_note": "The date is retained at year precision. Initial 1989 availability and subsequent wider distribution are not collapsed into a fabricated worldwide day. The selected model is the original wide Lynx, not the smaller 1991 Lynx II. The original Atari manual is a primary document despite being hosted by a third-party scan archive. Native review must confirm the selected artist asset includes its intended surface detail.",
        "requested_model_uid": "19163d8c9a464eda85977f245b3e6525", "requested_model_url": "https://sketchfab.com/models/19163d8c9a464eda85977f245b3e6525", "ready_for_assembly_when_model_attached": True,
    },
    {
        "id": "hanimex-7771", "title": "Hanimex 7771", "year": 1977, "era_id": "public-play",
        "date": {"month": 0, "day": 0, "precision": "year", "region": "French-labelled example; year recorded by hands-on restoration documentation"},
        "release_dates": [{"year": 1977, "month": 0, "day": 0, "precision": "year", "region": "Documented model year; exact first-sale day and regional rollout not established"}],
        "subtitle": "The television learns a new trick",
        "summary": "Two paddles and a fixed set of games turned an ordinary television into a shared playing surface, long before the idea of a console library became familiar.",
        "body": [
            "The French-labelled Hanimex 7771 belongs to a time when a television game could be an appliance with its games already inside. Its orange case, two detachable paddle controls and switches made the rules visible before the television was even on. A player adjusted a dial to meet a moving ball, sharing a screen with another person rather than choosing from shelves of cartridges.",
            "A documented restoration dates this model to 1977 and shows the General Instrument AY-3-8500 chip inside. Much of the game's behaviour was concentrated in that circuit. The original connection sent its picture through a television's aerial input; getting it on screen involved tuning a channel. Decades later, restoring the sound and picture meant dealing with corroded batteries, ageing connections and a television standard many newer screens no longer receive.",
            "The object also survives beyond private memories. France's national library recorded a Hanimex 7771 among the equipment received in a 2008 bequest. That modest entry is a reminder of what preservation can include: not only celebrated software, but the machines, connectors and ordinary domestic objects that made an evening's play possible. This is its own console, not a substitute model for the earlier Magnavox Odyssey."
        ],
        "tags": ["France", "hardware", "dedicated consoles", "Pong", "preservation"], "related_ids": ["pong", "odyssey", "preserving-play"],
        "image_file": "Hanimex Mod\u00e8le 7771 Jeu-Tele Electronique.jpg", "image_title": "French-labelled orange Hanimex 7771", "image_creator": "William G\u00e9rald Blondel",
        "sources": [
            source("Hanimex 7771 hands-on restoration - model year, circuit and original TV connection", "https://lesdocs.fr/composite-pong-hanimex-7771/", "Guillaume / Les Docs"),
            source("2008 donations and bequests report - Hanimex 7771, final page", "https://www.bnf.fr/sites/default/files/2018-11/dons_rapport_2008.pdf", "Biblioth\u00e8que nationale de France"),
            source("Original photograph of the French-labelled Hanimex 7771, Japan Touch Haru 2015", "https://commons.wikimedia.org/wiki/File:Hanimex_Mod%C3%A8le_7771_Jeu-Tele_Electronique.jpg", "William G\u00e9rald Blondel / Wikimedia Commons"),
        ],
        "factual_note": "1977 is the model year stated in first-hand restoration documentation, not a verified exact international launch date. The model author's unsupported claims about Nokiasho, Denis Stephane and an exact 8 June 1978 introduction are intentionally not used. The physical French-labelled object is independently documented by the BnF and an original exhibition photograph. It is separate from the Magnavox Odyssey and from later Hanimex cartridge-based hardware.",
        "requested_model_uid": "0642fd75d52b4fbdae0dfe6b95276715", "requested_model_url": "https://sketchfab.com/models/0642fd75d52b4fbdae0dfe6b95276715", "ready_for_assembly_when_model_attached": True,
    },
]
