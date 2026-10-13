# WireCraft project website

[Visit the project page](https://chongyuzhu.com/wirecraft/).

Project page for **WireCraft: A Simulation Benchmark for Industrial DLO Manipulation** (CoRL 2026 Spotlight).

This repository hosts the project website. The research-code repository is [WireManip/WireCraft](https://github.com/WireManip/WireCraft); its code release is planned for early November 2026, before CoRL.

## Edit and build

The site uses plain HTML, CSS, and JavaScript. Python 3.9+ builds the page without package installation.

```sh
python3 build.py --release
python3 validate.py
python3 -m http.server 8767 --directory docs
```

Edit `content/` for website text and reported results, `templates/index.html` for page structure, and `web/` for styles, interactions, and prepared assets. Rebuild `docs/` after changes.

`docs/` is the GitHub Pages publication directory. Configure Pages to deploy from `main` → `/docs`. Keep asset URLs relative and retain `.nojekyll`.

## Results and media

Simulation and physical-UR5 results are reported separately. Physical results include counts from 20 trials per condition and calculated Wilson 95% binomial intervals. Simulation uncertainty is reported as standard deviation, with protocol notes on the page. Task recordings are illustrative examples, without an assigned training mixture or checkpoint. The three task sections are visible in sequence; optional simulation recordings can be expanded. Physical videos place the same trial’s handheld, wrist, and side views in three equal-width horizontal panels using constant timing offsets estimated from motion events (approximately ±0.25 s), with no playback-speed change.

The CSV downloads summarize reported results; they are not the training-trajectory dataset. The paper link includes the latest submitted camera-ready PDF. The unversioned arXiv link is retained for future revisions.
