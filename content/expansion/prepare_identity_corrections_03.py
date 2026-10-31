"""Prepare a review declaration only; never modify catalogue, locales or media.

The English and seven translated Playhub editions are archived verbatim. Each
partition refers to original body indices (index zero is the introduction).
Wikipedia paragraphs retain immutable revision/contributor/licence attribution.
"""
from pathlib import Path
import copy
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'expansion/calendar-identity-corrections-03.json'
SOURCE = Path(r'F:\Playhub\Plugin\Playhub\catalog\on-this-day.json')
LANGUAGES = ('en', 'it', 'es', 'fr', 'de', 'pt', 'ru', 'uk')
LICENSE = 'https://creativecommons.org/licenses/by-sa/4.0/'

# These are reviewed semantic identities, not inferred retail anniversaries.
# title, kind, year, source article, full original body indices, calendar context.
CASES = {
 'daily-02-02': [('Frogger', 'game', 1981, 'Frogger', None, 'World Wetlands Day thematic scheduling')],
 'daily-03-14': [('The Witness', 'game', 2016, 'The Witness (2016 video game)', None, 'International Day of Mathematics thematic scheduling')],
 'daily-03-15': [('Homefront', 'game', 2011, 'Homefront (video game)', [1,2,3], 'Homefront release discussion'), ('Robin Hunicke', 'person', 1973, 'Robin Hunicke', [0,4,5,6], 'March15 birth commemoration;1973 is not a production date')],
 'daily-03-17': [('Folklore', 'game', 2007, 'Folklore (video game)', None, "St Patrick's Day thematic scheduling")],
 'daily-03-18': [('Terra Nil', 'game', 2023, 'Terra Nil', None, 'Global Recycling Day thematic scheduling')],
 'daily-04-06': [("Conker's Bad Fur Day", 'game', 2001, "Conker's Bad Fur Day", [1,2,3,4,5,6], 'European release discussion; primary regional-date review remains separate'), ('Wii Sports', 'game', 2006, 'Wii Sports', [0,7,8,9], 'International Day of Sport for Development and Peace thematic scheduling')],
 'daily-04-15': [('Chicory: A Colorful Tale', 'game', 2021, 'Chicory: A Colorful Tale', None, 'World Art Day thematic scheduling')],
 'daily-04-17': [('Tarn Adams', 'person', 1978, 'Tarn Adams', None, 'April17 birth commemoration;1978 is not Dwarf Fortress production date')],
 'daily-04-18': [("Assassin's Creed II", 'game', 2009, "Assassin's Creed II", None, 'International Day for Monuments and Sites thematic scheduling')],
 'daily-04-22': [('SimCity 2000', 'game', 1993, 'SimCity 2000', None, 'Earth Day thematic scheduling')],
 'daily-04-23': [('Pentiment', 'game', 2022, 'Pentiment (video game)', None, 'World Book and Copyright Day thematic scheduling')],
 'daily-05-02': [('DAVE THE DIVER', 'game', 2023, 'Dave the Diver', None, 'World Tuna Day thematic scheduling;2023 full release separate from2022 Early Access')],
 'daily-05-05': [('Mystery House', 'game', 1980, 'Mystery House', None, 'Original narrative claims May5,1980; precise retail date requires independent primary review')],
 'daily-05-16': [('Alan Wake', 'game', 2010, 'Alan Wake', None, 'International Day of Light thematic scheduling')],
 'daily-05-20': [('Bee Simulator', 'game', 2019, None, None, 'World Bee Day thematic scheduling;2019 first editions separate from2020 Steam release')],
 'daily-06-05': [('Eco', 'game', 2018, 'Eco (2018 video game)', None, 'World Environment Day thematic scheduling;2018 Steam Early Access year')],
 'daily-07-02': [('X-COM: UFO Defense', 'game', 1994, 'UFO: Enemy Unknown', None, 'World UFO Day thematic scheduling;1994 secondary-reference year, not verified exact retail day')],
 'daily-08-22': [('Never Alone', 'game', 2014, 'Never Alone (video game)', None, 'World Folklore Day thematic scheduling; preserve distinct May21 original edition')],
 'daily-08-25': [('GoldenEye 007', 'game', 1997, 'GoldenEye 007', None, 'Original narrative claims North American August25 release; primary regional-date review separate')],
 'daily-08-26': [('Nintendogs', 'game', 2005, 'Nintendogs', None, 'National Dog Day thematic scheduling;2004 in original intro dates observance, not game')],
 'daily-09-01': [('Metal Gear Solid V: The Phantom Pain', 'game', 2015, 'Metal Gear Solid V: The Phantom Pain', None, 'Regional release discussion; narrative distinguishes September1 from Japan/Asia September2')],
 'daily-09-04': [('Dune 2000', 'game', 1998, 'Dune 2000', None, 'North American Windows release discussion; primary exact-date review separate')],
 'daily-09-05': [('Yakuza', 'game', 2005, 'Yakuza (video game)', None, 'North American2006 regional arrival; canonical original Japanese game remains2005, distinct December8 edition preserved')],
 'daily-09-06': [('Shenmue II', 'game', 2001, 'Shenmue II', None, 'Japanese Dreamcast release discussion; primary exact-date review separate')],
}

