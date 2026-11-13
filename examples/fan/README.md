# Example: thirteen-part desk fan

This folder is the worked example that the skill's references are based on. It is a real
deliverable, not a mock: a 144 mm USB desk fan was photographed six times, rebuilt as a
single-file Three.js scene written by hand, rendered as a 43.5 second teardown film with
HyperFrames, and checked against the photographs with headless-Chrome screenshots.

Nothing here was imported from a modelling tool. The geometry is code.

## What was produced

| Item | Value |
| --- | --- |
| Parts in the model | 13 |
| Film length | 43.5 s, 1305 frames at 30 fps, 1920x1080 |
| Photographs used | 6 (one front three-quarter, five angle shots) |
| Audio | -16.0 LUFS integrated, true peak -1.9 dBTP, LRA 2.7 LU |
| Foley cues | 27, each within +/-5 ms of its visual event |
| Documented deviations from the photos | 7 |

The largest known deviation: the head centre in the model sits at 1.02 D above the base
(where D is the head diameter), while the photographs measure 1.04-1.10 D. The model is
therefore slightly more compact than the real object. All seven deviations are listed in
the case study notes that ship with the article; the point of listing them is that the
verification loop is honest about what it could not match.

## Layout

```
examples/fan/
├─ src/                     three.js scene and UI, written by hand
│   ├─ fan-scene.js         geometry: 13 parts, materials, lighting, exploded positions
│   ├─ director.js          camera moves and per-frame timeline used by the film
│   └─ fan-ui.js            the inspection UI of the standalone HTML build
├─ video/                   HyperFrames project (renders the film)
│   ├─ index.html           composition root, data-duration, clips
│   ├─ assets/director.js   the same director, compiled for the film
│   ├─ assets/vendor/       three.js bundle + GSAP, minified (lint skips .min.js)
│   ├─ assets/fonts/        Inter / Inter Tight, OFL 1.1 (license texts alongside)
│   └─ assets/audio/        foley synthesis scripts + sources.md (no binary audio in git)
├─ reference/               6 photographs; brand and model labels blurred on purpose
├─ out/                     poster, contact sheet, 6-angle review sheet, per-angle renders
└─ tools/                   4 measurement scripts (one runs as-is, three are provenance)
```

## Rebuild the film

The mixed audio track is a Release asset, because binary audio does not belong in git.

```bash
# 1. fetch the mix from the latest release
curl -L -o examples/fan/video/assets/audio/mix.wav \
  https://github.com/Mng12345/model-by-coding/releases/latest/download/mix.wav

# 2. render
cd examples/fan/video
npx --yes hyperframes@0.9.36 check
npx --yes hyperframes@0.9.36 render --quality delivery
```

`check` must report zero issues before rendering. The output lands in
`video/renders/video_<timestamp>.mp4`.

## Re-run the verification

The six per-angle renders in `out/verify2/` are checked in, so the review sheet can be
regenerated without a browser:

```bash
cd examples/fan
python tools/review_sheet.py     # writes out/review-sheet.png
```

Each row of the sheet is one camera angle: the photograph on the left, the model on the
right, both cropped to their own silhouette bounding box and fitted to the same tile, so
size and position are directly comparable. This is the check that caught the head-height
deviation.

To regenerate the renders themselves, screenshot the scene with headless Chrome at the
same camera angles (see `scripts/view.html` and the parameter table in
`references/03-verify.md`), then re-run the sheet.

## Regenerate the audio

`video/assets/audio/work/` holds the scripts that synthesised the foley and mixed the
track: `synth_foley.py`, `synth_beds.py`, `build_mix.py`, `master.py`, `verify_mix.py`.
They need the source music file, which is not redistributed here; read
`video/assets/audio/sources.md` for what the track is and where it came from.

## Notes

- The photographs are of a commercially sold fan. The brand and model labels were
  deliberately blurred before publishing, and the model carries no branding. This is a
  geometry study, not an endorsed reproduction.
- Product photos from shopping sites were consulted while modelling but are **not**
  redistributed in this repository; only the author's own six photographs are.
- Photographs and the rendered frames are licensed CC BY 4.0; code is MIT. See
  `../../README-LICENSES.md`.
