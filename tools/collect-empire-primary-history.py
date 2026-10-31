"""Collect public project history and explicit author-photo links for identity review."""
from pathlib import Path
import urllib.request,re,json,hashlib
from urllib.parse import urljoin
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/empire1972-existing-prose-primary-history'
base.mkdir(parents=True,exist_ok=True)
rows=[]
for filename,url in [('project-history.html','https://www.wolfpackempire.com/history.html'),
    ('langston-1978-info.txt','https://empserver.sourceforge.net/1978infofile.txt')]:
    path=base/filename
    if not path.exists():
        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(request,timeout=25)as response:data=response.read()
        path.write_bytes(data)
    text=path.read_text(encoding='utf8',errors='replace')
    rows.append(dict(file=path.relative_to(ROOT).as_posix(),url=url,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    if filename.endswith('.html'):
        for href,label in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',text,re.S|re.I):
            if 'photograph' in re.sub('<[^>]+>','',label).lower()or 'langston'in href.lower():
                print(json.dumps(dict(link=urljoin(url,href),label=re.sub('<[^>]+>','',label))))
(base/'source-downloads.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
