#!/usr/bin/env python3
"""Build the WireCraft project page for a GitHub Pages /docs deployment."""
import argparse
import csv
from html import escape
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
WEB = ROOT / 'web'
OUT = ROOT / 'docs'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--release', action='store_true')
args = parser.parse_args()
data = json.loads((ROOT / 'content/site.json').read_text())
used_assets = {'assets/favicon.svg'}

def text(value):
    return escape(str(value), quote=True)

def link(value):
    if urlsplit(value).scheme not in ('https', 'http'):
        raise ValueError(f'Expected an HTTP(S) URL: {value!r}')
    return text(value)

def asset(value):
    path = (WEB / value).resolve()
    if not value.startswith('assets/') or not path.is_relative_to((WEB/'assets').resolve()) or not path.is_file():
        raise ValueError(f'Missing or invalid local asset: {value!r}')
    if path.stat().st_size >= 100 * 1024 * 1024:
        raise ValueError(f'Asset exceeds GitHub single-file limit: {value}')
    used_assets.add(value)
    return text(value)

def media(item, eager=False):
    src = asset(item['src'])
    if not item.get('alt'):
        raise ValueError('Each image/video requires a description.')
    if item['type'] == 'video':
        poster = f' poster="{asset(item["poster"])}"' if item.get('poster') else ''
        visual = f'<video controls playsinline preload="none"{poster} aria-label="{text(item["alt"])}"><source src="{src}" type="video/mp4"><a href="{src}">Download this video</a>.</video>'
    elif item['type'] == 'image':
        loading = 'eager" fetchpriority="high' if eager else 'lazy'
        visual = f'<a class="figure-link" href="{src}" target="_blank" rel="noopener" aria-label="Open full-size image: {text(item["alt"])}"><img src="{src}" alt="{text(item["alt"])}" loading="{loading}" decoding="async"></a>'
    else:
        raise ValueError('Unknown media type.')
    caption = f'<figcaption>{text(item["caption"])}</figcaption>' if item.get('caption') else ''
    return f'<figure class="media">{visual}{caption}</figure>'

def table(columns, rows, caption):
    header = ''.join(f'<th scope="col">{text(c)}</th>' for c in columns)
    body = ''
    for row in rows:
        if len(row) != len(columns):
            raise ValueError('Table row width does not match headings.')
        body += '<tr>' + f'<th scope="row">{text(row[0])}</th>' + ''.join(f'<td>{text(c)}</td>' for c in row[1:]) + '</tr>'
    return f'<div class="results-table-wrap" role="region" aria-label="{text(caption)}" tabindex="0"><table class="results-table"><caption>{text(caption)}</caption><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>'

if args.release and data['preview']:
    raise SystemExit('Set preview to false before a release build.')
for field in ('abstract', 'affiliations', 'authors', 'tasks', 'bibtex'):
    if not data.get(field):
        raise ValueError(f'Required content is missing: {field}')

author_html = []
for author in data['authors']:
    if len(author_html) == 5:
        author_html.append('<span class="author-break" aria-hidden="true"></span>')
    name = f'<a href="{link(author["url"])}">{text(author["name"])}</a>' if author.get('url') else text(author['name'])
    marker = str(author['affiliation']) + ('*' if author.get('equalContribution') else '')
    author_html.append(f'<span>{name}<sup>{marker}</sup></span>')
affiliations = '<div class="affiliations">' + ''.join(f'<p><sup>{i+1}</sup> {text(a)}</p>' for i,a in enumerate(data['affiliations'])) + '<p class="contribution-note">* Equal contribution</p></div>'

panels = []
for i, task in enumerate(data['tasks']):
    ident = task['id']
    if not re.fullmatch('[a-z][a-z0-9-]*', ident):
        raise ValueError('Task IDs must be lowercase slugs.')
    simulation = ''
    if task.get('simulation'):
        simulation = f'<div class="simulation-demo"><p class="media-tag">General simulation environment · synchronized camera views</p>{media(task["simulation"])}</div>'
    panels.append(f'<article class="task-panel" id="task-{ident}" aria-labelledby="task-title-{ident}"><div class="task-copy"><div class="task-heading"><p class="task-number">TASK 0{i+1}</p><h3 id="task-title-{ident}">{text(task["title"])}</h3><p class="task-subtitle">{text(task["eyebrow"])}</p></div><p class="task-description">{text(task["description"])}</p></div><div class="task-demo"><p class="media-tag">Physical UR5 · three views · original playback speed</p>{media(task["media"])}</div><p class="task-criterion"><strong>Success criterion</strong>{text(task["criterion"])}</p>{simulation}</article>')

