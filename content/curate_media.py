"""Assemble selected remotely hosted media and their attribution records."""
import concurrent.futures,html,json,re,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def clean(s):return html.unescape(re.sub("<[^>]+>","",s)).strip()
def getjson(url):return json.load(urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"PixelMuseumCatalogue/1.0"}),timeout=25))

media={}
candidates=json.loads((ROOT/"media-candidates.json").read_text(encoding="utf-8"))
# Deliberate selections: search results are not assumed to identify the exhibit.
select={"nimrod":[0,2],"tennis-for-two":[0,1],"spacewar":[0,1],"brown-box":[0,2],"odyssey":[0,2],"pong":[0,1],"channel-f":[1],"atari-vcs":[0,1],"space-invaders":[2],"adventure":[0,1],"pac-man":[1],"dona-bailey":[0],"carol-shaw":[0,1],"commodore-64":[0,1],"famicom":[1,0],"mule":[0],"tetris":[0,2],"starcraft":[0,1],"dance-dance-revolution":[2],"dreamcast":[0,1],"playstation-2":[2],"the-sims":[0,1],"xbox-halo":[1],"steam":[0],"wii":[1],"braid":[0,2]}
captions={"nimrod":"Modern museum reconstruction of Nimrod; not the surviving 1951 original.","spacewar":"Spacewar! running on a restored PDP-1 at the Computer History Museum.","brown-box":"Ralph Baer's Brown Box hardware and its historical documentation.","channel-f":"Fairchild Channel F hardware. The interchangeable cartridge is central to the platform's design.","atari-vcs":"Atari 2600 four-switch hardware variant; the platform began as the VCS in 1977.","dance-dance-revolution":"A Dance Dance Revolution arcade cabinet.","famicom":"Nintendo Famicom; second image shows the later Disk System accessory.","starcraft":"Lim Yo-hwan, known as BoxeR, one of South Korea's influential professional StarCraft players.","playstation-2":"PlayStation 2 hardware variants, photographed together."}
for id,indexes in select.items():
    chosen=[]
    for i in indexes:
        if i>=len(candidates.get(id,[])):continue
        item=candidates[id][i]
        if not item.get("url") or not item.get("license") or not item.get("creator"):continue
        if item["source_page"].lower().endswith((".pdf",".webm",".svg")):continue
        x=dict(item);x["title"]=captions.get(id,x["title"]);chosen.append(x)
    if chosen:media[id]={"images":chosen}

