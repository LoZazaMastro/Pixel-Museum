"""Join reviewed calendar writing to the same museum subject, retaining event identity.

The published calendar slot is scheduling metadata, never evidence of a release day.
This module is independent of the renderer and does not perform network requests.
"""
from __future__ import annotations
import copy
import datetime
import re
import unicodedata


def apply_revisions(entries, documents, review):
    """Replace only the reviewed 53 templates, preserving their complete origin."""
    by_id = {entry['id']: entry for entry in entries}
    reviewed = {entry['id']: entry for entry in review.get('entries', [])}
    allowed = ('summary', 'body', 'story_headings', 'sources', 'editorial_credit', 'editorial_mode', 'title')
    applied, originals = [], []
    seen = set()
    for document in documents:
        for revision in document.get('entries', []):
            identifier = revision['id']
            if identifier in seen or identifier not in reviewed:
                raise ValueError(f'Duplicate or unreviewed calendar revision: {identifier}')
            seen.add(identifier)
            feature = by_id.get(identifier)
            if feature is None or not feature.get('calendar_only'):
                raise ValueError(f'Calendar revision has no scheduled feature: {identifier}')
            body, headings = revision['body'], revision['story_headings']
            if not 3 <= len(body) <= 4 or len(body) != len(headings):
                raise ValueError(f'Revision must have matched researched chapters: {identifier}')
            if any(not isinstance(p, str) or len(p.split()) < 25 for p in body):
                raise ValueError(f'Revision has empty or fragmentary prose: {identifier}')
            if any(key in revision for key in ('year', 'date', 'calendar', 'linked_exhibit_id', 'models', 'images', 'videos')):
                raise ValueError(f'Editorial revision attempts to change chronology or media: {identifier}')
            if feature['year'] != reviewed[identifier]['year'] or feature.get('calendar') != reviewed[identifier].get('calendar'):
                raise ValueError(f'Original reviewed event anchor has changed: {identifier}')
            originals.append(copy.deepcopy(feature))
            original_title = feature['title']
            for field in allowed:
                if field in revision:
                    feature[field] = copy.deepcopy(revision[field])
            feature['editorial_revision'] = copy.deepcopy(revision.get('revision_audit', {}))
            feature['editorial_revision']['original_record_archive'] = 'content/calendar-template-originals.json'
            if feature['title'] != original_title:
                feature['editorial_revision']['original_title'] = original_title
            applied.append(identifier)
    return applied, originals


def integrate(entries, corrections):
    by_id = {entry['id']: entry for entry in entries}
    date_rows = {row['id']: row for row in corrections.get('overrides', [])}
    date_applied = []
    for identifier, row in date_rows.items():
        entry = by_id.get(identifier)
        if entry is None:
            continue
        if entry['year'] != row['year']:
            raise ValueError(f"Date correction year differs from event: {identifier}")
        date = row['date']
        datetime.date(entry['year'], date['month'], date['day'])
        entry['date'] = copy.deepcopy(date)
        entry['date_provenance'] = {key: copy.deepcopy(row[key]) for key in ('event', 'source', 'verified_date')}
        source = copy.deepcopy(row['source'])
        if source['url'] not in {item['url'] for item in entry.get('sources', [])}:
            entry.setdefault('sources', []).append(source)
        if row.get('note') and row['note'] not in entry.get('factual_note', ''):
            entry['factual_note'] = (entry.get('factual_note', '') + ' ' + row['note']).strip()
        date_applied.append(identifier)

    preserved, merged, separate, quality_review = [], [], [], []
    targets = set()
    known_distinct = {
        'daily-01-12': 'Nintendo Switch presentation',
        'daily-05-17': 'Minecraft: first public version',
        'daily-08-31': 'Command & Conquer Gold: freeware release',
        'daily-09-09': 'PlayStation: North American launch',
    }
    template_markers = ('belongs in this calendar for more than an anniversary',
                        'enters this calendar through concrete design choices')
    for feature in entries:
        if not feature.get('calendar_only'):
            continue
        target_id = feature.get('linked_exhibit_id')
        linked = by_id.get(target_id)
        if linked is None:
            continue
        # Object/media identity can be shared by several events. It is not a
        # reason to overwrite a Japanese launch with a later US launch or a reveal.
        feature['images'] = copy.deepcopy(linked.get('images', []))
        feature['models'] = copy.deepcopy(linked.get('models', []))
        feature['videos'] = copy.deepcopy(linked.get('videos', []))
        def title_key(value):
            return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower())
        reviewed_title_correction = feature.get('editorial_revision', {}).get('original_title') == linked['title']
        distinct = (feature['id'] in known_distinct or feature['year'] != linked['year']
                    or (title_key(feature['title']) != title_key(linked['title']) and not reviewed_title_correction))
        if distinct:
            feature['calendar_link_provenance'] = {'original_linked_exhibit_id': target_id,
                'reason': 'A separate historical event; neither its date nor its narrative replaces the canonical event.'}
            feature['linked_exhibit_id'] = ''
            feature['title'] = known_distinct.get(feature['id'], feature['title'])
            if target_id not in feature.setdefault('related_ids', []):
                feature['related_ids'].append(target_id)
            separate.append({'id': feature['id'], 'year': feature['year'], 'related_id': target_id,
                             'canonical_year': linked['year']})
            continue
        if target_id in targets:
            raise ValueError(f"Multiple calendar editions would overwrite {target_id}")
        targets.add(target_id)
        # Do not promote known source fallback boilerplate over a real biography.
        intro = feature.get('body', [''])[0] if feature.get('body') else ''
        if any(marker in intro for marker in template_markers):
            feature['editorial_status'] = 'source_template_requires_factual_rewrite'
            quality_review.append({'id': feature['id'], 'linked_exhibit_id': target_id,
                'reason': 'Generic calendar template is not promoted over canonical text; source retained for revision.'})
            continue
        preserved.append(copy.deepcopy(linked))
        for field in ('body', 'story_headings', 'subtitle', 'editorial_credit'):
            if field in feature:
                linked[field] = copy.deepcopy(feature[field])
        if feature.get('editorial_revision'):
            linked['summary'] = feature['summary']
            linked['editorial_revision'] = copy.deepcopy(feature['editorial_revision'])
            if reviewed_title_correction:
                linked['title'] = feature['title']
        linked['editorial_mode'] = 'calendar_feature_story'
        linked['calendar_editorial'] = {'source_feature_id': feature['id'],
            'schedule': copy.deepcopy(feature.get('calendar', {})),
            'provenance': copy.deepcopy(feature.get('provenance', {})),
            'original_record_archive': 'content/calendar-editorial-originals.json'}
        source_urls = {source['url'] for source in linked.get('sources', [])}
        for source in feature.get('sources', []):
            if source['url'] not in source_urls:
                linked.setdefault('sources', []).append(copy.deepcopy(source))
                source_urls.add(source['url'])
        for related in feature.get('related_ids', []):
            if related != linked['id'] and related not in linked.setdefault('related_ids', []):
                linked['related_ids'].append(related)
        if target_id in date_rows:
            feature['date'] = copy.deepcopy(linked['date'])
            feature['date_provenance'] = copy.deepcopy(linked['date_provenance'])
        merged.append({'id': target_id, 'feature_id': feature['id'], 'year': linked['year']})
    return {'merged': merged, 'separate_events': separate, 'needs_editorial_review': quality_review,
            'verified_dates_applied': date_applied}, preserved