DISPLACED = {
 'daily-02-02':'Persona 3 Reload', 'daily-03-14':'Dark Souls II',
 'daily-03-15':"Tom Clancy's The Division 2", 'daily-03-17':'Grand Theft Auto: Chinatown Wars',
 'daily-03-18':'Metal Gear Solid V: Ground Zeroes', 'daily-04-06':'Oddworld: Soulstorm',
 'daily-04-15':'Skate 3', 'daily-04-17':'Yakuza 6: The Song of Life',
 'daily-04-18':'Minecraft Legends', 'daily-04-22':'Nier (video game)',
 'daily-04-23':"Don't Starve", 'daily-05-02':'Age of Wonders 4',
 'daily-05-05':'Wolfenstein 3D', 'daily-05-16':'Terraria',
 'daily-05-20':'Transistor (video game)', 'daily-06-05':'Tabletop Simulator',
 'daily-07-02':'Final Fantasy XIV: Shadowbringers', 'daily-08-22':'Uncharted: The Lost Legacy',
 'daily-08-25':'Psychonauts 2', 'daily-08-26':'Super Mario Sunshine',
 'daily-09-01':'Mad Max (2015 video game)', 'daily-09-04':"Tony Hawk's Pro Skater 1 + 2",
 'daily-09-05':'Test Drive Unlimited', 'daily-09-06':'Starfield (video game)',
}