# Additional known photographs, resolved as a single Commons metadata request.
titles={
"game-boy":["Game-Boy-Original.jpg","Game-Boy-FL.jpg"],
"playstation":["PSX-Console-wController.jpg","PSX-DualShock-Controller.jpg"],
"super-mario-64":["N64-Console-Set.jpg"],
"switch":["Nintendo-Switch-Console-Docked-wJoyConRB.jpg"],
"sonic":["Sega-Mega-Drive-JP-Mk1-Console-Set.jpg"],
"zx-spectrum":["Sinclair ZX Spectrum 48k.jpg"],
"channel-f":["Jerry Lawson at KJZZ (cropped).png","Cartridge Fairchild Channel F.jpg"],
"wii":["Satoru Iwata - Game Developers Conference 2011 - Day 2 (1).jpg"],
"steam-deck":["Steam Deck (front).png"],
"preserving-play":["Spacewar!-PDP-1-20070512.jpg"],
}
all_titles=["File:"+t for v in titles.values() for t in v]
params=dict(action="query",format="json",titles="|".join(all_titles),prop="imageinfo",iiprop="url|extmetadata|size",iiurlwidth=1280)
try:
    result=getjson("https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(params))
    pages={p["title"]:p for p in result.get("query",{}).get("pages",{}).values()}
    for id,files in titles.items():
        for file in files:
            page=pages.get("File:"+file,{})
            if not page.get("imageinfo"):continue
            ii=page["imageinfo"][0]; m=ii.get("extmetadata",{}); creator=clean(m.get("Artist",{}).get("value",""));license=clean(m.get("LicenseShortName",{}).get("value",""))
            if not creator or not license:continue
            image=dict(url=(ii.get("thumburl") or ii["url"]).split("?",1)[0],original_url=ii["url"].split("?",1)[0],source_page=ii["descriptionurl"],title=clean(m.get("ImageDescription",{}).get("value",file)),creator=creator,license=license,license_url=m.get("LicenseUrl",{}).get("value",""),credit=f"{creator} / Wikimedia Commons / {license}",width=ii["width"],height=ii["height"])
            media.setdefault(id,{}).setdefault("images",[]).append(image)
except Exception as e:print("Exact Commons batch unavailable:",e)

# Reuse the user's already curated external Playhub screenshot references.
# Game artwork remains copyrighted; no free licence is claimed for it.
playhub=Path(r"F:\Playhub\Plugin\Playhub\Source\Playhub\Assets\GamingModeDeckyPlugin\gaming-mode\quick_settings\history_images.json")
old=json.loads(playhub.read_text(encoding="utf-8"))
reuse={"roberta-williams":("women-science","Sierra / Roberta and Ken Williams"),"simcity":("cities","Maxis / Electronic Arts"),"super-mario-bros":("mario","Nintendo"),"zelda":("zelda","Nintendo"),"sonic":("sonic","Sega"),"doom":("doom","id Software"),"myst":("books","Cyan"),"pokemon":("pokemon","Nintendo / Creatures / Game Freak"),"super-mario-64":("mario64","Nintendo"),"street-fighter-ii":("streetfighter","Capcom"),"final-fantasy-vii":("earth","Square Enix"),"minecraft":("education","Mojang Studios / Microsoft"),"journey":("friendship","thatgamecompany / Sony Interactive Entertainment"),"papers-please":("papers","3909 / Lucas Pope"),"celeste":("mountains","Celeste development team"),"animal-crossing":("christmas","Nintendo")}
for id,(key,owner) in reuse.items():
    shots=[m for m in old.get(key,[]) if m.get("url","").startswith("https://images.igdb.com/") and m.get("kind")=="screenshot"][:2]
    for m in shots:
        media.setdefault(id,{}).setdefault("images",[]).append(dict(url=m["url"],source_page=m.get("sourceUrl",""),title=m.get("subject",id)+" — game screenshot",creator=owner,license="Copyright retained by the respective game rights holders; remote editorial reference",credit=f"Game imagery: {owner}. External image reference: IGDB.",provenance="External reference selected in the user's Playhub history collection; URL rechecked for this catalog."))

media.setdefault("game-boy",{})["models"]=[dict(url="https://sceneview.github.io/models/platforms/GameBoyClassic.glb",source_page="https://sketchfab.com/3d-models/game-boy-classic-0ae80019e6f046168923286d7e628f6f",title="Game Boy Classic",creator="Georg Klein (kleingeo)",license="CC BY 4.0",license_url="https://creativecommons.org/licenses/by/4.0/",credit="Game Boy Classic by Georg Klein (embedded asset attribution), CC BY 4.0; hosted by SceneView. SceneView's catalog additionally lists JonhyOliver.",provenance="GLB embedded metadata identifies Georg Klein and CC-BY-4.0; SceneView credits page differs on author. Original model page currently unavailable. Geometry is a third-party representation, not manufacturer CAD.")]
media.setdefault("switch",{})["models"]=[dict(url="https://sceneview.github.io/models/platforms/nintendo_switch_oled.glb",source_page="https://sketchfab.com/3d-models/nintendo-switch-oled-model-9b8721e10a4f4a689fc4f72cdcee4b01",title="Nintendo Switch OLED — 2021 hardware variant",creator="rtql8d",license="CC BY 4.0",license_url="https://creativecommons.org/licenses/by/4.0/",credit="Nintendo Switch OLED model by rtql8d, CC BY 4.0; hosted by SceneView.",provenance="Artist and license agree between embedded GLB metadata and SceneView's credits. OLED is the later 2021 variant, not the original 2017 model.")]

# YouTube IDs below come from iframes on the cited primary/curatorial pages.
videos={
"tennis-for-two":("u6mu5B-YZU8","https://www.bnl.gov/about/history/firstvideo.php","Watch the laboratory's reconstruction to see how the screen and two controllers work together."),
"karateka":("IrS2pipZaH0","https://www.digitaleclipse.com/games/karateka","Digital Eclipse introduces its documentary approach through prototypes, animation reference and playable history."),
"preserving-play":("IrS2pipZaH0","https://www.digitaleclipse.com/media/goldmasterseries","A game can be exhibited alongside the evidence of how it was made."),
"papers-please":("_QP5X6fcukM","https://papersplea.se/presskit/","The original desktop trailer demonstrates how an inspection desk becomes a dramatic interface."),
"celeste":("FqBj2IGg6Uw","https://www.celestegame.com/?lang=en","Notice the relationship between quick retries, animation and the mountain's changing spaces."),
"doom":("6y3sK4xKcVs","https://www.museumofplay.org/games/doom/","The Strong's selected video places the game in its historical collection context."),
"simcity":("MDeM2dMi7DY","https://www.museumofplay.org/games/simcity/","Watch the city as a system: roads and zones set consequences in motion."),
"starcraft":("UW3gZ7VC0_c","https://www.museumofplay.org/games/starcraft/","A curatorial video selected by The Strong introduces the game and its impact."),
"street-fighter-ii":("hyO4qHy0ij0","https://www.museumofplay.org/games/street-fighter-ii/","Look for how characters and repeated encounters make competition readable."),
"dance-dance-revolution":("93D2mk2_iRY","https://www.museumofplay.org/games/dance-dance-revolution/","Movement in front of the cabinet is as important as the arrows on its screen."),
"dragon-quest":("yR7uCS3cx30","https://www.museumofplay.org/games/dragon-quest/","A museum introduction to the collaboration behind Dragon Quest."),
"final-fantasy-vii":("9pWMDwojTq8","https://www.museumofplay.org/games/final-fantasy-vii/","A curatorial introduction selected by The Strong; watch how different visual modes carry a single world."),
"the-sims":("WDh0IhawXK8","https://www.museumofplay.org/games/the-sims/","Small household decisions become a source of open-ended stories."),
"oregon-trail":("nqW4mSS3DVE","https://www.museumofplay.org/games/the-oregon-trail/","A museum-selected introduction to the classroom game's continuing cultural memory."),
"tomb-raider":("ORfQSZM9ex4","https://www.museumofplay.org/games/tomb-raider/","Observe how architecture suggests a route before Lara moves."),
"pac-man":("7VpMje0loxQ","https://www.worldvideogamehalloffame.org/games/pac-man/","A museum introduction to a character whose cultural life extended beyond the arcade."),
}
def describe(pair):
    id,(yt,source,caption)=pair
    try:
        data=getjson("https://www.youtube.com/oembed?format=json&url="+urllib.parse.quote("https://www.youtube.com/watch?v="+yt,safe=""))
        return id,dict(youtube_id=yt,url="https://www.youtube.com/watch?v="+yt,title=data["title"],caption=caption,creator=data["author_name"],source_page=source,credit="Video by "+data["author_name"]+" on YouTube; shown via the original online source.",thumbnail_url=data.get("thumbnail_url",""),verified="2026-10-20")
    except Exception as e:print("Video unavailable:",yt,e);return id,None
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    for id,video in pool.map(describe,videos.items()):
        if video:media.setdefault(id,{})["videos"]=[video]

supplement=ROOT/"media-supplemental.json"
if supplement.exists():
    for id,parts in json.loads(supplement.read_text(encoding="utf-8")).items():
        for key,items in parts.items():media.setdefault(id,{}).setdefault(key,[]).extend(items)
overrides=ROOT/"thumbnail-overrides.json"
if overrides.exists():
    lookup=json.loads(overrides.read_text(encoding="utf-8"))
    for parts in media.values():
        for item in parts.get("images",[]):
            key=urllib.parse.unquote(item["url"])
            if key in lookup:
                item["original_url"]=item.get("original_url",item["url"])
                item["url"]=lookup[key]
labels={
"nimrod":["Nimrod — modern museum reconstruction","Nimrod — display diagram"],
"tennis-for-two":["Tennis for Two — oscilloscope display","Tennis for Two — later recreation"],
"spacewar":["Spacewar! on the Computer History Museum's restored PDP-1","Spacewar! — the display in play"],
"brown-box":["The Brown Box hardware","The Brown Box prototype — archival image"],
"odyssey":["Magnavox Odyssey and its controllers"],
"pong":["Pong — Atari arcade cabinet","Pong — arcade cabinet photograph"],
"channel-f":["Fairchild Channel F console","Jerry Lawson","A Fairchild Channel F cartridge"],
"atari-vcs":["Atari 2600 — later four-switch hardware variant"],
"space-invaders":["Space Invaders — arcade cabinet"],
"adventure":["Warren Robinett","Warren Robinett discussing Adventure"],
"pac-man":["Pac-Man — arcade cabinet","Pac-Man — gameplay","Pac-Man — gameplay detail"],
"dona-bailey":["Dona Bailey"],"carol-shaw":["Carol Shaw with her River Raid award","Carol Shaw"],
"commodore-64":["Commodore 64 — front view","Commodore 64 — rear view"],
"famicom":["Nintendo Famicom console","Famicom with the later Disk System"],
"mule":["Dani Bunten Berry"],"tetris":["Alexey Pajitnov","Tetris — gameplay","Tetris — gameplay detail"],
"starcraft":["Lim Yo-hwan, known as BoxeR","BoxeR in 2021"],
"dance-dance-revolution":["Dance Dance Revolution — early arcade cabinet"],
"dreamcast":["Sega Dreamcast — front-left view","Sega Dreamcast — front-right view"],
"playstation-2":["PlayStation 2 — hardware variants"],"the-sims":["Will Wright at the Game Developers Conference","Will Wright"],
"xbox-halo":["The original Xbox console"],"steam":["Valve's office lobby in 2016"],
"wii":["Nintendo Wii console","Satoru Iwata at the Game Developers Conference"],
"braid":["Jonathan Blow at the Game Developers Conference","Jonathan Blow"],
"playstation":["The original PlayStation console and controller","PlayStation DualShock controller"],
"game-boy":["Original Nintendo Game Boy","Game Boy — front-left view"],
"super-mario-64":["Nintendo 64 console and controller","Super Mario 64 — gameplay","Super Mario 64 — gameplay detail"],
"switch":["Original Nintendo Switch docked with Joy-Con"],"steam-deck":["Valve Steam Deck — front view"],
"preserving-play":["The restored PDP-1 at the Computer History Museum"],
}
# These alternative file formats/crops repeat the same photograph; keep one.
for id in ("odyssey","atari-vcs"):
    if id in media:media[id]["images"]=media[id].get("images",[])[:1]
if "tetris" in media and len(media["tetris"].get("images",[]))>1:
    del media["tetris"]["images"][1]
for id,parts in media.items():
    for index,item in enumerate(parts.get("images",[])):
        if id in labels and index<len(labels[id]):item["title"]=labels[id][index]
        elif len(item.get("title",""))>140:item["title"]=id.replace("-"," ").title()+" — collection image"
(ROOT/"media.json").write_text(json.dumps(media,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Media records:",len(media),"images:",sum(len(x.get("images",[])) for x in media.values()),"videos:",sum(len(x.get("videos",[])) for x in media.values()))
