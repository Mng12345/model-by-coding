# 02 — Rendering the teardown film with HyperFrames

HyperFrames turns an HTML page into a video: the page is loaded headless, driven frame by frame, and encoded.
Nothing in the page is allowed to run on wall clock time; the frame you ask for is the frame that gets rendered, which is also why the same page can be screenshot for verification.

The example project pins `hyperframes@0.9.36` in `video/package.json`:

```json
"scripts": {
  "dev": "npx --yes hyperframes@0.9.36 preview",
  "check": "npx --yes hyperframes@0.9.36 check",
  "snapshot": "npx --yes hyperframes@0.9.36 snapshot",
  "render": "npx --yes hyperframes@0.9.36 render"
}
```

## 0. Project shape

```
video/
  index.html              root composition (the film)
  hyperframes.json        project config
  meta.json               { id, name, createdAt }
  assets/
    vendor/*.min.js       three.js and gsap, vendored + minified
    fonts/*.woff2         local fonts, no network at render time
    audio/mix.wav         one mixed track
    director.js           pure timing functions (optional but recommended)
  compositions/           blocks/components, if the registry is used
  renders/                render output, git-ignored
```

`hyperframes.json` in the example sets `paths` (`blocks`, `components`,
`assets`) and `media.autoProxy`; keep the file that `hyperframes init`/`add`
writes and only edit paths if the directories really moved.

## 1. The render contract, item by item

1. **Root composition element.** One element declares the film:

   ```html
   <div id="root"
        data-composition-id="main"
        data-start="0"
        data-duration="43.5"
        data-width="1920"
        data-height="1080">
   ```

   `data-duration` is the length the renderer, the checker and the exporter all
   trust. A mismatch with the director's `DURATION` is the most common "the film
   ends early" bug.

2. **A paused GSAP timeline, registered by id.** The page must expose
   `window.__timelines["main"]` (the composition id) and keep it paused. The
   timeline exists to give the renderer a seekable playhead, not to animate DOM:

   ```js
   var driver = { t: 0 };
   var tl = gsap.timeline({ paused: true });
   tl.to(driver, {
     t: DURATION, duration: DURATION, ease: "none",
     onUpdate: function () {
       var t = tl.time();
       if (Math.abs(t - lastTime) > 1e-4) seek(t);
     },
   }, 0);
   window.__timelines = window.__timelines || {};
   window.__timelines["main"] = tl;
   tl.seek(0);
   ```

3. **Redraw on `hf-seek`.** The renderer dispatches a DOM event carrying the
   target time; the Three.js scene must be updated from that event only:

   ```js
   window.addEventListener("hf-seek", function (e) { seek(e.detail.time); });
   seek(0);
   ```

   `seek(t)` clamps `t` to `[0, DURATION]`, calls the director, applies the
   state to the scene API and calls `render()`. There is no animation loop in
   the page, and the scene bundle must not start one either.

4. **Media is a clip; everything else is animated by the timeline.** The canvas,
   label layer and cards can live statically in the composition and be animated
   from the GSAP timeline — the example marks only the `<audio>` element as a
   clip. Anything with its own independent start and duration (audio, video, an
   inserted scene) carries `class="clip"` plus `data-start` and `data-duration`
   (seconds); the checker uses those attributes to know what is on screen when.
   Do not sprinkle clip attributes onto decorative divs.

5. **Audio is a clip.** One `<audio>` element, one mixed file:

   ```html
   <audio id="soundtrack" class="clip"
          data-start="0" data-duration="43.5"
          data-track-index="10" data-volume="1"
          src="assets/audio/mix.wav"></audio>
   ```

   `data-track-index` separates it from other audio clips. Do not build a
   soundtrack out of twenty elements when one mix will do.

6. **Text floor is 28 px at 1080p.** The checker's craft pass flags type below
   28 px (2.6% of the 1080 px short side) that stays on screen for 0.5 s or
   more. Labels are the usual offender; size them for a phone screen, not for
   the editing monitor.

7. **Fonts are local and blocked.** Use `@font-face` with
   `font-display: block` and files under `assets/fonts/`. Re-seek once the fonts
   are ready, otherwise the first captured frames use a fallback face:

   ```js
   if (document.fonts && document.fonts.ready) {
     document.fonts.ready.then(function () { seek(lastTime < 0 ? 0 : lastTime); });
   }
   ```

