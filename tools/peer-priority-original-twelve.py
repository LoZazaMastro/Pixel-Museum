"""Independent read-only original-game media/edition/source/uniqueness peer."""
from pathlib import Path
import hashlib
import json
import zipfile
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/story-text-profile/priority-original-illustrations'
original=BASE/'twelve-original-game-illustrations-candidate.json'
candidate=BASE/'twelve-original-game-illustrations-credit-corrected-candidate.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(original)=='f7995716cd5f1c746c46ac548be04aae696fdea496d29b5407cf03fe969c8217'
assert sha(candidate)=='98d568dc0838772a7880b6c46e1b57bb318e3163fbd63e72dba1ada0daa4b7cc'
o,c=[json.loads(p.read_text(encoding='utf8')) for p in (original,candidate)]
catalog_path=ROOT/'content/catalog.json'
catalog=json.loads(catalog_path.read_text(encoding='utf8'))
entries={e['id']:e for e in catalog['entries']}
assert c['article_guards']==o['article_guards'] and c['source_receipts']==o['source_receipts']
assert c['gap_profile']==o['gap_profile'] and sha(ROOT/c['gap_profile']['path'])==c['gap_profile']['sha256']
assert set(c['entries'])==set(o['entries'])
changes=[]
for eid in c['entries']:
    for index,(a,b) in enumerate(zip(o['entries'][eid],c['entries'][eid])):
        for key in set(a)|set(b):
            if a.get(key)!=b.get(key):
                assert eid=='wikipedia-1508961' and key in ('creator','credit') and b[key]=='Capcom'
                changes.append({'entry_id':eid,'image_index':index,'field':key,'old':a[key],'new':b[key]})
assert len(changes)==8

source_receipts=[]
for r in c['source_receipts']:
    p=ROOT/r['path']
    assert sha(p)==r['sha256']
    source_receipts.append(dict(r,independently_read=True))
