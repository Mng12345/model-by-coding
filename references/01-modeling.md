# 01 — Modeling: shape from photographs

The goal of this step is proportion and part structure, not surface detail. A
model that has the right silhouette, the right layer order and the right
part count reads as "the object from the photo" in a video even with flat white
materials. A model with correct materials but wrong proportions never does.

## 0. The photo set

Minimum six photographs, each covering one verification pose:

| pose | what it fixes |
| --- | --- |
| front | outer diameter, rib count, blade count, cap size, knob spread |
| side (true 90°) | head thickness, base depth, neck curve, tilt |
| back | rear grille spoke count, control box, cable exit |
| back 3/4 | control box depth, yoke thickness, how rear parts nest |
| top | head depth profile, base outline, knob axis |
| bottom | base rings, feet positions, underside openings |

Criteria: object static during the whole set (a fan head tilted between shots
invalidates every ratio), one light source, plain background, object filling
60–80% of the frame. A phone ultrawide is acceptable if the object stays near
the frame centre; read every measurement as a ratio, which cancels most of the
lens distortion.

Before reading numbers, put a thin grid over each photo (5% or 10% of the short
side is enough). Reading a bounding box off a grid is faster and more reliable
than eyeballing pixel values, and it gives you the box you will later pass to
`scripts/verify_sheet.py`.

## 1. World contract (decide once, never change)

Pick one convention and hold it for the entire project, because the script, the
director and the film all assume it:

- metres as the unit; the model faces **+Z**; the object rests on **y = 0**.
- camera position = `target + dist * (sin(yaw)cos(pitch), sin(pitch), cos(yaw)cos(pitch))`;
  `yaw` and `pitch` in degrees. `yaw = 0` puts the camera on +Z looking at the
  front face. `pitch > 0` is above the horizon.
- a `view` is `{yaw, pitch, dist, target: [x,y,z], fov}`; `fov` is vertical.
- the scene API is pure state: `create(canvas, opts)` once, then
  `setView(view)`, `setExplode(p)`, `setSpin(rad)`, `setHeadTilt(deg)`,
  `setLift(m)`, `render()`. No animation loop, no wall clock. Two renders of the
  same state must be pixel-identical.

The same convention is what makes headless screenshots comparable: the poses
listed in `03-verify.md` are only meaningful against this contract.

## 2. One ruler, everything else a ratio

1. **Choose the ruler.** One large, sharply bounded dimension on the front
   photo. For the example fan it is the outer head diameter.
2. **Measure it with a radial scan**, not with two clicks: estimate the centre,
   cast 720 rays and report the radius plus the spread across rays. In the
   example the front scan gave centre (549.4, 803.5) px and R = 494.6 px; the
   per-ray spread was wide (29.6 px, ≈6% of R) because a ray crossing the heat
   slots leaves the rim at different sub-pixel edges, so judge the scan by its
   angular profile rather than by a small standard deviation: a clean rim shows
   one continuous edge at every angle, a background arc shows an erratic or
   bimodal profile.
3. **Convert to a decision, not a fact.** Apply the assumed real size
   (example: head Ø190 mm ⇒ 494.6 px). Every absolute number in the model is
   then a consequence of that assumption. Record it as such in a comment; see
   the `DIM` block in the example.
4. **Read the rest as ratios** of the ruler, each from a named photo. Then
   cross-check the ratio that appears in more than one photo and keep the range
   in a comment. Ratios survive lens distortion better than absolute pixels.

Worked-example calibration, taken from the shipped `DIM` block and expressed
against head diameter `D` (absolute scale inferred):

