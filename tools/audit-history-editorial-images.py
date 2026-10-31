"""Persist the individually reviewed 1994+ history image decisions.

This records a particular image URL, not permanent approval of a subject or of
whatever another acquisition pass happens to return later.
"""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
entries=json.loads((ROOT/'content/human-history.json').read_text(encoding='utf8'))['entries']
approved={}
for file in sorted((ROOT/'content/expansion').glob('human-history-official-images*.json')):
 for subject,image in json.loads(file.read_text(encoding='utf8')).get('entries',{}).items():
  if str(image.get('context_review_status','')).startswith('PASS'):approved[image['url']]=image
specific_work_images={'Apollo 13 (film)','28 Days Later','Shaun of the Dead','Django Unchained','Transformers (film)','Blade Runner 2049','Oppenheimer (film)','The Force Awakens'}
specific_holds={
 'Amazon (company)':'A2015office tower does not represent the1994founding or initial company.',
 'eBay':'Amodern shared Toronto office does not represent the1995auction site.',
 'USB':'Amodern market stall of assorted cables is not an original-generation USB artifact.',
 'Bluetooth':'The2012Voyager Legend headset is a later product, not an original-generation1998artifact.',
 'Google':'Amodern campus does not represent the1998founding or original search interface.',
 'International Space Station':'The completed2021configuration must not stand for the first1998orbital module.',
 'IPod':'Aline-up of later iPod generations does not depict the original2001model.',
 'Mac OS X 10.0':'Alogo is not the actual first-version operating-system interface.',
 'September 11 attacks':'AJuly2001skyline is a pre-event view, not a photograph of the September11event.',
 'Blu-ray':'UHD4Kretail media introduced later must not illustrate the original Blu-ray launch.',
 'SpaceX':'Amodern Starbase facility is not the original company or first Falcon product.',
 'Facebook':'A2011Egyptian protest sign does not depict the2004site or its creation.',
 'Google Maps':'Amodern street sculpture is not the original Maps service interface.',
 'Amazon Kindle':'The third-generation Kindle is not the original2007device.',
 'Spotify':'Amodern headquarters does not depict the original2008product.',
 'Bitcoin':'A2018industrial mining facility does not depict the original2009software.',
 'Instagram':'A2026profile screenshot is not the original2010application.',
 '2016 United Kingdom European Union membership referendum':'David Cameron as foreign secretary in2023is unrelated as the lead image of the2016referendum.',
 '2024 United States presidential election':'AJanuary2024Gaza rally does not show the presidential election.',
 'ChatGPT':'Agenerated interpretation of Wikipedia is not an image of the2022ChatGPTinterface.',
 'Rosetta (spacecraft)':'The selected artist concept depicts Mars Odyssey, a different spacecraft.',
 'Ingenuity (helicopter)':'The selected artist concept depicts Mars Odyssey, not the Ingenuity helicopter.',
 'First observation of gravitational waves':'AProxima b exoplanet illustration does not depict LIGO or the gravitational-wave discovery.',
 'Perseverance (rover)':'AnIngenuity landscape capture does not show the Perseverance rover.',
 '2024 Summer Olympics':'Akayak contest at the2017Natural Games is a different competition.',
 'Falcon Heavy':'The2019Arabsat flight must not be presented as the first2018demonstration flight.',
 'Human Genome Project':'Anineteenth-century comparative skeleton diagram does not depict the Human Genome Project.',
 'MP3':'Ageneric vinyl-record illustration does not represent MPEG audio compression.',
}
review=[];holds={}
for entry in entries:
 if entry['year']<1994:continue
 subject=entry['provenance']['seed_title'];image=entry['images'][0]
 lead=re.split(r'(?<=[.!?])\s+',entry['provenance'].get('full_source_extract',''),maxsplit=1)[0]
 work=bool(re.search(r'\b(?:film|album|television series|animated series|manga)\b',lead,re.I))
 reason=None
 if image['url'] not in approved:
  if subject in specific_holds:reason=specific_holds[subject]
  elif work and subject not in specific_work_images:reason='The displayed image is a cast/creator portrait, unrelated appearance, location, or other contextual substitute. This work requires its actual poster, cover, still, or identifiable original production artifact.'
 status='hold' if reason else 'pass'
 if not reason:reason='Reviewed actual contact-sheet image and source identity: the subject or original-generation artifact is recognizable, with native source dimensions and retained attribution.'
 row={'entry_id':entry['id'],'subject':subject,'year':entry['year'],'image_url':image['url'],'status':status,'reason':reason,'native_dimensions':[image['width'],image['height']],'review_scope':'Actual displayed imagery in contact sheets11–16 and its source description; exact URL only.'}
 review.append(row)
 if status=='hold':holds[subject]={'url':image['url'],'reason':reason,'entry_id':entry['id']}
(ROOT/'build/research/human-history/editorial-image-review.json').write_text(json.dumps({'schema_version':1,'entries':review},ensure_ascii=True,indent=2)+'\n',encoding='utf8')
(ROOT/'content/expansion/human-history-image-holds-editorial.json').write_text(json.dumps({'schema_version':1,'entries':holds},ensure_ascii=True,indent=2)+'\n',encoding='utf8')
print('Reviewed',len(review),'pass',len(review)-len(holds),'hold',len(holds),flush=True)
