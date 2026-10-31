"""Peer four exact narrative image associations without mutating production."""
from pathlib import Path
from PIL import Image
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];BASE='build/research/story-text-profile/priority-original-illustrations/three-studios-source-bound-images/'
PATH=BASE+'four-original-three-studio-narrative-images-caption-corrected-candidate.json';EXPECTED='4d71502ed27a91a2e34effe323a58b3c41009bf595283c65d6b1b38ec0ddfe2f'
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def pixels(p):
    with Image.open(ROOT/p) as im:
        rgb=im.convert('RGB');return list(im.size),hashlib.sha256(str(rgb.size).encode()+rgb.tobytes()).hexdigest()
assert sha(PATH)==EXPECTED
d=load(PATH);owners={x['id']:x for x in load('content/catalog.json')['entries']};manifest=load('assets/images/manifest.json')
for r in d['source_receipts']:assert sha(r['path'])==r['sha256']
rows=[];seen=set()
for eid,images in d['entries'].items():
    owner=owners[eid];g=d['article_guards'][eid]
    assert owner['body']==g['original_body'] and owner['story_headings']==g['original_headings']
    assert hashlib.sha256(json.dumps(owner['body'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==g['body_sha256']
    existing={pixels(manifest['images'][i['url']])[1] for i in owner['images']}
    for m in images:
        p=m['recovery_local_source'];v=m['verification'];assert sha(p)==v['source_sha256']
        dims,pixel=pixels(p);assert dims==[m['width'],m['height']]==v['native_dimensions'] and pixel==v['decoded_rgb_identity_sha256']
        assert pixel not in existing and pixel not in seen;seen.add(pixel)
        assert 0<=m['story_paragraph']<len(owner['body'])
        if 'steampowered' in m['source_page']:
            app=m['source_page'].strip('/').split('/')[-1];source=load(BASE+'steam-'+app+'-appdetails.json')[app]['data']
            assert any(x['path_full'].split('?')[0]==m['url'].split('?')[0] for x in source['screenshots'])
        rows.append(dict(entry_id=eid,url=m['url'],paragraph=m['story_paragraph'],dimensions=dims,sha256=sha(p)))
assert len(rows)==4
receipt=dict(status='PASS',candidate_path=PATH,candidate_sha256=EXPECTED,images=rows,source_files_verified=len(d['source_receipts']),observations=['All four native images individually viewed in full and all twelve current body paragraphs read. Gunstar original1993AmericanGenesis rear packaging visibly contains the described two-player/360degree/body-slam claims and four gameplay scenes. It is an original packaging artifact, not a falsely high-resolution screenshot.','Ikaruga displays contrasting projectile polarities, chain status in the documented laterPCpublication. The source URL delivers1280x720actual pixels despite its1920x1080filename; no enlargement claimed.','SystemShock2 original-game screenshot shows inventory, equipment and statistics over its original3Dcorridor; officialSteam238210gallery URL matches the cached publisher API and exact local source pixels. No2025remaster confusion.','Atlus paragraph3 concerns the modern Persona series calendar/relationship system generally. ExplicitPersona5RoyalPC later-edition illustration is appropriate: Kasumi dialogue with7JulyThursday/after-school label clearly visible. It is not attributed to Persona1996 or the original2016Persona5 release.','Every candidate pixel identity is distinct from every actual current image in its own complete article using the live local manifest, as well as distinct among the four proposals. Reserved game/publisher rights retained without inventedCClicence. Small640x480Gunstar/600x450FreedomForce alternatives remain held; no unrelated filler.'],master_modified=False)
out=BASE+'independent-four-caption-corrected-studio-original-images-review.json';(ROOT/out).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(out,sha(out))