8. **The model bundle is vendored and minified.** Put the built IIFE at
   `assets/vendor/model.bundle.min.js` (or any path under a `vendor/`
   directory). The checker's lint pass skips `.min.js` files and anything under
   `vendor/` or `node_modules/` when scanning for non-deterministic code, which
   is exactly why a 0.5 MB three.js bundle must not be loaded as an unminified
   `fan.bundle.js` from the project root.

9. **No wall clock, anywhere.** No `requestAnimationFrame`, no
   `setTimeout`/`setInterval`, no `Date.now()`/`performance.now()`, no
   `Math.random()`. All of these are lint errors (see §6); when third-party code
   needs entropy, vendor it as `.min.js` and drive every visual value from `t`.

The resulting page is deterministic: same `t`, same pixels.

## 2. The directing layer

Keep the film's logic in a plain script (`assets/director.js`), outside the
model bundle and outside the composition markup. The example's director is a
set of pure functions:

- `DURATION` — one number, also used for `data-duration` and the timeline.
- `PARTS` — the part id list, in explode order.
- `SHOTS` — an array of `{ name, start, end, view(u) }`; `u` is the shot's
  normalised progress, so each shot's camera is a continuous function of time
  and cuts between shots are hard cuts.
- `getFrame(t)` — returns `{ view, spin, exploded, explodeMap, lift, labels,
  title, end }` for a time; no side effects.
- `apply(ctl, t)` — pushes a frame into the scene API and returns the anchors
  and frame, so the page code stays trivial.

Explosion timing is also data. In the example: `EXPLODE_START = 21.15`, `EXPLODE_STAGGER = 0.30`; `REASSEMBLE_START = 33.98`, `REASSEMBLE_STAGGER = 0.25`, `REASSEMBLE_DUR = 1.2`, seats from `REASSEMBLE_TOUCH = 35.18` at `0.25 s` per part (final seat at 38.45); lift ramps `21.15 + 3.0` up and `33.9 + 3.6` down with a peak of `0.256 m`.
The sound cues read the same constants, which is how the audio stays in sync without hand-tuned numbers.

Labels are a separate layout pass: `getAnchors()` gives screen-space anchors
with a `visible` flag, `layoutLabels(anchors, frame)` decides which labels to
draw, where to put them and how to route the leader lines. Because anchors are
projected from the real 3D state, labels follow the parts through the explode.

## 3. Storyboard

Write the shot list before animating. The example, 43.5 s at 1920×1080 and
30 fps:

| # | shot | start | end | content | camera |
| --- | --- | --- | --- | --- | --- |
| 1 | title | 0.0 | 2.0 | title card over the assembled fan | slow push, yaw −26 → −20, dist 1.06 |
| 2 | orbit | 2.0 | 9.0 | full 360° reveal of the front | yaw −22 + 360° over the shot, dist 1.04 → 0.96 |
| 3 | grille-macro | 9.0 | 12.5 | rib geometry and cap | dist 0.62 → 0.56, pitch 12 → 5 |
| 4 | back-3q | 12.5 | 16.0 | rear cage, control box, cable | 3/4 rear view |
| 5 | hub-macro | 16.0 | 18.5 | blades behind the grille | close, slight pitch |
| 6 | wide | 18.5 | 21.0 | whole object, settled | wide, level |
| 7 | explode | 21.0 | 29.5 | 13 parts separate, labels appear | pull back while lifting |
| 8 | exploded-hold | 29.5 | 34.0 | the separated stack, labels steady | slow drift |
| 9 | reassemble | 34.0 | 39.5 | parts return and seat | reverse camera, lower |
| 10 | end | 39.5 | 43.5 | end card | settle, dist ~1.1 |

A workable rhythm is: two shots to establish, three to inspect, one wide before
the mechanism, then the long explode/hold/reassemble, then a short end card.
The explode gets the most seconds because it is the only part a still photo
cannot show.

## 4. Audio

- Deliver one `assets/audio/mix.wav`. In the example it is 43.500000 s,
  48 kHz, 16-bit stereo, measured −16.0 LUFS integrated with true peak
  −2.0 dBTP.
- Place it once at `data-start="0"` as shown above. HyperFrames does not mix
  multiple tracks for you; do the mix outside and hand over the result.
