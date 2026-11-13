# 06 — Gotchas

Every entry here was hit while building the example and is stated as symptom → cause → fix. The numbers are the values that worked, not universal constants: re-derive them per object, but start from them instead of from zero.

## 1. Tone mapping: white plastic turns either grey or a flat white sheet

**Symptom.** The shell either reads as grey cardboard, or the lit side is one
uniform white with no shading gradient. The first version used ACES and the
white plastic clipped into a flat sheet.

**Cause.** ACES filmic rolls off highlights aggressively; on a white object lit
to near-white that roll-off eats exactly the shading that describes the shape.

**Fix.** Use `THREE.NeutralToneMapping` (Khronos PBR Neutral) with
`toneMappingExposure = 0.68` and calibrate against the photo by numbers. The
example measured the head region's sRGB luma: reference photo mean 155.4,
std 29.0; render mean 187.7, std 39.0. The render sits a little brighter than
the photo on purpose (the photo is dim indoor light, the film is a studio look),
but the *spread* is in the same range, which is what preserves the shape.

Also relevant: `outputColorSpace = SRGBColorSpace`, `environmentIntensity = 0.45` with a `RoomEnvironment` PMREM, and a tone-mapped backdrop sphere instead of a flat `scene.background` (three applies fog after tone mapping in sRGB space).

**Judgement.** Do not chase a pixel-perfect luma match: matching lighting exactly makes the film look like the photo, which is not the goal. Match the contrast range, then light for readability.

## 2. A point light inside the head detonates it

**Symptom.** Adding a small fill light inside the head turns the whole grille
white; the interior looks self-lit and loses all shading.

**Cause.** three.js floors point-light attenuation at `1/0.01`, so a
"reasonable-looking" intensity of 1 is enormous at short range. The comment in
the example records exactly this: intensity near 1 detonates the whole head.

**Fix.** Treat point-light intensity as candela and stay tiny: `new THREE.PointLight(0xfff6ec, 0.010, 0.36, 2)` — intensity 0.010, distance 0.36 m, decay 2, no shadows, parented to the head pivot so it rides with the tilt.
At that value it reads as a soft bounce inside the drum and the grille slots stop going black.

## 3. Shadows on a curved shell read as banding

**Symptom.** Grey stripes across the white shell that look like a texture or a
normal-map artefact. They move when the model rotates and survive a material
change.

**Cause.** The rear cage casts a hard, low-radius shadow onto the shell. With a
small PCF radius and a tight shadow camera, the cage's shadow aliases into
bands that the eye reads as surface detail.

**Fix.** Soften and bias the one key light shadow:

```js
key.shadow.mapSize.set(4096, 4096);
key.shadow.camera.near = 0.1;   key.shadow.camera.far = 8;
key.shadow.camera.left = -0.50; key.shadow.camera.right = 0.50;
key.shadow.camera.top  =  0.50; key.shadow.camera.bottom = -0.50;
key.shadow.bias = -0.00020;
key.shadow.normalBias = 0.0030;
key.shadow.radius = 6.0;       // the rear cage's shadow must not read as banding
key.shadow.intensity = 0.66;
```

The radius is the parameter that matters; the map size only buys resolution for the same softness.
A second directional fill (0.5), a rim (1.35) and a hemisphere light (0.5) complete the setup without adding more shadow casters.

## 4. Grille ribs must be flat ribbons, not round tubes

**Symptom.** In close-ups the front grille reads as a cage of round tubes — like
a cheap toy — no matter how the material is tweaked.

**Cause.** A circular or heavily rounded cross-section produces a highlight line
down the middle of every rib. Real moulded grilles are etched flat faces with a
short bevel, and the eye recognises the flat specular shape.

