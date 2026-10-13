#!/usr/bin/env python3
"""Check the generated static site, its assets, and its GitHub project-site paths."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit, urljoin

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / 'docs'

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.refs = []
        self.images = []
        self.videos = []
        self.tables = 0
    def handle_starttag(self, tag, pairs):
        a = dict(pairs)
        if 'id' in a:
            self.ids.append(a['id'])
        for key in ('src','href','poster'):
            if a.get(key):
                self.refs.append(a[key])
        if tag == 'img':
            self.images.append(a)
        if tag == 'video':
            self.videos.append(a)
        if tag == 'table':
            self.tables += 1

html = (DOCS / 'index.html').read_text()
page = Page()
page.feed(html)
assert len(page.ids)==len(set(page.ids)), 'Duplicate HTML IDs'
assert page.images and all(i.get('alt') for i in page.images), 'Missing alt text'
assert len(page.videos)==6, 'Expected three physical and three simulation videos'
assert all('controls' in v and 'playsinline' in v and v.get('aria-label') for v in page.videos)
assert all('autoplay' not in v for v in page.videos)
local = set()
external = set()
for ref in page.refs:
    url = urlsplit(ref)
    if url.scheme:
        assert url.scheme in ('https','http'), f'Unexpected URL scheme: {ref}'
        external.add(ref)
        continue
    assert not url.netloc and not url.path.startswith('/'), f'Root-relative link would break project site: {ref}'
    resolved = urlsplit(urljoin('https://example.invalid/wirecraft/', ref))
    assert resolved.path.startswith('/wirecraft/'), ref
    if url.path:
        path = (DOCS / unquote(url.path)).resolve()
        assert path.is_relative_to(DOCS.resolve()) and path.is_file(), f'Missing asset: {ref}'
        local.add(url.path)
    elif url.fragment:
        assert url.fragment in page.ids, f'Missing anchor: {ref}'
for placeholder in ('@@','Template preview','Media slot','Abstract slot','localhost','/Users/'):
    assert placeholder not in html, f'Unfinished/local-only content: {placeholder}'
assert (DOCS / '.nojekyll').exists()
assert not (DOCS / 'CNAME').exists()
files = sorted(p for p in DOCS.rglob('*') if p.is_file())
assert not any(p.is_symlink() for p in DOCS.rglob('*'))
assert all(p.stat().st_size < 100*1024*1024 for p in files)
published = {str(p.relative_to(DOCS)) for p in files}
assert published <= local | {'index.html','robots.txt','.nojekyll'}, 'Unreferenced file in publication directory'
paper = DOCS / 'assets/paper/wirecraft-camera-ready.pdf'
assert hashlib.sha256(paper.read_bytes()).digest()==hashlib.sha256((ROOT/'web/assets/paper/wirecraft-camera-ready.pdf').read_bytes()).digest()
report = {
    'status':'passed',
    'html_ids':len(page.ids), 'local_references':len(local), 'external_links':sorted(external),
    'images':len(page.images), 'videos':len(page.videos), 'tables':page.tables,
    'project_subpath':'All local links resolve under /wirecraft/.',
    'publication_files':len(files), 'publication_bytes':sum(p.stat().st_size for p in files),
    'largest_file_bytes':max(p.stat().st_size for p in files),
    'paper_sha256':hashlib.sha256(paper.read_bytes()).hexdigest(),
    'checks':['unique IDs','local assets and anchors exist','described images and controlled videos','no template placeholders','relative subpath-safe URLs','only referenced assets published','no CNAME or symlinks','all files below 100 MiB'],
}
(ROOT/'audit').mkdir(exist_ok=True)
(ROOT/'audit/static-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
