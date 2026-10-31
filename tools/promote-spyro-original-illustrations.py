"""Associate the three original1998 artifacts with Spyro's existing paragraphs."""
from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'build/research/spyro-illustrated-history'
inventory={row['tag']:row for row in json.loads((folder/'original-artifacts-inventory.json').read_text(encoding='utf8'))}
target=ROOT/'content/expansion/museum-story-illustrations-editorial-reviewed.json'
doc=json.loads(target.read_text(encoding='utf8'))
rows=[]
for index,tag,title,caption in [
    (0,'B-ALL','The original Spyro adventure on the back cover','Original1998 North American packaging shows gliding, collecting and the dragon worlds.'),
    (1,'D-ALL','The original1998 PlayStation disc','The original SCUS-94228 disc credits Universal Interactive, Insomniac Games and Sony Computer Entertainment.'),
    (2,'A-1','Spyro-Mania / original1998 promotion','An original1998 promotional insert presents Spyro as a new PlayStation character.')]:
    source=inventory[tag];path=ROOT/source['path'];url=source['url'];transform=None
    assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']
    if tag=='A-1':
        output=folder/'SCUS-94228-A-1-upright.png'
        with Image.open(path)as image:image.transpose(Image.Transpose.ROTATE_270).save(output)
        transform=dict(operation='lossless quarter-turn clockwise of decoded source pixels',source_file=source['path'],source_sha256=source['sha256'],resize=False,crop=False)
        path=output;url+='#orientation=clockwise90'
    with Image.open(path)as image:image.load();width,height=image.size
    rows.append(dict(url=url,original_url=source['url'],title=title,caption=caption,
        source_page='https://psxdatacenter.com/games/U/S/SCUS-94228.html',
        creator='Insomniac Games / Universal Interactive / Sony Computer Entertainment',
        credit='Original1998 game, packaging and promotional art; scan preserved by PSX Data Center, contributor VUOTARE.',
        license='Original game, illustration, packaging and promotional rights retained by their respective owners; no open licence claimed.',
        license_url='',width=width,height=height,story_paragraph=index,
        recovery_local_source=path.relative_to(ROOT).as_posix(),
        verification=dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),native_dimensions=[width,height],no_upscale=True),
        identity_evidence=dict(game='Spyro the Dragon',year=1998,platform='Sony PlayStation',serial='SCUS-94228',artifact=tag),
        transformation=transform,visual_review='Root and editorial agents inspected the actual original artifacts; no Reignited artwork, front-cover reuse or unrelated Crash demo advertisement admitted.'))
doc['entries']['wikipedia-1353538']=rows
target.write_text(json.dumps(doc,indent=2,ensure_ascii=True)+'\n',encoding='utf8')
receipt=dict(status='PASS',entry_id='wikipedia-1353538',associations=[dict(paragraph=i['story_paragraph'],url=i['url'],dimensions=[i['width'],i['height']],sha256=i['verification']['sha256'])for i in rows],
    scope='Existing three full Wikipedia paragraphs unchanged. Gameplay back cover, original production disc and1998 mascot promotion are distinct original artifacts. Only orientation normalized for the sideways promotional scan; original retained.',
    excluded=['I-1 Crash Warped demo insert unrelated to the paragraphs','I-2 near-duplicate front-cover artwork'])
(folder/'three-paragraph-associations-review.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=True)+'\n',encoding='utf8')
print(json.dumps(receipt))
