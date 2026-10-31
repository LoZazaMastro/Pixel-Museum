"""Original museum text for hardware requested in the bulk model selection."""

BULK_STORIES = [
    {
        "id": "nes", "title": "Nintendo Entertainment System", "year": 1985, "era_id": "personal",
        "date": {"month": 0, "day": 0, "precision": "year", "region": "North America: initial NES release"},
        "release_dates": [{"year": 1985, "month": 0, "day": 0, "region": "North American initial release; rollout continued subsequently"}, {"year": 1986, "month": 0, "day": 0, "region": "European rollout began; dates varied by country"}],
        "subtitle": "A familiar world in a different box",
        "summary": "The grey NES carried Nintendo's cartridge library into new living rooms, with a different identity from Japan's Famicom.",
        "body": [
            "Nintendo brought the Nintendo Entertainment System to North America in1985. It followed the Japanese Family Computer, or Famicom, introduced in1983, but presented that platform in a different physical form. The grey front-loading case, detachable controllers and long cartridges belong to the western NES story. They should not be mistaken for the red-and-white machine's earlier Japanese debut.",
            "Its small controller concentrated play around a directional pad and two main action buttons. Across the growing library, those few inputs could mean running and jumping, exploring a maze or choosing when to fight. Super Mario Bros., The Legend of Zelda and Metroid helped give Nintendo's characters and worlds a place in everyday home life.",
            "The European rollout began in1986, with national markets following different schedules. The machine's history is therefore more than one release date or one claim to have transformed a market. It is also the story of how the same games reached different households through different objects, packaging and local experiences."
        ],
        "tags": ["hardware", "Nintendo", "cartridges", "regional design"], "related_ids": ["famicom", "snes-pal", "game-boy"],
        "image_file": "NES-Console-Set.png", "image_title": "Front-loading Nintendo Entertainment System and controller", "image_creator": "Evan-Amos",
        "sources": [
            {"title": "Nintendo of America history - NES launch in1985", "url": "https://careers.nintendo.com/our-history/", "publisher": "Nintendo of America"},
            {"title": "Nintendo history - Famicom origins and European NES rollout", "url": "https://www.nintendo.com/en-gb/Hardware/Nintendo-History/Nintendo-History-625945.html", "publisher": "Nintendo"},
            {"title": "Metroid creators - directional pad and two-button design", "url": "https://iwataasks.nintendo.com/interviews/wii/metroid-other-m/0/1/", "publisher": "Nintendo / Iwata Asks"}
        ],
        "factual_note": "1985 refers to the initial North American NES release, not Famicom's1983 Japanese launch or a simultaneous worldwide release. Exact North American rollout day is not inferred from the year-only source. European rollout began in1986 and varied by country.",
        "requested_model_uid": "3d05bd5b534f4d869934b09e9bf0c224", "requested_model_url": "https://sketchfab.com/3d-models/nintendo-entertainment-system-3d05bd5b534f4d869934b09e9bf0c224", "ready_for_assembly_when_model_attached": False
    },
    {
        "id": "snes-pal", "title": "Super Nintendo — PAL edition", "year": 1992, "era_id": "dimensions",
        "date": {"month": 0, "day": 0, "precision": "year", "region": "European/PAL release; country schedules varied"},
        "release_dates": [{"year": 1992, "month": 0, "day": 0, "region": "European/PAL rollout; no single country-specific day asserted"}],
        "subtitle": "More colour, more room to play",
        "summary": "Nintendo's16-bit generation reached European homes with a rounded case, colourful buttons and a library that stretched across very different kinds of worlds.",
        "body": [
            "For European players, the Super Nintendo arrived in1992. The PAL machine kept the rounded outline and multicolour controller buttons associated with the Japanese Super Famicom, rather than the angular purple-button design sold in North America. This exhibit follows that regional object, not an invented worldwide launch shared by every version.",
            "The controller expanded the familiar directional pad and face buttons with shoulder buttons under the player's index fingers. Stereo sound and richer imagery gave designers more room, but the results were not confined to spectacle. Super Mario World offered a colourful landscape of secrets; A Link to the Past built an adventure around revisiting places with new abilities; Super Metroid made exploration feel lonely and uncertain.",
            "F-Zero and Super Mario Kart turned the new machine towards a different sensation: speed and competition. Looking across this library, the generational change becomes visible through contrasts. A single cartridge system could hold races, long journeys and quiet discoveries, each asking something different of the same controller."
        ],
        "tags": ["hardware", "Nintendo", "PAL", "16-bit", "regional design"], "related_ids": ["nes", "famicom", "game-boy"],
        "image_file": "Wikipedia SNES PAL.png", "image_title": "PAL Super Nintendo console and controller", "image_creator": "JCD1981NL; derivative image by Aurora Romes",
        "sources": [
            {"title": "Super Nintendo - European1992 release, controller and library", "url": "https://www.nintendo.com/en-gb/Hardware/Nintendo-History/Super-Nintendo/Super-Nintendo-627040.html", "publisher": "Nintendo"},
            {"title": "Nintendo history - regional Super Nintendo chronology", "url": "https://www.nintendo.com/en-gb/Hardware/Nintendo-History/Nintendo-History-625945.html", "publisher": "Nintendo"},
            {"title": "Super Metroid - original game and exploration", "url": "https://www.nintendo.com/us/store/products/super-metroid-new-3ds/", "publisher": "Nintendo"}
        ],
        "factual_note": "1992 is the European/PAL rollout year, not the1990 Japanese Super Famicom or1991 North American SNES release. Nintendo's general history summarises Europe as June1992, while national launches varied; this entry deliberately retains year precision rather than assigning one country-specific date to all PAL regions.",
        "requested_model_uid": "31f4914a42e14631aeba15a539161e62", "requested_model_url": "https://sketchfab.com/3d-models/snes-pal-super-mario-world-31f4914a42e14631aeba15a539161e62", "ready_for_assembly_when_model_attached": False
    },
    {
        "id": "sega-saturn", "title": "Sega Saturn", "year": 1994, "era_id": "dimensions",
        "date": {"month": 11, "day": 22, "precision": "day", "region": "Japan: original platform launch"},
        "release_dates": [{"year": 1994, "month": 11, "day": 22, "region": "Japan"}, {"year": 1995, "month": 5, "day": 0, "region": "North America; month precision in cited Sega retrospective"}],
        "subtitle": "The arcade has more than one future",
        "summary": "Saturn brought Sega's arcade ambitions home while giving richly drawn2D games a place beside the new polygon worlds.",
        "body": [
            "Sega Saturn launched in Japan on22November1994 with Virtua Fighter among its defining attractions. Sega's arcade fighting game had made three-dimensional characters a compelling new spectacle. Bringing that kind of experience into the home became one of the machine's central promises.",
            "Yet Saturn's identity cannot be reduced to the arrival of polygons. Its library also became a home for2D fighting games and shooters, supported in some cases by additional memory cartridges. Sega's own retrospective places those games alongside arcade adaptations such as Daytona USA, Sega Rally Championship and Virtua Fighter2. The new generation could develop several visual languages at once.",
            "The platform reached North America in1995, in a market where Sega was also trying to extend the life of Genesis through the32X. Those overlapping plans made the transition complicated. The grey Japanese launch machine and black western versions also remind us that Saturn was never encountered in exactly the same way everywhere: its hardware, software library and position in the market depended on where a player lived."
        ],
        "tags": ["hardware", "Sega", "arcades", "2D", "3D"], "related_ids": ["dreamcast", "playstation", "virtua-fighter"],
        "image_file": "Sega-Saturn-JP-Mk1-Console-Set.jpg", "image_title": "Original grey Japanese Sega Saturn and controller", "image_creator": "Evan-Amos",
        "sources": [
            {"title": "Sega Saturn - Japanese launch and hardware overview", "url": "https://www.sega.jp/history/hard/segasaturn/index.html", "publisher": "Sega"},
            {"title": "Sega hardware story5 - Saturn, arcade ports and the32X transition", "url": "https://www.sega.jp/history/hard/column/column_05.html", "publisher": "Sega"}
        ],
        "factual_note": "The chronology date is the Japanese platform launch. The selected Unconid3D model depicts a black western-style case, while the photograph shows the grey Japanese original. Do not label the selected black case as the exact Japanese1994 launch colourway.",
        "requested_model_uid": "a0eab4c5a35f4ff68e5b83690e4179cd", "requested_model_url": "https://sketchfab.com/3d-models/sega-saturn-a0eab4c5a35f4ff68e5b83690e4179cd", "ready_for_assembly_when_model_attached": False
    },
    {
        "id": "xbox-one", "title": "Xbox One", "year": 2013, "era_id": "everywhere",
        "date": {"month": 11, "day": 22, "precision": "day", "region": "Initial13 markets; further territories followed"},
        "release_dates": [{"year": 2013, "month": 11, "day": 22, "region": "Australia, Austria, Brazil, Canada, France, Germany, Ireland, Italy, Mexico, New Zealand, Spain, UK and USA"}],
        "subtitle": "A console at the centre of the room",
        "summary": "Microsoft presented Xbox One as a shared home-entertainment hub, placing games beside television, communication and the Kinect sensor.",
        "body": [
            "Xbox One arrived on22November2013 in13 initial markets. Microsoft presented it as a machine for more than games: television, streaming, Skype and voice control were part of the same living-room proposal. The original large black console and Kinect sensor gave that ambition a physical form.",
            "The games still had to establish what this new Xbox felt like to play. Forza Motorsport5 focused on cars and circuits, Dead Rising3 filled its setting with zombies, and Ryse: Son of Rome pursued a cinematic historical spectacle. Around them, features such as Game DVR and Upload made recording and circulating play part of the platform's everyday activity.",
            "The original model displayed here belongs to that2013 beginning, before the smaller Xbox OneS and the later OneX. Its story captures a particular moment when a console maker tried to gather many activities beneath one interface. The object makes those priorities readable: a games machine designed to claim a broad place beneath the television."
        ],
        "tags": ["hardware", "Microsoft", "Kinect", "home entertainment"], "related_ids": ["xbox-halo", "playstation-4", "xbox-series-x", "xbox-series-s"],
        "image_file": "Microsoft-Xbox-One-Console-Set-wKinect.jpg", "image_title": "Original Xbox One with controller and Kinect", "image_creator": "Evan-Amos",
        "sources": [
            {"title": "Xbox One - thirteen initial launch markets", "url": "https://news.xbox.com/en-us/2013/09/04/xbox-one-to-launch-on-november-22-2013-in-13-markets/", "publisher": "Microsoft / Xbox Wire"},
            {"title": "Xbox One - launch-day entertainment and Kinect", "url": "https://news.xbox.com/en-us/2013/11/22/xbox-one-launch-blog/", "publisher": "Microsoft / Xbox Wire"},
            {"title": "Xbox One - launch games", "url": "https://news.xbox.com/en-us/2013/11/22/xbox-one-games-blog/", "publisher": "Microsoft / Xbox Wire"},
            {"title": "Xbox One - Game DVR and sharing proposal", "url": "https://news.xbox.com/en-us/2013/11/08/xbox-one-complete-games-entertainment/", "publisher": "Microsoft / Xbox Wire"}
        ],
        "factual_note": "22November2013 applies to13 named initial markets, not every country. The selected model represents the original Xbox One, not Xbox OneS or Xbox OneX. These are distinct from the2020 SeriesS and SeriesX.",
        "requested_model_uid": "8866e33768e84b27b69e07abcde8a593", "requested_model_url": "https://sketchfab.com/3d-models/xbox-one-8866e33768e84b27b69e07abcde8a593", "ready_for_assembly_when_model_attached": True
    },
    {
        "id": "xbox-series-x", "title": "Xbox Series X", "year": 2020, "era_id": "living-history",
        "date": {"month": 11, "day": 10, "precision": "day", "region": "Initial international launch markets"},
        "release_dates": [{"year": 2020, "month": 11, "day": 10, "region": "Initial international launch markets; availability varied by territory"}],
        "subtitle": "A new generation carries its library forward",
        "summary": "Fast storage, a tower-shaped case and compatibility with older games made continuity part of Microsoft's next-generation argument.",
        "body": [
            "Xbox SeriesX launched on10November2020 alongside the smaller SeriesS. Microsoft described the generation through power, speed and compatibility. The new console was intended to deliver more detailed games, but also to reduce waiting and bring existing collections into the new hardware generation.",
            "Its solid-state storage supported faster loading and Quick Resume, which could keep several supported games ready to continue. A disc drive remained part of the original SeriesX design. For players with compatible physical games, the old collection could still have a place beside digital purchases and subscription libraries.",
            "The tall black body gave those ambitions a different silhouette from the broad original Xbox One. Yet the platform's argument was partly about avoiding a complete break: compatible games, accessories and saved progress could travel forward. This exhibit follows that combination of change and continuity, rather than treating a console generation as nothing more than a reset of technical specifications."
        ],
        "tags": ["hardware", "Microsoft", "solid-state storage", "backward compatibility"], "related_ids": ["xbox-one", "xbox-series-s", "playstation-5", "preserving-play"],
        "image_file": "Xbox Series X mit Controller (transparent background).png", "image_title": "Retail Xbox Series X and controller", "image_creator": "Der. Bellemer",
        "sources": [
            {"title": "Xbox SeriesX and SeriesS -10November2020 launch", "url": "https://news.xbox.com/en-us/2020/11/10/power-your-dreams-xbox-series-x-and-xbox-series-s-available-now/", "publisher": "Microsoft / Xbox Wire"},
            {"title": "Xbox SeriesX - design decisions, storage and compatibility", "url": "https://news.xbox.com/en-us/2020/03/16/xbox-series-x-tech/", "publisher": "Microsoft / Xbox Wire"}
        ],
        "factual_note": "The platform date is the2020 retail launch. The user's selected jordanger88 model was published inDecember2019 and is explicitly described by its creator as a quick mock-up of the announced console. It must be labelled as a pre-release artist reconstruction, not a measured model or scan of final retail hardware. The photograph shows retail hardware.",
        "requested_model_uid": "e983b0e9ef984aa6934176e310b7f0f2", "requested_model_url": "https://sketchfab.com/3d-models/xbox-series-x-console-e983b0e9ef984aa6934176e310b7f0f2", "ready_for_assembly_when_model_attached": True
    },
    {
        "id": "xbox-series-s", "title": "Xbox Series S", "year": 2020, "era_id": "living-history",
        "date": {"month": 11, "day": 10, "precision": "day", "region": "Initial international launch markets"},
        "release_dates": [{"year": 2020, "month": 11, "day": 10, "region": "Initial international launch markets; availability varied by territory"}],
        "subtitle": "A smaller doorway into the same generation",
        "summary": "The compact, disc-free SeriesS traded a higher rendering target for a lower launch price while sharing the generation's core storage and processing approach.",
        "body": [
            "Xbox SeriesS launched on10November2020 as a second route into the same generation as SeriesX. Its small white case and large black circular vent made the difference visible. At a US launch price of$299, it was positioned below the$499 SeriesX, with a lower rendering target rather than a separate catalogue of next-generation games.",
            "The console retained the generation's emphasis on fast storage and Quick Resume. Microsoft designed SeriesS around similar CPU capability and the same input/output performance as SeriesX, allowing developers to scale imagery while keeping those shared foundations. That distinction mattered more than a simple comparison of how many pixels appeared on screen.",
            "There was no disc drive. A player's library therefore depended on digital purchases, compatible digital games and services, rather than inserting an existing disc. The original2020 SeriesS is a useful museum object because it makes an economic and cultural choice tangible: a smaller, less expensive console whose access to games is entirely digital."
        ],
        "tags": ["hardware", "Microsoft", "digital libraries", "access"], "related_ids": ["xbox-one", "xbox-series-x", "playstation-5", "preserving-play"],
        "image_file": "Xbox Series S with controller (transparent background).png", "image_title": "Original white Xbox SeriesS and controller", "image_creator": "AsmodeanUnderscore",
        "sources": [
            {"title": "Introducing Xbox SeriesS - design, shared capabilities and price", "url": "https://news.xbox.com/en-us/2020/09/09/introducing-xbox-series-s/", "publisher": "Microsoft / Xbox Wire"},
            {"title": "Xbox SeriesX and SeriesS - launch date and US pricing", "url": "https://news.xbox.com/en-us/2020/09/09/xbox-series-x-and-xbox-series-s-launching-november-10/", "publisher": "Microsoft / Xbox Wire"}
        ],
        "factual_note": "The object is the original white2020 SeriesS, not a later black1TB revision. Dollar figures are US launch prices, not current or worldwide pricing. November10,2020 is the initial international launch date, not a claim of availability in every territory.",
        "requested_model_uid": "61a9d3b53ba34841a9272f38e8be736a", "requested_model_url": "https://sketchfab.com/3d-models/xbox-series-s-61a9d3b53ba34841a9272f38e8be736a", "ready_for_assembly_when_model_attached": False
    }
]
