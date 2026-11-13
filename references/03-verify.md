# 03 — Verifying the model against the photos

A code-built model always looks plausible in isolation. The only honest test is
a same-pose comparison: render the model from the angle of a reference photo,
crop both to the object's bounding box, put them side by side at the same scale,
and read the differences. This step is cheap (under a minute per iteration once
the viewer exists) and catches the errors that matter: proportions, layer order
and part placement.

## 0. The loop

```
build bundle → screenshot one pose → crop both → compare → read → fix → rebuild
```

Run it per pose, not once at the end. Six poses, 3–6 iterations each is normal;
the model converges when two consecutive sheets show no dimensional change.

## 1. The viewer page

`scripts/view.html` is a single-frame viewer that exists only for verification:
no labels, no cards, no animation. It reads the pose from the query string,
loads the model bundle and renders exactly one frame.

| parameter | meaning | default |
| --- | --- | --- |
| `bundle` | script URL of the IIFE bundle | probes common paths next to the page |
| `global` | global name the bundle exposes | auto-detected (first global with `create` + `PARTS`) |
| `yaw`, `pitch`, `dist` | camera pose (degrees, metres) | −20, 10, 1.0 |
| `tx`, `ty`, `tz` | camera target (metres) | 0, 0, 0 |
| `fov` | vertical field of view | 30 |
| `explode` | disassembly amount 0–1 | 0 |
| `spin` | blade spin (radians) | 0 |
| `tilt`, `lift` | only if the bundle implements them | 0 |
| `w`, `h`, `dpr` | canvas size / pixel ratio | 1920×1080, 1 |
| `bg` | page background | `#e8e6e1` |

`noshadow`, `hide` and `only` are read by the model bundle from
`location.search`, so they pass through the viewer unchanged. Build the bundle
with the same entry point the film uses:

```powershell
npx --yes esbuild@0.24.2 src/scene.js --bundle --format=iife --global-name=Scene `
  --minify --target=chrome120 --outfile=dist/scene.bundle.min.js
```

(`--bundle --format=iife --global-name --minify --target --outfile` are the
documented esbuild 0.24.2 CLI flags; the film loads the same artefact from
`assets/vendor/`.)

## 2. Screenshot one pose with headless Chrome

```powershell
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$png    = "D:\work\model\out\front.png"
$udd    = Join-Path $env:TEMP ("view-" + [guid]::NewGuid().ToString("N"))
$url    = "file:///D:/work/model/scripts/view.html" +
          "?yaw=-10&pitch=12&dist=0.85&ty=0.185&fov=30&noshadow=1"

& $chrome --headless=new --use-angle=d3d11 --window-size=1920,1080 `
  --hide-scrollbars --virtual-time-budget=9000 `
  --screenshot=$png --user-data-dir=$udd $url
```

Rules that are not optional:

- **Window must be 1920×1080.** The canvas is fixed at that size and pixel-space
  comparison assumes it. A 1280×720 window silently rescales everything.
- **`--screenshot=` takes an absolute path**; create the parent directory
  first. Keep the project path free of spaces (use a short symlink or a
  no-space working directory) so the `file:///` URL stays simple.
- **One fresh `--user-data-dir` per run.** Chrome refuses to reuse a profile
  that another headless instance holds; a unique temp directory also avoids
  the disk cache hiding a rebuilt bundle.
- **Use `?noshadow=1` for geometry comparison.** The contact shadow and
  cast shadows darken the lower silhouette and inflate automatic bounding
  boxes; shadows are a film concern, not a shape concern.
- **Do not trust the exit code.** Measured here: three successful screenshots exited 0, and a run that failed to write the PNG ("Failed to write file screenshot.png: access denied") also exited 0; other recipes report exit 1 on success. The pass signal is the file itself.

Assert the result before looking at it:

```powershell
python -c "from PIL import Image; import numpy as np; im=Image.open(r'$png'); a=np.asarray(im.convert('RGB')); print(im.size, round(float(a.std()),2))"
```

Expect `(1920, 1080)` and a standard deviation of roughly 15–60 for a shaded
object on a plain ground; a std near 0 means a blank canvas (bundle failed to
load), and the viewer page then reports the error in its title
(`document.title === "error"`) instead of pretending to render.

## 3. The comparison sheet

`scripts/verify_sheet.py` builds the sheet: photo crop from `--bbox`, render
crop auto-detected against the background colour, both fitted to the same tile,
labels showing the crop sizes.

```powershell
python scripts/verify_sheet.py `
  --photo reference/fan.jpg `
  --render out/verify/front.png `
  --out out/verify/front-sheet.png `
  --bbox "130,245,1195,1455"
```

Output line from a real run:

```
saved out/verify/front-sheet.png  1112x702  | photo (130, 245, 1195, 1455)  | render (652, 264, 1252, 1080)
```

Reading the crop boxes matter: `--bbox` is read by eye off the photo (a 5–10%
grid is enough); the render box is found by comparing every pixel to the
corner-sampled background colour. Useful options:

