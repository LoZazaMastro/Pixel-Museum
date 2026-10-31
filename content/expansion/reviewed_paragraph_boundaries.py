"""Insert independently reviewed sentence-boundary breaks; never rewrite words."""
import copy,hashlib,json
from pathlib import Path

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf8')).hexdigest()

def transform(entry,row):
    assert digest(entry['body'])==row['original_body_sha256'] and len(entry['body'])==1
    assert digest(entry['images'])==row['images_before_sha256']
    assert digest(entry.get('story_headings',[]))==row['headings_before_sha256']
    before=copy.deepcopy(entry);text=entry['body'][0];offset=row['character_offset']
    assert 0<offset<len(text) and text[offset:].startswith(row['split_before'])
    parts=[text[:offset].rstrip(),text[offset:]]
    assert ' '.join(parts)==text and parts[0][-1] in '.!?'
    indices=row['image_indices'];assert len(indices)==2 and len(set(indices))==2
    cover=entry.get('preferred_image',0);assert cover not in indices
    for n in indices:assert 0<=n<len(entry['images']) and entry['images'][n].get('kind')!='video-poster'
    assert len(set(entry['images'][n]['url'] for n in indices))==2
    entry['body']=parts;entry['story_headings']=copy.deepcopy(row['chapter_headings'])
    assert len(entry['story_headings'])==2
    entry['explicit_story_media_only']=True
    for image in entry['images']:
        if image.get('kind')!='video-poster':image['story_paragraph']=-1
    for paragraph,n in enumerate(indices):entry['images'][n]['story_paragraph']=paragraph
    if 'attribution' in entry:
        entry['attribution']['changes']=entry['attribution'].get('changes','')+' One sentence-boundary paragraph break inserted without changing any wording; chapter headings supplied by Pixel Museum.'
    assert ' '.join(entry['body'])==before['body'][0]
    assert {k:v for k,v in before.items() if k not in {'body','story_headings','images','explicit_story_media_only','attribution'}}=={k:v for k,v in entry.items() if k not in {'body','story_headings','images','explicit_story_media_only','attribution'}}
    return {'entry_id':entry['id'],'paragraphs_before':1,'paragraphs_after':2,'original_wording_exact':True}

def apply(entries,root):
    root=Path(root);mp=root/'content/expansion/museum-paragraph-boundaries-reviewed.json'
    if not mp.exists():return {'status':'not_admitted'}
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();owners={e['id']:e for e in entries};changed=[]
    for batch in json.loads(mp.read_text(encoding='utf8'))['batches']:
        cp=root/batch['candidate_path'];pp=root/batch['peer_path']
        assert sha(cp)==batch['candidate_sha256'] and sha(pp)==batch['peer_sha256']
        c=json.loads(cp.read_text(encoding='utf8'));p=json.loads(pp.read_text(encoding='utf8'))
        assert p['status'].startswith('PASS') and p['candidate_sha256']==sha(cp)
        for source,expected in c['source_files'].items():assert sha(root/source)==expected
        for row in c['rows']:
            entry=owners[row['entry_id']]
            if digest(entry['body'])==row['body_after_sha256']:
                assert entry['story_headings']==row['chapter_headings'] and entry['explicit_story_media_only']
                assert all(entry['images'][n]['story_paragraph']==i for i,n in enumerate(row['image_indices']))
                continue
            changed.append(transform(entry,row));assert digest(entry['body'])==row['body_after_sha256']
    return {'status':'PASS_REVIEWED_PARAGRAPH_BREAKS_EXACT_ORIGINAL_WORDING','changed':changed}
