"""Apply returned prose by stable owner/card IDs; retain media and source credits."""
from pathlib import Path
import copy, hashlib, json, runpy

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'content/external-editorial/sol-pro-20261030'
FIELDS = ('title', 'subtitle', 'summary', 'body', 'story_headings')
LANGS = ('en', 'it', 'fr', 'de', 'es')

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def fields(x): return {k:x.get(k, [] if k in ('body','story_headings') else '') for k in FIELDS}
def digest(x): return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',',':')).encode()).hexdigest()
def write(p,x):
    temp=p.with_suffix('.tmp')
    temp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    temp.replace(p)
def converted(x):
    return {**{k:x[k] for k in ('title','subtitle','summary')}, 'body':[c['text'] for c in x['cards']], 'story_headings':[c['heading'] for c in x['cards']]}

def apply():
    docs={k:read(ROOT/'content'/f'{k}.json') for k in ('catalog','human-history')}
    locales={k:read(ROOT/'content/museum-locales'/f'{k}.json') for k in LANGS[1:]}
    index={name:{e['id']:e for e in d['entries']} for name,d in docs.items()}
    report={'applied_entries':[], 'conflicts':[], 'issues':[], 'owners':0,'cards_per_language':0,'batches':0}
    for path in sorted(BASE.glob('*/OUTPUT-*.json')):
        output=read(path); original=read(path.parent/'INPUT.json')
        assert output['completed'] is True and output['batch_id']==original['batch_id']
        assert output['source_sha256']==original['source_sha256']
        collection='human-history' if 'human-history' in output['batch_id'] else 'catalog'
        originals={e['entry_id']:e for e in original['entries']}
        assert set(originals)=={e['entry_id'] for e in output['entries']}
        report['batches']+=1
        for result in output['entries']:
            eid=result['entry_id']; source=originals[eid]; current=index[collection].get(eid)
            if current is None:
                report['conflicts'].append({'entry_id':eid,'reason':'Owner no longer exists'});continue
            pending=[]; reason=None
            feature_sources={f['feature_id']:f for f in source['features']}
            feature_results={f['feature_id']:f for f in result['features']}
            assert set(feature_sources)==set(feature_results)
            pairs=[(current,source['main'],result['main'])]
            features={f['id']:f for f in current.get('editorial_features',[])}
            for fid,old in feature_sources.items():
                if fid not in features:reason='Feature no longer exists';break
                pairs.append((features[fid],old,feature_results[fid]))
            for owner,old,new in pairs:
                expected=[c['card_id'] for c in old['cards']]
                for lang in LANGS:
                    x=new[lang]; assert [c['card_id'] for c in x['cards']]==expected,(eid,lang,'card IDs')
                    assert all(isinstance(x[k],str) for k in ('title','subtitle','summary'))
                    assert all(isinstance(c['text'],str) and c['text'].strip() and isinstance(c['heading'],str) and c['heading'].strip() for c in x['cards']),(eid,lang,'empty card')
                baseline=converted(old); replacement=converted(new['en'])
                # Absent headings historically equal an empty heading for each card.
                existing=fields(owner)
                if not existing['story_headings']:existing['story_headings']=['']*len(existing['body'])
                if existing!=baseline and existing!=replacement:
                    reason='English changed since exported input';break
                pending.append((owner,new,replacement))
            if reason:
                report['conflicts'].append({'entry_id':eid,'reason':reason});continue
            for owner,new,english in pending:
                owner.update(english)
                owner['external_editorial']={'batch_id':output['batch_id'],'output_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_fields_sha256':digest(english),'source':'User-supplied GPT Sol Pro returned text; original sources and media retained'}
                for lang in LANGS[1:]:
                    row=converted(new[lang]);row['editorial_credit']=owner.get('editorial_credit','')
                    row['provenance']={'source_fields_sha256':digest(english),'source_field_hashes':{k:digest(v) for k,v in english.items()},'mode':'user_supplied_external_editorial','batch_file':path.relative_to(ROOT).as_posix(),'source_units':[], 'english_fallback_units':[]}
                    locales[lang]['entries'][owner['id']]=row
                report['owners']+=1;report['cards_per_language']+=len(english['body'])
            report['applied_entries'].append(eid)
            if result.get('issues'):report['issues'].append({'entry_id':eid,'issues':result['issues']})
    report['metadata_applied']=[];report['metadata_conflicts']=[];report['media_applied']=[]
    metadata=BASE/'metadata-patches.json'
    if metadata.exists():
        for patch in read(metadata)['ready']:
            owner=index[patch['collection']].get(patch['entry_id'])
            if owner is None:continue
            before,after=patch['before'],patch['after']
            if any(owner.get(k) not in (v,after.get(k)) for k,v in before.items()):
                report['metadata_conflicts'].append(patch['entry_id']);continue
            owner.update(after)
            owner['external_metadata_evidence']={'audit_file':patch['audit_file'],'audit_sha256':patch['audit_sha256'],'scope':'Documented findings supplied by user; not a new independent historical audit'}
            report['metadata_applied'].append(patch['entry_id'])
        for doc in docs.values():
            doc['entries'].sort(key=lambda e:(e.get('year',0),e.get('date',{}).get('month',0),e.get('date',{}).get('day',0)))
    media=BASE/'media-patches.json'
    if media.exists():
        for patch in read(media)['patches']:
            owner=index[patch['collection']][patch['entry_id']]
            for change in patch.get('images',[]):
                n=change['index']; image=copy.deepcopy(change['replacement'])
                assert n<=len(owner['images'])
                if n==len(owner['images']):owner['images'].append(image)
                else:
                    old=owner['images'][n]
                    assert not change.get('before_url') or old['url'] in (change['before_url'],image['url'])
                    # Preserve existing paragraph bindings unless explicitly replaced.
                    if 'story_paragraph' not in image and 'story_paragraph' in old:image['story_paragraph']=old['story_paragraph']
                    owner['images'][n]=image
            if 'preferred_image' in patch:owner['preferred_image']=patch['preferred_image']
            report['media_applied'].append(patch['entry_id'])
    audit=ROOT/'build/research/returned-sol-pro-integration-private';audit.mkdir(parents=True,exist_ok=True)
    for name,doc in docs.items():
        p=ROOT/'content'/f'{name}.json';backup=audit/f'{name}-before.json'
        if not backup.exists():backup.write_bytes(p.read_bytes())
        write(p,doc)
    for lang,doc in locales.items():
        p=ROOT/'content/museum-locales'/f'{lang}.json';backup=audit/f'{lang}-before.json'
        if not backup.exists():backup.write_bytes(p.read_bytes())
        write(p,doc)
    # Keep bundled attribution records aligned with corrected images.
    credits_path=ROOT/'content/credits.json'
    credits=read(credits_path)
    affected={(p['collection'],p['entry_id']) for p in read(media)['patches']} if media.exists() else set()
    credits['media']=[r for r in credits['media'] if not (r.get('media_kind')=='image' and (r.get('collection'),r.get('exhibit_id')) in affected)]
    for collection,eid in sorted(affected):
        for image in index[collection][eid].get('images',[]):
            credits['media'].append({'exhibit_id':eid,'collection':collection,'media_kind':'image',**{k:image.get(k,'') for k in ('url','title','width','height','credit','source_page','license','license_url')}})
    backup=audit/'credits-before.json'
    if not backup.exists():backup.write_bytes(credits_path.read_bytes())
    write(credits_path,credits)
    write(audit/'integration.json',report)
    print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in report.items()}))
    return report

if __name__=='__main__':apply()
