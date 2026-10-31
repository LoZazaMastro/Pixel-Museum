"""Independent source-bound reviews following full visual inspection of each artifact."""
from pathlib import Path
import hashlib,json,re,tarfile,sys
from PIL import Image,ImageChops
import pypdfium2
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cases=[('galaxy1971-existing-prose-stanford-context','four-existing-galaxy-paragraphs-two-illustrated-scenes-contemporary1972-candidate.json',4,[[0],[1,2,3]]),
    ('empire1972-existing-prose-primary-history','two-existing-empire-paragraphs-two-primary-document-reproductions-candidate.json',2,[[0],[1]]),
    ('rebound-existing-prose-kee-spike-context','two-existing-rebound-paragraphs-two-authentic-conversion-context-scenes-candidate.json',2,[[0],[1]]),
    ('spasim-existing-prose-author-archive','two-existing-spasim-paragraphs-two-primary-author-artifacts-precise-code-caption-candidate.json',2,[[0],[1]])]
for directory,filename,count,groups in cases:
    if sys.argv[1:]and directory not in sys.argv[1:]:continue
    base=ROOT/'build/research'/directory;path=base/filename
    doc=json.loads(path.read_text(encoding='utf8'));row,=doc['rows'];old=row['old_entry'];new=row['new_entry']
    current=next(e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']if e['id']==row['entry_id'])
    assert current==old and new['body']==old['body']and len(old['body'])==count
    assert old.get('story_headings')==new.get('story_headings')and doc['expected_main_paragraph_groups']==groups
    for name,digest in doc['source_files'].items():assert sha(ROOT/name)==digest,name
    for item in new['images']:
        p=ROOT/item['recovery_local_source']
        with Image.open(p)as image:image.load();assert image.size==(item['width'],item['height'])
    assert len({sha(ROOT/i['recovery_local_source'])for i in new['images']})==len(new['images'])
    assert new['images'][0]['url']==old['images'][0]['url']
    if count==4:
        html=(base/'strong-original-galaxy1972-asset.html').read_text(encoding='utf8')
        records=[json.loads(x)for x in re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',html,re.S)]
        assert any(new['images'][-1]['url']in json.dumps(record,ensure_ascii=False)for record in records)
        assert '1972'in html and 'The Strong'in html
        assert old['videos']==new['videos']and old['images'][1]==new['images'][1]
        visual='Contemporary colour photograph of the blue second-version consoles with players at Stanford in 1972. Exact original museum-published 1200 by 788 rendition, not a photograph of the 1971 wooden prototype.'
        limits=['Published image is 1200 by 788; source-declared 2765 by 1816 original is not falsely claimed downloaded.',
            'Existing near-black video poster is not replaced with duplicate cover art; separate preview issue remains.']
    elif directory=='rebound-existing-prose-kee-spike-context':
        html=(base/'collector-original-conversion-flyer-source.html').read_text(encoding='utf8')
        assert 'convflyerbig.jpg'in html and 'original'in html.lower()
        assert new['videos']==old['videos']and new['images'][1]==old['images'][1]
        assert {k:v for k,v in new['images'][0].items()if k!='story_paragraph'}=={k:v for k,v in old['images'][0].items()if k!='story_paragraph'}
        visual='Whole original Atari TV-ping-pong to volleyball conversion-kit sales sheet, with the simulated volleyball display and interchangeable-board explanation. Directly pertinent to the existing conversion paragraph; not a Spike cabinet or Video Olympics capture.'
        limits=['Native 1272 by 1638 collector-published original scan retained.',
            'No printing date invented from the collector acquisition date; original Atari rights retained.']
    elif directory=='spasim-existing-prose-author-archive':
        readme=(base/'author-original-readme.md').read_text(encoding='utf8')
        assert new['images'][1]['url']in readme
        assert 'week before the first commit'in readme and 'cyber1.org'in readme
        original=(base/'author-original-xspasim.txt').read_text(encoding='utf8')
        excerpt=(base/'author-original-page2-exact-text.txt').read_text(encoding='utf8')
        assert excerpt in original and 'december 22, 2022'in excerpt
        assert len(excerpt.splitlines())==60
        pdf=pypdfium2.PdfDocument(base/'author-2022-original-source-page2-modern-reproduction.pdf')
        render=pdf[0].render(scale=300/72).to_pil().convert('RGB')
        with Image.open(ROOT/new['images'][2]['recovery_local_source'])as image:
            assert not ImageChops.difference(render,image.convert('RGB')).getbbox()
        assert new['videos']==old['videos']and new['images'][0]==old['images'][0]
        visual='The author-published orange wireframe view includes the planet, ships and SPASIM lettering. A distinct exact complete listing page shows ship coordinates, movement and control flags, retaining its December2022 header.'
        limits=['The author describes the picture as a recent Cyber1 preservation-system screenshot; it is not represented as a 1974 photograph or native 7041-pixel PLATO framebuffer.',
            'Listing image is plain modern mechanical typesetting of original text, not generated code or aged paper.',
            'Public source repository is not falsely declared an open-licensed asset.']
    else:
        proof=json.loads((base/'original-tape-source-extraction-proof.json').read_text(encoding='utf8'))
        tape=ROOT/'build/research/cover-duplicates/early-originals/usenix_80_delaware.tar.gz'
        with tarfile.open(tape)as archive:
            for item in proof['members_byte_identical']:
                assert archive.extractfile(item['member']).read()==(ROOT/item['file']).read_bytes()
            assert archive.extractfile('delaware/langston/READ_ME').read()==(base/'delaware-langston-READ_ME.txt').read_bytes()
            assert archive.extractfile('delaware/langston/EMP/READ_ME').read()==(base/'delaware-langston-EMP-READ_ME.txt').read_bytes()
        pdf=pypdfium2.PdfDocument(ROOT/'build/research/cover-duplicates/early-originals/empire-overview-1978.pdf')
        render=pdf[1].render(scale=300/72).to_pil().convert('RGB')
        with Image.open(ROOT/new['images'][1]['recovery_local_source'])as image:
            assert not ImageChops.difference(render,image.convert('RGB')).getbbox()
        assert not new['videos']
        visual='Plain modern typesetting of the authored May 1978 overview and original MAP help with its ASCII sector example. Both remain explicit source-document reproductions, not invented 1972 gameplay or aged paper scans.'
        limits=['Original 1972 game code is not represented as recovered.',
            'Unverified-edition film and poster are archived; not asserted definitively wrong.',
            'Source attribution retains Peter Langston copyright; no invented open licence.']
    report=dict(status='PASS_INDEPENDENT_PRIMARY_ARTIFACT_AND_EXISTING_PROSE_REVIEW',candidate=path.relative_to(ROOT).as_posix(),candidate_sha256=sha(path),
        current_owner_unchanged=True,all_existing_paragraphs_and_headings_preserved=True,all_source_hashes_checked=True,exclusive_cover=True,
        full_visual_review=visual,limits=limits+['Actual native composition and final staging checked separately.'])
    out=base/'root-independent-primary-artifact-existing-prose-peer-review.json'
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(receipt=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
