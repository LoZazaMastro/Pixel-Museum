"""Apply explicitly reviewed release dates to unchanged English references."""
from __future__ import annotations

import copy
import datetime
import hashlib


def apply(entries, document):
    lookup = {entry['id']: entry for entry in entries}
    applied = []
    for row in document.get('entries', []):
        entry = lookup.get(row['entry_id'])
        if not entry or entry.get('editorial_mode') != 'reference' or entry.get('calendar_only'):
            raise ValueError('Release-date target is not an independent reference')
        hashes = [hashlib.sha256(text.encode('utf-8')).hexdigest() for text in entry['body']]
        if hashes != row['body_sha256'] or entry.get('date') != row['expected_date']:
            raise ValueError('Release-date source or existing date changed')
        date = row['date']
        if (date.get('precision') != 'day' or entry['year'] != row['year']
                or row['expected_date'].get('precision') != 'year'):
            raise ValueError('Release-date scope or year changed')
        datetime.date(row['year'], date['month'], date['day'])
        index = row['source_paragraph']
        if index not in range(len(entry['body'])) or not row.get('source_url') or not date.get('region'):
            raise ValueError('Release date lacks its exact source or regional scope')
        entry['date'] = copy.deepcopy(date)
        entry['date_provenance'] = {
            'source_url': row['source_url'], 'source_paragraph': index,
            'source_paragraph_sha256': hashes[index],
            'event': row['event'], 'review': 'reference-release-date-review.json',
            'body_unchanged': True,
        }
        applied.append({'entry_id': entry['id'], 'date': copy.deepcopy(date)})
    return {'applied': applied, 'date_count': len(applied), 'body_or_year_changes': 0}
