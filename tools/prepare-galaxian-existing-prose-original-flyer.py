"""Distribute the existing Galaxian introduction beside its original arcade leaflet."""
from pathlib import Path
import copy, hashlib, json
from PIL import Image
root=Path(__file__).resolve().parents[1]
base=root/'build/research/galaxian-existing-prose-publisher-history'
old=next(e for e in json.loads((root/'content/catalog.json').read_text(encoding='utf8'))['entries'] if e['id']=='wikipedia-585780')
new=copy.deepcopy(old)
assert len(old['body'])==3 and old['preferred_image']==0
metadata=base/'launchbox-original-arcade-gallery-metadata.json'
assert any(r['DatabaseID']=='7866' and r['FileName']=='70d656fe-be76-4f47-b15d-18516897a13b.jpg' and r['Type']=='Advertisement Flyer - Back' for r in json.loads(metadata.read_text(encoding='utf8')))
scan=base/'original-namco-flyer-back.jpg'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(scan)=='e8e2ceb357022eed837082830aab48399323d3d29d042d6044ddc6dba9ae1026'
with Image.open(scan)as im:width,height=im.size
new['explicit_story_media_only']=True
new['images'][0]['story_paragraph']=-1
new['images'].append(dict(url='https://images.launchbox-app.com/70d656fe-be76-4f47-b15d-18516897a13b.jpg',source_page='https://gamesdb.launchbox-app.com/games/details/7866',title='Colour, formations and diving attacks',caption='The complete back of Namco\'s original Japanese Galaxian arcade leaflet, copyright 1979. Its screen view and scoring diagrams show the coloured alien formations and diving attacks. This is an original manufacturer document, not a later home conversion.',creator='Namco',credit='Namco / LaunchBox scan archive',license='Original manufacturer artwork and advertisement rights retained; no open licence asserted.',width=width,height=height,story_paragraph=1,recovery_local_source=scan.relative_to(root).as_posix(),verification=dict(sha256=digest(scan),processing='Complete original published scan; no crop, enlargement or retouch.')))
new['story_headings']=['Aliens leave the formation','Colour and movement','An arcade breakthrough']
candidate=dict(status='CANDIDATE_PENDING_INDEPENDENT_PEER',rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],source_files={p.relative_to(root).as_posix():digest(p) for p in [metadata,scan]},expected_main_paragraph_groups=[[0],[1,2]],scope='Three complete existing paragraphs unchanged; original arcade longplay retained; exclusive cover and distinct original Namco1979 leaflet back. Only three concrete descriptive headings added.',quality_limits=['The existing film has no preview yet; its preview gap remains explicit rather than fabricating a thumbnail.','The Namco maintenance page is deliberately excluded as it provides no historical evidence.'])
out=base/'three-existing-galaxian-paragraphs-original-namco-leaflet-final-candidate.json'
out.write_text(json.dumps(candidate,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(root).as_posix(),sha256=digest(out))))
