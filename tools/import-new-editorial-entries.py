"""Import reviewed new articles and their translations, preserving live content."""
from pathlib import Path
import argparse,copy,importlib.util,json
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('files',nargs='+');args=p.parse_args()
spec=importlib.util.spec_from_file_location('editorial_helpers',ROOT/'tools/apply-editorial-recovery-patches.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
catalog=h.read(ROOT/'content/catalog.json')
locales={l:h.read(ROOT/f'content/museum-locales/{l}.json')for l in h.LANGS[1:]}
known={e['id']:e for e in catalog['entries']};added=[];skipped=[]
for name in args.files:
    path=ROOT/name;source=h.read(path)
    assert source.get('completed') is True,(name,'not finished')
    for record in source['new_entries']:
        eid=record['id'];main=record['main'];assert set(main)==set(h.LANGS)
        count=len(main['en']['cards']);assert count>=6,(eid,'short article')
        assert len(main['en']['summary'].split())<=55,(eid,'long timeline summary')
        for l in h.LANGS:
            assert len(main[l]['cards'])==count
            assert all(c['heading'].strip()and c['text'].strip()for c in main[l]['cards'])
        if eid in known:
            assert known[eid]['body']==[c['text']for c in main['en']['cards']],(eid,'existing content differs')
            skipped.append(eid);continue
        row={k:copy.deepcopy(v)for k,v in record.items()if k!='main'}
        nearest=min(catalog['entries'],key=lambda e:abs(e['year']-row['year']))
        row.update(era_id=nearest['era_id'],calendar_only=False,layout='editorial',featured=False,
                   tags=copy.deepcopy(record.get('tags', ['games'] if record['kind']=='game' else ['industry','press'])),related_ids=[],videos=[],models=[],images=[],
                   editorial_mode='original',editorial_credit='Pixel Museum / Andrea Sgarro. Original editorial text based on the credited sources.')
        for l in h.LANGS:
            text=main[l];target=row if l=='en'else locales[l]['entries'].setdefault(eid,{})
            target.update(title=text['title'],subtitle=text.get('subtitle',''),summary=text['summary'],
                          body=[c['text']for c in text['cards']],story_headings=[c['heading']for c in text['cards']])
        h.refresh(row,locales,path.relative_to(ROOT).as_posix())
        catalog['entries'].append(row);known[eid]=row;added.append(eid)
catalog['entries'].sort(key=lambda e:(e['year'],e.get('date',{}).get('month')or 0,e.get('date',{}).get('day')or 0))
h.write(ROOT/'content/catalog.json',catalog)
for l,d in locales.items():h.write(ROOT/f'content/museum-locales/{l}.json',d)
receipt={'files':args.files,'added':added,'already_present':skipped,'media_queued_separately':True}
target=ROOT/'build/research/editorial-resume-20261030'/('new-entries-'+h.digest(args.files)[:10]+'.json')
h.write(target,receipt);print(json.dumps(receipt))
