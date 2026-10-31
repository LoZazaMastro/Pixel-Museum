"""Prepare only the two identified abstract Sakaguchi cards for NEXT peer."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'build/research/playhub-semantic-coverage/wiki-clarity/sakaguchi-bounded-two'
def sha(b):return hashlib.sha256(b).hexdigest()
catalog=ROOT/'content/catalog.json';raw=catalog.read_bytes();entry=next(e for e in json.loads(raw)['entries'] if e['id']=='daily-11-25')
rows=[]
for index,title,line,heading in [(0,'Hironobu Sakaguchi',0,'From Square to Mistwalker'),(6,'Fantasian',28,'Building more than 150 dioramas')]:
    file=FOLDER/(title+'.json');source_bytes=file.read_bytes();doc=json.loads(source_bytes);page=next(iter(doc['query']['pages'].values()));paragraph=page['extract'].splitlines()[line];body=paragraph;adaptations=[]
    if index==6:
        assert 'Yatsubo remembered' in body
        context=page['extract'].splitlines()[27]
        assert "Tomohiro Yatsubo" in context
        body=body.replace('Yatsubo remembered','Diorama modeller Tomohiro Yatsubo remembered',1)
        adaptations=['Expand the otherwise unresolved surname Yatsubo using his full name and diorama-modeller role stated in immediately preceding paragraph27 of the same revision. No other source wording changed.']
    revision=page['revisions'][0]['revid']
    rows.append(dict(entry_id=entry['id'],source_chapter_index=index,old_body=entry['body'][index],old_body_sha256=sha(entry['body'][index].encode()),old_heading=entry['story_headings'][index],body=body,body_sha256=sha(body.encode()),heading=heading,source=dict(title=page['title'],url=f'https://en.wikipedia.org/w/index.php?oldid={revision}',publisher='English Wikipedia contributors',license='Creative Commons Attribution-ShareAlike 4.0',license_url='https://creativecommons.org/licenses/by-sa/4.0/',attribution='Complete English Wikipedia paragraph; one disclosed full-name clarification in Fantasian; headings supplied editorially.'),provenance=dict(source_file=file.relative_to(ROOT).as_posix(),source_file_sha256=sha(source_bytes),page_id=page['pageid'],revision_id=revision,paragraph_indices=[line],source_paragraphs=[paragraph],full_paragraph=not adaptations,adaptations=adaptations,context_paragraphs=[context] if adaptations else [],locator='Zero-based raw splitlines index in the frozen plaintext API extract, including blank lines and section headings.')))
out=FOLDER/'two-concrete-sakaguchi-cards-candidate.json';assert not out.exists()
candidate=dict(schema_version=1,status='candidate_pending_independent_review',source_catalog_sha256=sha(raw),scope='NEXT10 only: replace two identified abstract intro/Fantasian bodies. Preserve concrete FFVII paragraph3, all other five bodies, current media and dates. No image-completeness claim.',replacements=rows,entry_invariant_sha256=sha(json.dumps({k:v for k,v in entry.items() if k not in ('body','story_headings','sources','provenance','editorial_credit')},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()),master_modified=False)
out.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(FOLDER/'projected-card-text.txt').write_text('\n\n'.join(r['heading']+'\n'+r['body'] for r in rows),encoding='utf8')
print(out.relative_to(ROOT),sha(out.read_bytes()))
