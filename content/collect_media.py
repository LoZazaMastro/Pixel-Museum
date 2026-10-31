"""Refresh candidate open-license collection photography from Wikimedia Commons."""
import html,json,re,time,urllib.parse,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parent
QUERIES={
"nimrod":"File:Nimrod computer 1951",
"tennis-for-two":"File:Tennis for Two oscilloscope",
"spacewar":"File:Spacewar PDP-1 Computer History Museum",
"brown-box":"File:Ralph Baer Brown Box",
"odyssey":"File:Magnavox Odyssey Evan Amos",
"pong":"File:Pong arcade cabinet Atari",
"channel-f":"File:Fairchild Channel F Evan Amos",
"atari-vcs":"File:Atari 2600 wood Evan Amos",
"space-invaders":"File:Space Invaders cabinet",
"mud":"File:Richard Bartle portrait",
"adventure":"File:Warren Robinett",
"pac-man":"File:Pac-Man arcade cabinet",
"roberta-williams":"File:Roberta Williams portrait",
"dona-bailey":"File:Dona Bailey",
"carol-shaw":"File:Carol Shaw",
"zx-spectrum":"File:ZX Spectrum 48K Evan Amos",
"commodore-64":"File:Commodore 64 Evan Amos",
"famicom":"File:Nintendo Famicom Evan Amos",
"mule":"File:Danielle Bunten Berry",
"tetris":"File:Alexey Pajitnov 2008",
"karateka":"File:Jordan Mechner portrait",
"super-mario-bros":"File:Shigeru Miyamoto portrait",
"zelda":"File:Koji Kondo portrait",
"game-boy":"File:Game Boy Original Evan Amos",
"sonic":"File:Sega Mega Drive Evan Amos",
"street-fighter-ii":"File:Yoko Shimomura",
"doom":"File:John Carmack GDC",
"myst":"File:Robyn Rand Miller Myst",
"playstation":"File:PlayStation Console Set Evan Amos",
"pokemon":"File:Game Boy link cable Evan Amos",
"super-mario-64":"File:Nintendo 64 console Evan Amos",
"starcraft":"File:StarCraft esports Korea",
"dance-dance-revolution":"File:Dance Dance Revolution arcade cabinet",
"dreamcast":"File:Sega Dreamcast console Evan Amos",
"playstation-2":"File:PlayStation 2 console Evan Amos",
"the-sims":"File:Will Wright GDC",
"xbox-halo":"File:Microsoft Xbox console Evan Amos",
"steam":"File:Valve headquarters lobby",
"wii":"File:Wii console Evan Amos",
"braid":"File:Jonathan Blow GDC",
"minecraft":"File:Minecraft Gamescom Mojang",
"journey":"File:Jenova Chen",
"papers-please":"File:Lucas Pope GDC",
"pokemon-go":"File:Pokemon Go players park",
"switch":"File:Nintendo Switch console Evan Amos",
"celeste":"File:Lena Raine",
"steam-deck":"File:Steam Deck console",
"preserving-play":"File:Computer History Museum PDP-1 restoration",
}

def clean(s): return html.unescape(re.sub("<[^>]+>","",s)).strip()
def search(pair):
    id,query=pair
    params=dict(action="query",format="json",generator="search",gsrsearch=query,gsrnamespace=6,gsrlimit=3,prop="imageinfo",iiprop="url|extmetadata|size",iiurlwidth=1280)
    try:
        url="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(params)
        req=urllib.request.Request(url,headers={"User-Agent":"PixelMuseum/0.1 educational catalogue research"})
        data=json.load(urllib.request.urlopen(req,timeout=30))
        out=[]
        for page in sorted(data.get("query",{}).get("pages",{}).values(),key=lambda p:p.get("index",999)):
            ii=page["imageinfo"][0];m=ii.get("extmetadata",{})
            creator=clean(m.get("Artist",{}).get("value",""))
            license=clean(m.get("LicenseShortName",{}).get("value",""))
            out.append(dict(url=(ii.get("thumburl") or ii["url"]).split("?",1)[0],original_url=ii["url"].split("?",1)[0],source_page=ii["descriptionurl"],title=clean(m.get("ImageDescription",{}).get("value",page["title"])),creator=creator,license=license,license_url=m.get("LicenseUrl",{}).get("value",""),credit=f"{creator} / Wikimedia Commons / {license}",width=ii["width"],height=ii["height"]))
        return id,out
    except Exception as e: return id,[{"error":str(e)}]

if __name__=="__main__":
    path=ROOT/"media-candidates.json"
    data=json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for key,query in QUERIES.items():
        if key in data and data[key] and "error" not in data[key][0]: continue
        time.sleep(2)
        key,result=search((key,query));data[key]=result
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for k,v in data.items(): print(k,[(x.get("source_page",x.get("error")),x.get("license")) for x in v])
