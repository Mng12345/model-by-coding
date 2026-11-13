---
name: model-by-coding
description: Use when a real object must become a code-built 3D model with a rendered teardown video and a looping GIF — measure the object from photographs, model it in Three.js code, verify every pose against the photos with headless screenshots, and render the film with HyperFrames 0.9.36.
---

# model-by-coding

Build a 3D model of a physical object from photographs, entirely in code, then
turn it into a teardown film and a GIF. The pipeline is opinionated about one
thing: the model is verified against the photos at every step, so the film shows
the object that was photographed rather than something plausible.

## When to use

- a hard-surface product (fan, lamp, speaker, camera, tool, kitchen appliance)
  should be explained or shown apart in a short video;
- the object exists physically and can be photographed from several angles;
- the output is a looping teardown clip for a README, a post, or a demo reel;
- an existing photo set must become an editable, re-renderable model — not a
  scanned mesh.

## When not to use

- photorealistic assets are needed: use photogrammetry or a scanner instead;
- the object is organic, soft, or deforms (fabric, plants, faces);
- no photographs are available, or the object is only visible in a video;
- a single still image is enough — the HyperFrames steps are then unnecessary;
- the subject is a text/UI animation: this pipeline is about geometry.

## Pipeline

| step | produce | acceptance gate |
| --- | --- | --- |
| 1. Measure | one ruler dimension, a ratio table, a `DIM` object | ratios cross-checked on ≥2 photos, every assumption marked inferred |
| 2. Model | a code-built Three.js scene, one IIFE bundle, the viewer page | assembled state has no gaps; `p = 1` separates every part |
| 3. Verify | six same-pose photo/render sheets | silhouette and feature ratios within tolerance on all six |
| 4. Film | a HyperFrames composition, `check` report, delivery MP4 | `ok: true`, no errors, duration matches `data-duration` |
| 5. Cut | a looping GIF | starts and ends on settled poses, under ~1 MB |

A realistic budget for one object is a few hours to two days, most of it in
steps 2–3. Skipping step 3 is what turns a week of modelling into a wrong model
delivered on time.

## Step 1 — Measure from the photos

Collect six poses (front, true side, back, back 3/4, top, bottom), pick one
large dimension as the ruler, measure it with a radial scan, and express
everything else as a ratio of it. Count discrete features (ribs, blades, spokes)
from their angular period rather than by eye. Keep every number in one `DIM`
object with a comment naming its source photo and whether it is measured or
inferred; absolute real-world size is a decision, not a measurement.

Depth: [`references/01-modeling.md`](references/01-modeling.md) §0–2.

## Step 2 — Model in code

One scene module with a pure-state API: `create`, `setView`, `setExplode`,
`setExplodeMap`, `setSpin`, `setHeadTilt`, `setLift`, `render`, `getAnchors`,
`resize`, `dispose`. World convention: object faces +Z, base on y = 0, metres.
Build housings as lathe profiles, the grille as flat ribbons (not round tubes),
blades as parametric sheets, and register every part through one function that
stores its assembled position, explosion offset and anchor offset. Name the
parts once; the film, labels, anchors and sound all key off those names.

Depth: [`references/01-modeling.md`](references/01-modeling.md) §3–6.

## Step 3 — Verify against the photos

Build the bundle with esbuild, render one frame per pose in headless Chrome, and
compare each render with its photo as a side-by-side sheet cropped to the
object's bounding box. Read proportions and part placement as fractions of each
object's own box; do not fit circles to edges on a busy background — the fit
latches onto background arcs. Six poses, a few iterations each.

Depth: [`references/03-verify.md`](references/03-verify.md).

## Step 4 — Render the film

Build the composition to the HyperFrames contract: a root composition element
with `data-duration`, a paused GSAP timeline at `window.__timelines["main"]`,
Three.js redrawn only from `hf-seek` (never from rAF/timers), media with its own
timing marked as `class="clip"` with `data-start`/`data-duration`, one audio mix
as an audio clip, text at 28 px or larger, and the big bundle vendored as
`assets/vendor/*.min.js`. Write the shot list before animating; drive camera,
explosion and labels from one director script so audio cues can share its
constants. Run `check`, read the report, then `render --quality delivery`.

