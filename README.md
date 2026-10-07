# MASK / Agent Lab

A static, bilingual research showcase for native agent-assisted lithographic mask optimization. Built for GitHub Pages; no frontend build, external fonts, analytics, API keys, or runtime dependencies.

## Website

The publication target is https://nanwang-ee.github.io/agent-mask-optimization-site/ after GitHub Pages deployment succeeds.

- Side-by-side, smooth-crossfade animation of the **retained** Astra masks in `coldstart15_case1` and `coldstart15_case2`, including initial state and all 15 proposal rounds. MP4 / WebM for playback, downloadable GIF, and a 16-position frame scrubber.
- Observe → propose → simulate → accept/rollback workflow.
- Actual Case 1, round 1 input images, prompt instructions, an input summary and a clearly labelled excerpt of the final proposal. Full geometry, full simulator state, raw prompt context, runtime events and internal reasoning streams are not published.
- Interactive EPE, PVB and squared-L2 curves for Astra 6, Sol 6, Sol 5.6, with an optional Astra SRAF-guidance comparison.
- Two-case comparison with original and reproduced baselines from OpenILT ASICON 2023, Tables I and II (page 3).
- Downloadable CSV, JSON and publication figures in SVG / PDF / PNG.

## Run locally

```sh
python -m http.server 8765
```

Open http://localhost:8765. The static content also works from `index.html` without fetching JSON; `data/site-data.js` packages the published data for the browser.

## GitHub Pages deployment

In this repository, open **Settings → Pages → Build and deployment → Source → GitHub Actions**. The included workflow publishes the repository's static website. If the first run occurred before Pages was enabled, re-run **Deploy static website to GitHub Pages** from Actions. No secrets are needed.

The workflow stages only `index.html`, `style.css`, `app.js`, `.nojekyll`, `assets/`, and `data/` for the deployed website. All asset paths are relative, so project-subpath hosting works.

## Data interpretation

- Website round 1 is stored experiment `iteration: 0`; round 0 is the original target / mask.
- Each curve and animation frame uses the actual retained mask after acceptance or rollback. Rejected candidates are not used as improvements. Invalid proposals still consume a proposal round.
- SRAF guidance is **off** for the main Astra animation. SRAF edits were permitted but none were proposed in these two original Astra trajectories. This is not a run with SRAF operations disabled.
- EPE is the upstream evaluator's nominal violation count at 15 nm. Squared L2 is nominal binary image error; PVB is the difference area between max/min process-corner binary prints. At 1 nm/grid, binary pixel sums are in nm².
- The optimization accepts lexicographic `(EPE, L2)` improvement subject to geometry, printing checks and a fixed PVB ceiling of `1.6 × original target PVB`. Case 1 / 2 ceilings are 73,398.4 / 59,256 nm². This does not monotonically minimize all three metrics.
- Each model/strategy/case has one trajectory. Astra is a historical reference. Equal proposal counts do not imply equal tokens, costs or elapsed times.
- The paper table uses **case1 and case2**, not the paper's 10-case averages. Original GAN-OPC EPE was not reported and remains null. `Our` in the paper is labelled `OpenILT reproduction` here.
- The paper comparison is contextual, not a claim of controlled, identical experimental conditions or a general model ranking. No baseline experiments were rerun for this website.
- The animation fades are visual transitions, not evaluated intermediate physical masks. Both case panels use the same fixed coordinate crop and scale; the vertical axis is flipped from array display to preserve x-right/y-up coordinates.

## Traceability and regeneration

`data/provenance.json` records SHA-256 hashes and workspace-relative source paths. `data/animation.json` records each displayed frame's retained source and acceptance state. Public inputs contain instruction text, input images and a summary only. Public proposal examples are labelled excerpts. Complete prompt context, geometry and simulation state remain in the local ignored `private-evidence/` folder and are excluded from deployment.

To regenerate figures and exported data, place this folder as `website/` beside the original experiment's `runs/` and `results/` folders, install NumPy, Pillow and Matplotlib, and run:

```sh
python scripts/build_assets.py
python scripts/package_data.py
```

To regenerate MP4 from GIF, use FFmpeg:

```sh
ffmpeg -y -i assets/optimization.gif -vf 'fps=30,format=yuv420p' -c:v libx264 -crf 19 -movflags +faststart assets/optimization.mp4
```

The exporter reads cached results only; it makes no model calls and performs no new optical simulation. The original complete experiment repository is not required to view or deploy the published website.

## Sources

- [OpenILT paper, ASICON 2023](https://www.cse.cuhk.edu.hk/~byu/papers/C179-ASICON2023-OpenILT.pdf), page 3, Tables I and II.
- [OpenILT upstream implementation](https://github.com/OpenOPC/OpenILT), experiment-recorded revision `dabb97c6ca3dfd159362e48273c436444c77353b`.
- Local experiments: `results/model15_study/{summary,rounds}.csv`, `runs/coldstart15_case{1,2}/`, and their stored first-round artifacts.

The exporter also retains a local-only copy of original evidence in `private-evidence/`; this directory must never be included in the public deployment.
