#!/usr/bin/env python3
"""Build a complete editorial work register without calling imported rows finished."""
from __future__ import annotations
import collections,csv,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTENT=ROOT/'content'
OUT=CONTENT/'editorial'
DOC=ROOT/'docs/editorial'
def read(path,default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default
def words(body):
    return len(re.findall(r"\b[\w’-]+\b",' '.join(body)))
def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def feature_register(feature, drafts):
    """Account for attached prose without replacing the parent sections."""
    draft=drafts[feature['id']]
    assert feature['body']==draft['body'], 'Attached prose changed: '+feature['id']
    assert len(feature['story_headings'])==len(draft['story_headings'])==len(feature['body'])
    photos=feature.get('images',[])
    sections=[]
    for index,text in enumerate(feature['body']):
        card=draft['cards'][index]
        sections.append({'index':index,'heading':feature['story_headings'][index],
            'words':words([text]),'body_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'image_urls':[image['url'] for image in photos if image.get('story_paragraph')==index],
            'authored_media_brief':card['media_brief'],'citations':card['citations'],
            'draft_heading':draft['story_headings'][index],
            'heading_changed_after_draft':feature['story_headings'][index]!=draft['story_headings'][index],
            'editorial_review':'pending'})
    return {'feature_id':feature['id'],'canonical_entry_id':feature['canonical_entry_id'],
        'title':feature['title'],'year':feature['year'],'date':feature['date'],
        'event_semantics':feature['event_semantics'],'words':words(feature['body']),
        'sections':sections,'images':len(photos),'sources':feature['sources'],
        'base_content_language':'en','available_original_locale_overrides':[],
        'status':'authored_requires_media_localization_and_native_review',
        'tasks':['Review factual claims and every cited source locator.',
                 'Complete the exact authored card media briefs; no parent-cover substitution.',
                 'Translate this new English feature separately from its original parent.',
                 'Inspect the attached cards and credits in the native layout.']}

def build():
    OUT.mkdir(exist_ok=True);DOC.mkdir(parents=True,exist_ok=True)
    catalog=read(CONTENT/'catalog.json',{})
    all_entries=catalog['entries'];canonical={e['id']:e for e in all_entries if not e.get('calendar_only')}
    entries=[e for e in all_entries if not (e.get('calendar_only') and e.get('linked_exhibit_id') in canonical and canonical[e['linked_exhibit_id']]['year']==e['year'])]
    readiness=read(CONTENT/'publication-readiness.json',{})
    ready_by_id={r['entry_id']:r for r in readiness.get('entries',[])}
    image_manifest=read(ROOT/'assets/images/manifest.json',{})
    def hd_photo(photo):
        meta=image_manifest.get('metadata',{}).get(photo.get('url'),{})
        width=meta.get('source_width',meta.get('width',photo.get('width',0)))
        height=meta.get('source_height',meta.get('height',photo.get('height',0)))
        return max(width,height)>=1280 and min(width,height)>=720
    drafts={row['id']:row for name in ('editorial-priority-music-design.json','editorial-priority-people.json','editorial-computing-networks-02.json','editorial-people-regions-03.json','editorial-cultures-production-04.json','editorial-authorship-design-05.json','editorial-composer-methods-06.json', 'editorial-systems-authors-06.json', 'editorial-music-craft-07.json', 'editorial-design-communities-08.json', 'editorial-preservation-worlds-09.json', 'editorial-hardware-choices-11.json', 'editorial-art-direction-12.json', 'editorial-people-practices-10.json', 'editorial-tools-audio-13.json', 'editorial-production-design-16.json', "editorial-markets-machines-14.json", "editorial-networks-history-15.json")
            for row in read(CONTENT/'expansion'/name,{}).get('entries',[])}
    integration=read(CONTENT/'calendar-integration-audit.json',{})
    source_map=collections.defaultdict(list)
    for r in integration.get('merged',[]):source_map[r['id']].append(r['feature_id'])
    locale_maps={}
    for locale in ('en','it','es','fr','de','pt','ru','uk'):
        j=read(CONTENT/'locales'/f'{locale}.json',{})
        locale_maps[locale]=j.get('entries',{})
    records=[]
    for e in entries:
        r=ready_by_id.get(e['id'],{});body=e.get('body',[]);photos=e.get('images',[])
        sections=[{'index':n,'heading':(e.get('story_headings',[])+['']*len(body))[n],
            'words':words([text]),'image_urls':[p['url'] for p in photos if p.get('story_paragraph')==n],
            'heading_status':'present' if n<len(e.get('story_headings',[])) and e['story_headings'][n].strip() else 'needs_specific_heading',
            'editorial_review':'pending'} for n,text in enumerate(body)]
        if e['id'] in drafts:
            for section,card in zip(sections,drafts[e['id']]['cards']):
                section['authored_media_brief']=card['media_brief']
                section['citations']=card['citations']
        covered=sum(bool(s['image_urls']) for s in sections)
        hd_covered={photo['story_paragraph'] for photo in photos if type(photo.get('story_paragraph')) is int and hd_photo(photo) and 0<=photo['story_paragraph']<len(body)}
        preferred=e.get('preferred_image',0)
        cover=photos[preferred] if photos and 0<=preferred<len(photos) else (photos[0] if photos else {})
        missing_headings=[section['index'] for section in sections if section['heading_status']=='needs_specific_heading']
        tasks=['Review every factual claim against the cited source; record the exact event and region.',
               'Review the opening and card sequence for a concrete human, design or cultural story.',
               'Check linked exhibits for a documented relationship, not just a shared decade.',
               'Proofread all cards in the running interface, including long headings and credits.']
        if missing_headings:tasks.append('Write a useful, subject-specific heading for narrative sections '+', '.join(str(n+1) for n in missing_headings)+'. Do not reuse generic chapter labels.')
        if not photos:tasks.insert(0,'Find and verify a relevant HD cover; do not substitute unrelated hardware or upscale a thumbnail.')
        if covered*2<=len(sections):tasks.append('Illustrate a majority of narrative cards with contextually matched HD images and captions.')
        if e.get('editorial_mode')=='reference':tasks.append('Check Wikipedia revision and attribution, then add a distinctive museum angle where the subject warrants it; keep reference prose clearly credited.')
        if r.get('generic_paragraphs'):tasks.insert(0,'Replace flagged generic prose with sourced, subject-specific narrative.')
        if not e.get('body') or words(body)<100:tasks.insert(0,'Expand the incomplete narrative before presentation review.')
        if e.get('date',{}).get('precision') not in ('day','month'):tasks.append('Research a more precise date only if it can be supported; retain honest year-only precision otherwise.')
        records.append({'entry_id':e['id'],'title':e['title'],'year':e['year'],'date':e.get('date',{}),
            'kind':e.get('kind'),'origin':e.get('editorial_mode','unclassified'),'playhub_editions':source_map[e['id']]+([e['id']] if e['id'].startswith('daily-') else []),
            'current_opening':e.get('summary',''),'words':words(body),'sections':sections,
            'historical_date_review':{'status':'requires_claim_level_review','event_semantics':e.get('event_semantics',''),'region':e.get('date',{}).get('region',''),'precision':e.get('date',{}).get('precision','year'),'calendar_slot_is_not_proof_of_event_date':bool(e.get('calendar_only') or source_map[e['id']])},
            'cover_url':cover.get('url'),'metadata_hd_cover':hd_photo(cover) if cover else False,
            'mapped_hd_sections':sorted(hd_covered),
            'images':len(photos),'illustrated_sections':covered,'videos':len(e.get('videos',[])),
            'soundtrack_tracks':len(e.get('soundtrack',{}).get('tracks',[])),'bundled_or_linked_models':len(e.get('models',[])),
            'sources':e.get('sources',[]),'related_ids':e.get('related_ids',[]),
            'base_content_language':'en','available_original_locale_overrides':[locale for locale,m in locale_maps.items() if locale!='en' and e['id'] in m],
            'has_source_english_restoration_override':e['id'] in locale_maps.get('en',{}),'missing_heading_indices':missing_headings,
            'priority':'P0' if not photos or not body or r.get('generic_paragraphs') else 'P1',
            'status':'imported_requires_editorial_review','tasks':tasks})
        records[-1]['editorial_features']=[feature_register(feature,drafts)
                                         for feature in e.get('editorial_features',[])]
    new_plan=read(OUT/'history-backlog.json',{})
    additions=new_plan if isinstance(new_plan,list) else new_plan.get('entries',new_plan.get('articles',[]))
    stats={'catalog_records':len(all_entries),'distinct_timeline_articles':len(records),'original_daily_slots':sum(e.get('calendar_only',False) for e in all_entries),
        'narrative_sections':sum(len(r['sections']) for r in records),'words':sum(r['words'] for r in records),
        'with_any_cover':sum(bool(r['cover_url']) for r in records),'with_metadata_hd_cover':sum(r['metadata_hd_cover'] for r in records),
        'with_majority_mapped_card_images':sum(r['illustrated_sections']*2>len(r['sections']) for r in records),
        'with_majority_mapped_hd_card_images':sum(len(r['mapped_hd_sections'])*2>len(r['sections']) for r in records),
        'reference_articles':sum(r['origin']=='reference' for r in records),'planned_new_articles':len(additions),
        'articles_needing_specific_headings':sum(bool(r['missing_heading_indices']) for r in records),
        'sections_needing_specific_headings':sum(len(r['missing_heading_indices']) for r in records),'editorially_signed_off_in_this_register':0}
    attached=[feature for record in records for feature in record['editorial_features']]
    standalone=[record for record in records if record['entry_id'] in drafts]
    stats.update(attached_editorial_features=len(attached),
        attached_editorial_sections=sum(len(feature['sections']) for feature in attached),
        attached_editorial_words=sum(feature['words'] for feature in attached),
        standalone_priority_features=len(standalone),
        standalone_priority_sections=sum(len(record['sections']) for record in standalone),
        priority_feature_cards=sum(len(feature['sections']) for feature in attached)+sum(len(record['sections']) for record in standalone),
        total_narrative_sections_including_attached=stats['narrative_sections']+sum(len(feature['sections']) for feature in attached))
    language_coverage={locale:{'source_localized_distinct_destinations':sum(locale in record['available_original_locale_overrides'] for record in records),
        'english_fallback_distinct_destinations':sum(locale not in record['available_original_locale_overrides'] for record in records)}
        for locale in locale_maps if locale!='en'}
    report={'schema_version':1,'catalog_sha256':hashlib.sha256((CONTENT/'catalog.json').read_bytes()).hexdigest(),
        'definition':'This is a complete task register for the current collection. Import, automated validation, editorial review and public readiness are separate states.',
        'image_dimensions_source':'Current bundled image manifest; HD requires original long edge >=1280 and short edge >=720. Dimension checks do not certify subject identity or final visual quality.',
        'counts':stats,'articles':records,'language_coverage':language_coverage,
        'attached_feature_language_note':'New attached features are English; a translated original parent does not establish a feature translation.',
        'history_backlog_file':'history-backlog.json','media_backlog_file':'media-backlog.json'}
    write(OUT/'production-plan.json',report)
    with (DOC/'article-register.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=['entry_id','title','year','kind','origin','words','images','illustrated_sections','metadata_hd_cover','priority','status'])
        writer.writeheader();writer.writerows({k:r[k] for k in writer.fieldnames} for r in records)
    decades=collections.defaultdict(list)
    for r in records:decades[(r['year']//10)*10].append(r)
    lines=['# Pixel Museum editorial production plan','','A museum of games, the people who make them and the cultures that grow around them. Each story should leave the visitor with something concrete to notice, hear or understand.','',
        '## What this plan covers','','Every distinct article currently present in the collection has a record, section inventory, source list and explicit remaining work in `content/editorial/production-plan.json`. The CSV register is a compact companion. A plan covering the collection is not a claim that the collection has passed editorial review.','',
        '## Current inventory','', '| Measure | Count |','| --- | ---: |']
    for label,key in [('Distinct timeline articles','distinct_timeline_articles'),('Narrative sections','narrative_sections'),('Words in current narrative bodies','words'),('Articles with any cover URL','with_any_cover'),('Articles with metadata-qualified HD covers','with_metadata_hd_cover'),('Articles with any images mapped to a majority of sections','with_majority_mapped_card_images'),('Articles with metadata-HD images mapped to a majority of sections','with_majority_mapped_hd_card_images'),('Articles needing specific section headings','articles_needing_specific_headings'),('Sections needing specific headings','sections_needing_specific_headings'),('Imported reference articles','reference_articles'),('New articles in the history backlog','planned_new_articles')]:lines.append(f'| {label} | {stats[key]:,} |')
    for label,key in [('Attached authored features','attached_editorial_features'),('Attached sections additional to original bodies','attached_editorial_sections'),('New standalone priority features','standalone_priority_features'),('Standalone priority sections already in narrative count','standalone_priority_sections'),('Priority feature cards across both placements','priority_feature_cards'),('All narrative sections including attached features','total_narrative_sections_including_attached')]:lines.append(f'| {label} | {stats[key]:,} |')
    lines += ['', 'These counts describe the files at the recorded catalogue hash. An image URL is not proof of availability, resolution, rights or contextual relevance. Mapped section coverage must still be reviewed by a person.','',
        '## Editorial sequence','',
        '1. Import every published Playhub edition, introduction, chapter and existing translation. Keep an edition-to-canonical-article map so deduplication never deletes its story. Console articles remain available even when a suitable model is missing.',
        '2. Resolve provenance, duplicate subjects and event dates. Distinguish release, announcement, regional launch, birth date and in-game calendar event. Never turn the day an article was published into a historical launch date.',
        '3. Fill media gaps in the imported collection before treating the wider reference collection as a finished gallery. Every timeline entry needs a relevant cover; most narrative cards need contextual illustrations.',
        '4. Review each article as a sequence of cards. Preserve the full source narrative, with short useful headings, meaningful captions and reading expansion where needed. Add original writing when it explains a person, decision, process or overlooked context better than the reference introduction.',
        '5. Complete the historical gaps recorded in the history backlog. Build cross-links between documented influences and consequences. Review geographical, cultural and disciplinary balance after each batch.',
        '6. Reuse Playhub language editions. Translate the English Wikipedia additions into the selected languages, retaining their revision and licence notices. Report fallback coverage per language; do not label untranslated English as localized.',
        '7. Run the entire collection through source, image, link, layout, controller and performance checks. Then review the resulting stories on the PS5 before release.','',
        '## Experience art direction','', 'Interactive studies retain paper and ink, simple abstract geometry and a single contextual accent. Richer mechanics, timing, feedback and sound add depth; literal scenery and game-specific colour schemes do not.', '', '## Article structure','',
        'An opening introduces the event and its stakes. Subsequent cards explain a few specific choices, the people involved, contemporary context and what changed afterward. A short reference entry can remain short when it is sufficient; a major turning point needs a fuller, illustrated story. Avoid repeated generic conclusions about legacy, immersion or innovation.', '',
        'For a game, show a concrete mechanic, artistic or musical choice alongside its historical circumstances. For a console, cover its intended audience, industrial design, technical trade-offs, software and regional life. For a person, explain their work and collaborators rather than reducing a career to a birthday. For a cultural story, include the players, institutions and working conditions that made it possible.','',
        '## Approval gates','',
        '| Gate | Evidence required |','| --- | --- |',
        '| Identity | The title, version, subject and region match every associated resource. |',
        '| Date | The event meaning and date precision are stated and supported; uncertainty stays visible. |',
        '| Text | Complete, specific narrative; no empty cards, repeated templates or unsupported superlatives. |',
        '| Sources | Claim-level research notes and durable source links; interviews distinguished from later recollections. |',
        '| Cover | Relevant remotely hosted image, verified dimensions and working fetch; no upscaled small source. |',
        '| Card media | A majority of narrative cards illustrated where sources exist, with reviewed bindings and captions. |',
        '| Rights | Creator, source and applicable licence or permission recorded; no blanket assumption that museum access permits reuse. |',
        '| Film and music | Exact title and publisher checked; availability and audio-only soundtrack behavior tested. |',
        '| Models | Faithful, licensed, detailed asset with material and on-device performance validation; absence does not suppress the article. |',
        '| Localization | Correct source edition, intact paragraph structure and explicit English fallback for missing translations. |',
        '| Presentation | Long titles, body expansion, gallery animation and credits readable with the controller. |',
        '| Review | Editorial sign-off recorded separately from script checks and device tests. |','',
        '## Language coverage','', 'Every article has English base text. Exact source-locale and English-fallback counts are recorded per language in the production JSON. Attached English features do not inherit a translation from their localized parent. The English sidecar restores source editions; it is not total English coverage. Feature and Wikipedia translations remain separate production tasks.', '', '## Work ownership','',
        'The import lane owns source fidelity, canonical mapping and translations. The history lane owns missing subjects, factual framing, dates and narrative briefs. The media lane owns archives, images, films, recordings and contextual card coverage. Integration owns the complete work register, duplicate review, links, presentation checks and the final release gates. Each batch must name concrete article IDs and report evidence, not just a number of added rows.','',
        '## Decade inventory','', '| Decade | Articles | Cover URLs | Metadata HD covers | Sections |','| --- | ---: | ---: | ---: | ---: |']
    for decade,rs in sorted(decades.items()):lines.append(f'| {decade}s | {len(rs)} | {sum(bool(r["cover_url"]) for r in rs)} | {sum(r["metadata_hd_cover"] for r in rs)} | {sum(len(r["sections"]) for r in rs)} |')
    lines += ['', '## Working files','',
        '- `article-register.csv`: one row for every distinct current timeline article.',
        '- `../../content/editorial/production-plan.json`: complete section-level work register and current catalogue hash.',
        '- `history-coverage-plan.md` and `../../content/editorial/history-backlog.json`: planned research commissions.',
        '- `media-and-experiences-plan.md` and `../../content/editorial/media-backlog.json`: media, archives and interactive-study plan.',
        '- `../../content/editorial-collection-audit.json`: Playhub edition and source-copy evidence.',
        '- `../../content/playhub-localization-audit.json`: available original language coverage.',
        '- `../../content/publication-readiness.json`: automated media and narrative blockers, without hiding imported articles.','',
        'Run `python tools/editorial-plan.py` after assembling the catalogue to refresh the register. Do not manually mark a missing image or an unreviewed article complete.','']
    (DOC/'plan.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(stats,indent=2))
if __name__=='__main__':build()
