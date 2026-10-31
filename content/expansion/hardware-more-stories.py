"""Additional hardware stories, conditional on the selected licensed model files."""

def source(title, url, publisher):
    return {"title": title, "url": url, "publisher": publisher}


MORE_STORIES = [
    {
        "id": "nintendo-64", "title": "Nintendo 64", "year": 1996, "era_id": "dimensions",
        "date": {"month": 6, "day": 23, "precision": "day", "region": "Japan: original hardware launch"},
        "release_dates": [{"year": 1996, "month": 6, "day": 23, "region": "Japan"}, {"year": 1997, "month": 3, "day": 0, "precision": "month", "region": "Europe"}],
        "subtitle": "Learning to move through space",
        "summary": "An unusual controller and four built-in ports connected the new problem of moving through 3D worlds with the familiar pleasure of playing together.",
        "body": [
            "Nintendo 64 reached Japan on 23 June 1996. Project Reality, the development partnership announced in 1993, had become an object that players could finally put beside a television. Super Mario 64 helped explain what the change meant: an environment to explore, rather than a picture to move across. The console's launch and its earlier announcement belong at different points on this timeline.",
            "Its controller made that transition physical. Three grips offered different ways to hold it, with an analogue stick in the centre and a trigger underneath. Moving the stick was a different action from choosing a direction on a pad. Designers could connect the direction and extent of a movement to what happened in a three-dimensional world, while familiar buttons remained within reach.",
            "Four controller ports made another ambition visible on the front of the machine. Mario Kart 64 and Mario Party could turn the same room into a shared playing space, with friends looking at one television. Europe's release followed in March 1997. The dark original-style body displayed here represents the platform; later transparent colours and special editions gave the same underlying machine different visual identities."
        ],
        "tags": ["Japan", "hardware", "3D", "controllers", "local multiplayer"], "related_ids": ["workbook-08-23-nintendo-64", "super-mario-64", "playstation"],
        "image_file": "Nintendo-64-wController-L.jpg", "image_title": "Nintendo 64 with its three-grip controller", "image_creator": "Evan-Amos",
        "sources": [
            source("Nintendo history - Japanese June 1996 launch and European March 1997 release", "https://www.nintendo.com/es-es/Hardware/La-historia-de-Nintendo/La-historia-de-Nintendo-625945.html", "Nintendo"),
            source("Nintendo 64 - controller, four ports and library", "https://www.nintendo.com/en-gb/Hardware/Nintendo-History/Nintendo-64/Nintendo-64-625959.html", "Nintendo"),
            source("Nintendo's 1996 Japanese software list - launch-day titles", "https://www.nintendo.co.jp/n01/n64/software/1996.html", "Nintendo"),
        ],
        "factual_note": "The date is the Japanese retail launch, separate from Project Reality's 1993 announcement. European timing is recorded to month precision from Nintendo's history. Do not repeat Nintendo's promotional 'first analogue stick' claim as a worldwide historical first. The artist model includes four controllers and a later game cartridge; it is not an authenticated launch-day boxed set.",
        "requested_model_uid": "0a6b8eb8097e4365a34b1af7b6eac408", "requested_model_url": "https://sketchfab.com/3d-models/nintendo-64-0a6b8eb8097e4365a34b1af7b6eac408", "model_selection_note": "Root selected this licensed candidate after public metadata and publisher-thumbnail review; it is not a silent substitution for a view-only user link.", "ready_for_assembly_when_model_attached": True,
    },
    {
        "id": "mega-drive", "title": "Mega Drive / Genesis", "year": 1988, "era_id": "personal",
        "date": {"month": 10, "day": 29, "precision": "day", "region": "Japan: original Mega Drive launch"},
        "release_dates": [{"year": 1988, "month": 10, "day": 29, "region": "Japan"}, {"year": 1989, "month": 0, "day": 0, "precision": "year", "region": "North America: Genesis"}, {"year": 1990, "month": 0, "day": 0, "precision": "year", "region": "Europe: Mega Drive"}],
        "subtitle": "One machine, more than one identity",
        "summary": "Sega's 16-bit console changed its name across regions, carrying a growing library from its Japanese launch into different markets and memories.",
        "body": [
            "The words on the case changed as Sega's console travelled. Mega Drive launched in Japan on 29 October 1988. North America received it as Genesis the following year, while the European Mega Drive arrived in 1990. Those names describe related regional histories, rather than rival machines or one simultaneous worldwide release. The model here carries the Mega Drive wordmark.",
            "Sega presented 16-bit hardware through the promise of stronger pictures, speed and sound. Its history also involved software makers beyond Sega itself and an expanding range of peripherals. The console was a platform around which games, accessories and different physical versions accumulated. A cartridge slot and a pair of controller ports were only part of that wider system.",
            "Sonic the Hedgehog gave it a particularly recognisable face in 1991. Sega's own retrospective links the game's arrival to the platform's growing international popularity. Later additions such as Mega-CD explored different storage and software possibilities, while redesigned cases changed the object on the shelf. The original form factor is useful precisely because it sits near the beginning of this branching story: before a long-lived family of names and versions became a single nostalgic image."
        ],
        "tags": ["Japan", "hardware", "16-bit", "regional releases", "Sega"], "related_ids": ["sonic", "sega-saturn", "snes-pal"],
        "image_file": "Sega-Mega-Drive-JP-Mk1-Console-Set.jpg", "image_title": "Japanese first-model Mega Drive and controller", "image_creator": "Evan-Amos",
        "sources": [
            source("Mega Drive - Japanese launch, hardware and regional branding", "https://www.sega.jp/history/hard/megadrive/index.html", "Sega"),
            source("Sega company timeline - Japan 1988, Genesis 1989 and Europe 1990", "https://www.sega.jp/history/companyTimeline/en/", "Sega"),
        ],
        "factual_note": "The main date is the Japanese Mega Drive launch. North American 1989 and European 1990 releases are retained at year precision here. Although the artist calls the model Sega_Genesis, its visible case is Mega Drive-branded; do not label it a verified North American Genesis specimen. This is the first case form factor, not a Mega Drive II/Genesis Model 2 or the Brazilian Mega Drive III.",
        "requested_model_uid": "d1487aa8b216490ba7c414b95531479e", "requested_model_url": "https://sketchfab.com/3d-models/sega-genesis-d1487aa8b216490ba7c414b95531479e", "model_selection_note": "Root selected this licensed candidate after public metadata and publisher-thumbnail review. The exhibit caption follows the Mega Drive branding visible on the model, not its imprecise source title.", "ready_for_assembly_when_model_attached": True,
    },
    {
        "id": "xbox-360", "title": "Xbox 360", "year": 2005, "era_id": "connected",
        "date": {"month": 11, "day": 22, "precision": "day", "region": "North America: original launch"},
        "release_dates": [{"year": 2005, "month": 11, "day": 22, "region": "North America"}, {"year": 2005, "month": 12, "day": 2, "region": "Europe"}, {"year": 2005, "month": 12, "day": 10, "region": "Japan"}],
        "subtitle": "A profile that follows you between games",
        "summary": "Xbox Live, Achievements and a dashboard full of downloadable games made the console's identity extend beyond the disc currently in its drive.",
        "body": [
            "Xbox 360 launched in North America on 22 November 2005, followed by Europe on 2 December and Japan on 10 December. Microsoft was introducing a new console, but it was also extending the role of Xbox Live. A gamer profile, messages and friends could connect experiences that otherwise belonged to separate games. The dashboard became a place to return to, rather than just a route to a disc.",
            "Achievements gave that shared identity another visible form. Progress could contribute to a Gamerscore that travelled across games. Xbox Live Marketplace offered demonstrations, trailers and downloadable content, while Xbox Live Arcade placed smaller games directly inside the console's interface. Geometry Wars Retro Evolved and Bejeweled 2 appeared alongside other launch downloads. A game did not need a large physical box to be encountered from the sofa.",
            "The curved original case became the object associated with this connected routine, but its colours and hardware configurations changed over time. The rotating model is a black version of that early form factor, rather than the white machine most closely associated with the 2005 launch. Keeping those details separate lets one exhibit explain both a platform's beginning and the later object an artist chose to reconstruct."
        ],
        "tags": ["hardware", "online communities", "Achievements", "digital distribution"], "related_ids": ["xbox-halo", "xbox-one", "journey"],
        "image_file": "Xbox-360-Pro-wController.jpg", "image_title": "White original-form-factor Xbox 360 and controller", "image_creator": "Evan-Amos",
        "sources": [
            source("Xbox 360 - contemporary regional launch announcement", "https://news.xbox.com/en-us/2005/09/15/xbox-launch-dates-announced/", "Xbox / Major Nelson"),
            source("Xbox 360 - profiles, Marketplace and hardware announcement", "https://news.xbox.com/en-us/2005/08/17/xbox-360-details-and-prices/", "Xbox / Major Nelson"),
            source("Xbox Live Marketplace and Arcade launch content", "https://news.xbox.com/en-us/2005/11/15/xbox-live-marketplace-launch-content/", "Xbox / Major Nelson"),
            source("Achievements and Gamerscore - platform history", "https://news.xbox.com/en-us/2013/06/12/xbox-one-achievements/", "Xbox"),
        ],
        "factual_note": "The chronology date is the North American 2005 launch. The photograph shows a white original-form-factor console; the selected artist model depicts a later black colourway. Do not identify the black model as a measured 2005 launch specimen or assert an exact Elite production revision without further evidence.",
        "requested_model_uid": "f65ac4721fd34dd8a8b63adfa712f5b8", "requested_model_url": "https://sketchfab.com/3d-models/xbox-360-black-3d-model-by-rob-bryant-jr-f65ac4721fd34dd8a8b63adfa712f5b8", "model_selection_note": "Root selected this licensed black original-form-factor candidate after public metadata and publisher-thumbnail review. Platform launch and the model's later black colourway are explicitly distinguished.", "ready_for_assembly_when_model_attached": True,
    },
]
