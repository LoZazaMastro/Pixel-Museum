"""Pending portable exhibits: hardware variants and release regions stay explicit."""

def source(title, url):
    return {"title": title, "url": url, "publisher": "Nintendo"}


PORTABLE_STORIES = [
    {
        "id": "nintendo-dsi", "title": "Nintendo DSi", "year": 2008, "era_id": "connected",
        "date": {"month": 11, "day": 1, "precision": "day", "region": "Japan: original DSi launch"},
        "release_dates": [{"year": 2008, "month": 11, "day": 1, "region": "Japan"}, {"year": 2009, "month": 4, "day": 3, "region": "Europe"}, {"year": 2009, "month": 4, "day": 5, "region": "North America"}],
        "subtitle": "A handheld becomes a personal collection",
        "summary": "Cameras, sound tools and downloadable software gave the DS family another way to make a handheld feel like your own.",
        "body": [
            "The original Nintendo DS had introduced its two-screen format in North America in November 2004. DSi was a later revision, first released in Japan on 1 November 2008. Europe followed on 3 April 2009 and North America two days later. Its name belongs to that particular machine, rather than to the beginning of the entire DS family.",
            "Nintendo put two cameras, sound manipulation tools and internal storage into a thinner case. A player could photograph a friend, distort the result or experiment with the pitch of a recording. These activities made the machine a small creative tool as well as a place to play cartridges. The touchscreen already familiar to DS owners now helped arrange material they had made themselves.",
            "DSiWare added downloadable games and applications through the DSi Shop. Software could remain inside the handheld alongside personal photographs and recordings. The physical object still opened into two screens, but the collection it carried was becoming less dependent on which cartridge was in its slot. This exhibit shows the DSi revision; it should not be mistaken for the original 2004 DS or the 2006 DS Lite."
        ],
        "tags": ["Japan", "hardware", "handhelds", "cameras", "digital libraries"], "related_ids": ["game-boy", "wii"],
        "image_file": "Nintendo-DSi-Bl-Open.png", "image_title": "Nintendo DSi, the 2008 revision of the DS family", "image_creator": "Evan-Amos",
        "sources": [
            source("Nintendo Conference Fall 2008 - DSi Japanese launch", "https://www.nintendo.co.jp/event/conference2008fall/presen/e/05.html"),
            source("Nintendo DSi European launch and creative features", "https://www.nintendo.com/en-gb/News/2009/Nintendo-DSi-arrives-in-Europe-on-3-April-2009-251500.html"),
            source("Nintendo's DS family chronology - DS, DS Lite and DSi", "https://www.nintendo.com/nl-nl/Nieuws/2009/Nintendo-verscheept-het-100-miljoenste-draagbare-Nintendo-DS-systeem-251524.html"),
        ],
        "factual_note": "DSi is the 2008 Japanese revision, not the original DS launched in 2004. The selected model's creator identifies it as DSi and acknowledges missing camera and button details; the source title 'Nintendo DS' is less precise than the creator's description. Historical references to DSi Shop describe its original operation, not a currently available service.",
        "requested_model_uid": "934fdde060874d5c99b40cdf1dbb37f2", "requested_model_url": "https://sketchfab.com/3d-models/nintendo-ds-934fdde060874d5c99b40cdf1dbb37f2", "ready_for_assembly_when_model_attached": True,
    },
    {
        "id": "game-boy-advance", "title": "Game Boy Advance", "year": 2001, "era_id": "connected",
        "date": {"month": 3, "day": 21, "precision": "day", "region": "Japan: original horizontal GBA launch"},
        "release_dates": [{"year": 2001, "month": 3, "day": 21, "region": "Japan"}],
        "subtitle": "More room for a familiar world",
        "summary": "A wider colour screen and shoulder buttons changed the shape of Game Boy, while older cartridges kept a route into its past.",
        "body": [
            "Game Boy Advance moved the screen between the player's hands. The original horizontal model launched in Japan on 21 March 2001. Its wider colour display and new shoulder buttons made the change immediately visible, before a game had even started. Nintendo was giving developers a different canvas while keeping the familiar idea of a small machine built around interchangeable cartridges.",
            "The transition also carried a player's collection forward. Alongside software made for its 32-bit hardware, the Advance could play earlier Game Boy and Game Boy Color cartridges, with compatibility qualifications noted in Nintendo's documentation. The machine connected two moments in portable play: a new display and controls, and games already kept in drawers or passed between friends.",
            "A link cable could connect up to four systems in supported games. Some titles even allowed several people to join using one cartridge. The result depended on a physical arrangement of handhelds, cables and players rather than an invisible network. This entry concerns the original 2001 body. The folding Advance SP was a later redesign, not an alternative shape sold at the first Japanese launch."
        ],
        "tags": ["Japan", "hardware", "handhelds", "backward compatibility", "local multiplayer"], "related_ids": ["game-boy", "nintendo-dsi"],
        "image_file": "Nintendo-Game-Boy-Advance-Purple-FL.png", "image_title": "Original horizontal Game Boy Advance in violet", "image_creator": "Evan-Amos",
        "sources": [source("Game Boy Advance - original hardware, Japanese release and link play", "https://www.nintendo.co.jp/n08/hardware/gba/index.html")],
        "factual_note": "The chronology uses the original Japanese release. The original horizontal GBA and the later folding GBA SP are different hardware revisions. Nintendo documents qualifications for some older cartridges. No view-only model is approved for integration.",
        "requested_model_uid": "ba9435d1e90b4eafbefee53ace5549d4", "requested_model_url": "https://sketchfab.com/3d-models/game-boy-advance-substance-painter-project-ba9435d1e90b4eafbefee53ace5549d4", "ready_for_assembly_when_model_attached": False,
    },
    {
        "id": "nintendo-3ds", "title": "Nintendo 3DS", "year": 2011, "era_id": "everywhere",
        "date": {"month": 2, "day": 26, "precision": "day", "region": "Japan: original 3DS launch"},
        "release_dates": [{"year": 2011, "month": 2, "day": 26, "region": "Japan"}],
        "subtitle": "Depth without a pair of glasses",
        "summary": "The familiar two-screen handheld gained a stereoscopic upper display, a Circle Pad and a new relationship with movement and space.",
        "body": [
            "Nintendo 3DS retained a recognisable arrangement: two screens, physical buttons and a touchscreen below. Its upper display changed what that familiar object could show. Stereoscopic depth was visible without wearing special glasses, and a slider let players adjust the effect. The first Japanese systems arrived on 26 February 2011.",
            "A Circle Pad added analogue movement beside the D-pad. Cameras, motion sensing and a gyroscope gave software further ways to respond to the world around the screen. Older DS and DSi game cards remained usable, so the new machine carried an existing library into a different set of possibilities. Not every game had to use every feature; choosing which inputs mattered remained a design decision.",
            "The hardware's identity also appeared through later colours and special editions. Nintendo's black-and-gold Zelda 25th Anniversary bundle reached Europe on 25 November 2011, with a Hyrule emblem and Ocarina of Time 3D. That edition belongs to the same first-year 3DS body, but its November release should not replace the February date of the original system. The larger XL and later New Nintendo 3DS designs are separate revisions."
        ],
        "tags": ["Japan", "hardware", "handhelds", "stereoscopic display", "controllers"], "related_ids": ["nintendo-dsi", "game-boy"],
        "image_file": "Nintendo-3DS-AquaOpen.png", "image_title": "Original 2011 Nintendo 3DS in Aqua Blue", "image_creator": "Evan-Amos",
        "sources": [
            source("Original Nintendo 3DS - Japanese release, inputs and specifications", "https://www.nintendo.co.jp/hardware/3dsseries/3ds/index.html"),
            source("Zelda 25th Anniversary 3DS - European edition announcement", "https://www.nintendo.com/en-gb/News/2011/Nintendo-announces-Limited-Edition-The-Legend-of-Zelda-25th-Anniversary-bundle-253367.html"),
        ],
        "factual_note": "The chronology is the original Japanese launch, not a worldwide date. A Zelda 25th Anniversary model represents a later 2011 special edition; XL and New Nintendo 3DS variants must not be silently presented as the original small 2011 body. Both user-selected sources so far are view-only; no replacement is silently approved.",
        "requested_model_uid": "69fb907885d44d3484521ab7e0fdd750", "requested_model_url": "https://sketchfab.com/3d-models/nintendo-3ds-69fb907885d44d3484521ab7e0fdd750", "ready_for_assembly_when_model_attached": False,
    },
]