REFERENCE_HEADINGS = {
 'daily-02-02':['The Dark Hour returns','Rebuilding the cast, art and sound'],
 'daily-03-14':['An undead traveller in Drangleic','Release and a disputed difficulty'],
 'daily-03-15':['Rebuilding Washington after Green Poison','An endgame built across studios'],
 'daily-03-17':["Huang Lee's route through Liberty City",'Touch controls and a trading economy'],
 'daily-03-18':['Snake at Camp Omega','A prologue released on its own'],
 'daily-04-06':["Abe's story rebuilt for Soulstorm"],
 'daily-04-15':['A team in Port Carverton','Glitches, videos and a later revival'],
 'daily-04-17':['From the Japanese launch to Western editions'],
 'daily-04-18':['Minecraft becomes an action-strategy game','Platforms, release and the end of development'],
 'daily-04-22':['The original and the 2021 remaster','Reception of two editions'],
 'daily-04-23':['A survival game across platforms','Wilson and the Constant'],
 'daily-05-02':['A new turn in the Age of Wonders series'],
 'daily-05-05':['Escaping Castle Wolfenstein','From an engine experiment to shareware'],
 'daily-05-16':['A world to explore, fight and reshape','A small team and years of updates'],
 'daily-05-20':['Supergiant returns with Transistor','Red, the Process and a changing combat rhythm'],
 'daily-06-05':['Tabletop games inside a physics sandbox'],
 'daily-07-02':['The third expansion and its production team','Restoring a world on the First'],
 'daily-08-22':['Chloe and Nadine in the Western Ghats','Building a different Uncharted partnership'],
 'daily-08-25':['Raz returns in a new Psychonauts adventure','A mystery inside other minds'],
 'daily-08-26':['Nintendo returns to three-dimensional Mario','Cleaning Isle Delfino with F.L.U.D.D.'],
 'daily-09-01':['Building the Magnum Opus','Reworking a linear project into an open world'],
 'daily-09-04':['Two skateboarding games rebuilt','Reception and a later successor'],
 'daily-09-05':["An open-road version of Oʻahu",'Sequels and a later reboot'],
 'daily-09-06':['An expedition across planetary systems','A new setting for the Creation Engine'],
}

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def era(year):
    if year < 1970: return 'origins'
    if year < 1980: return 'public-play'
    if year < 1990: return 'personal'
    if year < 2000: return 'dimensions'
    if year < 2010: return 'connected'
    if year < 2020: return 'everywhere'
    return 'living-history'

def paragraphs(page):
    return [p.strip() for p in page['extract'].split('\n') if p.strip()]

def wiki_evidence(page, cache_path):
    rev = page['revisions'][0]
    assert page.get('pageid') and rev.get('revid') and rev.get('sha1')
    url = page['canonicalurl']
    return dict(title=page['title'], page_id=page['pageid'], revision_id=rev['revid'],
        revision_timestamp=rev['timestamp'], revision_sha1=rev['sha1'],
        immutable_url=f"https://en.wikipedia.org/w/index.php?oldid={rev['revid']}",
        article_url=url, contributors_url=url+'?action=history',
        license='CC BY-SA 4.0',license_url=LICENSE,
        cache_file=str(cache_path.relative_to(ROOT)),cache_sha256=sha(cache_path),
        extract_sha256=hashlib.sha256(page['extract'].encode()).hexdigest(),
        verification_scope='Exact article identity and attributed revision snapshot; not independent primary-source validation of every assertion.')

def restored_reference(identifier, title, year, page, cache_path, selected):
    ps = paragraphs(page)
    body = [ps[i] for i in selected]
    evidence = wiki_evidence(page,cache_path)
    notice = (f"Selected complete English introduction paragraphs from '{page['title']}', "
        'by Wikipedia contributors, under CC BY-SA 4.0. Selected paragraph text is unchanged; selection and headings are editorial.')
    attr = dict(text=notice,source_url=evidence['immutable_url'],article_url=evidence['article_url'],
        contributors_url=evidence['contributors_url'],license='CC BY-SA 4.0',license_url=LICENSE,
        revision_id=evidence['revision_id'],revision_timestamp=evidence['revision_timestamp'],
        changes='Selected complete source paragraphs in original order; plain-text extraction; editorial headings. No sentence rewriting.')
    headings = ['Reference introduction'] + [f'Reference context {i+1}' for i in range(1,len(body))]
    if title.startswith('NieR Replicant'):
        headings = ['The original and the2021 remaster','Reception of the original and remaster'][:len(body)]
    return dict(id=identifier,title=title,year=year,kind='game',era_id=era(year),
        date=dict(month=0,day=0,precision='year',region='Reference year only; original calendar slot does not prove a retail day.'),
        subtitle='From the reference collection',summary=re.split(r'(?<=[.!?])\s+',ps[0])[0],
        body=body,story_headings=headings,layout='essay',featured=False,
        tags=['reference','Wikipedia'],related_ids=[],images=[],videos=[],models=[],
        editorial_mode='reference',editorial_credit=notice,attribution=attr,
        provenance=dict(provider='English Wikipedia',page_id=page['pageid'],article_title=page['title'],
            source_revision=evidence['revision_id'],retrieved='2026-10-21',
            selected_intro_paragraph_indices=selected,opaque_museum_id_retained=identifier.startswith('workbook-')),
        sources=[dict(title=page['title']+' — immutable article revision',url=evidence['immutable_url'],publisher='English Wikipedia contributors'),
            dict(title='Contributors and article history',url=evidence['contributors_url'],publisher='English Wikipedia contributors'),
            dict(title='Creative Commons Attribution-ShareAlike 4.0',url=LICENSE,publisher='Creative Commons')],
        factual_note='An unrelated imported narrative is moved to its actual subject. This reference restores the original destination without transferring the unrelated text or images. Primary historical, prose-quality and media reviews remain separate.')

