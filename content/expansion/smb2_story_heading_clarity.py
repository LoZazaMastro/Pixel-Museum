"""Give the two existing Western SMB2 chapters distinct, descriptive headings."""
ENTRY_ID = 'wikipedia-141869'
OLD = ['Super Mario Bros. 2', 'Super Mario Bros. 2']
NEW = ['A different sequel for Western audiences', 'Super Mario USA and the later remakes']


def apply(entries):
    matches = [entry for entry in entries if entry['id'] == ENTRY_ID]
    if len(matches) != 1:
        raise ValueError('SMB2 heading clarification requires exactly one owner')
    owner = matches[0]
    if len(owner.get('body', [])) != 2 or 'Doki Doki Panic' not in owner['body'][0] or 'Super Mario USA' not in owner['body'][1]:
        raise ValueError('SMB2 existing two-chapter evidence changed')
    if owner.get('story_headings') not in (OLD, NEW):
        raise ValueError('SMB2 story headings changed outside bounded clarification')
    changed = owner['story_headings'] != NEW
    owner['story_headings'] = NEW[:]
    return {'status': 'PASS', 'entry_id': ENTRY_ID, 'changed': changed,
            'scope': 'Two chapter headings only. Distinct descriptions of existing paragraphs replace repeated game title. No body, date, summary, image, video or other owner changes.'}
