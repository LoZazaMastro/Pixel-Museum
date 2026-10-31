"""Illustrate the existing companion-book paragraph without repeating its cover."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/taipan-existing-prose-companion-book'
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
master = json.loads((ROOT / 'build/research/current1387-after-storage-native-qa/master.json').read_text())
old = next(e for e in master['entries'] if e['id'] == 'wikipedia-8888585')
new = copy.deepcopy(old)
new['images'][0].update(story_paragraph=-1,
    title='Taipan: the later Apple II companion book',
    caption='The cover of the 1986 Hayden companion book for the Apple II edition, retained as historical context. This is a book cover, not the original 1979 TRS-80 packaging.',
    creator='Hayden Book Company / Paul Perlow (cover design)',
    credit='Hayden Book Company; cover design Paul Perlow / LaunchBox archive',
    license='Original book and cover-design rights retained; no open licence asserted.')
new['images'].append({'url':'https://taipangame.com/pdf/TaipanAHistoricalAdventureForTheAppleComputerAppleIIEdition.pdf#page=2',
    'source_page':'https://taipangame.com/',
    'title':'The companion book and its artists',
    'caption':'The complete title page of the 1986 Apple II companion book names Art Canfil, Karl Albrecht and Jim McClenahan, and credits the original artwork to Chrisann Brennan. This is the later book discussed in the text, not a 1979 game screen or the separate Ocean game.',
    'creator':'Hayden Book Company / Art Canfil, Karl Albrecht and Jim McClenahan',
    'credit':'Hayden Book Company / Taipangame preservation archive',
    'license':'Copyright 1986 Hayden Book Company, all rights reserved. No open licence asserted.',
    'width':1338,'height':1959,'story_paragraph':3,
    'recovery_local_source':'build/research/taipan-existing-prose-companion-book/original-book-title-page2-complete.png',
    'verification':{'sha256':sha(BASE/'original-book-title-page2-complete.png'),'processing':'Complete original PDF page 2 rendered with PDFium at 216dpi; no crop or retouching.'}})
new['explicit_story_media_only']=True
new['sources'].append({'title':'Taipan: A Historical Adventure for the Apple Computer, Apple II Edition (1986)',
    'url':'https://taipangame.com/pdf/TaipanAHistoricalAdventureForTheAppleComputerAppleIIEdition.pdf','publisher':'Hayden Book Company / Taipangame preservation archive'})
files=[BASE/'preservation-source.html',BASE/'original-appleii-companion-book.pdf',BASE/'original-book-title-page2-complete.png',ROOT/old['images'][0]['recovery_local_source']]
x={'status':'CANDIDATE_PENDING_INDEPENDENT_PEER','rows':[{'entry_id':old['id'],'old_entry':old,'new_entry':new}],
    'source_files':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in files},
    'expected_main_paragraph_groups':[[0,1,2],[3]],
    'scope':'Four complete existing paragraphs retained. Add a distinct primary title-page illustration for the book paragraph; correct only the existing cover metadata which had mislabelled this same book as 1982 game packaging. Existing TRS-80 film unchanged.',
    'quality_limits':['No claim that the book is a 1979 artifact or that its title page is gameplay.', 'The Ocean 1987 comparison paragraph remains in the opening narrative; film is not claimed to depict that separate game.']}
out=BASE/'four-existing-taipan-paragraphs-film-and-distinct-book-title-candidate.json'
out.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
print(out.relative_to(ROOT),sha(out))