kh_html=(BASE/'kh2-official-timeline.html').read_text(encoding='utf8')
assert 'kh2' in kh_html and 'SQUARE ENIX' in kh_html and 'Disney' in kh_html
steam=json.loads((BASE/'steam-32500.json').read_text(encoding='utf8'))['32500']
assert steam['success'] and steam['data']['steam_appid']==32500 and 'II' in steam['data']['name']
steam_urls={r['path_full'] for r in steam['data']['screenshots']}
zip_path=BASE/'onimusha3-original-art.zip'
zip_receipt=next(r for r in c['source_receipts'] if r['path'].endswith(zip_path.name))
assert sha(zip_path)==zip_receipt['sha256']==c['archive_acquisition']['zip_sha256']
archive_index=json.loads((BASE/'capcom-original-press-zip-index.json').read_text(encoding='utf8'))
assert any(r['name']=='CapcomDPK/Onimusha 3/art.zip' and r['size']==zip_path.stat().st_size for r in archive_index)
media=[]
guards=[]
all_new_hashes=set()
all_pixel_hashes=set()
for eid,images in c['entries'].items():
    e=entries[eid];guard=c['article_guards'][eid]
    assert e['body']==guard['body']
    assert hashlib.sha256(json.dumps(e['body'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==guard['body_sha256']
    existing_urls=[im['url'] for im in e['images']]
    assert existing_urls==guard['existing_image_urls']
    assert len(e['body'])==len(images)==4 and [im['story_paragraph'] for im in images]==list(range(4))
    existing_hashes=set()
    existing_pixels=set()
    for im in e['images']:
        p=ROOT/im['recovery_local_source']
        existing_hashes.add(sha(p))
        with Image.open(p) as decoded:
            decoded.load();existing_pixels.add(hashlib.sha256(str(decoded.size).encode()+decoded.convert('RGB').tobytes()).hexdigest())
    guards.append({'entry_id':eid,'body_sha256':guard['body_sha256'],'existing_urls':existing_urls,
                   'cover_and_body_unchanged':True,'existing_native_covers_visually_reviewed':True})
    for im in images:
        p=ROOT/im['recovery_local_source'];h=sha(p)
        assert h==im['verification']['source_sha256']
        assert h not in existing_hashes and h not in all_new_hashes
        all_new_hashes.add(h)
        with Image.open(p) as decoded:
            decoded.load();dimensions=list(decoded.size)
            assert dimensions==im['verification']['native_dimensions']==[im['width'],im['height']]
            pixel_hash=hashlib.sha256(str(decoded.size).encode()+decoded.convert('RGB').tobytes()).hexdigest()
        assert pixel_hash not in existing_pixels and pixel_hash not in all_pixel_hashes
        all_pixel_hashes.add(pixel_hash)
        extra={}
        if eid=='wikipedia-1745270':
            assert 'timeline/series/soft/kh2/z/'+p.name.replace('kh2-primary-','pic0').replace('.jpg','.jpg') in kh_html
            extra={'edition':'Official later HD retrospective of the same KHII scenes; no 2005 PS2 framebuffer claim.'}
        elif eid=='wikipedia-25414501':
            assert im['url'] in steam_urls
            extra={'edition':'Original2010 game, PC promotional presentation; native1280x720 despite1920 URL suffix.'}
        else:
            member=im['verification']['press_archive_member']
            with zipfile.ZipFile(zip_path) as z:
                data=z.read(member)
                assert data==p.read_bytes()
                z.getinfo(member) # read() also validates original member CRC.
            assert im['creator']==im['credit']=='Capcom'
            extra={'edition':'Original Capcom E3 2003 pre-release promotional art for Onimusha3.',
                   'original_zip_member':member,'member_bytes_exact':True,
                   'rights_correction':'Uncorroborated FuLong/Samanosuke likeness assertion removed, including Jacques-only image.'}
        assert 'original rights retained' in im['license'].lower() and not im.get('license_url')
        media.append({'entry_id':eid,'paragraph':im['story_paragraph'],'local_file':im['recovery_local_source'],
                      'source_url':im['url'],'source_page':im['source_page'],'sha256':h,'native_dimensions':dimensions,
                      'native_image_viewed_in_full':True,'distinct_from_cover_and_other_story_images':True,**extra})
assert len(media)==len(all_new_hashes)==len(all_pixel_hashes)==12

associations=[
 {'entry_id':'wikipedia-1745270','paragraphs':[
  'Sora, Donald and Goofy in Disney Castle identify the returning party in the sequel introduction.',
  'Sora and Axel surrounded by Nobodies illustrate the OrganizationXIII/Nobody conflict, without claiming the picture is a production artifact.',
  'Sora and Riku in an action scene provide character/combat context, not documentary proof of development or a split-screen co-op feature.',
  'Roxas and his friends above TwilightTown illustrate character staging and presentation discussed in reception; no award/sales proof asserted.']},
 {'entry_id':'wikipedia-25414501','paragraphs':[
  'Starkiller visibly uses the Force against stormtroopers, with dual weapons identifying the sequel action.',
  'Starkiller stands with Rebel soldiers, corresponding to the Alliance and protagonist story paragraph.',
  'Force lightning and airborne enemies illustrate the effects/combat presentation, not a recording-session photograph.',
  'Dual blue lightsabers confront an Imperial enemy, providing visuals/gameplay context for reception.']},
 {'entry_id':'wikipedia-1508961','paragraphs':[
  'Original promotional render shows both Samanosuke and Jacques, matching the two-protagonist introduction.',
  'Jacques and his magical weapon illustrate the second protagonist and weapon-based mechanics.',
  'Detailed cinematic-style faces of Samanosuke and Jacques illustrate character/CGI presentation; not claimed as a frame from the opening movie.',
  'A different Samanosuke pose accompanies commercial reception as campaign artwork, not an award or sales document.']}]
out={'schema_version':1,'publication_status':'PASS','candidate_path':candidate.relative_to(ROOT).as_posix(),
     'candidate_sha256':sha(candidate),'superseded_candidate_sha256':sha(original),
     'source_catalog_sha256':sha(catalog_path),'candidate_catalog_sha256':c['catalog_sha256'],
     'article_guards':guards,'source_receipts':source_receipts,'images':media,
     'required_credit_correction_applied':changes,'body_image_associations':associations,
     'rights_review':'Publisher promotional material retains original copyright. No individual illustration authors, exclusive ownership, separate likeness ownership or CreativeCommons permissions inferred.',
     'limits':['KHII publisher retrospective images show later HD presentation; no original2005 PS2 framebuffer claim.',
               'Eight KHII/TFUII sources are native1280x720 historical promotional images, without upscaling or a4K master claim.',
               'Onimusha3 renders retain original grey/black backgrounds and their original pre-release forms; no AI cutout, restoration or invented pixels.',
               'Only this media addition is reviewed; a pre-existing Onimusha3 lead contains mojibake in its parenthetical Japanese title and should be corrected separately.',
               'No final Screen render, asset bundle, production/master write or console transfer was performed.'],
     'master_modified':False}
target=BASE/'independent-twelve-original-game-illustrations-review.json'
target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':target.relative_to(ROOT).as_posix(),'sha256':sha(target),'status':'PASS','images':len(media)}))
