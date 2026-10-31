"""Add only release days explicitly visible in the primary-source review."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
file = ROOT / 'date-corrections.json'
data = json.loads(file.read_text(encoding='utf-8'))
review = json.loads((ROOT/'calendar-template-review.json').read_text(encoding='utf-8'))
by_id = {e['id']: e for e in review['entries']}
rows = [
 ('03-14',3,11,'North America','Dark Souls II: original PS3 North American release','https://blog.playstation.com/2014/03/11/dark-souls-ii-out-today-on-ps3/','Bandai Namco / PlayStation'),
 ('03-16',3,16,'Europe','Kirby Star Allies: Nintendo Switch release','https://www.nintendo.com/en-gb/Games/Nintendo-Switch-games/Kirby-Star-Allies-1233956.html','Nintendo'),
 ('03-17',3,20,'United Kingdom','Chinatown Wars: regional Nintendo DS release','https://www.nintendo.com/en-gb/Games/Nintendo-DS/Grand-Theft-Auto-Chinatown-Wars-270913.html','Nintendo / Rockstar Games'),
 ('03-18',3,18,'North, Central and South America','Ground Zeroes: original console release in the Americas','https://www.konami.com/games/ca/en/topics/10/','Konami'),
 ('03-19',3,19,'North America','Gears of War: Judgment: original Xbox 360 launch','https://blogs.microsoft.com/blog/2013/03/19/gears-of-war-judgment-unleashed-on-xbox-360/','Microsoft'),
 ('03-20',3,20,'Europe','Animal Crossing: New Horizons: original Nintendo Switch release','https://www.nintendo.com/en-gb/Games/Nintendo-Switch-games/Animal-Crossing-New-Horizons-1438623.html','Nintendo'),
 ('03-21',3,21,'Japan','Game Boy Advance: original AGB-001 Japanese hardware launch','https://www.nintendo.co.jp/n08/hardware/gba/index.html','Nintendo'),
 ('03-22',3,22,'North America','God of War: original PlayStation 2 release','https://sony.mediaroom.com/2005-03-22-Rave-Reviews-Nationwide-Spark-High-Anticipation-for-God-of-War-as-the-2005-Must-Have-Game-on-PlayStation-2','Sony Computer Entertainment America'),
 ('03-23',3,23,'Original Windows / SteamVR release','Half-Life: Alyx: original release','https://www.half-life.com/en/alyx','Valve'),
 ('03-24',3,24,'North America','Bloodborne: original PlayStation 4 release','https://blog.playstation.com/2015/03/24/bloodborne-out-now-only-on-ps4-let-the-hunt-begin/','PlayStation / FromSoftware'),
 ('03-25',3,25,'Initial Windows and Mac availability','Reaper of Souls: original desktop expansion release','https://investor.activision.com/node/20936','Blizzard Entertainment'),
 ('03-26',3,26,'Original Windows, Mac and Linux release','Pillars of Eternity: original desktop release','https://eternity.obsidian.net/eternity/news/pillars-of-eternity-has-gone-gold','Obsidian Entertainment'),
 ('03-27',3,27,'Japan','Monster Hunter Portable 2nd G: Japanese PSP release','https://www.capcom.co.jp/ir/english/news/pdf/e080424.pdf','Capcom'),
 ('03-28',3,28,'Japan','Kingdom Hearts: original Japanese PlayStation 2 release','https://www.jp.square-enix.com/kingdom/archives/index.html','Square Enix'),
 ('03-29',3,29,'Europe','Yoshi’s Crafted World: original Nintendo Switch release','https://www.nintendo.com/en-gb/Games/Nintendo-Switch-games/Yoshi-s-Crafted-World-1233953.html','Nintendo'),
 ('03-30',3,30,'Original desktop and Xbox One release','Thimbleweed Park: developer launch announcement','https://blog.thimbleweedpark.com/released.html','Ron Gilbert / Terrible Toybox'),
 ('03-31',3,31,'Original desktop release','Hyper Light Drifter: original release','https://store.steampowered.com/app/257850/Hyper_Light_Drifter/','Heart Machine'),
 ('04-01',4,1,'Original desktop release','Goat Simulator: original release','https://store.steampowered.com/app/265930/Goat_Simulator/','Coffee Stain Studios'),
 ('04-02',4,2,'Japan','Final Fantasy VI: original Super Famicom release','https://jp.finalfantasy.com/titles/finalfantasy6','Square Enix'),
 ('04-03',4,3,'Original iOS release','Monument Valley: original release','https://ustwo.com/blog/monument-valley-out-now/','ustwo'),
 ('04-04',4,4,'Original PC and Mac release','The Elder Scrolls Online: original desktop launch','https://www.prnewswire.com/news-releases/bethesda-softworks-launches-the-elder-scrolls-online-253889861.html','Bethesda Softworks / PR Newswire'),
 ('04-05',4,5,'Initial multi-platform release','LEGO Star Wars: The Skywalker Saga: original release','https://www.lego.com/en-us/aboutus/news/2022/april/lego-star-wars-the-skywalker-saga','LEGO / Warner Bros. Games / TT Games')
]
existing = {row['id'] for row in data['overrides']}
added = []
for suffix, month, day, region, event, url, publisher in rows:
    original = by_id['daily-'+suffix]
    identifier = original['linked_exhibit_id']
    assert identifier
    if identifier in existing:
        continue
    row = dict(id=identifier, year=original['year'], date=dict(month=month, day=day, precision='day', region=region),
        event=event, source=dict(title=event, url=url, publisher=publisher, type='Primary: date verification',
            supports='Explicit release date in the cited manufacturer, publisher or developer record; platform and regional qualifier retained.'),
        note='The published calendar slot is independent scheduling metadata, not evidence for this release day.', verified_date='2026-10-20')
    data['overrides'].append(row)
    existing.add(identifier)
    added.append(identifier)
file.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'added':len(added),'verified_overrides':len(data['overrides'])}))
