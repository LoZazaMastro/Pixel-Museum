"""Keep one SNES chronology stop, with regional industrial designs inside it."""
import copy

def apply(entries):
    by_id={entry['id']:entry for entry in entries}
    source=by_id.get('snes-pal');target=by_id.get('daily-11-21')
    if source is None:return {'status':'already_consolidated'}
    if target is None:raise ValueError('Original Super Famicom exhibit is absent')
    original=copy.deepcopy(source)
    old_target=copy.deepcopy(target)
    target.update(title='Super Nintendo Entertainment System',year=1990,
        date={'month':11,'day':21,'precision':'day','region':''},
        subtitle='Super Famicom and the Super Nintendo family')
    body=target['body'];heads=target.setdefault('story_headings',[])
    while len(heads)<len(body):heads.append('Super Famicom')
    mapping={}
    regional_titles=['The PAL design arrives in Europe','The controller and its games','A library of different experiences']
    for index,paragraph in enumerate(source.get('body',[])):
        # Remove exhibition-process warnings, not historical information.
        paragraph=paragraph.replace('This exhibit follows that regional object, not an invented worldwide launch shared by every version.','').strip()
        if paragraph not in body:
            body.append(paragraph);heads.append(regional_titles[index]if index<len(regional_titles)else'The PAL design')
        mapping[index]=body.index(paragraph)
    if body:
        body[0]=body[0].replace('The date therefore concerns the Japanese launch, not the North American or European ones. ','')
    preferred_url=target['images'][target.get('preferred_image',0)]['url']
    known={image['url']for image in target.get('images',[])}
    for index,original_image in enumerate(source.get('images',[])):
        if original_image['url']in known:continue
        image=copy.deepcopy(original_image)
        paragraph=image.get('story_paragraph')
        if isinstance(paragraph,int)and paragraph>=0:image['story_paragraph']=mapping.get(paragraph,-1)
        elif index==source.get('preferred_image',0):image['story_paragraph']=mapping.get(0,-1)
        target['images'].append(image);known.add(image['url'])
    target['preferred_image']=next(n for n,image in enumerate(target['images'])if image['url']==preferred_url)
    known={model.get('asset_file')for model in target.get('models',[])}
    for original_model in source.get('models',[]):
        if original_model.get('asset_file')in known:continue
        model=copy.deepcopy(original_model);model['display_caption']='Super Nintendo / PAL design1992'
        model['representation_note']='Later European PAL industrial design, shown as a regional object variant of the system released inJapan in1990; not the Japanese launch unit.'
        target.setdefault('models',[]).append(model);known.add(model.get('asset_file'))
    for field,key in [('sources','url'),('videos','youtube_id'),('editorial_features','id')]:
        seen={item.get(key)for item in target.get(field,[])}
        for original_item in source.get(field,[]):
            if original_item.get(key)in seen:continue
            item=copy.deepcopy(original_item)
            if field=='videos'and isinstance(item.get('story_paragraph'),int)and item['story_paragraph']>=0:item['story_paragraph']=mapping.get(item['story_paragraph'],-1)
            target.setdefault(field,[]).append(item);seen.add(item.get(key))
    provenance=target.setdefault('provenance',{})
    provenance['regional_variant_previous_record']=original
    provenance['canonical_release_previous_record']=old_target
    provenance['regional_variant_consolidation']={'alias':'snes-pal','canonical_id':'daily-11-21',
        'source_paragraph_index_map':{str(key):value for key,value in mapping.items()},'primary_object':'models/super-famicom.glb',
        'additional_object':'models/snes-pal.glb','policy':'One first-release chronology stop; later regional design kept inside the same article.'}
    target['explicit_story_media_only']=True
    for entry in entries:
        entry['related_ids']=list(dict.fromkeys('daily-11-21'if value=='snes-pal'else value for value in entry.get('related_ids',[])))
        entry['related_ids']=[value for value in entry['related_ids']if value!=entry['id']]
    entries[:]=[entry for entry in entries if entry['id']!='snes-pal']
    return {'status':'PASS','canonical_id':'daily-11-21','removed_id':'snes-pal',
        'complete_paragraphs':len(target['body']),'preserved_models':[model['asset_file']for model in target.get('models',[])],
        'original_regional_record_archived':True}