Depth: [`references/02-render.md`](references/02-render.md).

## Step 5 — Cut the GIF

Pick a 3–4 s settled segment (usually the exploded hold), cut it in gif-master
(width 480, 12 fps, loop) or with the ffmpeg two-pass palette command, and verify
size, frame count and loop before posting. Depth:
[`references/04-gif.md`](references/04-gif.md),
[`scripts/make_gif.md`](scripts/make_gif.md).

## Hard constraints

These are the rules that break the pipeline when violated; they are not style
preferences.

1. **Contract first.** Object faces +Z, base on y = 0, metres, camera
   `target + dist * (sin(yaw)cos(pitch), sin(pitch), cos(yaw)cos(pitch))`,
   yaw/pitch in degrees. Every script and the film share it.
2. **Pure state.** The scene API must render the same state to the same pixels.
   No animation loop, no wall clock, no `Math.random()` in code the frame
   depends on.
3. **Frame = f(t).** Camera, explosion, spin, labels, cards and sound are all
   functions of the film time; nothing else.
4. **Composition contract.** `data-composition-id`, `data-start`,
   `data-duration`, `data-width`, `data-height` on the root element; paused
   timeline registered as `window.__timelines["<id>"]`; redraw inside
   `hf-seek` using `e.detail.time`.
5. **Clips.** Media with its own start and duration (audio, video, inserts)
   carries `class="clip"`, `data-start`, `data-duration`; audio additionally
   `data-track-index`. DOM animated by the timeline needs no clip attributes.
6. **Legibility.** Nothing informational below 28 px at 1080p (the checker's
   type floor is 28 px = 2.6% of the short side).
7. **Vendored weights.** three.js and GSAP as `.min.js` under
   `assets/vendor/`; local fonts; no network during render.
8. **Scripts are generic.** No object name, no absolute path, no personal
   directory in `scripts/`; each script must run from a fresh checkout.
9. **Verify commands.** Every command and parameter written into docs, scripts
   or the film must be executed once against the pinned versions before it is
   trusted.

## Reference routing

| task | read |
| --- | --- |
| measuring, ratios, lathe profiles, grille/blade parameters, parts, explosion, anchors | [`references/01-modeling.md`](references/01-modeling.md) |
| composition contract, director/storyboard, audio sync, HyperFrames commands and outputs | [`references/02-render.md`](references/02-render.md) |
| screenshot loop, comparison sheets, reading angles, the circle-fit failure | [`references/03-verify.md`](references/03-verify.md) |
| gif-master operation card, credits, ffmpeg GIF recipe | [`references/04-gif.md`](references/04-gif.md) |
| repository, GitHub Release, community-list PR, YouTube/X | [`references/05-publish.md`](references/05-publish.md) |
| symptom → cause → fix catalogue (lighting, shadows, ribs, type, bundles, Chrome) | [`references/06-gotchas.md`](references/06-gotchas.md) |

Tools shipped with this skill:

| file | role |
| --- | --- |
| [`scripts/view.html`](scripts/view.html) | single-frame viewer; pose and bundle from query params |
| [`scripts/verify_sheet.py`](scripts/verify_sheet.py) | photo-vs-render side-by-side sheet (`--photo --render --out --bbox`) |
| [`scripts/hf_read_check.py`](scripts/hf_read_check.py) | summarise a HyperFrames check report; `--fail-on-error` for CI |
| [`scripts/make_gif.md`](scripts/make_gif.md) | browser/ffmpeg operation card for the GIF |

## Minimal runnable sequence

The commands run from the repository root against the worked example in
`examples/fan/`; for a new object, substitute `src/scene.js`, `photos/` and
`video/`. Working files go to `%TEMP%` so the checkout stays clean. Keep the
parameters — they are the verified ones. Run in PowerShell.

