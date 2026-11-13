English · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [Deutsch](README.de.md)

# model-by-coding

An Agent Skill for rebuilding a physical object from photographs as a deterministic three.js model, then turning that model into a teardown film and a GIF without opening a 3D modelling application.

The repository is the skill itself: instructions an agent can follow, reusable scripts, long-form reference notes, and one complete worked example — a white USB desk fan rebuilt as code and rendered as a 43.5 s film with 13 parts at 1920×1080 and 30 fps.

- [What this is](#what-this-is)
- [What problem it solves](#what-problem-it-solves)
- [The four-step pipeline](#the-four-step-pipeline)
- [Quick start](#quick-start)
- [Repository layout](#repository-layout)
- [Scripts](#scripts)
- [Known limitations](#known-limitations)
- [License](#license)
- [Acknowledgements and links](#acknowledgements-and-links)

## What this is

An Agent Skill is a directory an agent can load: a `SKILL.md` entry point, plus whatever notes and scripts the task needs. This repository has four parts:

| Part | Contents |
| --- | --- |
| `SKILL.md` | The entry point: when the skill applies, the pipeline, and the rules that are not optional. |
| `references/` | Six long-form notes with the details that do not fit in a skill file: modelling, rendering, verification, GIF export, publishing, and a list of traps. |
| `scripts/` | Reusable tooling: a single-frame viewer, a photo-versus-render comparison sheet, a check-output reader, and the GIF operation card. |
| `examples/fan/` | The worked example, with its photographs, model source, HyperFrames project, verification renders and outputs. |

The example is not a mock. The photographs are the author's own; the model is written by hand in JavaScript; the film is rendered from that model; and the six-angle comparison sheet is checked in. Together they show what the instructions produce when followed end to end. [examples/fan/README.md](examples/fan/README.md) records the numbers, including the deviations that were not fixed.

Read `SKILL.md` first. The references are the parts that need more room:

| File | Topic |
| --- | --- |
| `references/01-modeling.md` | Coordinate system, measured proportions, lathe profiles, grille and blade parameters, per-part anchors. |
| `references/02-render.md` | The HyperFrames rendering contract, the shot table, and the audio sync points. |
| `references/03-verify.md` | Headless capture, bounding-box comparison, angle-by-angle review, and the failed overlay experiment. |
| `references/04-gif.md` | The gif-master step-by-step card, its credit limits, and an ffmpeg fallback. |
| `references/05-publish.md` | Publishing checklists and the practical gates for the places the output usually goes. |
| `references/06-gotchas.md` | Among other things: tone mapping and exposure, light falloff, shadow banding, grille ribs that must be flat ribbons rather than round tubes, the minimum text size, and vendored `.min.js` files. |

## What problem it solves

An agent asked for "a 3D model of this object" tends to produce one of two things: a single good-looking render that cannot be checked, or a mesh with arbitrary proportions and no route to a video. Both are hard to review. The camera of a render is usually unknown, so it cannot be placed next to the photograph; and the asset cannot be re-derived after a change.

This skill replaces that with a loop that leaves evidence at every step.

1. **Proportions are measured, not guessed.** Every constant in the model is either traced to a measurement on a photograph or marked as inferred. The ratio, not the absolute size, is what carries over.
2. **A frame is reproducible.** The model exposes plain state — camera pose, explosion amount, blade spin — and nothing else. No clock, no randomness, no network. The same inputs produce the same frame, so a review can refer to an exact camera pose.
3. **The check compares like with like.** Each render is captured from the camera pose of a reference photograph, and both sides are cropped to their own silhouette bounding box and scaled to the same tile. Framing and distance stop hiding proportion errors.
4. **One model feeds every deliverable.** The same bundle drives the verification stills, the interactive page and the film, so a fix in the model appears everywhere.
5. **The result is reviewable in git.** The model is code and named constants. Changes are diffs, not binary assets.

It is not:

- photogrammetry or a 3D scanner — no geometry is reconstructed automatically;
- CAD — the dimensions are proportions traceable to photographs, not measurements of the physical object;
- a Blender replacement or a general modelling tool;
- a hosted service, and it ships no model weights.

## The four-step pipeline

Each step produces an artifact that the next step consumes. The order below keeps measurement inside step 1; `SKILL.md` lists measurement as its own step, and the example started verifying early and kept re-running the check while the film was built.

### Step 1 — Model from the photographs, in code

Input: one front photograph, plus any additional angles that exist. The example uses six: a front three-quarter view and five angle shots (side-left, back, back three-quarter, bottom, top).

What the agent does:

- Measure the photograph. In the example, a radial scan of the outer rim fixes the head circle and its centre; the angular period at a fixed radius gives the grille rib count; ratios give head thickness, cap diameter, base diameter and knob diameter.
- Pick one world scale and state it as an assumption. The example uses a 190 mm head diameter and keeps every other dimension as a ratio to it.
- Build the geometry in three.js from primitives and lathe profiles: rings, struts, blades, a motor cylinder, grille ribs, base parts. Parts are separate named objects because the film moves them independently.
- Give each part an explode offset and a screen-space anchor for its leader label.
- Keep the API free of time: `setView()`, `setExplode()`, `setSpin()`, `render()`, `getAnchors()`. No `Date.now()`, no `requestAnimationFrame`, no network requests.
- Bundle the scene and three.js with esbuild into one IIFE, so the page, the viewer and the film load identical code.
- Remove branding. The model has blank label surfaces, and the reference photographs have their brand and model labels blurred for the same reason.

Output: `examples/fan/src/fan-scene.js`, and the built `examples/fan/video/assets/vendor/fan.bundle.min.js`.

### Step 2 — Render the teardown film with HyperFrames

[HyperFrames](https://github.com/heygen-com/hyperframes) turns an HTML page into a video by driving a paused timeline and capturing frames.

- `examples/fan/video/index.html` is the composition root: `data-duration="43.5"`, 1920×1080.
- A paused GSAP timeline is registered on `window.__timelines.main`. The page listens for `hf-seek` and redraws the canvas from `event.detail.time`; nothing advances on its own, so any frame can be captured.
- The 43.5 s example has ten shots: title, orbit, grille macro, rear three-quarter, hub macro, wide, explode, hold with 13 leader labels, reassemble, end card.
- The explode is one progress value per part. Releases are staggered by 0.30 s starting at 21.15 s; the reassembly touches start at 35.18 s in 0.25 s steps; the last part seats at 38.45 s. Each leader label starts fading in 0.30 s after its part starts moving (the fade itself takes 0.45 s).
- The soundtrack is cut to the same contract. The example mix is 43.5 s, 48 kHz, 16-bit stereo, −16.0 LUFS integrated with a true peak of −2.0 dBTP. `examples/fan/video/assets/audio/sources.md` lists the sources and the processing chain.
- `check` is the gate: do not render before it reports zero issues. `snapshot --at <seconds>` captures stills for inspection; the example poster is the 27.6 s frame.

Output: an MP4 in `examples/fan/video/renders/`, named `video_<YYYY-MM-DD>_<HH-MM-SS>.mp4` by default.

### Step 3 — Verify against the photographs

The check is a same-camera comparison, not a visual impression.

1. Capture the model with headless Chrome at the camera pose of a reference photograph. `scripts/view.html` takes the pose from the URL query (`yaw`, `pitch`, `dist`, `tx`, `ty`, `tz`, `fov`) and renders one frame at 1920×1080. It has no animation loop and makes no network requests of its own.
2. Crop the photograph to its hand-read box and the render to its own bounding box. In the example, the photo boxes were read from a grid overlay and the render boxes are projected analytically from the head rim and base rim. `scripts/verify_sheet.py` can also find the render box from the background colour.
3. Scale both crops to the same tile and put them side by side. Framing and distance are normalised away, so head thickness, cap diameter, rib count and base width can be compared directly.
4. Review every angle, write down the disagreements, adjust the measured constants, re-render, and repeat.

The example sheet has six rows. The documented result is a close match with seven known deviations, among them head-centre height (1.02 D in the model against 1.04–1.10 D in the photographs), a slightly wider rear-grille outer ring, and a control box a few percent too large. They are listed in the example notes instead of being hidden.

The approach also carries a recorded negative result. An earlier plan used a same-camera 50/50 overlay with the head circle fitted and normalised. Circles were first fitted across five of the photographs; in four of them the strongest curved edges belonged to the background, so the normalised radius could not be trusted. Only the front photograph, where the object fills the frame against a uniform wall, produced a usable radial scan. The overlay was dropped in favour of bounding-box comparison, and the reason is kept in `references/03-verify.md`.

This step is a visual review with explicit boxes, not a numerical certificate.

### Step 4 — Export a GIF

The final step is manual because it runs in a browser:

1. Open the tool: [video to GIF, English](https://gif-master.com/en/tools/video-to-gif) or [video to GIF, Chinese](https://gif-master.com/zh/tools/video-to-gif).
2. Add the rendered MP4. The file is processed in the browser and is not uploaded.
3. Trim to one action — an explosion or a close-up rather than the whole 43.5 s film — set the frame rate and size, and preview.
4. Export. Editing is free; downloading requires signing in, and the free allowance is 3 credits per day.

`references/04-gif.md` holds the same steps as a checklist and records an ffmpeg fallback for local conversion.

### The artifacts, in order

```
examples/fan/
├─ reference/fan.jpg, reference/angles/*.jpg    input: six photographs
├─ src/fan-scene.js                             step 1: model, materials, camera, anchors
├─ video/assets/vendor/fan.bundle.min.js        step 1: the bundle every consumer loads
├─ video/index.html, video/assets/director.js   step 2: composition and timeline
├─ video/assets/audio/mix.wav                   step 2: Release asset, not in git
├─ video/renders/*.mp4                          step 2: output, git-ignored
├─ out/verify2/*-render.png                     step 3: same-camera stills
├─ out/review-sheet.png                         step 3: six photo-versus-model pairs
├─ out/poster.png                               deliverable: 1920×1080 teardown still
└─ out/contact-sheet.png                        deliverable: 4×3 contact sheet
```

## Quick start

### Requirements

| Requirement | Used for |
| --- | --- |
| Node.js 22 (tested with 22.19.0) | Running the HyperFrames CLI and esbuild through `npx`. |
| Python 3.11 with Pillow | `scripts/verify_sheet.py` (numpy optional); `examples/fan/tools/review_sheet.py` needs numpy; the example's audio rebuild scripts use numpy and scipy. |
| ffmpeg | HyperFrames rendering, and the audio work in the example. |
| Chrome or Chromium | Headless screenshots and HyperFrames frame capture. |
| HyperFrames CLI 0.9.36 | Fetched by `npx --yes hyperframes@0.9.36`; no global install is required. |
| git | Cloning the skill and the example. |

`scripts/hf_read_check.py` uses only the Python standard library. `scripts/view.html` needs only a browser and a built model bundle.

### Install the skill

Clone the repository into a skills directory. A project-local install keeps the skill with the project that uses it; a user-wide install makes it available to every project.

```bash
# project-local
git clone https://github.com/Mng12345/model-by-coding.git .agents/skills/model-by-coding

# or user-wide
git clone https://github.com/Mng12345/model-by-coding.git ~/.agents/skills/model-by-coding
```

Agents such as DeepSeek Harness and Claude Code read skills from `.agents/skills/` in a project or `~/.agents/skills/` for the user.

If the skills CLI is available, the same installation is one command:

```bash
npx skills add Mng12345/model-by-coding
```

Start a new agent session afterwards, and name the skill (`model-by-coding`) in the request. How the skill is invoked depends on the client.

### Render the example film

The repository does not contain binary audio. Download `mix.wav` from the [latest Release](https://github.com/Mng12345/model-by-coding/releases/latest) and put it back before running the check.

```bash
# 1. put the mixed track back (asset name: mix.wav)
curl -L -o examples/fan/video/assets/audio/mix.wav \
  https://github.com/Mng12345/model-by-coding/releases/latest/download/mix.wav

# 2. check the HyperFrames project, then render
cd examples/fan/video
npx --yes hyperframes@0.9.36 check
npx --yes hyperframes@0.9.36 render --quality delivery
```

`check` must report zero issues before the render. The result is written to `examples/fan/video/renders/video_<YYYY-MM-DD>_<HH-MM-SS>.mp4`; the CLI names the file after the project directory and the render time. Add `preview` before the render if a local preview in the browser is useful:

```bash
npx --yes hyperframes@0.9.36 preview
```

To inspect a single moment instead of the whole film:

```bash
npx --yes hyperframes@0.9.36 snapshot --at 27.6
```

Snapshots are written under the project's `.hyperframes/artifacts/snapshots/` directory.

The still images shipped in `examples/fan/out/` — the poster, the 4×3 contact sheet, the six-angle review sheet and the six per-angle renders — are checked in, so they can be viewed without rendering anything.

## Repository layout

```
model-by-coding/
├─ SKILL.md                          skill entry point
├─ README.md                         this file
├─ README.zh-CN.md                   Simplified Chinese translation
├─ README.zh-TW.md                   Traditional Chinese translation
├─ README.ja.md                      Japanese translation
├─ README.de.md                      German translation
├─ README-LICENSES.md                license scope, attribution format, third-party assets
├─ LICENSE                           MIT, with the media exception noted at the end
├─ references/
│  ├─ 01-modeling.md
│  ├─ 02-render.md
│  ├─ 03-verify.md
│  ├─ 04-gif.md
│  ├─ 05-publish.md
│  └─ 06-gotchas.md
├─ scripts/
│  ├─ view.html                      single-frame viewer driven by URL query
│  ├─ verify_sheet.py                photo-versus-render comparison sheet
│  ├─ hf_read_check.py               reads the JSON form of a HyperFrames check
│  └─ make_gif.md                    gif-master operation card (documentation)
└─ examples/
   └─ fan/                           worked example; see examples/fan/README.md
      ├─ README.md                   the example's own notes, measurements and deviations
      ├─ src/
      │  ├─ fan-scene.js             geometry, materials, lighting, anchors
      │  ├─ director.js              camera moves and timeline for the film
      │  └─ fan-ui.js                inspection UI for the standalone HTML build
      ├─ video/
      │  ├─ index.html               composition root, 43.5 s
      │  ├─ hyperframes.json         HyperFrames project configuration
      │  ├─ meta.json                project id and name
      │  ├─ package.json             npx shortcuts for preview (dev), check, snapshot, render
      │  └─ assets/
      │     ├─ director.js           the director compiled for the film
      │     ├─ fonts/                Inter and Inter Tight woff2, with OFL license texts
      │     ├─ vendor/               fan.bundle.min.js and gsap.min.js
      │     └─ audio/
      │        ├─ sources.md         soundtrack sources, processing chain, measured levels
      │        └─ work/              synthesis, mixing, mastering and verification scripts
      ├─ reference/
      │  ├─ fan.jpg                  front three-quarter photograph
      │  └─ angles/                  five additional angles (side-left, back, back 3/4, bottom, top)
      ├─ tools/
      │  ├─ review_sheet.py          builds out/review-sheet.png; runs as-is
      │  ├─ grid6.py                 historical one-off measurement script
      │  ├─ measure-photo.py         historical one-off measurement script
      │  └─ expo_check.py            historical one-off measurement script
      └─ out/
         ├─ poster.png               1920×1080 teardown still
         ├─ contact-sheet.png        4×3 contact sheet of the film
         ├─ review-sheet.png         six photo-versus-model pairs
         └─ verify2/                 six per-angle renders, 1920×1080 each
```

## Scripts

| Path | Kind | What it does |
| --- | --- | --- |
| `scripts/view.html` | Browser page | Renders one frame of a code-built model at a camera pose taken from the URL. Parameters: `bundle`, `global`, `yaw`, `pitch`, `dist`, `tx`, `ty`, `tz`, `fov`, `explode`, `spin`, `tilt`, `lift`, `w`, `h`, `dpr`, `bg`; the per-part debug flags `noshadow`, `hide` and `only` are passed through to the bundle. |
| `scripts/verify_sheet.py` | Python | Crops a photograph and a render to their own bounding boxes, scales both to the same tile, and writes one side-by-side comparison image. Requires `--photo`, `--render`, `--out` and a hand-read `--bbox x0,y0,x1,y1`; optional `--render-bbox` (auto-detected from the background by default), `--bg`, `--threshold`, `--pad` (default `0.04`), `--tile` (default `520x620`), `--gap`, `--label-height`, `--label-photo`, `--label-render`. Pillow is required; numpy only speeds up the background mask. |
| `scripts/hf_read_check.py` | Python | Reads a HyperFrames check report — either the JSON that `check --json` prints or the artifact HyperFrames saves under `.hyperframes/artifacts/checks/` — and prints `ok` plus finding counts by section (lint, runtime, layout, motion, contrast, craft, audio). `--max` limits printed findings, `--json` prints the summary as JSON, `--fail-on-error` exits non-zero when the report failed. Standard library only; accepts UTF-8 and UTF-16 reports. |
| `scripts/make_gif.md` | Documentation | The gif-master operation card: steps, limits, and the local ffmpeg alternative. Not executable. |

The viewer loads the bundle named in the query. The shipped example bundle is a plain IIFE, so the camera can be set directly:

```
file:///<path-to-repo>/scripts/view.html?bundle=../examples/fan/video/assets/vendor/fan.bundle.min.js&yaw=-10&pitch=12&dist=0.85&ty=0.185&fov=30
```

Capture it with headless Chrome at the same size:

```bash
chrome --headless=new --hide-scrollbars --window-size=1920,1080 \
  --screenshot=front.png \
  "file:///<path-to-repo>/scripts/view.html?bundle=../examples/fan/video/assets/vendor/fan.bundle.min.js&yaw=-10&pitch=12&dist=0.85&ty=0.185&fov=30"
```

Build a comparison sheet from the example's checked-in render:

```bash
python scripts/verify_sheet.py \
  --photo examples/fan/reference/fan.jpg \
  --render examples/fan/out/verify2/front-render.png \
  --bbox 130,245,1195,1455 \
  --out front-pair.png
```

Read a saved check report. HyperFrames saves its own copy under `.hyperframes/artifacts/checks/<uuid>.json`; the script also accepts a report captured from stdout:

```bash
cd examples/fan/video
npx --yes hyperframes@0.9.36 check --json > check.json
python ../../../scripts/hf_read_check.py check.json

# or point it at the report the CLI saved itself
python ../../../scripts/hf_read_check.py .hyperframes/artifacts/checks/<uuid>.json
```

The reusable tools are parameterised: no object names, no fan-specific paths, no absolute paths. The four scripts in `examples/fan/tools/` are the scripts actually used for the case study. `review_sheet.py` is relative-path based and runs inside the repository; `grid6.py`, `measure-photo.py` and `expo_check.py` are kept as provenance and say in their headers that their inputs are not part of this repository, so they do not run as-is.

## Known limitations

- **Proportions, not certified dimensions.** The example fixes an absolute scale at a 190 mm head diameter as a stated assumption, because the photographs carry no scale. Every other dimension is a ratio that follows from it. The model is not a measuring instrument.
- **Hidden surfaces are inferred.** Rear-grille details, motor internals, the clip-hook mechanism and parts of the base were not fully visible in the photographs. They are marked as inferred in the notes and should not be read as facts about the real product.
- **The verification is visual.** Bounding-box alignment removes framing differences, but the photo boxes are read by hand, and there is no numeric pass threshold. A sheet can look close while a detail outside the silhouette is wrong.
- **The example's conclusions are the example's.** Thirteen parts, ten shots, this timing and these deviations belong to the fan case study; they are not defaults for another object.
- **Audio is not in git.** The film references `examples/fan/video/assets/audio/mix.wav`, which ships as a Release asset. Without it the project is incomplete, so put it back before `check` or `render`.
- **Version pinning.** The commands pin `hyperframes@0.9.36`, the version the example was built with. Other versions may behave differently; no compatibility list is claimed here.
- **Three of the four example tools do not run as-is.** They are historical measurement scripts with paths to the author's original workspace. The parameterised versions are in `scripts/`.
- **The GIF step is manual.** gif-master runs in a browser, needs a sign-in to download, and allows 3 free downloads per day. The repository does not automate this step.
- **Rendering needs a real browser and ffmpeg.** HyperFrames captures frames through Chrome, so a machine without a working browser install cannot render the film.

## License

- **Code** — MIT. The full text is in [`LICENSE`](LICENSE).
- **Photographs and rendered media** — the six reference photographs under `examples/fan/reference/`, the still images under `examples/fan/out/`, and the film `fan-teardown-43s.mp4` are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attribution: **Mng12345/model-by-coding**, with a link to https://github.com/Mng12345/model-by-coding.
- **Third-party libraries and assets** keep their own licenses; the bundled three.js, GSAP, HyperFrames and the Inter/Inter Tight fonts are listed in [`README-LICENSES.md`](README-LICENSES.md).

If a use is not covered by either license, open an issue in the repository before reusing the material.

## Acknowledgements and links

- [three.js](https://threejs.org) — MIT. The model geometry, materials and renderer are three.js.
- [GSAP](https://gsap.com) 3.13.0 — used under the [GSAP standard license](https://gsap.com/standard-license). The bundled copy keeps its license header.
- [HyperFrames](https://github.com/heygen-com/hyperframes) 0.9.36 — the HTML-to-video renderer used for the film. Project site: https://hyperframes.heygen.com
- [gif-master.com](https://gif-master.com) — the browser-based video-to-GIF tool used in step 4.
- Inter and Inter Tight — webfonts under the SIL Open Font License 1.1; the license texts ship next to the font files in `examples/fan/video/assets/fonts/`.
- The reference photographs were taken by the author; brand and model labels were blurred before publication. The model carries no branding. This is a geometry study, not an endorsed reproduction.
- Repository: https://github.com/Mng12345/model-by-coding
- Film on YouTube: https://youtu.be/cwNxK5GSSjY
- Releases: https://github.com/Mng12345/model-by-coding/releases/latest
- Issues: https://github.com/Mng12345/model-by-coding/issues

The fan example is one object and one film. The parts worth reusing are the measurement notes, the same-camera check, and the serialization of the model into code — not the fan's specific numbers.
