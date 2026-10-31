"""Regression checks for archive video identities using observed public titles."""
import importlib.util
from pathlib import Path
p=Path(__file__).with_name('discover-museum-videos.py');spec=importlib.util.spec_from_file_location('discovery',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
cases=[
('Street Fighter II',1991,'Arcade Longplay [370] Street Fighter II: The World Warrior',True),
('Street Fighter II',1991,'Street Fighter II Turbo SNES Longplay',False),
('Metal Gear Solid 2: Sons of Liberty',2001,'PS2 Longplay [092] Metal Gear Solid 2: Sons of Liberty (US)',True),
('Metal Gear Solid 2: Sons of Liberty',2001,'Metal Gear Solid 2 HD Collection Walkthrough',False),
('Final Fantasy XVI',2023,'Final Fantasy 16 - Combat Gameplay Overview | State of Play 2023',True),
('Dishonored 2',2016,'Dishonored 2 – Corvo Gameplay Trailer',True),
('Deus Ex',2000,'Deus Ex Mankind Divided Official Trailer',False),
('The Sims',2000,'The Sims 4 Gameplay Trailer',False),
('Max Payne',2001,'Max Payne 3 Gameplay Trailer',False),
('Shadow of the Colossus',2005,'Shadow of the Colossus | Launch Trailer | PS4',False),
('LittleBigPlanet',2008,'LittleBigPlanet PlayStation Vita Gamescom Trailer',False),
('Forza Motorsport',2005,'Forza Motorsport - Official Announce Trailer',False),
('Forza Motorsport',2005,'Forza Motorsport (2005) original Xbox gameplay',True),
('Maniac Mansion',1987,'Maniac Mansion (NES) Playthrough',False),
('Pac-Man',1980,'Pac-Man World Re-Pac Official Trailer',False),
('Ninja Gaiden',2004,'Ninja Gaiden NES Full Game',False),
('Ninja Gaiden',2004,'Xbox Longplay Ninja Gaiden (2004)',True),
]
for title,year,film,expected in cases:
 actual,reason=m.relevant({'title':title,'year':year,'kind':'game'},{'title':film,'duration':300})
 assert actual==expected,(title,film,actual,reason)
# A successful resolver must retain the native codec receipt when presentation
# metadata is normalized; otherwise fresh selections silently lose the gate.
import tempfile
with tempfile.TemporaryDirectory() as folder:
 m.CACHE=Path(folder)
 m.urlopen=lambda *a,**k: (_ for _ in ()).throw(OSError('Offline fixture'))
 m.app_metadata=lambda *a:{'ok':True,'id':'fixture','playable_video_formats':2,'format_count':3,'video_codecs':['AVC'],'audio_codecs':['AAC'],'avc_format_count':2,'aac_format_count':1,'native_compatible_avc_aac':True,'native_selection':'itag=137 1920x1080 AVC (plain) ceiling=1080p'}
 receipt=m.metadata('fixture',{'title':'A real archive film','channel':'Original creator'})
 assert receipt['native_compatible_avc_aac'] is True and receipt['aac_format_count']==1
 assert receipt['native_selection'].startswith('itag=137')
 m.app_metadata=lambda *a:{'ok':True,'id':'unsupported','playable_video_formats':2,'native_compatible_avc_aac':False,'error':'No AAC audio'}
 try:m.metadata('unsupported',{})
 except ValueError:pass
 else:raise AssertionError('A missing native AAC pair must not pass the publication gate')
print('PASS',len(cases),'observed-title checks and 3 codec receipt/gate checks')
