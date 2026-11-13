# Asset licenses

`model-by-coding` mixes code, photographs and rendered media, and it vendors third-party libraries. This file states which license applies to which part, how to attribute the media, and what the third-party terms are. The root [`LICENSE`](LICENSE) file carries the MIT text; this file is the longer explanation referenced from its closing note.

## At a glance

| Path | What it is | License |
| --- | --- | --- |
| `SKILL.md`, `README*.md`, `references/**`, `scripts/**` | This skill's instructions, documentation and tools | MIT |
| `examples/fan/src/**`, `examples/fan/video/index.html`, `examples/fan/video/assets/director.js`, `examples/fan/tools/**` | The example's model, timeline and tooling, written for this project | MIT |
| `examples/fan/reference/**` | Six photographs of the fan | CC BY 4.0 |
| `examples/fan/out/**` | Poster, contact sheet, review sheet, per-angle renders | CC BY 4.0 |
| `fan-teardown-43s.mp4` (Release asset) | The rendered film | CC BY 4.0, with the music caveat below |
| `examples/fan/video/assets/vendor/fan.bundle.min.js` | three.js plus the model, minified | MIT (three.js) |
| `examples/fan/video/assets/vendor/gsap.min.js` | GSAP 3.13.0 | GreenSock standard license |
| `examples/fan/video/assets/fonts/*.woff2` | Inter and Inter Tight webfonts | SIL Open Font License 1.1 |
| Audio files | No binary audio is tracked; `mix.wav` is a Release asset | See [Audio](#audio) |

Anything not listed here — configuration files, JSON metadata, the example's notes — is covered by the MIT license unless it contains third-party material.

## MIT — code and text

The MIT license covers the skill itself: `SKILL.md`, the READMEs, the reference notes, the scripts, the example's source and the example's tooling. The full text is in [`LICENSE`](LICENSE).

In short: use, copy, modify, merge, publish, distribute, sublicense and sell the code, provided the copyright notice and permission notice are kept. The software is provided without warranty.

The model geometry was written by hand for this project; it was not imported from a modelling application and it is not a copy of the product's CAD data.

## CC BY 4.0 — photographs and rendered media

The following are licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0), as noted at the end of [`LICENSE`](LICENSE):

- the six reference photographs: `examples/fan/reference/fan.jpg` and the five files under `examples/fan/reference/angles/`;
- the still images under `examples/fan/out/`: `poster.png`, `contact-sheet.png`, `review-sheet.png` and the six renders under `out/verify2/`;
- the film `fan-teardown-43s.mp4`, distributed as an asset of the `v1.0.0` release.

CC BY 4.0 allows sharing and adaptation, including for commercial use, provided attribution is given and changes are indicated. No additional restrictions may be applied.

### Attribution

A usable attribution for the media above:

```
model-by-coding — Mng12345
https://github.com/Mng12345/model-by-coding
Licensed under CC BY 4.0: https://creativecommons.org/licenses/by/4.0/
Changes: <describe any crop, recolor or re-edit, or write "none">
```

For a video or article that uses the film or a still, the credit can be placed in the description, the credits or the figure caption, as long as it is reachable and includes the source link and the license.

Two points about the photographs: the fan is a commercially sold product, and its brand and model labels were blurred before publication. The model carries no branding. This is a geometry study, not an endorsed reproduction, and the MIT and CC BY grants cover the author's photographs, code and renders — not any design rights or trademarks of the product's manufacturer.

## Third-party components

The example vendors two JavaScript libraries and two font families. They keep their own licenses; the MIT and CC BY grants above do not replace them.

