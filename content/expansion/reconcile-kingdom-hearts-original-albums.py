"""Research only: compare actual public chapter markers with cited album inventories."""
import hashlib
import html
import json
import pathlib
import re
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/kingdom-hearts-complete'


def clean(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', value))).strip()


def norm(value):
    value = unicodedata.normalize('NFKD', value).casefold()
    return re.sub(r'[^a-z0-9]', '', value)


def chapters(video_id):
    record = json.loads((OUT / (video_id + '-actual-publication-research.json')).read_text(encoding='utf-8'))
    publication = record['publication']
    result = []
    for line in publication['shortDescription'].splitlines():
        match = re.match(r'^(\d+:\d+(?::\d+)?)\s+(?:-\s*)?(.+)$', line.strip())
        if not match:
            continue
        timestamp, title = match.groups()
        seconds = 0
        for piece in timestamp.split(':'):
            seconds = seconds * 60 + int(piece)
        result.append({'number': len(result) + 1, 'title': title, 'start_seconds': seconds})
    for index, row in enumerate(result):
        row['end_seconds'] = result[index + 1]['start_seconds'] if index + 1 < len(result) else int(publication['lengthSeconds'])
        row['duration_seconds'] = row['end_seconds'] - row['start_seconds']
        assert row['duration_seconds'] > 0
    return result, record


def kh1_inventory():
    text = (OUT / 'kh1-original-album-secondary.html').read_text(encoding='utf-8')
    result = []
    for table in re.findall(r'<table\b[^>]*>(.*?)</table>', text, re.S):
        header = clean(table[:table.find('</tr>')])
        if not all(word in header for word in ['Track', 'Title', 'Length', 'Arranger', 'Composer']):
            continue
        disc = 1 if not result else 2
        for tr in re.findall(r'<tr\b[^>]*>(.*?)</tr>', table, re.S):
            cells = [clean(td) for td in re.findall(r'<t[dh]\b[^>]*>(.*?)</t[dh]>', tr, re.S)]
            if len(cells) < 5 or not cells[0].isdigit() or not re.match(r'^\d+:\d+$', cells[2]):
                continue
            minute, second = map(int, cells[2].split(':'))
            result.append({'number': len(result) + 1, 'disc': disc, 'disc_track': int(cells[0]),
                           'title': cells[1].strip('"'), 'expected_seconds': minute * 60 + second,
                           'secondary_arranger': cells[3], 'secondary_composer': cells[4]})
    assert len(result) == 76, len(result)
    return result


def kh3_inventory():
    text = (OUT / 'kh3-publisher-original-eight-disc.html').read_text(encoding='utf-8')
    result = []
    for block in re.split(r'<h3 class="disc-no">', text)[1:]:
        disc = int(re.match(r'Disc(\d+)', block).group(1))
        for number, title in re.findall(r'<li><span class="track-no">(\d+)</span>(.*?)</li>', block, re.S):
            result.append({'disc': disc, 'disc_track': int(number), 'title': clean(title),
                           'scope': 'KHIII/Re Mind' if disc <= 7 else 'OTHER GAMES - not KHIII'})
    assert len(result) == 159, len(result)
    return result


def kh2_complete2007_inventory():
    text = (OUT / 'kh-complete2007-secondary.html').read_text(encoding='utf-8')
    result = []
    disc = 0
    for table in re.findall(r'<table\b[^>]*>(.*?)</table>', text, re.S):
        header = clean(table[:table.find('</tr>')])
        if not all(word in header for word in ['Track', 'Title', 'Length']):
            continue
        disc += 1
        for tr in re.findall(r'<tr\b[^>]*>(.*?)</tr>', table, re.S):
            cells = [clean(td) for td in re.findall(r'<t[dh]\b[^>]*>(.*?)</t[dh]>', tr, re.S)]
            if len(cells) < 6 or not cells[0].isdigit() or not re.match(r'^\d+:\d+$', cells[2]):
                continue
            if disc not in [3, 4, 5, 6] and not (disc == 9 and 'HEARTS II FINAL' in cells[3]):
                continue
            minute, second = map(int, cells[2].split(':'))
            result.append({'number': len(result) + 1, 'disc': disc, 'disc_track': int(cells[0]),
                           'title': cells[1].strip(' "'), 'expected_seconds': minute * 60 + second,
                           'game': cells[3], 'secondary_arranger': cells[4], 'secondary_composer': cells[5]})
    assert len(result) == 103, len(result)
    return result


def main():
    kh1, receipt1 = chapters('1xwQs5gKTo4')
    inventory1 = kh1_inventory()
    comparisons = []
    for expected, actual in zip(inventory1, kh1):
        comparisons.append({'expected': expected, 'actual_source_chapter': actual,
                            'duration_delta_seconds': actual['duration_seconds'] - expected['expected_seconds'],
                            'title_exact_normalized': norm(expected['title']) == norm(actual['title'])})
    kh3, receipt3 = chapters('XZMWD-qwwr0')
    inventory3 = kh3_inventory()
    matched = []
    for row in inventory3:
        found = [item for item in kh3 if norm(item['title']) == norm(row['title'])]
        matched.append({'expected': row, 'exact_title_chapters': found})
    report = {
        'publication_status': 'research_only',
        'scope': 'Real publisher/secondary inventories and actual public chapter markers; no admission or audio-master equivalence asserted.',
        'kh1': {'inventory_source': 'https://www.khwiki.com/Kingdom_Hearts_Original_Soundtrack',
                'inventory_source_kind': 'Community album/liner transcription, not publisher-hosted primary',
                'production_roles_source': 'https://www.squareenixmusic.com/albums/k/kingdomhearts.shtml',
                'production_roles_source_kind': 'Independent music reference liner transcription, not official Square Enix',
                'actual_video_id': '1xwQs5gKTo4', 'chapter_count': len(kh1), 'expected_count': len(inventory1),
                'comparisons': comparisons,
                'holds': ['Final Destati source passage is187s versus175s listed originalCD; do not fabricate a shorter cut.',
                          'Secondary PLANITb arranger mismatch: KHwiki namesUtada versus production transcription RussellMcNamara; resolve original liner role.']},
        'kh3': {'inventory_source': 'https://www.jp.square-enix.com/music/en/lineup/item/SQEX-10794-801.html',
                'inventory_source_kind': 'Actual publisher Square Enix eight-disc product tracklist',
                'actual_video_id': 'XZMWD-qwwr0', 'chapter_count': len(kh3),
                'publisher_full_product_tracks': len(inventory3),
                'publisher_kh3_remind_tracks': sum(row['disc'] <= 7 for row in inventory3),
                'publisher_other_game_disc8_tracks': sum(row['disc'] == 8 for row in inventory3),
                'matches': matched,
                'holds': ['Do not attach disc8 other-game music to KHIII.',
                          '139source chapters are not the159item publisher compilation; Japanese/English vocal variants and reprise additions require explicit mapping.',
                          'Disney reprises/Utada themes require actual cue roles, not blanket Shimomura credit.']},
        'source_sha256': {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in [
            'kh1-original-album-secondary.html', 'kh1-original-production-secondary.html', 'kh3-publisher-original-eight-disc.html']},
    }
    kh2, receipt2 = chapters('n_H2iL7Lfeg')
    inventory2 = kh2_complete2007_inventory()
    normalize2 = lambda value: norm(value.replace('[', '-').replace(']', '-').replace('Passion [Instrumental]', 'Passion -KINGDOM Orchestra Instrumental Version-').replace('Passion [Opening Version]', 'Passion -opening version-'))
    kh2_matches = []
    for row in inventory2:
        found = [item for item in kh2 if normalize2(item['title']) == normalize2(row['title'])]
        kh2_matches.append({'expected': row, 'exact_title_chapters': found,
                            'duration_delta_seconds': found[0]['duration_seconds'] - row['expected_seconds'] if len(found) == 1 else None})
    report['kh2'] = {'inventory_source': 'https://www.khwiki.com/Kingdom_Hearts_Original_Soundtrack_Complete',
                     'inventory_source_kind': 'Secondary exact2007 album transcription; original printed booklet scan independently acquired for title/credit corroboration',
                     'source_video_id': 'n_H2iL7Lfeg', 'source_chapters': len(kh2),
                     'kh2_complete2007_base_tracks': sum(row['disc'] != 9 for row in inventory2),
                     'kh2_finalmix2007_bonus_tracks': sum(row['disc'] == 9 for row in inventory2), 'matches': kh2_matches,
                     'scope': 'Research only. 2007 extended official soundtrack versions, not the shorter2006 two-disc edits. Remaining chapter title/duration/context differences require review.'}
    target = OUT / 'original-album-inventory-chapter-reconciliation.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'kh1_inventory': len(inventory1), 'kh1_chapters': len(kh1),
                      'kh1_duration_gaps_over3s': [(row['expected']['number'], row['expected']['title'], row['duration_delta_seconds']) for row in comparisons if abs(row['duration_delta_seconds']) > 3],
                      'kh1_title_differences': [(row['expected']['number'], row['expected']['title'], row['actual_source_chapter']['title']) for row in comparisons if not row['title_exact_normalized']],
                      'kh3_counts': [len(inventory3), len(kh3)],
                      'kh3_missing_exact': [row['expected'] for row in matched if row['expected']['disc'] <= 7 and not row['exact_title_chapters']]}, ensure_ascii=False))
    print(json.dumps({'kh2_2007_expected': len(inventory2), 'kh2_chapters': len(kh2),
                      'kh2_missing_exact': [row['expected'] for row in kh2_matches if not row['exact_title_chapters']],
                      'kh2_duration_gaps': [(row['expected']['title'], row['duration_delta_seconds']) for row in kh2_matches if row['duration_delta_seconds'] is not None and abs(row['duration_delta_seconds']) > 3]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