**Fix.** Make ~76% of the rib width a flat crest with a small bevel and vertical
flanks. The example's profile puts the crest at `±0.38w` with the bevel starting
at `±0.46w`, and the width follows the measured pitch: 2.7 mm at the hub,
4.4 mm at mid radius, 5.6 mm at the rim against a 4.3–11.6 mm pitch. The rib
must still be a *rib*: if the flat crest is widened until the slots close, the
grille becomes a solid disc and the silhouette goes wrong.

Same idea applies to the rear cage: spokes with a short kink and flat hoops read
as stamped metal; smooth round spokes read as wire.

## 5. Type floor: 28 px

**Symptom.** `check` reports `text_below_floor`: "Type floor is 28 px (2.6% of
the 1080 px short side, what a phone can read) and N text elements stay under it
for 0.5 s or more".

**Cause.** Labels and sub-text sized on a desktop monitor. At 1080p a phone
screen makes anything under 28 px unreadable, and the checker enforces that as a
craft warning.

**Fix.** Set the smallest label to at least 28 px (32 px is a comfortable
floor), shorten the text instead of shrinking it, and verify with
`check` rather than by eye. If a small text is intentionally a texture (a logo
on the object), that is a rare exception — make it obviously decorative, not
information.

## 6. The model bundle must live in `vendor/` as `.min.js`

**Symptom.** `check` reports lint errors `non_deterministic_code` (from
`Math.random()`) and `requestanimationframe_in_composition` (from
`requestAnimationFrame`) whose `sourceFile` is your own bundle, even though your
scene code has no such calls.

**Cause.** The lint pass scans project scripts; a full three.js build contains
`Math.random` and some modules touch rAF. The pass deliberately skips minified
vendor files, but not unminified code in the project root.

**Fix.** Build with esbuild and load the file from a vendor path:

```
assets/vendor/model.bundle.min.js
```

The skip rule in hyperframes 0.9.36 is a regex on the path: it ignores `.js`
files that end in `.min.js` **or** sit under a `vendor/` or `node_modules/`
directory. Both conditions are intentional escapes for third-party code — do not
rename your own unminified code to `.min.js` to silence real findings.

## 7. Headless Chrome's exit code lies

**Symptom.** The screenshot command returns 0 but no PNG exists (observed here),
or returns 1 even though the PNG was written (reported elsewhere).

**Cause.** On this machine both were observed: a successful run exited 0, and a run that printed `Failed to write file screenshot.png: access denied (0x5)` also exited 0; the documented recipe elsewhere says success can return 1. The exit code is not a reliable pass signal.

**Fix.** Assert on the artefact, not the exit code:

```powershell
Test-Path $png                                     # must be True
python -c "from PIL import Image; import numpy as np; im=Image.open(r'$png'); a=np.asarray(im.convert('RGB')); print(im.size, round(float(a.std()),2))"
```

Require 1920×1080 and a non-trivial standard deviation. Also: absolute
`--screenshot=` path, existing parent directory, one fresh `--user-data-dir`
per run (a reused profile fails with "access denied").

## 8. Lathe profiles: degenerate points and flipped winding

**Symptom.** Missing triangles, black patches, NaN warnings, or normals inside
out on a surface of revolution.

**Cause.** A profile point at exactly `r = 0` produces degenerate triangles; a
profile that doubles back along its axis flips the winding.

**Fix.** Clamp every radius to `Math.max(0.00005, r)`, order points
monotonically along the axis, and call `computeVertexNormals()` after
`rotateX`. Use `DoubleSide` only for genuinely open surfaces; a shell built as a
closed profile (outer wall, lip, inner wall) needs no DoubleSide and shadows
correctly. Faceted moulded plastic can use `flatShading = true`.

## 9. Determinism is a rendering contract, not a style preference

**Symptom.** The check fails with `non_deterministic_code`; or renders differ
between runs; or the snapshot at 27.6 s does not match the render at 27.6 s.

**Cause.** Wall-clock time or randomness inside the frame: `Math.random()`,
`Date.now()`, `performance.now()`, `setTimeout`, `setInterval`,
`requestAnimationFrame`. The renderer seeks the page to a time and captures
whatever is there, so any value not derived from `t` is a bug.

