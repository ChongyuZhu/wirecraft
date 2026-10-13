#!/usr/bin/env python3
"""Build the WireCraft project page for a GitHub Pages /docs deployment."""
import argparse
import csv
from html import escape
import json
import math
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

def wilson(k, n):
    z = 1.959963984540054
    p = k/n
    center = (p+z*z/(2*n))/(1+z*z/n)
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return 100*(center-half), 100*(center+half)

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
        simulation = f'<details class="simulation-example"><summary>See the parallel simulation</summary>{media(task["simulation"])}</details>'
    panels.append(f'<article class="task-panel" id="task-{ident}" aria-labelledby="task-title-{ident}"><div class="task-copy"><div class="task-heading"><p class="task-number">TASK 0{i+1}</p><h3 id="task-title-{ident}">{text(task["title"])}</h3><p class="task-subtitle">{text(task["eyebrow"])}</p></div><p class="task-description">{text(task["description"])}</p></div><div class="task-demo"><p class="media-tag">Physical UR5 · three views · original playback speed</p>{media(task["media"])}</div><p class="task-criterion"><strong>Success criterion</strong>{text(task["criterion"])}</p>{simulation}</article>')

real = list(csv.DictReader((ROOT/'content/real-robot.csv').open()))
mixtures = ['R','R+S','R+P','R+S+P']
task_specs = [('insertion','Connector insertion','insert'),('routing','1-clip routing','task success'),('seating','Straight-channel seating','task success')]
charts, interval_rows = [], []
for task_id, title, metric in task_specs:
    bars = []
    for i, mixture in enumerate(mixtures):
        row = next(r for r in real if r['task']==task_id and r['training_data']==mixture and r['metric']==metric)
        k,n = int(row['successes']),int(row['trials'])
        pct = 100*k/n
        assert abs(pct-float(row['success_rate_percent'])) < 0.00001
        low,high = wilson(k,n)
        bars.append(f'<div class="bar-row mixture-{i}"><span class="bar-label">{text(mixture)}</span><span class="bar-track" aria-hidden="true"><span style="width:{pct:g}%"></span></span><span class="bar-value">{pct:g}% <small>{k}/{n}</small></span></div>')
        interval_rows.append([title,mixture,f'{k}/{n}',f'{pct:g}%',f'{low:.1f}–{high:.1f}%'])
    charts.append(f'<div class="result-chart"><h4>{title}</h4><p class="chart-subtitle">Task success · 20 trials per condition</p>{"".join(bars)}</div>')
hardware = '<div class="hardware-charts">'+''.join(charts)+'</div>'
hardware += '<p class="data-key"><strong>R</strong> real demonstrations <span>·</span> <strong>S</strong> scripted simulation <span>·</span> <strong>P</strong> State PPO simulation</p>'
hardware += '<details class="result-details"><summary>Trial counts and 95% confidence intervals</summary><p>Wilson binomial intervals, calculated from the reported successes and trials. Each condition has 20 hardware trials; these intervals describe sampling uncertainty, not a paired significance test.</p>' + table(['Physical task','Training data','Successes / trials','Success rate','95% Wilson interval'],interval_rows,'Physical UR5 · ACT task success') + '</details>'

sim = json.loads((ROOT/'content/simulation-cross-task.json').read_text())
sim_rows = []
for task in ('routing','seating'):
    records = [r for r in sim['rows'] if r['task']==task]
    sim_rows.append([records[0]['task_label'].capitalize()] + [f'{r["mean_percent"]:.2f} ± {r["sd_percent"]:.2f}' for r in records])
simulation = table(['Task','State PPO','ACT','DiT VLA'],sim_rows,'Simulation · success rate (%), mean ± standard deviation')
simulation += '<p class="result-note">ACT and DiT VLA use three evaluation seeds and the final training checkpoint, with 1,600 scripted trajectories for routing and 1,000 for seating. State PPO uses privileged state; RL results use three seeds. Per-seed rollout counts for these tasks are not specified in the paper. Values after ± are standard deviations, not confidence intervals.</p>'
insertion = json.loads((ROOT/'content/simulation-insertion.json').read_text())
insertion_rows = [[r['connector'],r['policy'],f'{r["reach_mean_percent"]:.2f} ± {r["reach_sd_percent"]:.2f}',f'{r["insert_mean_percent"]:.2f} ± {r["insert_sd_percent"]:.2f}'] for r in insertion['full_connector_rl_matrix']]
insertion_table = '<details class="result-details"><summary>Results across four connector geometries</summary>'+table(['Connector','Policy','Reach (%)','Insert (%)'],insertion_rows,'Simulation · 3 mm clearance · mean ± standard deviation across three seeds')+'</details>'
baseline_rows = [[r['policy'],f'{r["reach_mean_percent"]:.2f} ± {r["reach_sd_percent"]:.2f}',f'{r["insert_mean_percent"]:.2f} ± {r["insert_sd_percent"]:.2f}'] for r in insertion['ethernet_style_all_baselines']]
insertion_table += '<details class="result-details"><summary>Insertion values and evaluation protocol</summary>'+table(['Policy','Reach (%)','Insert (%)'],baseline_rows,'Simulation · Ethernet-style connector · 3 mm clearance')+'<p>Reach: the held connector comes within 2 cm of the socket. Insert: the connector tip seats in the socket. RL uses three seeds. Insertion imitation-learning and VLA baselines use four evaluation seeds × 16 rollouts per checkpoint; results are the best observed among three reach-selected checkpoints, selected on evaluation rollouts. Their training budgets differ. All ± values are standard deviations.</p></details>'

values = {
    'PAGE_TITLE':text(data['title']+': '+data['subtitle']), 'DESCRIPTION':text(data['intro']),
    'ROBOTS':'<meta name="robots" content="noindex, nofollow">' if data['preview'] else '',
    'TITLE':text(data['title']), 'SUBTITLE':text(data['subtitle']), 'VENUE':text(data['venue']),
    'SECONDARY_VENUE':text(data['secondaryVenue']), 'AUTHORS':' '.join(author_html), 'AFFILIATIONS':affiliations,
    'GITHUB':link(data['links']['github']), 'PAPER':link(data['links']['paper']), 'PDF':asset(data['links']['localPaper']),
    'RELEASE_NOTE':text(data['releaseNote']), 'HERO_MEDIA':media(data['hero']['media'],eager=True),
    'INTRO':text(data['intro']), 'ABSTRACT':text(data['abstract']), 'TASK_PANELS':''.join(panels),
    'METHOD_DESCRIPTION':text(data['method']['description']), 'METHOD_MEDIA':media(data['method']['media']),
    'METHOD_POINTS':''.join('<div><h3>'+text(p['title'])+'</h3><p>'+text(p['description'])+'</p></div>' for p in data['method']['points']),
    'REAL_SUMMARY':text(data['results']['realSummary']), 'REAL_RESULTS':hardware,
    'REAL_PROTOCOL':text(data['results']['realProtocol']), 'SIM_RESULTS':simulation,
    'INSERTION_FIGURE':media(data['results']['insertionMedia']), 'INSERTION_TABLE':insertion_table,
    'SCOPE':text(data['results']['scope']), 'BIBTEX':text(data['bibtex']),
    'REAL_CSV':asset('assets/data/real-robot-success.csv'), 'SIM_CSV':asset('assets/data/simulation-cross-task.csv'),
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
