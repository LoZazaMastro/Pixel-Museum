"""Resolve game release dates from the release field, excluding source dates.

The output is a separate override: original English narrative, media and third-
party attribution are retained. It does not turn announcements or regional
calendar wrappers into additional releases.
"""
from pathlib import Path
import importlib.util, json, re, sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('release_source', HERE/'major-release-additions.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

def pages_in(value):
    if not isinstance(value, dict):
        return []
    return value.get('query', {}).get('pages', [])

def title_key(value):
    return helper.norm(re.sub(r'\s*\((?:\d{4} )?video game\)$','',value,flags=re.I))

def main():
    catalog = json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']
    pages = {}
    for path in helper.CACHE.glob('*.json'):
        try:
            value = json.loads(path.read_text(encoding='utf8'))
        except Exception:
            continue
        for page in pages_in(value):
            if page.get('revisions') and page['revisions'][0].get('slots'):
                pages[page['pageid']] = page
    target_ids = []
    for entry in catalog:
        if entry['kind'] != 'game':
            continue
        if re.fullmatch(r'wikipedia-\d+', entry['id']):
            target_ids.append(int(entry['id'].split('-')[1]))
    missing = sorted(set(target_ids)-pages.keys())
    if '--offline-only' not in sys.argv:
        for start in range(0, len(missing), 20):
            batch = missing[start:start+20]
            try:
                result = helper.api('https://en.wikipedia.org/w/api.php', {
                    'action':'query', 'pageids':'|'.join(map(str,batch)),
                    'prop':'extracts|revisions', 'exintro':1, 'explaintext':1,
                    'exlimit':'max', 'rvprop':'ids|timestamp|content', 'rvslots':'main'
                }, 'canonical-release-fields')
                for page in pages_in(result):
                    if page.get('revisions') and page['revisions'][0].get('slots'):
                        pages[page['pageid']] = page
            except Exception as error:
                print('Source batch held:', str(error), flush=True)
            print('Original release fields', min(start+20,len(missing)), '/',len(missing),flush=True)
        # Old Playhub rooms have stable editorial IDs rather than Wikipedia
        # page IDs. Resolve their exact titles, then require the original year
        # and a real game article instead of borrowing the first source URL
        # from a multi-game calendar story.
        known_titles={title_key(page['title']) for page in pages.values()}
        unknown_titles=sorted({entry['title'] for entry in catalog if entry['kind']=='game'
            and not re.fullmatch(r'wikipedia-\d+',entry['id']) and title_key(entry['title']) not in known_titles})
        for start in range(0,len(unknown_titles),18):
            try:
                result=helper.api('https://en.wikipedia.org/w/api.php',{
                    'action':'query','titles':'|'.join(unknown_titles[start:start+18]),'redirects':1,
                    'prop':'extracts|revisions','exintro':1,'explaintext':1,'exlimit':'max',
                    'rvprop':'ids|timestamp|content','rvslots':'main'
                },'canonical-release-titles')
                for page in pages_in(result):
                    if page.get('revisions') and page['revisions'][0].get('slots'):pages[page['pageid']]=page
            except Exception as error:print('Original-title batch held:',str(error),flush=True)
            print('Original release titles',min(start+18,len(unknown_titles)),'/',len(unknown_titles),flush=True)
    by_title={}
    for page in pages.values():by_title.setdefault(title_key(page['title']),[]).append(page)
    overrides = {}
    changes = []
    examined = []
    for entry in catalog:
        if entry['kind'] != 'game':
            continue
        pageid = entry.get('provenance', {}).get('page_id') or entry.get('provenance', {}).get('pageid')
        if re.fullmatch(r'wikipedia-\d+',entry['id']):
            pageid = int(entry['id'].split('-')[1])
        page = pages.get(pageid)
        if not page:
            for candidate in by_title.get(title_key(entry['title']),[]):
                lead=candidate.get('extract','').split('\n',1)[0]
                if not re.search(r'\b'+str(entry['year'])+r'\b',lead):continue
                if re.search(r'\b(?:franchise|series of|video game series)\b',lead[:500],re.I):continue
                page=candidate;break
        if not page:
            continue
        date = helper.date_from(page,entry['year'])
        examined.append({'id':entry['id'],'title':entry['title'],'source_article':page['title'],'date':date})
        if date['precision'] != 'day':
            continue
        # A deliberately supplied general-release rule beats a premium-access
        # note even if the latter appears in the source infobox.
        if entry['id'] == 'wikipedia-81179631':
            date = {'month':5,'day':19,'precision':'day','region':''}
        revision = page['revisions'][0]['revid']
        overrides[entry['id']] = {'year':entry['year'],'date':date,
            'sources':[{'title':page['title']+' — original release infobox, Wikipedia revision '+str(revision),
                'url':'https://en.wikipedia.org/w/index.php?oldid='+str(revision),'publisher':'English Wikipedia contributors'}],
            'release_date_audit':{'article_title':page['title'],'revision_id':revision,
                'method':'Release field only, excluding citations, publication dates, explanatory footnotes and later release years.'}}
        old = entry.get('date',{})
        if (old.get('month',0),old.get('day',0)) != (date['month'],date['day']):
            changes.append({'id':entry['id'],'title':entry['title'],'year':entry['year'],'old':old,'new':date,'source_article':page['title']})
    # Polyphony's product page gives the commercial day explicitly. The title
    # refers to the 2001 motor show, not a 2001 game launch.
    overrides['workbook-01-02-gran-turismo-concept'] = {
        'year':2002,'date':{'month':1,'day':1,'precision':'day','region':''},
        'sources':[{'title':'Gran Turismo Concept 2001 TOKYO — original product release date',
            'url':'https://www.gran-turismo.com/jp/products/gtc/','publisher':'Polyphony Digital / Sony Interactive Entertainment'}]}
    # An episodic or cross-platform article can mix public alpha, regional
    # releases and completed editions. These source-reviewed original releases
    # are deliberately explicit rather than the earliest year-matching number.
    canonical = {
        'minecraft': (2011,11,18,'day','Minecraft: original Java full release, excluding Pocket Edition public alphas.'),
        'workbook-04-17-yakuza-6-the-song-of-life': (2016,12,8,'day','Yakuza 6: original Japanese commercial release; 2018 is the later worldwide edition.'),
        'wikipedia-638696': (1983,11,0,'month','Spy Hunter: original North American arcade release; later home ports are not the original launch.'),
        'wikipedia-746221': (1983,2,0,'month','Xevious: original arcade release as dated by the source article; no invented precise day.'),
        'wikipedia-3863276': (1996,12,0,'month','Realms of the Haunting: original European release; March1997 is the later North American release.'),
        'wikipedia-38350849': (2013,1,7,'day','Kentucky Route Zero: Act I starts the original episodic commercial release; Act V completes it in2020.'),
    }
    for entry_id,(year,month,day,precision,note) in canonical.items():
        entry=next((e for e in catalog if e['id']==entry_id),None)
        if not entry:continue
        pageid=int(entry_id.split('-')[1]) if re.fullmatch(r'wikipedia-\d+',entry_id) else None
        page=pages.get(pageid)
        if not page:
            page=next(iter(by_title.get(title_key(entry['title']),[])),None)
        if not page:raise RuntimeError('Missing reviewed source for '+entry_id)
        revision=page['revisions'][0]['revid']
        overrides[entry_id]={'year':year,'date':{'month':month,'day':day,'precision':precision,'region':''},
            'sources':[{'title':page['title']+' — original release infobox, Wikipedia revision '+str(revision),
                'url':'https://en.wikipedia.org/w/index.php?oldid='+str(revision),'publisher':'English Wikipedia contributors'}],
            'release_date_audit':{'article_title':page['title'],'revision_id':revision,'method':note}}
    output = {'schema_version':1,'entries':overrides}
    (HERE/'museum-release-date-corrections.json').write_text(json.dumps(output,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
    report = {'game_entries':sum(e['kind']=='game' for e in catalog),'source_fields_examined':len(examined),
        'exact_release_dates':len(overrides),'changed_dates':changes,'examined':examined,
        'scope_note':'Exact-ID original Wikipedia articles plus explicitly identified standalone source articles. Entries without source-supported days retain honest prior precision; this is not a claim that every old calendar date has been verified.'}
    (ROOT/'build/research/original-release-date-audit.json').write_text(json.dumps(report,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
    print('Release fields examined',len(examined),'exact dates',len(overrides),'changes',len(changes),flush=True)

if __name__ == '__main__':
    main()
