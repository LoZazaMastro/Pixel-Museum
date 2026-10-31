"""Authoritative exact annual-sports exclusions; source artifacts stay archived."""
import json,re,hashlib
from pathlib import Path

def policy(root):
    p=Path(root)/'content/expansion/user-sports-exclusions.json'
    if not p.exists():return {'rows':[],'exceptions':[],'annual_patterns':[]}
    rules=json.loads(p.read_text(encoding='utf8'))
    assert hashlib.sha256((Path(root)/rules['archive_path']).read_bytes()).hexdigest()==rules['archive_sha256'],'Excluded original archive changed'
    return rules

def excluded_ids(root):
    selected=json.loads((Path(root)/'content/expansion/user-selected-game-exclusions.json').read_text(encoding='utf8'))
    return {row['id'] for row in policy(root)['rows']} | {row['id'] for row in selected['rows']}

def apply(entries,root):
    rules=policy(root);guards={row['id']:row for row in rules['rows']};exceptions={row['id'] for row in rules['exceptions']};removed=[]
    assert not exceptions.intersection(guards)
    for entry in entries:
        guard=guards.get(entry['id'])
        if guard:
            assert all(entry.get(key)==guard[key] for key in ('title','year','date')),'Sports exclusion identity drift: '+entry['id']
            removed.append({key:entry[key] for key in ('id','title','year','date')})
        elif entry['id'] not in exceptions and any(re.search(pattern,entry['title'],re.I) for pattern in rules['annual_patterns']):
            raise ValueError('Annual-sports identity requires inventory before admission: '+entry['id']+' '+entry['title'])
    entries[:]=[entry for entry in entries if entry['id'] not in guards]
    return {'status':'PASS_EXACT_REQUESTED_ANNUAL_SPORTS_EXCLUSIONS','removed':removed,'retained_exceptions':[entry['id'] for entry in entries if entry['id'] in exceptions],'assets_deleted':False}

def prune_references(entries,root):
    forbidden=excluded_ids(root);cleaned=[]
    for entry in entries:
        for owner in [entry]+entry.get('editorial_features',[]):
            old=owner.get('related_ids',[]);new=[key for key in old if key not in forbidden]
            if new!=old:owner['related_ids']=new;cleaned.append(owner['id'])
            for key in ('linked_exhibit_id','canonical_entry_id','story_entry_id'):
                assert owner.get(key) not in forbidden,'Dependent alias requires exact inventory: '+owner['id']+' '+key
    assert not forbidden.intersection(e['id'] for e in entries)
    return {'status':'PASS_NO_ORPHAN_EXCLUDED_SPORTS_REFERENCES','changed_owners':cleaned}
