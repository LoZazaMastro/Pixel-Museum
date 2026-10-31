"""Clean presentation labels only, retaining dates, prose and source identities."""
import re

def apply(entries):
    # Explicit event labels only: numeric creative titles such as 2001 remain intact.
    event_titles={
        'Guernica (Picasso)':'Guernica',
        'Z3 (computer)':'Z3',
        'Foundation (Asimov novel)':'Foundation',
        'Dune (novel)':'Dune',
        'Revolver (Beatles album)':'Revolver',
        'Black Sabbath (album)':'Black Sabbath',
        'C (programming language)':'C',
        'Autobahn (album)':'Autobahn',
        'Thriller (album)':'Thriller',
        'Dragon Ball (manga)':'Dragon Ball',
        'Dolly (sheep)':'Dolly',
        'One More Time (Daft Punk song)':'One More Time',
        'Discovery (Daft Punk album)':'Discovery',
        'IPad (1st generation)':'iPad',
        'Rita Levi-Montalcini':'Rita Levi-Montalcini wins the Nobel Prize',
        '1896 Summer Olympics':'Summer Olympics',
        '1906 San Francisco earthquake':'San Francisco earthquake',
        'Wall Street crash of 1929':'Wall Street crash',
        '1936 Summer Olympics':'Summer Olympics',
        'The War of the Worlds (1938 radio drama)':'The War of the Worlds',
        'Civil Rights Act of 1964':'Civil Rights Act',
        'Voting Rights Act of 1965':'Voting Rights Act',
        '1972 Summer Olympics':'Summer Olympics',
        '1973 oil crisis':'Oil crisis',
        '1989 Tiananmen Square protests and massacre':'Tiananmen Square protests and massacre',
        '2004 Indian Ocean earthquake and tsunami':'Indian Ocean earthquake and tsunami',
        '2008 Summer Olympics':'Summer Olympics',
        '2008 United States presidential election':'United States presidential election',
        '2009 swine flu pandemic':'Swine flu pandemic',
        '2012 Summer Olympics':'Summer Olympics',
        'Russo-Ukrainian war (2022–present)':'Russo-Ukrainian war',
        '2024 Summer Olympics':'Summer Olympics',
    }
    changed=[]
    for entry in entries:
        title=entry.get('title','')
        cleaned=re.sub(r' \((?:[0-9]{4} )?film\)$','',title)
        cleaned=event_titles.get(cleaned,cleaned)
        if cleaned==title:
            continue
        entry['title']=cleaned
        entry['story_headings']=[cleaned if heading==title else heading for heading in entry.get('story_headings',[])]
        changed.append({'id':entry['id'],'before':title,'after':cleaned})
    return {'status':'PASS','scope':'film disambiguation, explicit encyclopaedia labels and user-requested event display titles only','changed':changed,'count':len(changed)}
