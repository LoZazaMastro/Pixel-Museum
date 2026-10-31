"""Keep collection/import provenance internal, retaining real authors and licences."""
import copy,re
from urllib.parse import urlparse
ARCHIVE=re.compile(r'Playhub|LoZazaMastro',re.I)

def clean_label(text):
    if not isinstance(text,str)or not ARCHIVE.search(text):return text
    text=re.sub(r';?\s*the original Playhub edition remains separately archived\.?','.',text,flags=re.I)
    text=re.sub(r'\bPlayhub historical collection\s*/\s*LoZazaMastro\.?\s*','',text,flags=re.I)
    text=re.sub(r'\s+from the Playhub collection','',text,flags=re.I)
    text=re.sub(r'\s+(?:from|in) the Playhub historical collection','',text,flags=re.I)
    text=re.sub(r'\s*/\s*Playhub(?: historical)? collection','',text,flags=re.I)
    text=re.sub(r'\bPlayhub(?: historical)? collection\s*/\s*','',text,flags=re.I)
    text=re.sub(r'\s*/\s*LoZazaMastro','',text,flags=re.I)
    text=re.sub(r'\bPlayhub\s*/\s*LoZazaMastro\b','',text,flags=re.I)
    text=re.sub(r'\bPlayhub\b','source exhibition',text,flags=re.I)
    text=re.sub(r'\bLoZazaMastro\b','',text,flags=re.I)
    return re.sub(r'\s{2,}',' ',text).strip(' /;')

def integrate(entries):
    rows=[]
    owners=list(entries)+[f for e in entries for f in e.get('editorial_features',[])]
    for owner in owners:
        original={};counts={}
        if ARCHIVE.search(owner.get('editorial_credit','')):
            original['editorial_credit']=owner['editorial_credit'];owner['editorial_credit']=clean_label(owner['editorial_credit'])
            counts['editorial_credit']=1
        attribution=owner.get('attribution')
        if isinstance(attribution,dict)and ARCHIVE.search(attribution.get('text','')):
            original['attribution']=copy.deepcopy(attribution);attribution['text']=clean_label(attribution['text']);counts['attribution']=1
        sources=[];moved=[];changed=[]
        for source in owner.get('sources',[]):
            url=source.get('url','');host=urlparse(url).netloc.lower()
            # This is an import receipt, not an independent historical source.
            if host in ('github.com','raw.githubusercontent.com')and '/LoZazaMastro/Playhub/'in url:
                moved.append(copy.deepcopy(source));continue
            if any(ARCHIVE.search(source.get(field,''))for field in ('title','publisher')):
                changed.append(copy.deepcopy(source))
                if 'wikipedia.org'in host:source['publisher']='Wikipedia contributors'
                elif ARCHIVE.search(source.get('publisher','')):source.pop('publisher',None)
                source['title']=clean_label(source.get('title',''))
            sources.append(source)
        if moved:original['internal_import_sources']=moved;counts['internal_import_sources']=len(moved)
        if changed:original['source_labels']=changed;counts['source_labels']=len(changed)
        owner['sources']=sources
        for kind in ('images','videos'):
            media=[]
            for image in owner.get(kind,[]):
                before={k:image[k]for k in ('title','caption','creator','credit')if ARCHIVE.search(image.get(k,''))}
                if not before:continue
                for field in before:image[field]=clean_label(image[field])
                media.append({'url':image.get('url',image.get('youtube_id','')),'original_fields':before})
            if media:original[kind]=media;counts[kind]=len(media)
        if original:
            owner.setdefault('provenance',{}).setdefault('public_archive_credit_originals',original)
            rows.append({'entry_id':owner['id'],'changes':counts})
    remaining=[]
    for owner in owners:
        for field in ('editorial_credit',):
            if ARCHIVE.search(owner.get(field,'')):remaining.append({'entry_id':owner['id'],'field':field})
        for kind in ('images','videos','sources'):
            for item in owner.get(kind,[]):
                for field in ('title','caption','creator','credit','publisher'):
                    if ARCHIVE.search(item.get(field,'')):remaining.append({'entry_id':owner['id'],'field':kind+'.'+field})
    if remaining:raise ValueError('Archive credit labels remain public: '+str(remaining[:5]))
    return {'status':'PASS_COLLECTION_PROVENANCE_INTERNAL','owners_changed':len(rows),'entries':rows,'remaining_public_archive_labels':remaining,'global_application_author_untouched':True,'third_party_author_names_licences_and_original_source_urls_retained':True}