**Fix.** Make the whole frame a pure function of `t`: camera, explosion map,
spin angle, labels, cards, audio. Keep the pure functions in a director script
and call them from the `hf-seek` handler and from the GSAP timeline's
`onUpdate` — nothing else. If randomness is needed (dust, grain), seed a PRNG
from `t`.

## 10. Check reports come in two encodings and two shapes

**Symptom.** A JSON check report fails to parse in a quick script; or a script
expects a top-level `issues` array that is not there.

**Cause.** Two independent variations: 0.9.36 writes a sectioned report
(`lint`, `runtime`, `layout`, `motion`, `contrast`, `craft`, `audio`, `hdr`,
`snapshots`, each with `findings` and `errorCount`), and a PowerShell 5.1 `>`
redirect writes that JSON as UTF-16LE with a BOM while the artifact file is
UTF-8.

**Fix.** Use `scripts/hf_read_check.py`, which normalises both shapes, counts
per-section severities, tolerates UTF-8/UTF-8-BOM/UTF-16, and can gate CI with
`--fail-on-error`. The report also carries `ok`, `strict` and
`layout.duration`; trust `ok` and the per-section counts, not the command's exit
code.

## 11. Snapshot gives you one more frame than you asked for

**Symptom.** `snapshot --at 27.6` produces `frame-00-at-27.6s.png` and a second
image at the end of the film.

**Cause.** The snapshot command captures the requested time and also the last
frame of the composition.

**Fix.** Not a bug: use the requested frame, ignore the trailing one, and keep
the `contact-sheet.jpg` next to them as a quick index. Snapshot directories are
`.hyperframes/artifacts/snapshots/<uuid>/`.

## 12. `canvas_content_at_edge` and intentional bleed

**Symptom.** `check` reports an info-level `canvas_content_at_edge` finding:
"Canvas content touches the frame edge (bottom)".

**Cause.** The composition (usually the backdrop or a card) reaches the frame
edge by design, or the object is too close to the camera and really is clipped.

**Fix.** Decide which it is. A backdrop that bleeds is fine — it is an info, not
an error. An object touching the edge is a framing bug: pull the camera back or
widen `fov`, and verify with a snapshot at the same time.

## 13. Silent film

**Symptom.** `check` warns `film_silent`: no sound source at all.

**Cause.** The audio was never added, or an `<audio>` element exists without
`class="clip"` / `data-start` / `data-duration`, so the checker does not count
it as a sound source.

**Fix.** Place one mixed track (see `02-render.md` §4) as a clip at
`data-start="0"` for the full duration, and keep the individual foley files out
of the composition. If a bed risks Content ID, synthesise the foley and beds
locally instead (see `02-render.md` §4).

## 14. First frames use the fallback font

**Symptom.** A text card in the first captured frames looks different from the
rest, or the title is measured with the wrong font.

**Cause.** The page was captured before the woff2 files finished loading.

**Fix.** `font-display: block`, local font files, and re-seek after
`document.fonts.ready` (see the code in `02-render.md` §1 item 7). Also raise
`--virtual-time-budget` for the screenshot path if the bundle is large, so the
single frame waits for the model too.

## 15. The bundle you look at is not the bundle the film uses

**Symptom.** The screenshot shows a change but the rendered video does not (or
the reverse).

**Cause.** Two copies of the bundle: the build script writes `dist/` and copies
into `assets/vendor/`, and a stale copy in one of the two places is easy to
miss.

**Fix.** One build command writes every consumer in one step (esbuild to the
viewer's location and to `assets/vendor/model.bundle.min.js`), and the viewer's
auto-detection is documented so it is obvious which file it loaded. Print the
resolved path (`view.html` sets `window.__viewerBundle` and logs it) and check
the timestamp after every build.
