"""Freeze the complete existing Playhub authoring source and authentic local media.

No catalogue assembly, remote media playback, or FTP writes occur here.
"""
import copy, hashlib, json, shutil, urllib.request
from pathlib import Path
from PIL import Image

R=Path(__file__).resolve().parents[2]
P=Path('F:/Playhub/Plugin/Playhub')
D=R/'build/research/kojima-playhub-complete';D.mkdir(exist_ok=True)
S=R/'content/expansion/playhub-theme-sources';S.mkdir(exist_ok=True)
O=D/'originals';O.mkdir(exist_ok=True)
def write(f,d):f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
source_files={}
for name in ['history_editorial.json','history_images.json']:
 src=P/'Source/GamingModeDeckyPlugin/quick_settings'/name;dst=S/name
 shutil.copyfile(src,dst);source_files[dst.relative_to(R).as_posix()]=sha(dst)
themes=json.loads((S/'history_editorial.json').read_text(encoding='utf8'))['themes']
theme=next(t for t in themes if t['id']=='kojima')
metadata=json.loads((S/'history_images.json').read_text(encoding='utf8'))['kojima']
byfile={m['file']:m for m in metadata};assert len(theme['chapters'])==10
catalog=json.loads((R/'content/catalog.json').read_text(encoding='utf8'))['entries']
old=next(e for e in catalog if e['id']=='daily-08-24')
archive=R/'content/expansion/playhub-kojima-previous-record.json';assert not archive.exists();write(archive,{'source_record':copy.deepcopy(old),'scope':'Exact pre-import article retained, including body, images, video and original provenance; replaced only by complete existing theme, not appended as duplicate prose.'})
base='https://raw.githubusercontent.com/LoZazaMastro/Playhub/0c5c103403813431e23b40f90c75fba6d51a9759/assets/on-this-day/v1/'
files=['kojima-intro.png','kojima-portrait.jpg']+[c['image_file'] for c in theme['chapters'][1:]]
titles=['Hideo Kojima','Hideo Kojima — contemporary portrait; not a photograph of his youth']+[c['subject']+' — '+c['title']['en'] for c in theme['chapters'][1:]]
images=[];pixels=set();original_digests=set()
for n,(name,title) in enumerate(zip(files,titles)):
 src=P/'assets/on-this-day/v1'/name;dst=O/name;shutil.copyfile(src,dst)
 with Image.open(dst) as im:
  im.load();width,height=im.size;pixel_sha=hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
 assert min(width,height)>=550 and max(width,height)>=1000
 assert pixel_sha not in pixels;pixels.add(pixel_sha);original_digests.add(sha(dst))
 m=byfile.get(name,{})
 if 'metal-gear' in name or 'kojima-mgs' in name:
  credit='Game imagery: Konami Digital Entertainment.';source=m.get('sourceUrl','https://www.konami.com/mg/archive/mgs_tlc/')
 elif name=='death-stranding-game.png':credit='Death Stranding / Kojima Productions / Sony Interactive Entertainment.';source='https://www.kojimaproductions.jp/en/death-stranding'
 else:credit='Photograph: original photographer and rights holder; photographer not identified in the supplied source record.';source=base+name
 images.append({'url':base+name,'title':title,'width':width,'height':height,'source_width':width,'source_height':height,'credit':credit,'source_page':source,'license':'Original photographic, artwork or game-publisher rights retained. Historical illustration; no new licence asserted.','license_url':'','story_paragraph':n,'portrait':n<2,'recovery_local_source':dst.relative_to(R).as_posix(),'source_asset_sha256':sha(dst),'source_pixel_sha256':pixel_sha,'quality_verified':'Original local source decoded at native resolution; no upscaling. Unique decoded pixels within this article.'})
videos=[]
for vid,caption in [('6thnV_sV96M','Hideo Kojima and filmmaker Fatih Akin discuss cinema and game direction in an official Kojima Productions conversation.'),('r1f4LuF74cM','Hideo Kojima and Yoji Shinkawa discuss their creative collaboration in an original Hamilton publication.')]:
 m=json.loads((D/(vid+'-metadata.json')).read_text(encoding='utf8'));assert m['native_compatible_avc_aac'] is True
 poster='https://i.ytimg.com/vi/'+vid+'/maxresdefault.jpg';local=O/(vid+'-poster.jpg')
 if not local.exists():local.write_bytes(urllib.request.urlopen(urllib.request.Request(poster,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read())
 with Image.open(local) as im:im.load();w,h=im.size;ph=hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
 assert w>=1000 and ph not in pixels;pixels.add(ph)
 credit=m['channel']+' / original YouTube publication'
 images.append({'url':poster,'title':'Film preview: '+m['title'],'width':w,'height':h,'credit':credit+' thumbnail','source_page':'https://www.youtube.com/watch?v='+vid,'license':'Original creator and publisher rights retained; historical preview of the linked film.','kind':'video-poster','story_paragraph':-1,'recovery_local_source':local.relative_to(R).as_posix(),'source_asset_sha256':sha(local),'source_pixel_sha256':ph})
 videos.append({'youtube_id':vid,'url':'https://www.youtube.com/watch?v='+vid,'title':m['title'],'creator':m['channel'],'source_page':'https://www.youtube.com/watch?v='+vid,'credit':credit,'caption':caption,'duration_s':m['duration'],'channel_id':m['channel_id'],'poster_url':poster,'license':'Original creator and publisher rights retained; streamed from the original publication.','verification':{'metadata_resolved':True,'native_codec_metadata_verified':True,'avc_format_count':m['avc_format_count'],'aac_format_count':m['aac_format_count'],'native_selection':m['native_selection'],'receipt':(D/(vid+'-metadata.json')).relative_to(R).as_posix(),'checked_utc':m['checked_utc'],'scope':'Public native-compatible format metadata resolved; not a claim of console playback.'}})
out={'schema_version':1,'publication_status':'complete_source_reuse_verified','target_entry_id':'daily-08-24','theme_id':'kojima','source_files':source_files,'previous_record_archive':archive.relative_to(R).as_posix(),'previous_record_archive_sha256':sha(archive),'title':old['title'],'subtitle':theme['title']['en'],'summary':theme['intro']['en'],'body':[theme['intro']['en']]+[c['body']['en'] for c in theme['chapters']],'story_headings':[theme['title']['en']]+[c['title']['en'] for c in theme['chapters']],'images':images,'videos':videos,'preferred_image':0,'sources':[{'url':u,'title':'Source for Hideo Kojima and his work','publisher':urllib.parse.urlparse(u).hostname or ''} for u in theme['sources']],'media_replacement_notes':[{'source_chapter':1,'original_file':'kojima-youth.png','original_dimensions':[598,334],'replacement_file':'kojima-portrait.jpg','reason':'A distinct native-HD contemporary portrait replaces a small childhood photograph. Caption explicitly identifies the contemporary image, not youth.'}],'text_policy':'Exact existing English introduction and all ten chapter bodies/headings retained, in order. All original source languages remain in the hash-bound authoring snapshot.'}
write(R/'content/expansion/playhub-theme-complete-kojima.json',out)
print('Kojima frozen:',len(out['body']),'paragraphs;',len(images),'unique images;',len(videos),'verified videos')
