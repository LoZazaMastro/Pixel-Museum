"""Peer concrete Mega Drive paragraphs and two historically identified objects."""
from pathlib import Path
from PIL import Image
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1];BASE='build/research/mega-drive-three-concrete-cards/'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
tp=BASE+'three-concrete-wikipedia-mega-drive-cards-clear-identities-candidate.json';ip=BASE+'two-original-mega-drive-hardware-illustrations-candidate.json'
assert sha(tp)=='cad11714e75eee53c238ff8133d2cffb8310572b5f32ed838f778b3efa620623'
assert sha(ip)=='82986ef84ae3b5810483e4d927b4350968de4629852ca9b1594a04ec04e8a08c'
t=load(tp);d=load(ip);owner=next(x for x in load('content/catalog.json')['entries'] if x['id']=='mega-drive')
rows=[]
for row in t['replacements']:
    i=row['source_chapter_index'];p=row['provenance'];assert owner['body'][i]==row['old_body']
    assert hashlib.sha256(row['old_body'].encode()).hexdigest()==row['old_body_sha256']
    assert hashlib.sha256(row['body'].encode()).hexdigest()==row['body_sha256']
    assert sha(p['source_file'])==p['source_file_sha256']
    page=load(p['source_file'])['query']['pages'][0]
    assert page['pageid']==p['page_id'] and page['revisions'][0]['revid']==p['revision_id']
    paragraphs=[x.strip() for x in page['extract'].splitlines() if x.strip()]
    original=[paragraphs[n] for n in p['paragraph_indices']]
    assert original==p['source_paragraphs']
    text=' '.join(s[a:b].strip() for s,(a,b) in zip(original,p['selected_character_spans']))
    for edit in p['adaptations']:
        if isinstance(edit,dict):
            assert edit['from'] in text;text=text.replace(edit['from'],edit['to'])
            assert [paragraphs[n] for n in edit['context_paragraph_indices']]==p['context_source_paragraphs']
    assert text==row['body']
    assert row['source']['license']=='Creative Commons Attribution-ShareAlike 4.0'
    rows.append(dict(index=i,heading=row['heading'],body_sha256=row['body_sha256']))
g=d['article_guards']['mega-drive'];assert owner['body']==g['original_body'] and owner.get('story_headings',[])==g['original_headings']
assert hashlib.sha256(json.dumps(owner['body'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==g['body_sha256']
queries=[]
for r in d['source_receipts']:
    assert sha(r['path'])==r['sha256']
    if 'query' in r['path']:queries.extend(load(r['path'])['query']['pages'])
images=[]
for m in d['entries']['mega-drive']:
    assert sha(m['recovery_local_source'])==m['verification']['source_sha256']
    with Image.open(ROOT/m['recovery_local_source']) as im:
        assert list(im.size)==[m['width'],m['height']]==m['verification']['native_dimensions']
        if im.mode=='RGBA':assert im.getchannel('A').getextrema()==(0,255)
    info=next(x['imageinfo'][0] for x in queries if x.get('imageinfo') and x['imageinfo'][0]['url']==m['url'])
    assert info['extmetadata']['LicenseShortName']['value']=='Public domain' and 'Evan-Amos' in info['extmetadata']['Artist']['value']
    assert m['url'] not in [x['url'] for x in owner['images']]
    images.append(dict(url=m['url'],paragraph=m['story_paragraph'],dimensions=[m['width'],m['height']],sha256=sha(m['recovery_local_source'])))
tr=dict(status='PASS',candidate_path=tp,candidate_sha256=sha(tp),body_records=rows,observations=['All three full new texts and old passages read. Intro is an exact selected two-sentence overview plus complete hardware paragraph, excluding the regional release catalogue. CPU/Z80/video/cartridge/add-on/network details remain from the frozen revision.','Kalinske strategy paragraph is otherwise whole source22; only the first sentence resolves HayaoNakayama and MichaelKatz using same-revision context7/20, independently reconstructed. Sonic bundle strategy is concrete and distinct from the technical overview.','Add-on paragraph remains complete source3, including the source judgement on fragmentation. No new release date, object identity, soundtrack, image or cover change in this textual candidate. Original wording archived and CC BY-SA4 attributed. Paragraph locator convention independently checked as nonempty stripped extract lines.'],master_modified=False)
ir=dict(status='PASS',candidate_path=ip,candidate_sha256=sha(ip),images=images,observations=['Original4500x2160EUfirst-model MegaDrive/controller and3700x2800Genesis/SegaCD set individually viewed in full. The European unit is explicitly a family variant; Japanese cover/model identity is retained, no extra timeline launch.','The originalRGBA file contains hidden RGB striping outside the object. Existing dark inspection composite confirms that the authored alpha cleanly removes it. Keep the actualPNG intact for app rendering; the composited JPEG is inspection-only, not the publication asset.','Source Commons metadata matches native dimensions, exact URL and EvanAmos public-domain declaration for each photograph. Current body guard is the old3paragraph text by design because media hook precedes reviewed clarity. Associations0hardware and2expansions remain pertinent to the new texts.','Paragraph1Sonic-bundle imagery remains held for quality, not padded with an unrelated console photograph. No enlargement, new frame, lost alpha or all-cards-complete claim.'],master_modified=False)
for name,record in [('independent-three-concrete-mega-drive-cards-review.json',tr),('independent-two-original-mega-drive-images-review.json',ir)]:
    path=BASE+name;(ROOT/path).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(path,sha(path))
