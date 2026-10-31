"""Reviewed original calendar writing; never alters release or scheduling fields."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
originals = {e['id']: e for e in json.loads((ROOT / 'calendar-template-review.json').read_text(encoding='utf-8'))['entries']}
rows = []

def add(identifier, summary, headings, body, sources, note='', evidence=None):
    original = originals[identifier]
    assert len(body) == len(headings) == 3
    assert all(25 <= len(p.split()) <= 90 for p in body)
    urls = [s[1] for s in sources]
    rows.append({
        'id': identifier, 'summary': summary, 'body': body, 'story_headings': headings,
        'sources': [dict(title=s[0], url=s[1], publisher=s[2], type='Primary developer or publisher source') for s in sources] + [{
            'title': 'Playhub: original calendar selection',
            'url': 'https://github.com/LoZazaMastro/Playhub/blob/main/catalog/on-this-day.json',
            'publisher': 'Playhub / LoZazaMastro',
            'attribution': 'Original subject selection, calendar slot and historical anchor. Previous template prose replaced with new Pixel Museum editorial text.'}],
        'editorial_credit': 'Pixel Museum editorial revision. Calendar selection and original collection: Playhub / LoZazaMastro. Research sources credited individually.',
        'editorial_mode': 'researched_calendar_revision',
        'revision_audit': {
            'checked_on': '2026-10-20',
            'original_body_sha256': hashlib.sha256(json.dumps(original['body'], ensure_ascii=False, separators=(',', ':')).encode()).hexdigest(),
            'historical_anchor': {'year': original['year'], 'source_event_kind': 'release'},
            'event_semantics': 'The scheduled calendar slot is not proof of an exact release day; regional and later-version differences are retained in the writing.',
            'note': note,
            'source_urls': urls,
            'paragraph_evidence': [{'paragraph': n, 'urls': evidence[n] if evidence else urls} for n in range(3)]
        }
    })

add('daily-03-11', 'A fairground accident sends Crono across centuries, while combined attacks make the travelling party matter in battle.',
    ['A demonstration goes wrong', 'Time changes the company', 'Wait for the right combination'], [
    "Crono meets Marle at Guardia's Millennial Fair. They visit Lucca's Telepod demonstration, and a malfunction sends Marle into the past. Crono follows with her pendant. A public celebration becomes the doorway to a journey through different periods of the same planet, released by Square in 1995.",
    "Prehistory, the medieval world and the distant future give the journey different surroundings and companions. The premise makes travelling through time a practical way of exploring a world. The collaboration brought together Dragon Quest creator Yuji Horii, Final Fantasy creators and Akira Toriyama's character designs.",
    "In battle, action gauges fill while enemies change position. Characters can combine their special Tech abilities into joint attacks. Waiting for another party member can therefore create a different opportunity from acting immediately. The people travelling together affect both the story's company and the choices available during a fight."
    ], [('Chrono Trigger: story and battle systems', 'https://gb.store.square-enix-games.com/chrono-trigger---digital', 'Square Enix'),
        ('Chrono Trigger: creator credits', 'https://www.jp.square-enix.com/chronotrigger/', 'Square Enix')],
    'The current publisher page describes the later PC version too. Extra dungeons, autosave and upgraded presentation are deliberately not attributed to the 1995 original.')

add('daily-03-12', 'Yakuza 0 places two young men inside the property deals, nightlife and criminal pressure of Japan in 1988.',
    ['A tiny plot of expensive land', 'Two cities, two young men', 'Money makes the pressure visible'], [
    "In December 1988, a small vacant plot interrupts a major redevelopment scheme in Kamurocho. Kazuma Kiryu, a twenty-year-old debt collector, becomes implicated in a killing. The supposedly empty land has owners, claimants and consequences. A property dispute gives the 2015 prequel a concrete reason for rival interests to collide.",
    "Across the country in Osaka's Sotenbori district, twenty-four-year-old Goro Majima manages the Grand cabaret. His successful public role sits beside punishment and exclusion from the organisation he wants to rejoin. Moving between the two protagonists lets the same period appear through very different kinds of obligation.",
    "SEGA's story places luxurious redevelopment beside people whose lives can be redirected by a single order. Kiryu's predicament begins with an ordinary collection job; Majima's apparent status does not give him freedom. That contrast makes the prequel more than a younger face for a familiar protagonist: each city gives ambition a price."
    ], [('Yakuza 0: original story and setting', 'https://ryu-ga-gotoku.com/zero/sp/story/story0.html', 'SEGA')],
    '1988 is the fictional setting, not the release year. Kiryu and Majima ages refer to that setting.')

add('daily-03-13', 'Code Name: S.T.E.A.M. turns a limited third-person view and a shared steam reserve into tactical decisions.',
    ['Lincoln recruits an unlikely squad', 'A battlefield seen from the ground', 'Keep something in reserve'], [
    "An alien invasion meets an alternative nineteenth century powered by steam. Abraham Lincoln directs an unusual defensive force in Intelligent Systems' 2015 Nintendo 3DS game. Its comic-book presentation gives a strange collection of agents a common setting, while missions place a squad of four under the player's control.",
    "There is no overhead battlefield map to reveal everything at once. The third-person viewpoint makes scouting part of the turn: an agent must reach a useful position before the player can see what lies beyond it. Moving a soldier also changes the information available for the rest of the squad.",
    "Both movement and weapon attacks consume steam. Spending the whole reserve can achieve more now, but holding some back permits an overwatch attack during the enemy's turn. Equipment and boilers alter those possibilities. A resource that sounds like period decoration becomes the link between positioning, attack and protection."
    ], [('Code Name: S.T.E.A.M.: original mechanics', 'https://www.nintendo.com/en-gb/Games/Nintendo-3DS-games/Code-Name-S-T-E-A-M-893949.html', 'Nintendo')],
    'The linked UK product page gives the later European release of 15 May 2015. The March calendar slot is not treated as the UK release date.')

add('daily-03-14', 'Dark Souls II makes survival a matter of resource management, observation and uneasy relationships with other players.',
    ['Arriving in Drangleic', 'The cost of another attempt', 'Help and danger from elsewhere'], [
    "Dark Souls II sends the player into Drangleic, a kingdom where unfamiliar enemies and dangerous terrain make progress uncertain. Released in 2014, FromSoftware's sequel expects attention before commitment. A doorway, a narrow ledge or a distant opponent can matter as much as the size of the weapon being carried.",
    "The publisher's original survival guide explains an especially severe rule: repeated deaths reduce maximum health. Human Effigies can reverse hollowing, but are resources to consider rather than spend without thought. Returning after defeat is therefore also a decision about what to risk and when to restore an advantage.",
    "Covenants give online encounters different purposes. Some players offer protection or assistance; others invade, set traps or defend particular places. A stranger entering the world is not merely another enemy type. The same connected system can interrupt a lonely journey with cooperation, rivalry or a threat whose intentions must be read."
    ], [('Dark Souls II: original survival guide', 'https://blog.playstation.com/2014/03/05/dark-souls-ii-survival-guide/', 'Bandai Namco / PlayStation'),
        ('Dark Souls II: launch and Covenants', 'https://blog.playstation.com/2014/03/11/dark-souls-ii-out-today-on-ps3/', 'Bandai Namco / PlayStation')],
    'Sources concern the original 2014 game, not the 2015 Scholar of the First Sin edition. The US launch post is dated March 11; the scheduled March 14 slot is not used as universal launch evidence.')

add('daily-03-15', 'Homefront and The Division 2 use different occupied American settings to organise two very different kinds of shooter.',
    ['Homefront: an occupied America', 'The Division 2: a city to rebuild', 'The same day, eight years apart'], [
    "Homefront reached North American stores on 15 March 2011. THQ and Kaos Studios placed its campaign in a fictional 2027 America occupied by a Greater Korean Republic. Writer John Milius helped shape the setting. Its premise turns recognisable domestic surroundings into the stage for an armed resistance story.",
    "On 15 March 2019, The Division 2 launched on PC, PlayStation 4 and Xbox One. Ubisoft's Washington, DC could be approached alone or with up to three teammates. Helping citizens, improving a base and gathering equipment connect individual firefights to the work of regaining ground across an open city.",
    "These releases share a calendar date, not a launch year or a single design. Homefront frames a fictional military occupation; The Division 2 builds repeated missions around equipment, skills and cooperative play. Placing them together makes the setting's job visible: a ruined familiar place can organise a campaign or sustain a much longer cycle of return visits."
    ], [('Homefront: THQ launch announcement', 'https://www.prnewswire.com/news-releases/homefront-invades-america-117993404.html', 'THQ / PR Newswire'),
        ('The Division 2: launch announcement', 'https://news.ubisoft.com/en-us/article/5gguy1pfxxM7mrCw1vjjQC/the-division-2-available-now-on-xbox-one-pc-and-ps4', 'Ubisoft')],
    'This remains a multi-work feature anchored to Homefront in 2011. The Division 2 is explicitly dated 2019; neither is described as the same release event.',
    [['https://www.prnewswire.com/news-releases/homefront-invades-america-117993404.html'], ['https://news.ubisoft.com/en-us/article/5gguy1pfxxM7mrCw1vjjQC/the-division-2-available-now-on-xbox-one-pc-and-ps4'], ['https://www.prnewswire.com/news-releases/homefront-invades-america-117993404.html', 'https://news.ubisoft.com/en-us/article/5gguy1pfxxM7mrCw1vjjQC/the-division-2-available-now-on-xbox-one-pc-and-ps4']])

add('daily-03-16', 'Kirby Star Allies turns enemies into companions and lets a group combine powers while travelling through its stages.',
    ['Make a friend out of an enemy', 'Abilities that work together', 'A group on one screen'], [
    "Kirby Star Allies arrived on Nintendo Switch in 2018 with a generous recruitment tool. Throwing a Friend Heart can turn an enemy into an ally. A creature that would otherwise interrupt the journey becomes a member of the party, bringing its own ability into the next stretch of the stage.",
    "Some powers interact. An ally can add an element to another character's weapon, creating a useful combination rather than simply another body in a fight. The familiar Kirby act of borrowing an enemy's ability expands into arranging a small group whose different powers can support each other.",
    "Up to three other people can join Kirby, with computer-controlled allies available when fewer players are present. The adventure therefore works with different groups around the same television. Its cooperative structure makes the Friend Heart more than a story symbol: recruiting, sharing powers and moving together are things players repeatedly do."
    ], [('Kirby Star Allies: friends and combined abilities', 'https://www.nintendo.com/en-gb/Games/Nintendo-Switch-games/Kirby-Star-Allies-1233956.html', 'Nintendo')])

add('daily-03-17', 'Chinatown Wars adapts Liberty City to Nintendo DS with an elevated view and small actions on the touch screen.',
    ['Liberty City in a handheld', 'A city touched as well as steered', 'A different shape for the same series'], [
    "Grand Theft Auto: Chinatown Wars first reached Nintendo DS in March 2009. Rockstar Leeds and Rockstar North returned to Liberty City in a form designed for a handheld. The elevated viewpoint makes streets and traffic readable on a small screen without simply reproducing the console games' camera.",
    "The touch screen makes parts of the criminal routine into direct tasks. Breaking into vehicles and handling objects use a different kind of input from steering through traffic. These short interactions give the second screen a job within the action, alongside information that supports movement around the city.",
    "The result is useful to compare with the larger-screen Grand Theft Auto games. Its identity comes from finding a workable arrangement for DS controls and two displays. The original handheld release preceded later PSP and mobile versions; those adaptations should not be mistaken for the hardware on which this version first appeared."
    ], [('Grand Theft Auto: Chinatown Wars: DS product record', 'https://www.nintendo.com/en-gb/Games/Nintendo-DS/Grand-Theft-Auto-Chinatown-Wars-270913.html', 'Nintendo / Rockstar Games'),
        ('Chinatown Wars: official release record', 'https://www.rockstargames.com/games/chinatownwars', 'Rockstar Games')],
    'Rockstar records March 17, 2009; Nintendo UK records the regional March 20 DS release. No claim that all territories launched on March 17.')

add('daily-03-18', 'Ground Zeroes turns one rescue operation into a testing ground for the routes and systems of Metal Gear Solid V.',
    ['One camp, several approaches', 'A prologue with room to experiment', 'Repeat the mission differently'], [
    "Metal Gear Solid V: Ground Zeroes puts Big Boss inside Camp Omega, a secret prison camp in Cuba, for a rescue operation set in 1975. Kojima Productions released the game in 2014 as a prologue to The Phantom Pain. The setting is contained, but the route through it is not prescribed.",
    "Players can attempt the infiltration quietly, use open force or change tactics when circumstances shift. The FOX Engine supports lighting and weather conditions that affect decisions. Rather than changing its geography for every challenge, the game invites a different reading of a space the player gradually learns.",
    "Side missions and mission rankings provide reasons to return after the main operation. Konami also described an iDROID companion app that could show maps or call support without covering the action. These systems make the small playable area a place for repeated trials, with knowledge of its layout becoming part of the player's equipment."
    ], [('Ground Zeroes: original launch announcement', 'https://www.konami.com/games/ca/en/topics/10/', 'Konami / Kojima Productions')],
    '1975 is the fictional setting. The source dates the American release March 18, 2014; it does not establish every regional launch.')

add('daily-03-19', 'Gears of War: Judgment revisits the war through Kilo Squad and asks players to change the terms of an encounter.',
    ['Before the familiar trilogy', 'An encounter with extra conditions', 'Attack and defence exchange sides'], [
    "Gears of War: Judgment follows Kilo Squad shortly after Emergence Day, before the events of the original trilogy. Damon Baird and Augustus Cole fight alongside Sofia Hendrick and Garron Paduk in Halvo Bay. Epic Games and People Can Fly released the Xbox 360 game in March 2013.",
    "Its Mission Declassification system introduces additional challenges during the campaign. The Smart Spawn System can vary enemy types, arrival times and positions. A familiar combat space can consequently ask a different question on a return visit, rather than relying entirely on remembering where every opponent appeared before.",
    "OverRun changes the shape of multiplayer through five-player teams with distinct classes. Teams alternate between the COG and Locust, so attacking and defending require different tools and responsibilities. It extends the series' cover-based firefights into a contest where understanding another role is part of understanding the battle."
    ], [('Gears of War: Judgment: launch and campaign systems', 'https://blogs.microsoft.com/blog/2013/03/19/gears-of-war-judgment-unleashed-on-xbox-360/', 'Microsoft'),
        ('Judgment: OverRun and development credits', 'https://news.xbox.com/en-us/2013/01/28/get-early-access-to-gears-of-war-judgment-overrun-mode-through-gamestop-pre-order/', 'Xbox / Epic Games')])

add('daily-03-20', 'Animal Crossing: New Horizons builds an island routine from gathering materials, making objects and choosing who to share it with.',
    ['Begin with an island', 'Make a place through small jobs', 'An invitation to return'], [
    "Animal Crossing: New Horizons arrived for Nintendo Switch on 20 March 2020. Tom Nook's island getaway begins with a modest camp rather than a finished town. The player gathers supplies, meets animal neighbours and gradually turns a shared patch of land into somewhere recognisably their own.",
    "Crafting gives branches, stones and other materials an immediate purpose. Furniture can be placed outdoors, so decorating extends beyond the walls of a house. Tasks such as fishing, collecting and making a tool sit beside decisions about where objects and buildings should stand. The island changes through repeated small contributions.",
    "Time and seasons give those contributions a rhythm. Returning on another day can bring something different to find, while visits let other players see the place being made. The game provides activities but leaves room to choose their order. A collection, a carefully arranged garden or a conversation can become the reason for that day's visit."
    ], [('Animal Crossing: New Horizons: original island and crafting systems', 'https://www.nintendo.com/en-gb/Games/Nintendo-Switch-games/Animal-Crossing-New-Horizons-1438623.html', 'Nintendo')],
    'Writing concerns the 2020 base game. Later paid expansions and later-platform features are not presented as launch features.')

add('daily-03-21', 'Game Boy Advance widens the handheld, adds shoulder buttons and carries an existing cartridge library into a new generation.',
    ['A wider way to hold a game', 'New hardware, existing cartridges', 'Four players and a cable'], [
    "The original Game Boy Advance launched in Japan on 21 March 2001. Its horizontal body places the screen between the controls, with L and R buttons on the shoulders. Nintendo paired a 32-bit processor with a reflective colour display. This AGB-001 hardware should not be confused with the later folding SP.",
    "The cartridge slot accepted Game Boy and Game Boy Color software as well as new Advance games, subject to compatibility exceptions. Continuing an existing library gave the new machine a connection to its predecessors. New Advance cartridges were also physically smaller, making the change visible in the objects players carried.",
    "A dedicated link cable could connect up to four systems for supported software. Some games allowed multiplayer from a single cartridge; others required one in every machine. That difference mattered when arranging a game with friends. The handheld's social possibilities depended on the particular software as well as the socket on its side."
    ], [('Game Boy Advance: original Japanese hardware specifications and launch', 'https://www.nintendo.co.jp/n08/hardware/gba/index.html', 'Nintendo')],
    'Original AGB-001 reflective display, not a claimed backlit screen. Cable, software and cartridge requirements vary by game; four players is not universal.')

add('daily-03-22', 'The original God of War builds Kratos around chained blades, mythological obstacles and a revenge story told in flashback.',
    ['A bargain with Ares', 'Weapons that shape movement', 'A journey through hostile architecture'], [
    "Sony released God of War in North America on 22 March 2005 for PlayStation 2. Santa Monica Studio cast Kratos as a former Spartan whose pact with Ares leads to a revenge quest. The original story draws on Greek mythology; it is a different period of the character's life from the later Norse games.",
    "The Blades of Chaos attach to Kratos through chains, giving combat a distinctive reach and silhouette. Battles share the journey with climbing, rope swings, swimming and traps. A weapon animation or movement across a gap can therefore carry the same exaggerated physical force as the creatures being fought.",
    "The campaign tells its backstory through flashbacks while driving Kratos towards Pandora's box and a confrontation with Ares. Mythological places become working obstacles: submerged ruins, sandstorms and a temple carried by a giant. Their scale is experienced through the actions needed to cross them, as well as through cinematic sequences."
    ], [('God of War: original North American launch and gameplay description', 'https://sony.mediaroom.com/2005-03-22-Rave-Reviews-Nationwide-Spark-High-Anticipation-for-God-of-War-as-the-2005-Must-Have-Game-on-PlayStation-2', 'Sony Computer Entertainment America')])

add('daily-03-23', 'Half-Life: Alyx makes searching, aiming and handling objects into physical actions inside a virtual-reality resistance story.',
    ['Alyx before Half-Life 2', 'Search with your hands', 'Make room for different bodies'], [
    "Valve released Half-Life: Alyx on 23 March 2020. Set between Half-Life and Half-Life 2, it follows Alyx Vance and her father Eli as resistance forms under the Combine's occupation. Putting Alyx in the player's role changes the viewpoint without needing to continue directly from the series' last episode.",
    "The virtual-reality design gives small objects and nearby surfaces more work to do. Shelves must be searched for supplies; tools operate alien interfaces; aiming can involve leaning around a wall. These actions place some of the tension in handling the environment, before an enemy has even reached the player.",
    "Valve provided seated, standing and room-scale options, alongside teleport, shift and continuous movement. Those alternatives recognise that a virtual world is entered through a real room and a real body. Its included Source 2 tools also allowed community authors to construct further environments using the game's VR components."
    ], [('Half-Life: Alyx: setting, original release and VR interaction', 'https://www.half-life.com/en/alyx', 'Valve')],
    'Current official page also advertises newer Steam Frame support. That later hardware is deliberately excluded from this account of the 2020 release.')

add('daily-03-24', 'Bloodborne encourages the wounded hunter to make a difficult choice: withdraw, or strike quickly enough to recover.',
    ['Enter Yharnam as a hunter', 'An injury opens a short opportunity', 'Learn what the weapon can become'], [
    "Bloodborne arrived on PlayStation 4 in 2015 with Yharnam's streets and inhabitants as its threatening introduction. FromSoftware's hunter must study opponents while exploring the city. The original launch guidance treats caution as useful preparation, but it also gives players a strong reason to move towards danger after being hit.",
    "Lost health briefly remains recoverable through successful attacks. That window makes an injury into a decision: try to win the health back now, or retreat and spend a healing item. An aggressive response can help, but repeating it without reading the enemy can turn one mistake into another.",
    "Trick weapons change form, altering their attacks and reach. Firearms and carefully timed responses add further possibilities, while Blood Vials supply healing. Learning a fight consequently involves more than memorising a safe distance. The hunter's available tools can change that distance and the opportunities worth pursuing."
    ], [('Bloodborne: original launch', 'https://blog.playstation.com/2015/03/24/bloodborne-out-now-only-on-ps4-let-the-hunt-begin/', 'PlayStation / FromSoftware'),
        ('Bloodborne: original survival guidance', 'https://blog.playstation.com/2015/03/23/bloodborne-24-tips-for-survival/', 'PlayStation / FromSoftware')],
    'The March 24 launch source is North American. The account describes the original game rather than later Old Hunters additions.')

add('daily-03-25', 'Reaper of Souls adds a new act and Crusader, then offers a different reason to revisit Diablo III beyond its story.',
    ['Death comes to Westmarch', 'Separate the expansion from the update', 'A different route through familiar places'], [
    "Diablo III: Reaper of Souls launched for Windows and Mac on 25 March 2014. Its fifth act takes the fight to Westmarch and Malthael, while the Crusader joins the playable classes. The increased level cap of seventy extends character development alongside the new section of the campaign.",
    "Not every improvement associated with this period required buying the expansion. Blizzard's launch announcement distinguishes its new content from the preceding free update, which revised loot and Paragon progression and added social features. That distinction matters when tracing how an existing online game changed for different groups of players.",
    "Adventure Mode reorganises the world around Bounties and randomised Nephalem Rifts rather than following the campaign in order. The Mystic also provides ways to adjust equipment. Completing the story is no longer the only structure available for another session: choosing tasks and refining a character become an alternative reason to return."
    ], [('Reaper of Souls: original release and feature distinctions', 'https://investor.activision.com/node/20936', 'Blizzard Entertainment')],
    'The source records later retail dates in some territories. March 25 is not claimed as the date of every physical regional edition.')

add('daily-03-26', 'Pillars of Eternity used crowdfunding to support a new role-playing world built around the strengths of older computer RPGs.',
    ['Ask the audience to back a new world', 'Recognisable influences, original rules', 'From a campaign to a finished game'], [
    "Obsidian announced in March 2015 that Pillars of Eternity had gone gold, with release set for 26 March on Windows, Mac and Linux. The project began its crowdfunding campaign in September 2012 as Project Eternity. Kickstarter and PayPal contributions together brought in more than four million dollars.",
    "The studio named Baldur's Gate, Icewind Dale and Planescape: Torment among its influences. It was making a new setting and rules rather than another licensed entry in those series. That combination offered backers something recognisable while giving the team room to build a world whose details it controlled.",
    "The finished release followed roughly two and a half years of development. The funding story makes the relationship between audience and production unusually visible: players committed support before there was a completed game to buy. Obsidian's gold announcement marks the point where that proposal became software ready for release."
    ], [('Pillars of Eternity has gone gold', 'https://eternity.obsidian.net/eternity/news/pillars-of-eternity-has-gone-gold', 'Obsidian Entertainment')],
    'Contemporary original announcement checked earlier in this research pass; a subsequent web-tool re-open returned an internal error. Do not attribute current-site later turn-based updates to the original 2015 game.')

add('daily-03-27', 'Monster Hunter Portable 2nd G makes a portable hunting party and continuity with an existing save part of its appeal.',
    ['A Japanese release with several names', 'Bring the hunting party together', 'Keep the progress already made'], [
    "Monster Hunter Portable 2nd G launched for PSP in Japan on 27 March 2008. Capcom's English investor announcement called it Monster Hunter Freedom 2G. The later western release is known as Freedom Unite. Keeping those names and dates separate prevents a Japanese launch from being silently relabelled as the western one.",
    "Ad-hoc wireless play allowed nearby players to hunt together. Capcom emphasised this cooperative portable experience in its contemporary announcement. A difficult quarry gave the group a shared task, while the handheld hardware made meeting up with the other hunters part of arranging the session.",
    "Save transfer from the preceding game let returning players carry progress forward rather than begin the expanded release empty-handed. Capcom reported two million units shipped in Japan by 24 April, twenty-nine days after launch. That is a dated shipment measure, not a claim about sales to players or the later worldwide total."
    ], [('Monster Hunter Freedom 2G: Japanese release, multiplayer, save transfer and shipments', 'https://www.capcom.co.jp/ir/english/news/pdf/e080424.pdf', 'Capcom')],
    'Uses the original Japanese Portable 2nd G identity and explicitly distinguishes later western Freedom Unite. Two million means Japanese shipments reported April 24, 2008, not sell-through.')

add('daily-03-28', 'Kingdom Hearts brought an original travelling party into Disney worlds and made that unlikely meeting the basis of a new series.',
    ['An unusual partnership', 'A travelling party crosses familiar worlds', 'The beginning, before the collections'], [
    "Kingdom Hearts first released in Japan for PlayStation 2 on 28 March 2002. The collaboration between Square and Disney brought Sora, an original young protagonist, together with Donald Duck and Goofy. The familiar characters were companions in a continuing adventure rather than a collection of unrelated guest appearances.",
    "Their journey moves through Disney worlds threatened by the Heartless. Sora's Keyblade connects that travelling party to the larger conflict. Recognisable characters and places provide an entry into a story that also asks the player to follow new relationships, so prior familiarity with Disney is useful without explaining everything in advance.",
    "The first game later appeared within collections and on other platforms. Those packages bring different points in the series together, but the original 2002 release was its starting point. Looking back from the many sequels makes the initial proposition strikingly simple: three unlikely companions have to travel together."
    ], [('Kingdom Hearts: original Japanese release archive', 'https://www.jp.square-enix.com/kingdom/archives/index.html', 'Square Enix'),
        ('Kingdom Hearts: companions and Heartless', 'https://na.store.square-enix-games.com/kingdom-hearts---the-story-so-far', 'Square Enix'),
        ('Kingdom Hearts: series collaboration and original platform', 'https://www.hd.square-enix.com/eng/ir/library/pdf/ar_2025en_06feature.pdf', 'Square Enix')],
    'Later collection sources are used only for shared characters/premise. Later combat systems, Pixar worlds and collection release dates are not assigned to the original.')

add('daily-03-29', 'Yoshi’s Crafted World uses the backs of its handmade stages to turn familiar places into a different search.',
    ['A world made from ordinary materials', 'Walk around to the other side', 'Bring another Yoshi'], [
    "Yoshi's Crafted World launched on Nintendo Switch on 29 March 2019. Good-Feel built its stages from the appearance of paper, cartons, cups and other household materials. The Yoshis pursue the scattered gems of the Sundream Stone, with a landscape that openly shows how its scenery has been assembled.",
    "The Flip Side turns most stages around, exposing the backs of their props. The new objective is to locate three hidden Poochy Pups and reach the end quickly. A route already crossed becomes another search because changing the view reveals objects that the front-facing composition concealed.",
    "Two players can share the adventure, with one Yoshi carrying another on its back. Mellow Mode adds wings to help clear obstacles. These options allow different approaches to the same spaces. The handmade style supports both: a stage can be an obstacle course, a small scavenger hunt or something to explore together."
    ], [('Yoshi’s Crafted World: original stages, Flip Side and cooperative play', 'https://www.nintendo.com/en-gb/Games/Nintendo-Switch-games/Yoshi-s-Crafted-World-1233953.html', 'Nintendo / Good-Feel')])

add('daily-03-30', 'Thimbleweed Park turns a small-town mystery into a shared investigation across five playable characters.',
    ['A body is only the beginning', 'Five people, overlapping problems', 'A new game in an older form'], [
    "Ron Gilbert announced Thimbleweed Park's release on 30 March 2017. The mystery is set in 1987, in a town with an abandoned circus, a strange hotel and a burnt-out pillow factory. A body under a bridge brings investigators into a place whose other problems quickly demand attention.",
    "Five playable characters bring different concerns into the same story. Agents Ray and Reyes investigate, while aspiring developer Delores, the clown Ransome and the ghost Franklin have their own situations to resolve. Switching between them lets the player see connections that no single character initially understands.",
    "Gilbert and Gary Winnick returned to a point-and-click adventure form associated with their earlier work. The publisher offered Casual and Hard modes, varying the puzzle challenge within the same mystery. The 2017 release and its fictional 1987 setting therefore do different jobs: one dates the production, the other supplies the world being investigated."
    ], [('Thimbleweed Park: developer launch post', 'https://blog.thimbleweedpark.com/released.html', 'Ron Gilbert / Terrible Toybox'),
        ('Thimbleweed Park: original characters and modes', 'https://store.steampowered.com/app/569860/Thimbleweed_Park/', 'Terrible Toybox')],
    'Developer launch post read before user comments; audience comments are not used as developer evidence. 1987 is explicitly the setting, not release.')

expected = set(json.loads((ROOT/'calendar-template-review.json').read_text(encoding='utf-8'))['assignment']['curation'][:20])
assert {r['id'] for r in rows} == expected
out = {'schema_version': 1, 'checked_on': '2026-10-20',
       'editorial_scope': '20 researched replacements of inherited generic calendar templates; historical and scheduling metadata untouched.',
       'entries': rows}
(ROOT/'calendar-template-revisions-curation.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'entries': len(rows), 'paragraphs': sum(len(e['body']) for e in rows), 'words': sum(len(p.split()) for e in rows for p in e['body'])}))
