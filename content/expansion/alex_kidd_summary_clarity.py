"""Remove an inherited calendar-production note from Alex Kidd's public summary."""
ENTRY_ID = 'workbook-11-02-alex-kidd-in-miracle-world'
OLD = 'On November 2, 1986, for this editorial exception in the calendar, Alex Kidd in Miracle World is associated with its Japanese debut on the Sega Mark III.'
NEW = 'Alex Kidd in Miracle World is a platform game developed and published by Sega for the Master System.'


def apply(entries):
    matches = [entry for entry in entries if entry['id'] == ENTRY_ID]
    if len(matches) != 1:
        raise ValueError('Alex Kidd summary correction requires exactly one owner')
    owner = matches[0]
    if not owner.get('body') or not owner['body'][0].startswith(NEW + ' '):
        raise ValueError('Alex Kidd existing first-sentence evidence changed')
    if owner.get('summary') not in (OLD, NEW):
        raise ValueError('Alex Kidd summary changed outside the bounded correction')
    changed = owner['summary'] != NEW
    owner['summary'] = NEW
    return {'status': 'PASS', 'entry_id': ENTRY_ID, 'changed': changed,
            'scope': 'Only public summary; verbatim first sentence already in body. No date, paragraph, heading, image, video or other owner changed.'}