real = list(csv.DictReader((ROOT/'content/real-robot.csv').open()))
mixtures = ['R','R+S','R+P','R+S+P']
task_specs = [('insertion','Connector insertion'),('routing','1-clip routing'),('seating','Straight-channel seating')]
charts = []
for task_id, title in task_specs:
    records = [r for r in real if r['task']==task_id]
    descriptions = []
    for row in records:
        k,n = int(row['successes']),int(row['trials'])
        pct = 100*k/n
        assert abs(pct-float(row['success_rate_percent'])) < 0.00001
        descriptions.append(f'{row["training_data"]} {row["metric"]}: {pct:g}% ({k}/{n})')
    alt = title + '. ' + '; '.join(descriptions) + '. Blue marks each metric’s highest rate, including ties.'
    src = asset(f'assets/media/hardware-{task_id}.svg')
    charts.append(f'<figure class="result-chart"><h4>{title}</h4><p class="chart-subtitle">20 trials per condition</p><img src="{src}" alt="{text(alt)}" loading="lazy" decoding="async"></figure>')
hardware = '<div class="hardware-charts">'+''.join(charts)+'</div>'
hardware += '<p class="data-key"><strong>R</strong> real demonstrations <span>·</span> <strong>S</strong> scripted simulation <span>·</span> <strong>P</strong> State PPO simulation</p>'
hardware += '<p class="chart-key"><span aria-hidden="true"></span>Blue marks the highest observed rate for each metric, including ties.</p>'

sim = json.loads((ROOT/'content/simulation-cross-task.json').read_text())
sim_rows = []
for task in ('routing','seating'):
    records = [r for r in sim['rows'] if r['task']==task]
    sim_rows.append([records[0]['task_label'].capitalize()] + [f'{r["mean_percent"]:.2f} ± {r["sd_percent"]:.2f}' for r in records])
simulation = table(['Task','State PPO','ACT','DiT VLA'],sim_rows,'Simulation · success rate (%), mean ± standard deviation')
simulation += '<p class="result-note">ACT and DiT VLA use three evaluation seeds and the final training checkpoint, with 1,600 scripted trajectories for routing and 1,000 for seating. State PPO uses privileged state; RL results use three seeds. Per-seed rollout counts for these tasks are not specified in the paper. Values after ± are standard deviations, not confidence intervals.</p>'
values = {
    'PAGE_TITLE':text(data['title']+': '+data['subtitle']), 'DESCRIPTION':text(data['intro']),
    'ROBOTS':'<meta name="robots" content="noindex, nofollow">' if data['preview'] else '',
    'TITLE':text(data['title']), 'SUBTITLE':text(data['subtitle']), 'VENUE':text(data['venue']),
    'SECONDARY_VENUE':text(data['secondaryVenue']), 'AUTHORS':' '.join(author_html), 'AFFILIATIONS':affiliations,
    'GITHUB':link(data['links']['github']), 'PAPER':link(data['links']['paper']), 'PDF':asset(data['links']['localPaper']),
    'RELEASE_NOTE':text(data['releaseNote']), 'HERO_MEDIA':media(data['hero']['media'],eager=True),
    'TLDR':text(data['tldr']), 'ABSTRACT':text(data['abstract']), 'TASK_PANELS':''.join(panels),
    'METHOD_DESCRIPTION':text(data['method']['description']), 'METHOD_MEDIA':media(data['method']['media']),
    'METHOD_POINTS':''.join('<div><h3>'+text(p['title'])+'</h3><p>'+text(p['description'])+'</p></div>' for p in data['method']['points']),
    'REAL_SUMMARY':text(data['results']['realSummary']), 'REAL_RESULTS':hardware,
    'SIM_RESULTS':simulation,
    'INSERTION_FIGURE':media(data['results']['insertionMedia']),
    'SCOPE':text(data['results']['scope']), 'BIBTEX':text(data['bibtex']),
}
html = (ROOT/'templates/index.html').read_text()
for key,value in values.items():
    html = html.replace('@@'+key+'@@',value)
if re.search(r'@@[A-Z_]+@@',html):
    raise ValueError('Unfilled template token.')
# docs/ is generated; publish only files used by the page, not unused source media.
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir()
for relative in sorted(used_assets | {'styles.css', 'site.js'}):
    destination = OUT / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(WEB / relative, destination)
(OUT/'index.html').write_text(html)
(OUT/'.nojekyll').write_text('\n')
(OUT/'robots.txt').write_text('User-agent: *\n'+('Disallow: /\n' if data['preview'] else 'Allow: /\n'))
(ROOT/'PREVIEW.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=docs/index.html"><title>WireCraft project preview</title><p><a href="docs/index.html">Open the WireCraft project page</a></p></html>')
print(f'Built {OUT / "index.html"}.')
