"""Collect authentic source-site names offline for the general credits panel."""
import hashlib
import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

def domains_in(value):
    domains = set()
    if isinstance(value, dict):
        for child in value.values(): domains.update(domains_in(child))
    elif isinstance(value, list):
        for child in value: domains.update(domains_in(child))
    elif isinstance(value, str):
        for url in re.findall(r'https?://[^\s<>"\x27]+', value):
            try:
                host = (urlsplit(url).hostname or '').lower().rstrip('.')
            except ValueError:
                continue
            if not host or '.' not in host or not re.fullmatch(r'[a-z0-9.-]+', host): continue
            if host.endswith(('.local', '.localhost', '.invalid', '.test', '.example')) or host in ('example.com', 'example.net', 'example.org'):
                continue
            try:
                ipaddress.ip_address(host)
                continue
            except ValueError:
                pass
            if host == 'wikipedia.org' or host.endswith('.wikipedia.org'): host = 'www.wikipedia.org'
            domains.add(host)
    return domains

def generate(root):
    files = [root/'content/catalog.json', root/'content/human-history.json', root/'content/credits.json']
    culture_audio = root/'content/culture-memories.json'
    if culture_audio.is_file(): files.append(culture_audio)
    trophy_sources = root/'assets/trophies/sources-credits.json'
    if trophy_sources.is_file(): files.append(trophy_sources)
    domains = set()
    for p in files: domains.update(domains_in(json.loads(p.read_text(encoding='utf-8'))))
    # Merge the site's literal bare/www spellings only when actually observed.
    domains = {host for host in domains if not (host.startswith('www.') and host[4:] in domains)}
    ordered = sorted(domains, key=lambda host: (host != 'www.wikipedia.org', host.removeprefix('www.')))
    text = ' | '.join(ordered)
    output = root/'src/museum/feature_resources.hpp'
    header = '// Source-site names generated offline by tools/build-feature-resources.py.\n// SPDX-License-Identifier: GPL-3.0-or-later\n#pragma once\nnamespace museum {\n'
    for p in files: header += '// '+p.relative_to(root).as_posix()+' SHA256 '+hashlib.sha256(p.read_bytes()).hexdigest()+'\n'
    header += 'inline constexpr const char* feature_resources_sites=R"sites('+text+')sites";\n'
    header += 'inline constexpr unsigned feature_resources_site_count='+str(len(ordered))+';\n}\n'
    encoded = header.encode('utf-8')
    if not output.exists() or output.read_bytes() != encoded:
        output.write_bytes(encoded)
    return ordered, output

if __name__ == '__main__':
    sites, output = generate(Path(__file__).resolve().parents[1])
    print('Authentic unique source sites:', len(sites), '; generated header bytes:', output.stat().st_size)