| quantity | value | ratio | basis |
| --- | --- | --- | --- |
| head diameter | 0.190 m | 1.00 D | front radial scan |
| head centre height | 0.194 m | 1.02 D | front + side read 1.04–1.10 D; shipped lower, a logged deviation |
| head depth (front face to control-box face) | 0.096 m | 0.505 D | `Z_FRONT` +0.038 → `Z_BOX` −0.058; the side photo suggests ≈0.61 D |
| base diameter | 0.114 m | 0.60 D | front + side, perspective-corrected |
| front cap diameter | 0.061 m | 0.321 D | front, re-measured |
| neck (stalk) diameter | 0.023 m | 0.12 D | front + side |
| tilt knob diameter | 0.022 m | 0.116 D | side + back 3/4 |
| tilt axis below head centre | 0.010 m | 0.053 D | side, inferred |
| front ribs | 46 | — | angular period, see §4 |
| blades | 7 | — | visible petal count |
| rear spokes | ~46 | — | back photo |

Two rows disagree with their photo: the shipped head sits lower (1.02 D against
1.04–1.10 D) and shallower (0.505 D against ≈0.61 D on the side photo). Both
are calibration choices the film was rendered with; the first is logged as a
deviation in the example. When the model and the photo disagree, record the
choice — do not edit the table until it looks measured.

Counting discrete features is its own measurement: at radius `r` the angular
period is `2πr / n`. Measure one period in pixels at two radii and solve for
`n`; the example lands on 46 ± 2, which matches the 46 given by the scan at
`r = 0.6 R` (40.0 px measured vs 40.5 px expected).

## 3. Lathe profiles

Most plastic housings are surfaces of revolution plus one or two breaking
details, so build them as profiles and keep the detail as separate meshes.

```js
// lathe around +Z: points are [radius, z]
function latheZGeo(points, segments = 96) {
  const pts = points.map(([r, z]) => new THREE.Vector2(Math.max(0.00005, r), z));
  const geo = new THREE.LatheGeometry(pts, segments);
  geo.rotateX(Math.PI / 2);
  geo.computeVertexNormals();
  return geo;
}

// lathe around +Y: points are [radius, y]
function latheYGeo(points, segments = 64) {
  const pts = points.map(([r, y]) => new THREE.Vector2(Math.max(0.00005, r), y));
  const geo = new THREE.LatheGeometry(pts, segments);
  geo.computeVertexNormals();
  return geo;
}
```

Profile rules that save hours:

- clamp `r` to a small positive floor (`0.00005`). A literal `r = 0` at both
  ends produces degenerate triangles and NaN normals on some drivers.
- order the profile monotonically along the axis. A profile that doubles back
  gives you flipped faces and dark bands that look like a lighting bug.
- a shell needs a real thickness: outer wall, rounded lip, inner wall, so the
  lathe closes on itself. A single open surface renders with no interior and
  breaks the moment the camera looks into it.
- 96 segments for the head-sized lathes, 64 for base parts, 48 or fewer for
  knobs and small details; more only costs shadow-map time.
- hard-edged moulded plastic can use `flatShading = true` on the material;
  the example marks its faceted plastic parts this way.

## 4. Grille and blades: the parts that decide whether it reads correctly

The front grille is what the audience sees in close-up, so it gets the most
attention.

**Ribs are swept ribbons, not tubes.** Each rib follows a spiral from the hub to
the rim and has a flat crest. Example parameters: 46 ribs; sweep 35° with an
angular exponent of 1.28 (`a = a0 + sweep * t^1.28`); crest z between 0.0352
(back), 0.0360 (shoulder) and 0.0378 (front), dished as
`z = 0.0378 - 0.0018(1-t)² - 0.0012t²`; cross-section 76% flat crest with a
short bevel and vertical flanks. The profile comments in the example say it
plainly: a rounder section reads as a cage of tubes in close-ups, which is the
single most common "it looks like a toy" failure.

Rib width should follow the pitch: the ribs widen from 2.7 mm at the hub to 4.4 mm at
mid radius and 5.6 mm at the rim while the pitch grows from 4.3 to 11.6 mm, so the
see-through gap stays visible at the rim. Build the ribbon by walking the spiral,
emitting a cross-section quad strip, and capping both ends so the geometry stays
watertight for shadows.

**The rear grille** is a spoke cage rather than a spiral: radial spokes with a
tangential kink near the rim, plus one or two flat hoops (example hoops at
r = 0.0550 and 0.0760) and a rim ring. Read the kink angle from the back photo;
it is what makes the rear cage look stamped rather than extruded.