| Component | Where | License |
| --- | --- | --- |
| [three.js](https://threejs.org) | Bundled into `examples/fan/video/assets/vendor/fan.bundle.min.js`, together with the model code | MIT. License text: https://github.com/mrdoob/three.js/blob/dev/LICENSE |
| GSAP 3.13.0 | `examples/fan/video/assets/vendor/gsap.min.js` | GreenSock standard license. The file keeps its banner: "Copyright 2025, GreenSock. All rights reserved. Subject to the terms at https://gsap.com/standard-license" |
| Inter, Inter Tight | `examples/fan/video/assets/fonts/` (`inter-latin-400-normal.woff2`, `inter-latin-500-normal.woff2`, `inter-tight-latin-600-normal.woff2`) | SIL Open Font License 1.1. The license texts ship next to the fonts: `LICENSE-Inter-OFL.txt` and `LICENSE-InterTight-OFL.txt` |
| HyperFrames 0.9.36 | Not vendored — it is the renderer the film was produced with | See the project's repository for its license: https://github.com/heygen-com/hyperframes. Project site: https://hyperframes.heygen.com |
| gif-master.com | Not vendored — it is the browser tool used in step 4 | The site's own terms: https://gif-master.com |

The minified `fan.bundle.min.js` is a build output: it contains three.js and the example's scene module. The file itself carries no license banner, so a redistribution should include the three.js MIT text linked above next to the bundle.

None of these components are modified by the MIT license of this repository, and none of them change the license of the code they are combined with.

## Audio

No audio binary is committed to the repository. The `.gitignore` excludes `*.wav` and `*.mp3`, and the mixed track `mix.wav` ships only as a Release asset, so a fresh clone has to download it before rendering (see the README's quick start). The un-mixed source music is not redistributed at all.

The soundtrack of the example is built from two source layers, then mixed:

1. **Original synthesized foley and ambience.** 27 plastic-mechanism sounds, a fan whirr loop and a room-tone loop were synthesized from scratch by `examples/fan/video/assets/audio/work/synth_foley.py` and `synth_beds.py`. No samples were used, so there is no third-party audio right in these layers.
2. **Music: "Minimal Technology" by fugu_vibes.** Downloaded from the Pixabay music library: https://pixabay.com/music/ambient-minimal-technology-623485/. It is used under the Pixabay Content License, which allows free use, including commercial use, without attribution; the current terms are on the track page and the Pixabay site.

The mix itself is built by `work/build_mix.py` and `work/master.py`, which cut, compress, EQ and master the layers into the 43.5 s track.

The film's soundtrack therefore contains third-party music even though the repository tracks no music file. The CC BY 4.0 license on the film covers the author's contribution; it does not relicense the music. If the film is republished, the Pixabay terms still apply to that track.

Two practical notes from `examples/fan/video/assets/audio/sources.md`:

- The track page is marked **Content ID Registered**. Publishing the film on platforms with automatic content matching may trigger a claim even though the Pixabay license permits the use. Check before publishing, or replace the track.
- The foley is synthesized, not recorded. It is not a sample library and carries no restriction beyond the project's own licensing.

`examples/fan/video/assets/audio/sources.md` records the full provenance: source files, processing chain, measured loudness, per-cue timing and the self-check results.

## Fonts

Inter and Inter Tight are distributed under the SIL Open Font License 1.1. The complete license texts are checked in beside the font files:

- `examples/fan/video/assets/fonts/LICENSE-Inter-OFL.txt`
- `examples/fan/video/assets/fonts/LICENSE-InterTight-OFL.txt`

If the fonts are redistributed separately from this repository, keep those notices with them. They are not covered by the MIT license.

## What the licenses do not cover

- **The product itself.** The reference photographs show a commercially sold fan. Nothing here grants rights to the product's design, trademarks or trade dress, and there is no affiliation with or endorsement by its manufacturer.
- **Product photos from shopping sites.** Product images were consulted while modelling, but none of them are redistributed. Only the author's six photographs are in the repository.
- **Third-party audio beyond the mix.** The source music file is not in the repository; only the mixed track is distributed, and only through the Release.
- **Downstream uses of third-party components.** If you extract the fonts, GSAP or three.js from this repository, their own licenses — not the MIT license of this skill — govern that use.

## Questions

If a reuse is not covered by the terms above, open an issue at https://github.com/Mng12345/model-by-coding/issues before reusing the material. For the third-party components, ask their maintainers; this repository cannot grant rights it does not hold.