```powershell
$work = Join-Path $env:TEMP "mbc-verify"; New-Item -ItemType Directory -Force $work | Out-Null

# 1. bundle the scene (template for a new object; needs `three` installed).
#    The example ships its bundle at examples/fan/video/assets/vendor/fan.bundle.min.js,
#    so this step can be skipped for the example.
npx --yes esbuild@0.24.2 src/scene.js --bundle --format=iife --global-name=Scene `
  --minify --target=chrome120 --outfile=dist/scene.bundle.min.js

# 2. screenshot one verification pose of the example (1920x1080, fresh profile per run)
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$png = Join-Path $work "front.png"
$udd = Join-Path $env:TEMP ("view-" + [guid]::NewGuid().ToString("N"))
& $chrome --headless=new --use-angle=d3d11 --window-size=1920,1080 `
  --hide-scrollbars --virtual-time-budget=12000 `
  --screenshot=$png --user-data-dir=$udd `
  "file:///$(($PWD.Path).Replace('\','/'))/scripts/view.html?bundle=../examples/fan/video/assets/vendor/fan.bundle.min.js&yaw=-10&pitch=12&dist=0.85&ty=0.185&fov=30&noshadow=1"

# 3. compare that render with the front photograph at the same pose
python scripts/verify_sheet.py --photo examples/fan/reference/fan.jpg --render $png `
  --out (Join-Path $work "front-sheet.png") --bbox "130,245,1195,1455"

# 4. check the film against the HyperFrames contract, then read the report
Set-Location examples/fan/video
# needs assets/audio/mix.wav (Release asset; see examples/fan/README.md)
npx --yes hyperframes@0.9.36 check --at 21.15,27.6,35.18
$report = Get-ChildItem .hyperframes/artifacts/checks/*.json |
  Sort-Object LastWriteTime | Select-Object -Last 1
python ../../../scripts/hf_read_check.py $report.FullName --fail-on-error
npx --yes hyperframes@0.9.36 snapshot --at 29.6

# 5. render the delivery master
npx --yes hyperframes@0.9.36 render --quality delivery
Set-Location ../../..

# 6. cut the GIF with ffmpeg (browser route: scripts/make_gif.md)
$mp4 = (Get-ChildItem examples/fan/video/renders/*.mp4 | Sort-Object LastWriteTime | Select-Object -Last 1).FullName
ffmpeg -hide_banner -loglevel error -y `
  -ss 29.6 -t 3.8 -i "$mp4" `
  -vf "fps=12,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=sierra2_4a" `
  -loop 0 (Join-Path $work "teardown.gif")
```

Step 3 prints the two crop boxes; the verified run prints
`saved ...\front-sheet.png  1112x702  | photo (130, 245, 1195, 1455)  | render (652, 264, 1252, 1080)`.

Outputs to expect: `check` writes
`video/.hyperframes/artifacts/checks/<uuid>.json`; `snapshot` writes
`video/.hyperframes/artifacts/snapshots/<uuid>/frame-00-at-29.6s.png`; `render`
writes `video/renders/video_<YYYY-MM-DD>_<HH-MM-SS>.mp4` (about 36 MB for 43.5 s
at 1920×1080/30 fps, roughly 2.5 minutes of capture with a hardware GPU).

## Requirements

- Node.js (tested 22.19.0) with `npx`; esbuild 0.24.2 via npx.
- Python 3.11 (tested 3.11.1) with Pillow for the sheet; numpy optional.
- ffmpeg on PATH (tested with a 2025-12-28 git build).
- Chrome for headless screenshots (tested 157.0.8103.40); the path above is the
  Windows default.
- HyperFrames pinned to 0.9.36 via `npx --yes hyperframes@0.9.36`.
- `check` and `render` drive headless Chrome with `--browser-gpu` on auto:
  hardware GPU when present, software (SwiftShader) otherwise; `preview` is
  smoother with a GPU.

## Definition of done

- six comparison sheets read acceptably, with the deviations listed and
  explained;
- `hf_read_check.py --fail-on-error` exits 0 on the final check report;
- the delivery MP4 exists and its duration equals the composition's
  `data-duration`;
- the GIF loops cleanly and is small enough to post;
- every command in this skill has been run once in a fresh checkout.
