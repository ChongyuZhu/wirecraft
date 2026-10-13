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

Simulation results appear before the physical UR5 results. The overview presents a TL;DR followed by the full abstract. Three task charts pair hatched reach and solid insert bars within connector insertion, alongside routing and seating, with counts from 20 trials per condition. Blue marks the highest observed rate for each metric, including ties. Detailed source data remain in `content/`; the introduction page has no CSV download links or expanded result tables.

Task recordings are illustrative examples, without an assigned training mixture or checkpoint. The three task sections are visible in sequence; the three simulation demos are collapsed by default below each physical example and can be opened with the "Simulation demo · wrist + side cameras" control. Closing a demo pauses its playback. Physical videos place the same trial’s handheld, wrist, and side views in three horizontal 640×480 images. The handheld recording uses a centered 4:3 crop; the wrist and side views retain their full camera frames. Constant timing offsets were estimated from motion events (approximately ±0.25 s) and checked with 12 keyframes from the final videos, with no playback-speed change.

The paper link includes the latest submitted camera-ready PDF. The unversioned arXiv link is retained for future revisions.

Simulation demos come from the wrist and side videos embedded in the WireCraft presentation, paired in a single video clock. Presentation playback timing is retained. Both views are shown as equal square images; only black pillarboxes are cropped from the source exports. These demos show the general environment without real-to-sim calibration or matching to the physical UR5 setup.