**Blades** are parametric sheets, not boxes. The example builds 7 blades with:
root radius 0.0205, tip 0.0885, sweep `0.80 * t^1.25` rad, half-width
`0.4 - 0.1t`, pitch angle `30° - 11t`, camber `0.003(1-s²)(0.35+0.65t)`, and a
hub drum of r 0.0225→0.0212 with thickness 0.0075. The comment records the
empirical part: a ~6° effective pitch reads as a flat disc through the grille,
while the reference petals overlap in z.

**The front cap** is a shallow lathe boss with a small hub button, blank in the
centre. Do not model a brand mark; if the reference has one, leave the face
blank (the example does) — the video is about the mechanism.

## 5. Parts, explosion and anchors

Name the parts before building the film; the names are the contract shared by
the director, the labels, the anchors and the sound cues. The example has 13:

```
frontGrille, blades, motor, rearGrille, rearControl, knobL, knobR,
yoke, neck, hook, baseTop, baseBottom, feet
```

Register every part through one function so the exploded offsets and the
anchors cannot drift apart:

```js
addPart(name, object3d, parent, assembledPosition, anchorOffset)
// stores object3d.userData.anchorOffset in the part's local space
```

Explosion: give every part a `+y` strip in physical stack order, with side parts
fanned out in x/z so labels do not collide. Example offsets (metres, from the
assembled position):

| part | x | y | z |
| --- | --- | --- | --- |
| frontGrille | 0.000 | +0.135 | +0.100 |
| blades | 0.000 | +0.100 | +0.050 |
| motor | 0.000 | +0.066 | +0.002 |
| rearGrille | 0.000 | +0.032 | -0.046 |
| rearControl | 0.000 | +0.000 | -0.100 |
| knobL | -0.150 | -0.012 | -0.030 |
| knobR | +0.150 | -0.012 | -0.030 |
| yoke | 0.000 | -0.046 | -0.028 |
| neck | 0.000 | -0.090 | 0.000 |
| hook | +0.145 | -0.128 | +0.050 |
| baseTop | 0.000 | -0.150 | 0.000 |
| baseBottom | 0.000 | -0.204 | 0.000 |
| feet | 0.000 | -0.252 | 0.000 |

While the model is apart it can lift off its plinth: the example uses
`lift = 0.256 * up * (1 - down)` with the ramps tied to the explode and
reassemble constants, so the lift always matches the part animation.

Anchors: default is the part's bounding-box centre. Open or hollow parts need a
bias toward the visible face, as fractions of the bbox (0.5 = centre,
1 = max side). Example: `yoke [0.5, 0.04, 0.5]` (stem), `rearControl`,
`hook`, `baseTop`, `baseBottom`, `feet` at `z = 1.0` (front face). `getAnchors()`
projects them to 1920×1080 pixels and returns `{x, y, z, visible}`; the film
uses `visible` to decide whether a leader line is drawn in the current shot.

## 6. Failure modes

| symptom | cause | fix |
| --- | --- | --- |
| camera orbits the wrong way | model faces -Z or yaw sign flipped | re-check the front view at yaw 0 |
| inside-out shading, black inner surfaces | lathe profile ordered backwards | reverse point order or set `DoubleSide` on purpose |
| NaN normals, missing triangles | `r = 0` in a lathe profile | clamp to `0.00005` |
| grille reads as a tube cage | rib cross-section too round | flatten the crest, add a bevel, keep vertical flanks |
| parts intersect when assembled | explosion offset reused as assembly offset | keep `assembled` and `EXPLODE` separate; test `p = 0` and `p = 1` |
| labels land on empty space | anchor still at bbox centre of a hollow part | add a bias toward the visible face |
| proportions drift between sessions | absolute mm guessed per part | one ruler, ratio table, one `DIM` object |
| rear parts glow dark/grey | normals not recomputed after transforms | `computeVertexNormals()` after every geometry edit |