def main():
    source = read(SOURCE)
    original = {e['theme']['id']:e for e in source['editions']['entries']}
    imported_doc = read(ROOT/'expansion/calendar-features.json')
    imported = {e['id']:e for e in imported_doc['entries']}
    queue_doc = read(ROOT/'editorial/playhub-identity-review-queue.json')
    queue = {e['edition_id']:e for e in queue_doc['editions']}
    current_doc = read(ROOT/'catalog.json')
    current = {e['id']:e for e in current_doc['entries']}
    cache = ROOT/'expansion/wikipedia-cache/identity-review-03-verified-pages.json'
    wiki = {p['title']:(p,cache) for p in read(cache)['pages'] if not p.get('missing')}
    for filename in ('identity-review-03-eco-corrected.json','identity-review-03-mixed-subjects.json'):
        f=cache.with_name(filename)
        for page in read(f)['response']['query']['pages']:
            wiki[page['title']] = (page,f)
    records=[]
    for edition_id,parts in CASES.items():
        old = imported[edition_id]
        q = queue[edition_id]
        source_entry = original[q['source_record_id']]
        theme=source_entry['theme']
        assert digest(old['body']) == q['published_english_body_sha256']
        assert digest(old['story_headings']) == q['published_english_headings_sha256']
        language_archives={}
        for lang in LANGUAGES:
            body=[theme['intro'][lang]]+[c['body'][lang] for c in theme['chapters']]
            headings=[theme['title'][lang]]+[c['title'][lang] for c in theme['chapters']]
            assert len(body)==len(old['body'])==len(headings)
            if lang=='en':assert body==old['body'] and headings==old['story_headings']
            baseline=q['locale_reference_rows'][lang]
            assert digest(body)==baseline['body_sha256'] and digest(headings)==baseline['headings_sha256'],(edition_id,lang)
            language_archives[lang]=dict(body=body,story_headings=headings,
                body_sha256=digest(body),headings_sha256=digest(headings),
                paragraph_sha256=[hashlib.sha256(s.encode()).hexdigest() for s in body])
        proposed_parts=[]
        used=[]
        for title,kind,year,article,indices,context in parts:
            indices=list(range(len(old['body']))) if indices is None else indices
            used.extend(indices)
            found=[e for e in current.values() if not e.get('calendar_only') and e['title'].casefold()==title.casefold()]
            if title=='DAVE THE DIVER':found=[e for e in current.values() if not e.get('calendar_only') and e['title'].lower()=='dave the diver']
            if article:
                page,cp=wiki[article]
                evidence=wiki_evidence(page,cp)
                target_id=found[0]['id'] if found else 'wikipedia-'+str(page['pageid'])
            else:
                target_id='bee-simulator'
                evidence=dict(title='Bigben publisher release announcement',url='https://bigben-group.com/news/last-news/wrc-8-paranoia-happiness-is-mandatory-and-bee-simulator-will-make-their-debut-exclusively-on-the-epic-games-store/',
                    publisher='Bigben',published='2019-08-26',checked='2026-10-21',
                    locator='Publisher announces Bee Simulator PC debut November14,2019. Steam lists November17,2020; these are different editions, not a contradiction to erase.',
                    verification_scope='First-party publication establishes2019 edition; exact regional first-release dates remain separate. No English Wikipedia article found.')
            projected_locales={lang:dict(body=[v['body'][i] for i in indices],story_headings=[v['story_headings'][i] for i in indices],
                body_sha256=digest([v['body'][i] for i in indices]),headings_sha256=digest([v['story_headings'][i] for i in indices]))
                for lang,v in language_archives.items()}
            existing=found[0] if found else None
            proposed_parts.append(dict(target_id=target_id,title=title,kind=kind,proposed_historical_year=year,
                canonical_original_year=year,
                calendar_edition_anchor_year=2006 if edition_id=='daily-09-05' else year,
                year_context='birth commemoration, not production year' if kind=='person' else 'Original game or named full-release edition year; exact regional dates remain separately reviewed',
                source_body_indices=indices,source_heading_indices=indices,
                exact_source_locales=projected_locales,
                existing_destination=copy.deepcopy(existing),
                application_recommendation='Attach this complete original edition separately; never overwrite the destination existing distinct prose' if existing else 'Create a distinct destination using these exact original sections and their source attribution',
                calendar_event_semantics=context,subject_evidence=evidence,
                source_policy='Keep every original source URL in the archive; runtime source lists require actual-subject review and may only add verified identity evidence. Do not silently relabel wrong-game sources.',
                media_policy='Do not transfer any inherited image, video, model, soundtrack or reference label automatically. All require exact subject/version review.',
                proposed_media=dict(images=[],videos=[],models=[])))
        assert sorted(used)==list(range(len(old['body']))) and len(used)==len(set(used)),edition_id
        displaced_title=DISPLACED[edition_id]
        page,cp=wiki[displaced_title]
        old_id=old.get('linked_exhibit_id')
        restore_id=old_id or 'wikipedia-'+str(page['pageid'])
        title=old['title'] if old_id else displaced_title
        year=old['year'] if old_id else (2019 if edition_id=='daily-03-15' else 2021)
        ps=paragraphs(page)
        selected=([0,3] if edition_id=='daily-04-22' and len(ps)>3 else list(range(min(2,len(ps)))))
        reference=restored_reference(restore_id,title,year,page,cp,selected)
        reference['story_headings']=REFERENCE_HEADINGS[edition_id]
        assert len(reference['story_headings'])==len(reference['body']),edition_id
        if edition_id=='daily-04-22':
            reference['summary']=ps[0][ps[0].index('A remaster of the Replicant version called'):]
            reference['factual_note']+=' The English Wikipedia title redirects to the 2010 original; the selected complete paragraphs explicitly identify the 2021 Replicant remaster. Do not imply the remake was developed by Cavia in 2021.'
        if edition_id=='daily-04-17':
            # The source's second sentence calls this the final main game with
            # Kiryu as primary protagonist. SEGA explicitly identifies him as
            # a later dual protagonist in Infinite Wealth. Omit that complete
            # sentence, retaining exact surviving source sentence text.
            sentences=re.split(r'(?<=[.!?])\s+',ps[0])
            assert 'final main game' in sentences[1] and len(sentences)==5
            kept=[0,2,3,4]
            reference['body']=[' '.join(sentences[i] for i in kept)]
            reference['provenance']['selected_intro_sentence_indices']={'0':kept}
            notice=(f"Selected unchanged English sentences from '{page['title']}', by Wikipedia contributors, under CC BY-SA 4.0. "
                'One complete unsupported final-protagonist sentence is omitted; editorial selection and heading are identified.')
            reference['editorial_credit']=notice
            reference['summary']=sentences[2]
            reference['attribution']['text']=notice
            reference['attribution']['changes']='Introduction paragraph0 sentences0,2,3,4 retained verbatim in source order; sentence1 omitted because current SEGA evidence identifies Kiryu as a later dual protagonist. Editorial heading added.'
            reference['factual_note']+=' The2018 destination is the Western regional release context; the reference also describes the earlier2016 Japanese release. The source final-protagonist sentence is excluded, not silently rewritten.'
            reference['sources'].append(dict(title='Like a Dragon: Infinite Wealth Out Now!',url='https://www.sega.co.jp/en/release/240126_1.html',publisher='SEGA CORPORATION',checked='2026-10-21',locator='January26,2024 release announcement explicitly identifies Ichiban Kasuga and Kazuma Kiryu as dual protagonists.'))
        if edition_id=='daily-07-02':
            reference['sources'].append(dict(title='FINAL FANTASY XIV for Nintendo Switch2 Launches August4!',url='https://na.finalfantasyxiv.com/lodestone/topics/detail/58ad66d20503b1387fe14f88c6b9df605549daa5?pubDate=20260804',publisher='Square Enix / The Lodestone',checked='2026-10-21',locator='Current official announcement confirms August4,2026 Switch2 release; do not remove the later-platform fact merely because older background knowledge predates it.'))
        if edition_id=='daily-09-01':
            # Warner Bros. is an abbreviation, not the end of this sentence.
            reference['summary']=ps[0].split('Interactive Entertainment.',1)[0]+'Interactive Entertainment.'
        if edition_id=='daily-09-05':
            old_phrase='with Atari Melbourne House developed the PlayStation 2 and PlayStation Portable versions'
            new_phrase='with Atari Melbourne House developing the PlayStation 2 and PlayStation Portable versions'
            require_count=sum(b.count(old_phrase) for b in reference['body'])
            assert require_count==1
            original_selected=copy.deepcopy(reference['body'])
            reference['body']=[b.replace(old_phrase,new_phrase) for b in reference['body']]
            reference['summary']=reference['summary'].replace(old_phrase,new_phrase)
            reference['provenance']['mechanical_replacements']=[dict(old=old_phrase,new=new_phrase,occurrences=1,reason='Correct malformed participial clause in copied source; no change of developer attribution or platform scope.')]
            reference['provenance']['selected_source_body_before_mechanical_correction']=original_selected
            reference['provenance']['selected_source_body_sha256']=digest(original_selected)
            reference['provenance']['corrected_body_sha256']=digest(reference['body'])
            notice=(f"Selected English introduction paragraphs from '{page['title']}', by Wikipedia contributors, under CC BY-SA 4.0. "
                'One explicitly recorded grammatical correction changes developed to developing; the original selected text is archived. Editorial headings are added.')
            reference['editorial_credit']=notice
            reference['attribution']['text']=notice
            reference['attribution']['changes']='Complete source paragraphs selected in original order; one participial-clause correction: with Atari Melbourne House developed → with Atari Melbourne House developing. Original text, exact replacement and before/after hashes retained in provenance. Editorial headings added.'
        records.append(dict(edition_id=edition_id,status='prepared_pending_root_review_not_applied',
            correction_kind='mixed_original_sections' if len(parts)>1 else 'whole_subject_mapping',
            source_record_id=q['source_record_id'],source_body_sha256=digest(old['body']),
            source_headings_sha256=digest(old['story_headings']),archived_published_edition=copy.deepcopy(old),
            archived_original_theme=copy.deepcopy(theme),source_locale_archives=language_archives,
            original_anniversary=copy.deepcopy(source_entry['anniversary']),
            wrong_metadata_title=old['title'],wrong_metadata_year=old['year'],
            wrong_canonical_id=old_id,calendar_slot_unchanged=copy.deepcopy(old['calendar']),
            proposed_calendar_historical_year=None if len(parts)>1 else (2006 if edition_id=='daily-09-05' else parts[0][2]),
            calendar_year_policy='Mixed original subjects have distinct year anchors; root must explicitly decide calendar presentation without inventing one common historical event.' if len(parts)>1 else ('September5 edition retains Western regional2006 context while original Yakuza canonical remains2005.' if edition_id=='daily-09-05' else 'Use the reviewed actual narrative subject year; scheduled day is not release-date evidence.'),
            current_master_observation=copy.deepcopy(current[edition_id]),
            proposed_partitions=proposed_parts,
            restored_original_destination=reference,
            restored_reference_source=wiki_evidence(page,cp),
            displaced_destination_recommendation='Restore this opaque ID with an attributed correct-game reference, clear unrelated locale overlays and archive their original strings' if old_id else 'No opaque canonical ID exists for this composite; add this separate correct-game reference if no duplicate destination is found',
            locale_migration_policy='Daily-edition translated body/headings remain exact. Move old canonical overlays with the original story, archive old keys, and never apply their unrelated paragraphs to the restored correct-game reference. New reference translations require separate reviewed overlays.',
            historical_signoff=False,media_signoff=False))
    document=dict(schema_version=1,reviewed='2026-10-21',status='prepared_identity_migration_declaration_pending_root_review_no_assembly',
        scope='24 newly confirmed imported narrative/metadata conflicts. The two already reviewed corrections in02 remain separate. No source prose, catalogue, locale, media or runtime file is modified.',
        source_original_playhub_sha256=sha(SOURCE),source_import_sha256=sha(ROOT/'expansion/calendar-features.json'),
        source_catalog_sha256_snapshot=sha(ROOT/'catalog.json'),source_queue_sha256_snapshot=sha(ROOT/'editorial/playhub-identity-review-queue.json'),
        review_receipts=[dict(path='editorial/playhub-identity-reviews-01-10.json',sha256=sha(ROOT/'editorial/playhub-identity-reviews-01-10.json')),
            dict(path='editorial/playhub-identity-reviews-11-25.json',sha256=sha(ROOT/'editorial/playhub-identity-reviews-11-25.json'))],
        already_reviewed_in_02=['daily-05-21','daily-08-30'],
        date_corrections_owner='Separate independent-reviewer event/date sidecar; this declaration does not promote scheduled days into release evidence.',
        unresolved_factual_holds=['Original generic biography prose mechanically uses birth years as later production dates: Ed Boon1964, Sid Meier1954, Ralph Baer1922 and Robin Hunicke1973. Exact source strings are preserved but need transparent archival status plus corrected, independently sourced notes.',
            'The X-COM original year is1994 in the attributed secondary reference; period primary release evidence remains pending. Do not accept Steam December31,1993 as precise evidence.',
            'Never Alone August22 and May21 are distinct original editions. Yakuza September5 and December8 are distinct original editions. Preserve each original prose/locales separately.',
            'A copied Wikipedia reference is not an editorial, historical or media publication signoff. The24 restored references have new subject-specific headings, but remain proposals pending root review.'],
        cases=records,
        counts=dict(new_conflict_editions=len(records),whole_subject_cases=sum(r['correction_kind']=='whole_subject_mapping' for r in records),mixed_cases=sum(r['correction_kind']=='mixed_original_sections' for r in records),
            original_sections_preserved=sum(len(r['archived_published_edition']['body']) for r in records),languages_per_edition=len(LANGUAGES),
            exact_locale_sections_archived=sum(sum(len(v['body']) for v in r['source_locale_archives'].values()) for r in records),
            proposed_original_partitions=sum(len(r['proposed_partitions']) for r in records),restored_reference_destinations=len(records),
            original_media_automatically_transferred=0,net_new_runtime_destinations_claimed=0))
    OUT.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(document['counts'],indent=2))
    print('declaration_sha256',sha(OUT),'bytes',OUT.stat().st_size)

if __name__=='__main__':
    main()