- Contact cues: one release and one close per part plus a final seat in the
  example, derived from the constant list in §2 (13 release, 13 close, 1 final
  seat = 27 contact cues, mixed with a fan whirr bed and room tone). Put every
  cue within a few milliseconds of the visual hit — the example's spec uses
  ≤ 5 ms.
- Verify sync by measuring, not by ear: `work/verify_mix.py` in the example
  reads the mix, compares each event's peak with the director constants
  (27/27 within ±5 ms, worst 0.854 ms) and cross-checks with `ebur128`.
- Music licences matter, and so does the Content ID mark. The example's first bed was a
  Pixabay track whose page carries "Content ID Registered" — the licence allows
  commercial use, but a platform claim is still possible. It was replaced with a
  track whose page shows no such mark, and the mix was rebuilt around it; the foley was
  synthesised locally, partly because Pixabay's sound-effect downloads were blocked by
  a Turnstile check. Read the mark per track (it follows the uploader, not the
  individual track) before publishing; a claim on a demo video is not worth the risk.

## 5. Command cycle

Verified against 0.9.36 on this machine:

| command | what it does | output |
| --- | --- | --- |
| `npx --yes hyperframes@0.9.36 preview` | studio/preview server for the composition | local URL (port 3002 by default) |
| `npx --yes hyperframes@0.9.36 check` | headless contract/craft/lint/contrast/audio pass at 9 sampled times | `.hyperframes/artifacts/checks/<uuid>.json` |
| `check --json` | the same report on stdout | pipe/redirect it |
| `check --at 21.15,27.6` | sample exactly those seconds | same report |
| `check --range 21,30` | sample a window | same report |
| `npx --yes hyperframes@0.9.36 snapshot --at 27.6` | grab stills | `.hyperframes/artifacts/snapshots/<uuid>/frame-00-at-27.6s.png`, `contact-sheet.jpg` |
| `npx --yes hyperframes@0.9.36 render --quality delivery` | encode the film | `renders/<project>_<YYYY-MM-DD>_<HH-MM-SS>.mp4` |

Details worth remembering:

- `check` samples 9 times by default (`--samples`), caps output at 80 findings
  (`--max-issues`), times out after 45 s (`--timeout`), and runs the contrast
  pass by default (`--contrast`). It prints progress to stderr and writes the
  report to the artifact path it logs.
- `snapshot --at` produces the requested frame and also a last frame of the
  film; both land in the same snapshot directory.
- `render --quality` accepts `draft`, `looks`, `delivery` (`looks` is the
  default CRF 16; `delivery` is the high-quality one to ship). `--fps` accepts
  1–240 and defaults to the root's `data-fps`, else 30.
- Exit codes are not a full contract check: always read the report JSON with
  `scripts/hf_read_check.py`, and gate CI with `--fail-on-error`.

A cycle that keeps the project honest:

1. `check --at <times of the risky moments>` until `ok: true` and no errors.
2. `snapshot --at <the same times>` and look at the stills.
3. `render --quality delivery`, then verify the file exists, is not tiny, and
   its duration matches `data-duration` (`ffprobe -v error -show_entries
   format=duration -of default=noprint_wrappers=1 <file>`).

## 6. Failure modes

| check code / symptom | cause | fix |
| --- | --- | --- |
| `requestanimationframe_in_composition` | the page or bundle drives itself with rAF | remove the loop; redraw from `hf-seek` only |
| `non_deterministic_code` | `Math.random()` / `Date.now()` in project code (or unminified vendor code) | seed or remove; vendor third-party bundles as `.min.js` under `assets/vendor/` |
| `text_below_floor` | type under 28 px for 0.5 s+ | raise size or shorten the label |
| `film_silent` | no audio clip | add the mix as an audio clip |
| `canvas_content_at_edge` (info) | composition bleeds off the 1920×1080 frame | intentional? then leave it; otherwise pull the camera back |
| report `ok: false` with only warnings | craft/audio warnings | read them; warnings still ship, but fix the loud ones |
| render ends early / trailing black | `data-duration` ≠ director `DURATION` | one number, both places |
| first frames show fallback font | seek before fonts ready | re-seek in `document.fonts.ready` |
| render is slow but check is fast | `--quality delivery` + 4096 shadow map | render draft first, delivery last |
