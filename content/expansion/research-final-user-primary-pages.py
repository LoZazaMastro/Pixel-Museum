import json,hashlib,importlib.util,re
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p);D=p.RESEARCH/'final-user-score-priorities/primary';D.mkdir(parents=True,exist_ok=True)
sources={
 'automodellista-original-album':('https://musicbrainz.org/release/696fce06-f009-4199-b96c-5105cfb7adb8','secondary specific2002album per-track credit transcription',['Auto Modellista','Tetsuya Shibata']),
 'automodellista-game':('https://en.wikipedia.org/wiki/Auto_Modellista','secondary originalgame composer/source edition',['2002','Tetsuya Shibata','Isao Abe']),
 'matrix-first-person-composers':('https://www.matrixfans.net/enter-the-matrix-interview-with-composers-don-davis-and-erik-lundborg/','first-person composer interview reprint',['None of the actual recordings','re-recorded','Erik Lundborg']),
 'getaway-original-game':('https://en.wikipedia.org/wiki/The_Getaway_(video_game)','secondary exact2002game music credits',['Andrew Hale','Shawn Lee']),
 'matrix-path-original-game':('https://en.wikipedia.org/wiki/The_Matrix:_Path_of_Neo','secondary exact2005game composer context',['Tobias Enhus','2005']),
 'simpsons-original-game':('https://en.wikipedia.org/wiki/The_Simpsons:_Hit_%26_Run','secondary exact2003game composition roles',['Marc Baril','Jeff Tymoschuk','Allan Levy']),
 'onimusha-remaster-composer-own-blog':('https://reikondoh.blog.jp/archives/cat_10009843.html','primary composer ownblog2018lead and twoothercomposers',['Lead Composer','Rei Kondoh','Sho Kobayashi','Keisuke Mochizuki']),
 'onimusha-remaster-album':('https://vgmdb.net/album/81546','secondary exact2018CapcomalbumCPDA10121booklet transcription',['CPDA-10121','Rei Kondoh','Sho Kobayashi']),
 'onimusha2-publisher-orchestra':('https://store.steampowered.com/app/3128200/?l=english','primary Capcom identifies Iwashiro game score and selectedorchestraalbum',['Taro Iwashiro','Onimusha']),
 'onimusha3-original-game':('https://en.wikipedia.org/wiki/Onimusha_3:_Demon_Siege','secondary exact2004original game',['Akari Kaida','2004']),
 'onimusha-dawn-original-game':('https://en.wikipedia.org/wiki/Onimusha:_Dawn_of_Dreams','secondary original2006game music distinction',['Hideyuki Fukasawa','Jamie Christopherson','cutscene']),
}
receipts={}
for key,(url,kind,markers) in sources.items():
 f=D/(key+'.html')
 try:
  raw=f.read_text(encoding='utf-8') if f.exists() else p.fetch(url)
  assert len(raw)>1000 and not re.search('client challenge|just a moment',raw[:4000],re.I)
  body=p.text(raw);assert all(m in body for m in markers),(key,[m for m in markers if m not in body])
  f.write_text(raw,encoding='utf-8');receipts[key]={'source_page':url,'source_kind':kind,'local_source':str(f.relative_to(R)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'actual_body_retrieved':True,'semantic_markers_checked':markers};print(key,'actualbody',flush=True)
 except Exception as ex:receipts[key]={'source_page':url,'source_kind':kind,'actual_body_retrieved':False,'error':str(ex)};print(key,str(ex),flush=True)
(D/'source-receipts.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