| option | use |
| --- | --- |
| `--bbox x0,y0,x1,y1` | photo crop, required |
| `--render-bbox x0,y0,x1,y1` | override the auto-detected model box |
| `--bg auto` / `--bg #f3f1ec` | background colour for detection |
| `--threshold 18` | per-channel difference that counts as object |
| `--pad 0.04` | padding added around the detected model box |
| `--tile 520x620` | panel size in the sheet |

Auto-detection fails in two predictable ways: a power cable or stand
protruding from the object inflates the box (the model then looks smaller than
the photo), and a strong contact shadow is close enough to the background to be
partly included. Fix the first with `?noshadow=1` plus an explicit
`--render-bbox`; fix the second with a larger `--threshold` or an explicit box.
Do not "fix" either by editing the photo crop.

One sheet holds one pair, so loop the six poses with a `foreach` in PowerShell
or a `for` in bash and inspect the six PNGs.

## 4. Reading the sheets

Each panel is cropped to its own bbox and fitted to the same tile, which makes
*relative* proportions comparable: where a feature sits inside the silhouette,
how large it is against the overall envelope, and where parts overlap. Do not
compare absolute pixels between panels; compare fractions of the object's own
box.

Pose set used by the example (yaw, pitch, dist, target height, fov):

| pose | camera | what to check |
| --- | --- | --- |
| front | −10, 12, 0.85, 0.185, 30 | cap diameter ≈ 0.32 D; rib count/density; blade count; knobs just outside the head edge |
| side-left | −62, 10, 0.85, 0.175, 30 | head depth (shipped 0.505 D; side photo suggests ≈0.61 D); neck curve; base depth; 5° tilt |
| back | 176, 8, 0.85, 0.185, 30 | rear spoke count; control box size and position; cable exit low right |
| back-3q | 138, 10, 0.85, 0.185, 30 | how the rear cage nests into the yoke; yoke thickness |
| top | 15, 50, 0.95, 0.130, 30 | head depth profile; base outline; knob axis |
| bottom | 0, −62, 0.40, 0.020, 34 | base rings, feet, underside openings |

The tuple order matters: a render from yaw −10 must be compared with the
front photo, not with a 3/4 photo; a small pose error reads as a shape error.

Working tolerances (judgement, not measured): a ratio within ~3% of the photo
is invisible in the film; 5–10% is noticeable on a side-by-side sheet; above
10% the object reads as a different product. The first iterations usually
show the largest errors in head depth and base diameter, because single-photo
perspective flatters both.

Record what you changed and why in a short deviation list (the example's spec
keeps seven known deviations with the reason for each). That list is what
prevents "fixing" an intentional simplification on the next pass.

## 5. The lesson: circle fitting fails on background arcs

The first attempt at a scale lock fit circles to the head outline across five
photos and normalised every dimension by the fitted radius. It failed, badly,
for a reason worth writing down: circle fitting is a global least-squares
problem and the background wins. On four of the five photos the strongest
curved edges belonged to the background — window frames, a table edge, a
doorframe — and the fit locked onto those arcs instead of the grille rim, so
the normalised radius was meaningless and the comparison scaled the model by a
random factor. Only the front photo, where the object fills the frame against a
uniform wall, produced a usable radial scan (centre (549.4, 803.5) px,
R = 494.6 px; the per-ray spread is wide, 29.6 px, because the rays also cross
rib slots).

Rules that came out of it:

- automatic shape fitting needs an object mask; with a cluttered background,
  fit nothing and measure bounding boxes instead;
- never normalise by a fitted radius; normalise by an explicitly drawn
  bounding box on both sides;
- if a single photo is usable for a radial scan, use it for the ruler only and
  keep the other poses for visual comparison;
- the bbox comparison survived where the circle fit failed, which is why
  `verify_sheet.py` is built around crops rather than fits.

## 6. Failure modes

| symptom | cause | fix |
| --- | --- | --- |
| everything off by a constant factor | screenshot window not 1920×1080 | fix `--window-size`, recreate the viewer default |
| no PNG, no error | path not absolute / parent missing / profile in use | absolute path, `New-Item -ItemType Directory -Force`, unique `--user-data-dir` |
| blank or white sheet panel | bundle did not load, or render still black | check `document.title == "ready"`, rebuild the bundle, raise `--virtual-time-budget` |
| model looks smaller than photo | auto bbox inflated by cable/shadow | `?noshadow=1`, explicit `--render-bbox` |
| silhouette clipped | camera too close or fov too narrow | back off `dist`, widen `fov`, keep the object inside the frame |
| identical model in every pose | viewer ignored query params (or old bundle cached) | fresh `--user-data-dir`; view the URL once in a browser |
| "fixed" a real error by cropping the photo | comparison box drifted | re-read the photo bbox from the grid, compare the same feature |
| sync between photos and renders drifts | pose tuple typo, target height mismatch | keep the pose table in one file and copy it from there |
