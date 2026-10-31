"""Give the Fantasian excerpt a standalone subject and physical-photo context."""
from pathlib import Path
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[1];FOLDER=ROOT/'build/research/playhub-semantic-coverage/wiki-clarity/sakaguchi-bounded-two'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=FOLDER/'two-concrete-sakaguchi-cards-candidate.json';assert sha(old)=='88fc0149d8f858d6c313e0d366633077eb9cabd4dd9a1080d16ff12ab26e005a'
doc=copy.deepcopy(json.loads(old.read_text(encoding='utf8')));r=doc['replacements'][1];assert r['source_chapter_index']==6
r['heading']='Fantasian: more than 150 dioramas'
assert 'many being veterans of the tokusatsu industry. ' in r['body']
r['body']='Fantasian uses photographs of physical dioramas to create its environments. '+r['body'].replace(', many being veterans of the tokusatsu industry. ','. ',1)
assert 'tokusatsu' not in r['body']
r['body_sha256']=hashlib.sha256(r['body'].encode()).hexdigest()
r['provenance']['adaptations']+=['Prepend a standalone sentence naming Fantasian and explaining photographed physical environments, directly based on source paragraph27 photographic extraction passage and source paragraph1 real-world diorama statement.','Omit the subordinate tokusatsu-industry clause from the first original paragraph28 sentence to keep the terminology readable; its original wording remains in the frozen source and source_paragraphs.']
r['provenance']['full_paragraph']=False
r['source']['attribution']='Adapted from English Wikipedia paragraph28 with a subject-setting sentence from paragraph27, one full-name clarification and one omitted technical clause; all changes recorded in provenance. Heading supplied editorially.'
doc['variant_basis']=dict(original_candidate_sha256=sha(old),changes='Only paragraph6 body/heading and its corresponding adaptation metadata change. Paragraph0 and all current other entry fields remain as the original candidate.')
out=FOLDER/'two-concrete-sakaguchi-cards-standalone-fantasian-candidate.json';assert not out.exists();out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(out.relative_to(ROOT),sha(out))
(FOLDER/'projected-standalone-card-text.txt').write_text('\n\n'.join(r['heading']+'\n'+r['body'] for r in doc['replacements']),encoding='utf8')
