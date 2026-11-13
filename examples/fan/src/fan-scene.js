// fan-scene.js - canonical 3D model of the white USB clip fan (C7-1 style, unbranded).
// Bundled by tools/build.mjs into dist/fan.bundle.js (IIFE, global name "FanScene").
//
// CONTRACT (see ../CONTRACT.md):
//   create(canvas, opts) -> ctl
//   ctl.setView({yaw,pitch,dist,target,fov})  world: fan faces +Z, base sits on y=0
//   ctl.setExplode(0..1)                     global explode amount, 0 = assembled
//   ctl.setExplodeMap(map|null)              per-part {part: 0..1 | [x,y,z]} (director)
//   ctl.setSpin(rad)                         blade rotation around the head axis
//   ctl.setHeadTilt(deg)                     head pitch about the lateral knob axis
//   ctl.render()                             render current state
//   ctl.getAnchors()                         { [part]: {x,y,z,visible} } screen px anchors
//   ctl.resize(w,h), ctl.dispose()
//
// Proportions are measured on reference/fan.jpg (front) plus reference/angles/{a..e}.jpg
// (side-left, back, back-3/4, bottom, top). Every dimension below is traceable to
// SPEC-v2.md 5; values that could not be measured are marked there as inferred.
// The product label reads 144 mm grille dia; this model keeps v1's 190 mm world scale,
// so only ratios carry over to the photos (head dia = 2 x headRadius).

import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { toCreasedNormals } from "three/examples/jsm/utils/BufferGeometryUtils.js";

export const PARTS = Object.freeze([
  "frontGrille",
  "blades",
  "motor",
  "rearGrille",
  "rearControl",
  "knobL",
  "knobR",
  "yoke",
  "neck",
  "hook",
  "baseTop",
  "baseBottom",
  "feet",
]);

// Absolute dimensions are inferred (no physical measurement); proportions come from fan.jpg.
export const DIM = Object.freeze({
  headRadius: 0.095, // grille outer radius = 0.5 x 190 mm world scale
  headCenterY: 0.194, // head-centre height = 1.02 x head diameter (a, c photos, inferred)
  headDepth: 0.096, // front face z +0.038 .. control-box face z -0.058 (a photo)
  headTiltDeg: 5, // slight upward pose; tilt direction is inferred (photos near level)
  baseRadius: 0.0570, // base plate 0.60 x head diameter (c/a photos, perspective-corrected)
  baseHeight: 0.016, // plate 16 mm thick; the arched cover reaches y 0.050
  neckRadius: 0.0115, // waisted stalk 0.12 x head diameter
  capRadius: 0.0305, // front cap 0.321 x head diameter (re-measured on fan.jpg)
  ribCount: 46, // 46 +/- 2 front ribs on fan.jpg; rear spokes ~46 (b photo)
  knobRadius: 0.0110, // tilt knob 22 mm dia = 0.116 x D (b photo)
  tiltAxisDrop: 0.010, // knob axis sits slightly below the head centre (b/c photos, inferred)
});

const PLASTIC = 0xf7f6f2;
const PLASTIC_INNER = 0xe9e7e2;
const METAL = 0x9fa3a8;
const DARK = 0x2c2d30;

// ---------------------------------------------------------------------------
// geometry helpers (all return THREE.BufferGeometry in world-axis orientation)
// ---------------------------------------------------------------------------

function deg(d) {
  return (d * Math.PI) / 180;
}

/** Lathe around +Z: pass [r, z] pairs. */
function latheZGeo(points, segments = 96) {
  const pts = points.map(([r, z]) => new THREE.Vector2(Math.max(0.00005, r), z));
  const geo = new THREE.LatheGeometry(pts, segments);
  geo.rotateX(Math.PI / 2);
  geo.computeVertexNormals();
  return geo;
}

/** Lathe around +Y (vertical): pass [r, y] pairs. */
function latheYGeo(points, segments = 64) {
  const pts = points.map(([r, y]) => new THREE.Vector2(Math.max(0.00005, r), y));
  const geo = new THREE.LatheGeometry(pts, segments);
  geo.computeVertexNormals();
  return geo;
}

function cylZGeo(rTop, rBottom, len, segments = 64) {
  const geo = new THREE.CylinderGeometry(rTop, rBottom, len, segments);
  geo.rotateX(Math.PI / 2);
  return geo;
}

function cylXGeo(rTop, rBottom, len, segments = 48) {
  const geo = new THREE.CylinderGeometry(rTop, rBottom, len, segments);
  geo.rotateZ(Math.PI / 2);
  return geo;
}

function makeBackdropTexture() {
  const c = document.createElement("canvas");
  c.width = 16;
  c.height = 1024;
  const g = c.getContext("2d");
  const grad = g.createLinearGradient(0, 0, 0, 1024);
  grad.addColorStop(0.0, "#f8f7f4");
  grad.addColorStop(0.16, "#f3f1ed");
  grad.addColorStop(0.26, "#f2f0ec");
  grad.addColorStop(0.55, "#f2f0ec");
  grad.addColorStop(0.78, "#efede8");
  grad.addColorStop(1.0, "#e9e6e0");
  g.fillStyle = grad;
  g.fillRect(0, 0, 16, 1024);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function makeRadialShadowTexture() {
  const c = document.createElement("canvas");
  c.width = 256;
  c.height = 256;
  const g = c.getContext("2d");
  const grad = g.createRadialGradient(128, 128, 4, 128, 128, 126);
  grad.addColorStop(0.0, "rgba(0,0,0,0.34)");
  grad.addColorStop(0.36, "rgba(0,0,0,0.18)");
  grad.addColorStop(0.7, "rgba(0,0,0,0.05)");
  grad.addColorStop(1.0, "rgba(0,0,0,0)");
  g.fillStyle = grad;
  g.fillRect(0, 0, 256, 256);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function polygonPath(pts) {
  const path = new THREE.Path();
  path.moveTo(pts[0].x, pts[0].y);
  for (let k = 1; k < pts.length; k++) path.lineTo(pts[k].x, pts[k].y);
  path.closePath();
  return path;
}

// Rib cross-section, in the (tangential u, axial z) plane of the swept rib.
const RIB_Z_BACK = 0.0352;
const RIB_Z_SHOULDER = 0.0360;
const RIB_Z_FRONT = 0.0378;

/**
 * 46 sculpted spiral ribs: rounded ridges with real see-through gaps, so the blades
 * stay visible behind the grille exactly as in the reference photo.
 */
function buildGrilleRibGeometry() {
  const ribs = DIM.ribCount;
  const rIn = 0.0244;
  const rOut = 0.0905;
  const sweep = deg(35);
  const segs = 80;
  const nProf = 8;

  // Ribs are near-touching at the cap ring (the photo shows them merging there), then
  // widen through the mid span and flare again toward the rim lip, leaving narrow slots.
  const widthAt = (t) => {
    // measured on fan.jpg: spokes take ~50-55 % of the pitch (2.7 mm at the hub,
    // 4.4 mm at mid radius, 5.6 mm at the rim, against a 4.3-11.6 mm pitch)
    return 0.0027 + 0.0027 * t + 0.0005 * Math.sin(Math.PI * t);
  };
  // nearly flat ribbon crest with short vertical flanks (the reference grille reads as a
  // shallow etched surface, not as a cage of round tubes)
  // 76 % of the width is a flat crest with a small bevel: the reference grille is an
  // etched flat face, and a rounder section reads as a cage of tubes in close-ups.
  const profile = (w, zFront) => [
    [-w * 0.5, RIB_Z_BACK],
    [-w * 0.5, Math.max(RIB_Z_BACK + 0.0005, zFront - 0.0011)],
    [-w * 0.46, zFront - 0.00035],
    [-w * 0.38, zFront],
    [w * 0.38, zFront],
    [w * 0.46, zFront - 0.00035],
    [w * 0.5, Math.max(RIB_Z_BACK + 0.0005, zFront - 0.0011)],
    [w * 0.5, RIB_Z_BACK],
  ];

  const positions = [];
  const indices = [];

  // design-space parameter: 0 at the hub ring, 1 at the rim lip
  const designT = (r) => Math.min(1, Math.max(0, (r - 0.0330) / (0.0886 - 0.0330)));
  const pushRing = (r, a, w, zFront) => {
    const ct = Math.cos(a);
    const st = Math.sin(a);
    for (const [u, z] of profile(w, zFront)) {
      positions.push(r * ct - u * st, r * st + u * ct, z);
    }
  };

  for (let i = 0; i < ribs; i++) {
    const a0 = (i / ribs) * Math.PI * 2;
    const base = positions.length / 3;
    for (let s = 0; s <= segs; s++) {
      const r = rIn + (rOut - rIn) * (s / segs);
      const t = designT(r);
      const a = a0 + sweep * Math.pow(t, 1.28);
      const w = widthAt(t);
      // dished surface: crest sits lower near the hub and dips again at the rim
      const zFront = RIB_Z_FRONT - 0.0018 * (1 - t) * (1 - t) - 0.0012 * t * t;
      pushRing(r, a, w, zFront);
    }
    for (let s = 0; s < segs; s++) {
      for (let p = 0; p < nProf; p++) {
        const p2 = (p + 1) % nProf;
        const a = base + s * nProf + p;
        const b = base + s * nProf + p2;
        const c = base + (s + 1) * nProf + p;
        const d = base + (s + 1) * nProf + p2;
        indices.push(a, b, c, b, d, c);
      }
    }
    // watertight end caps: a fan over the cross-section polygon at both ends, so a rib
    // can never show a hollow opening no matter where the camera looks from
    for (const s of [0, segs]) {
      const r = s === 0 ? rIn : rOut;
      const te = designT(r);
      const a = a0 + sweep * Math.pow(te, 1.28);
      const ct = Math.cos(a);
      const st = Math.sin(a);
      const wEnd = widthAt(te);
      const zEnd = RIB_Z_FRONT - 0.0019 * (1 - te) * (1 - te) - 0.0014 * te * te;
      const endProf = profile(wEnd, zEnd);
      // centroid sits mid-thickness of the real cross-section, never above its crest
      let zc = 0;
      for (const [, z] of endProf) zc += z;
      zc /= endProf.length;
      const mid = positions.length / 3;
      positions.push(r * ct, r * st, zc);
      for (let p = 0; p < nProf; p++) {
        const p2 = (p + 1) % nProf;
        indices.push(base + s * nProf + p, base + s * nProf + p2, mid);
      }
    }
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setIndex(indices);
  geo.computeVertexNormals();
  return geo;
}

/** Seven-bladed propeller: seven parametric blade sheets + a hub drum. */
function buildBladesGeometry() {
  const blades = 7;
  const r0 = 0.0205;
  const r1 = 0.0885;
  const rs = 14;
  const ss = 8;
  const positions = [];
  const indices = [];

  for (let b = 0; b < blades; b++) {
    const baseAngle = (b / blades) * Math.PI * 2;
    const start = positions.length / 3;
    for (let i = 0; i <= rs; i++) {
      const tr = i / rs;
      const r = r0 + (r1 - r0) * tr;
      const sweep = 0.80 * Math.pow(tr, 1.25);
      const halfA = 0.4 - 0.1 * tr;
      // root 30 deg tapering to 19 deg at the tip: a ~6 deg effective pitch reads as
      // a flat disc through the grille, while the reference petals overlap in z
      const pitch = deg(30 - 11 * tr);
      for (let j = 0; j <= ss; j++) {
        const s = -1 + (2 * j) / ss;
        const chord = s * halfA * r;
        const phi = baseAngle + sweep + s * halfA;
        const camber = 0.003 * (1 - s * s) * (0.35 + 0.65 * tr);
        const z = 0.0165 + Math.tan(pitch) * chord * 0.62 + camber + 0.0018 * tr * tr;
        positions.push(r * Math.cos(phi), r * Math.sin(phi), z);
      }
    }
    for (let i = 0; i < rs; i++) {
      for (let j = 0; j < ss; j++) {
        const a = start + i * (ss + 1) + j;
        const c = a + ss + 1;
        indices.push(a, c, a + 1, c, c + 1, a + 1);
      }
    }
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setIndex(indices);
  geo.computeVertexNormals();

  const hub = new THREE.CylinderGeometry(0.0225, 0.0212, 0.0075, 40);
  hub.rotateX(Math.PI / 2);
  hub.translate(0, 0, 0.0181);
  return [geo, hub];
}

// ---------------------------------------------------------------------------
// v2 helpers — swept strap (yoke), radial spoke cage (rear grille), rounded rects
// All return THREE.BufferGeometry in head-centre coordinates (fan faces +Z).
// ---------------------------------------------------------------------------

/** Rounded rectangle outline, centred on the origin, as a THREE.Shape. */
function roundedRectShape(w, h, r) {
  const s = new THREE.Shape();
  const x = -w / 2;
  const y = -h / 2;
  const rr = Math.min(r, w / 2, h / 2);
  s.moveTo(x + rr, y);
  s.lineTo(x + w - rr, y);
  s.quadraticCurveTo(x + w, y, x + w, y + rr);
  s.lineTo(x + w, y + h - rr);
  s.quadraticCurveTo(x + w, y + h, x + w - rr, y + h);
  s.lineTo(x + rr, y + h);
  s.quadraticCurveTo(x, y + h, x, y + h - rr);
  s.lineTo(x, y + rr);
  s.quadraticCurveTo(x, y, x + rr, y);
  return s;
}

/** Same outline as a THREE.Path, for use as a hole. */
function roundedRectPath(w, h, r) {
  const s = new THREE.Path();
  const x = -w / 2;
  const y = -h / 2;
  const rr = Math.min(r, w / 2, h / 2);
  s.moveTo(x + rr, y);
  s.lineTo(x + w - rr, y);
  s.quadraticCurveTo(x + w, y, x + w, y + rr);
  s.lineTo(x + w, y + h - rr);
  s.quadraticCurveTo(x + w, y + h, x + w - rr, y + h);
  s.lineTo(x + rr, y + h);
  s.quadraticCurveTo(x, y + h, x, y + h - rr);
  s.lineTo(x, y + rr);
  s.quadraticCurveTo(x, y, x + rr, y);
  return s;
}

/**
 * Sweep a closed profile along a circular arc in the X-Y plane.
 * profile = [[u, v], ...]; u is the radial offset from `radius`, v the axial (Z)
 * offset. widthAt(t) scales v so the strap can flare at its ends.
 */
function sweepBandGeometry({ radius, profile, theta0, span, segs = 120, widthAt = null }) {
  const nP = profile.length;
  let uMid = 0;
  let vMid = 0;
  for (const [u, v] of profile) {
    uMid += u;
    vMid += v;
  }
  uMid /= nP;
  vMid /= nP;

  const pos = [];
  const idx = [];
  const width = (t) => (widthAt ? widthAt(t) : 1);
  for (let s = 0; s <= segs; s++) {
    const t = s / segs;
    const th = theta0 + span * t;
    const ct = Math.cos(th);
    const st = Math.sin(th);
    const w = width(t);
    for (let p = 0; p < nP; p++) {
      const rr = radius + profile[p][0];
      pos.push(rr * ct, rr * st, profile[p][1] * w);
    }
  }
  for (let s = 0; s < segs; s++) {
    for (let p = 0; p < nP; p++) {
      const p2 = (p + 1) % nP;
      const a = s * nP + p;
      const b = s * nP + p2;
      const c = (s + 1) * nP + p;
      const d = (s + 1) * nP + p2;
      idx.push(a, b, c, b, d, c);
    }
  }
  // watertight end caps (the ends hide inside the tilt knobs, but never show a hole)
  for (const s of [0, segs]) {
    const t = s / segs;
    const th = theta0 + span * t;
    const ct = Math.cos(th);
    const st = Math.sin(th);
    const w = width(t);
    const mid = pos.length / 3;
    pos.push((radius + uMid) * ct, (radius + uMid) * st, vMid * w);
    for (let p = 0; p < nP; p++) {
      idx.push(s * nP + p, mid, s * nP + ((p + 1) % nP));
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  return geo;
}

/**
 * Rear grille: `count` thin radial spokes that kink tangentially near the rim, as in
 * reference/angles/b_back.jpg. Bars are rectangular in cross-section, swept radially.
 * Built at z = 0 (the caller offsets it to the head's rear grille plane).
 */
function buildRearGrilleGeometry({ count = 46, rIn = 0.0285, rOut = 0.0870, kink = 17 }) {
  const segs = 26;
  const wRoot = 0.0016; // tangential width at the root
  const wTip = 0.0022; // ... at the rim
  const hBar = 0.0034; // axial depth
  const kinkRad = deg(kink);
  const pos = [];
  const idx = [];
  for (let i = 0; i < count; i++) {
    const a0 = (i / count) * Math.PI * 2;
    const base = pos.length / 3;
    for (let s = 0; s <= segs; s++) {
      const t = s / segs;
      const r = rIn + (rOut - rIn) * t;
      const k = t <= 0.78 ? 0 : Math.pow((t - 0.78) / 0.22, 1.7) * kinkRad;
      const a = a0 + k;
      const ct = Math.cos(a);
      const st = Math.sin(a);
      const w = wRoot + (wTip - wRoot) * t;
      const corners = [
        [-w / 2, -hBar / 2],
        [w / 2, -hBar / 2],
        [w / 2, hBar / 2],
        [-w / 2, hBar / 2],
      ];
      for (const [u, zz] of corners) pos.push(r * ct - u * st, r * st + u * ct, zz);
    }
    for (let s = 0; s < segs; s++) {
      for (let p = 0; p < 4; p++) {
        const p2 = (p + 1) % 4;
        const a = base + s * 4 + p;
        const b = base + s * 4 + p2;
        const c = base + (s + 1) * 4 + p;
        const d = base + (s + 1) * 4 + p2;
        idx.push(a, b, c, b, d, c);
      }
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  return geo;
}

// ---------------------------------------------------------------------------
// scene
// ---------------------------------------------------------------------------

export function create(canvas, opts = {}) {
  const width = opts.width || canvas.width || 1920;
  const height = opts.height || canvas.height || 1080;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
  renderer.setPixelRatio(opts.pixelRatio ?? 1);
  renderer.setSize(width, height, false);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  // Khronos PBR Neutral keeps bright white plastic from clipping to a flat sheet,
  // which ACES does above ~0.8 linear; measured against the reference photo's head
  // region (mean 155, std 29 in sRGB luma).
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = opts.exposure ?? 0.68;
  // debug hook for QA renders: ?noshadow=1 disables shadow casting
  const noShadow = /[?&]noshadow=1/.test(location.search);
  renderer.shadowMap.enabled = !noShadow;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene = new THREE.Scene();

  const pmrem = new THREE.PMREMGenerator(renderer);
  const envTexture = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  pmrem.dispose();
  scene.environment = envTexture;
  scene.environmentIntensity = 0.45;

  scene.background = null;
  // A tone-mapped backdrop sphere (instead of scene.background) keeps the backdrop in the
  // same colour pipeline as the fogged floor, so the horizon never shows a seam.
  const backdrop = new THREE.Mesh(
    new THREE.SphereGeometry(16, 48, 32),
    new THREE.MeshBasicMaterial({
      map: makeBackdropTexture(),
      side: THREE.BackSide,
      depthWrite: false,
      fog: false,
      toneMapped: false, // three applies fog after tonemapping in sRGB space; match that pipeline
    }),
  );
  backdrop.renderOrder = -1;
  scene.add(backdrop);

  // Fog fades the ground disc into the backdrop so no floor edge / horizon seam shows.
  scene.fog = new THREE.Fog(0xf2f0ec, 1.4, 5.2);

  const floor = new THREE.Mesh(
    new THREE.CircleGeometry(12, 128),
    new THREE.MeshStandardMaterial({ color: 0xf4f2ee, roughness: 0.95, metalness: 0 }),
  );
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  scene.add(floor);

  const contact = new THREE.Mesh(
    new THREE.PlaneGeometry(0.22, 0.22),
    new THREE.MeshBasicMaterial({
      map: makeRadialShadowTexture(),
      transparent: true,
      depthWrite: false,
      opacity: 0.55,
    }),
  );
  contact.rotation.x = -Math.PI / 2;
  contact.position.set(0, 0.0008, 0.006);
  scene.add(contact);

  // Studio light: key from screen upper-left (+X), cool fill from the right (-X),
  // white rim from behind. Neutral white balance so the plastic reads white, not cream.
  const key = new THREE.DirectionalLight(0xfff7f0, 2.1);
  key.position.set(1.9, 2.7, 1.7);
  key.castShadow = true;
  key.shadow.mapSize.set(4096, 4096);
  key.shadow.camera.near = 0.1;
  key.shadow.camera.far = 8;
  key.shadow.camera.left = -0.50;
  key.shadow.camera.right = 0.50;
  key.shadow.camera.top = 0.50;
  key.shadow.camera.bottom = -0.50;
  key.shadow.bias = -0.00020;
  key.shadow.normalBias = 0.0030;
  key.shadow.radius = 6.0; // soft: the rear cage's own shadow on the shell must not read as banding
  key.shadow.intensity = 0.66;
  scene.add(key);

  const fill = new THREE.DirectionalLight(0xe8f0ff, 0.5);
  fill.position.set(-2.1, 1.1, 1.4);
  scene.add(fill);

  const rim = new THREE.DirectionalLight(0xffffff, 1.35);
  rim.position.set(-0.4, 2.1, -2.5);
  scene.add(rim);

  const hemi = new THREE.HemisphereLight(0xffffff, 0xcfcac2, 0.5);
  scene.add(hemi);

  const camera = new THREE.PerspectiveCamera(opts.fov ?? 30, width / height, 0.01, 40);

  // materials -----------------------------------------------------------------
  const plastic = new THREE.MeshPhysicalMaterial({
    color: PLASTIC,
    roughness: 0.52,
    metalness: 0.0,
    clearcoat: 0.05,
    clearcoatRoughness: 0.6,
  });
  const plasticSoft = plastic.clone();
  plasticSoft.roughness = 0.52;
  plasticSoft.clearcoat = 0.05;
  const plasticInner = plastic.clone();
  plasticInner.color = new THREE.Color(0x8e8a83);
  plasticInner.roughness = 0.68;
  plasticInner.clearcoat = 0.04;
  plasticInner.side = THREE.DoubleSide;
  plasticInner.envMapIntensity = 0.06;
  // housing shell: the lathe winds inward, so it needs both faces to read as a shell
  const plasticShell = plastic.clone();
  plasticShell.side = THREE.DoubleSide;
  const bladeMat = plasticSoft.clone();
  bladeMat.side = THREE.DoubleSide;
  bladeMat.color = new THREE.Color(0xaeaaa2);
  bladeMat.roughness = 0.74;
  bladeMat.envMapIntensity = 0.05;
  const plasticGrille = plastic.clone();
  plasticGrille.side = THREE.DoubleSide;
  plasticGrille.roughness = 0.62;
  plasticGrille.clearcoat = 0.03;
  const metal = new THREE.MeshStandardMaterial({ color: METAL, roughness: 0.38, metalness: 0.82 });
  const metalDark = new THREE.MeshStandardMaterial({ color: 0x6a6d72, roughness: 0.5, metalness: 0.6 });
  const dark = new THREE.MeshStandardMaterial({ color: DARK, roughness: 0.62 });
  const pcbMat = new THREE.MeshStandardMaterial({ color: 0x3d5546, roughness: 0.7 });

  // ---------------------------------------------------------------------------
  // assembly
  // ---------------------------------------------------------------------------
  const root = new THREE.Group();
  scene.add(root);

  const H = DIM.headCenterY;
  const headPivot = new THREE.Group();
  headPivot.position.set(0, H, 0);
  root.add(headPivot);

  const parts = {};
  const basePos = {};
  const V = (x, y, z) => new THREE.Vector3(x, y, z);

  function addPart(name, object3d, parent, assembled, anchor) {
    object3d.position.copy(assembled);
    object3d.traverse((o) => {
      if (o.isMesh) {
        o.castShadow = true;
        o.receiveShadow = true;
      }
    });
    (parent || root).add(object3d);
    parts[name] = object3d;
    basePos[name] = assembled.clone();
    object3d.userData.anchorOffset = anchor ? anchor.clone() : new THREE.Vector3();
    return object3d;
  }

  function put(geo, mat, parent, x, y, z) {
    const m = new THREE.Mesh(geo, mat);
    if (x !== undefined) m.position.set(x, y, z);
    parent.add(m);
    return m;
  }

  // ---------------------------------------------------------------------------
  // v2 assembly — 13 parts, measured on reference/fan.jpg + reference/angles/{a..e}.jpg
  // (see SPEC-v2.md §5 for every number and its basis)
  // ---------------------------------------------------------------------------
  const R = DIM.headRadius; // 0.095
  const HY = H; // head-centre height 0.194
  const TILT_DROP = DIM.tiltAxisDrop; // knob axis below the head centre
  const KNOB_Z = -0.008;
  const ARC_R = 0.1005; // yoke strap centreline radius about the tilt axis
  const BAND_T = 0.0040; // strap half thickness (radial)
  const BAND_W = 0.0105; // strap half width (axial)
  const Z_FRONT = 0.0380; // front grille face
  const Z_GR = -0.0400; // rear grille plane
  const Z_RIM = -0.0480; // rear lip of the shell
  const Z_BOX = -0.0580; // control-box face
  const STUD = 0.0105; // grille stud / rib spacing helper

  // v2 detail materials ------------------------------------------------------
  const rubber = new THREE.MeshStandardMaterial({ color: 0x232427, roughness: 0.88, metalness: 0.0 });
  const brass = new THREE.MeshStandardMaterial({ color: 0x8f7038, roughness: 0.52, metalness: 0.88 });
  const sticker = plastic.clone();
  sticker.color = new THREE.Color(0xfbfaf7);
  sticker.roughness = 0.26;
  sticker.clearcoat = 0.4;
  const plasticFacet = plastic.clone();
  plasticFacet.flatShading = true;
  const plasticBand = plastic.clone();
  plasticBand.side = THREE.DoubleSide;
  const plasticWell = plastic.clone();
  plasticWell.color = new THREE.Color(0xdad7d0);
  plasticWell.roughness = 0.72;
  const plasticDark = plasticInner.clone();
  plasticDark.color = new THREE.Color(0x6f6b65);
  const wellDeep = plastic.clone();
  wellDeep.color = new THREE.Color(0x8a867f);
  wellDeep.roughness = 0.82;
  const steel = new THREE.MeshStandardMaterial({ color: 0x8d9095, roughness: 0.42, metalness: 0.85 });

  // --- tilt pivot: the whole head rotates about the lateral knob axis --------
  headPivot.position.set(0, HY - TILT_DROP, KNOB_Z);
  const headCore = new THREE.Group();
  headCore.position.set(0, TILT_DROP, -KNOB_Z);
  headPivot.add(headCore);

  // Interior bounce: the head is a closed drum, so the grille slots would read black
  // without a soft fill inside. No shadows, short range, rides with the head pivot.
  // candela units: three.js floors point-light attenuation at 1/0.01, so an
  // intensity near 1 detonates the whole head. 0.010 reads as a soft bounce.
  const headFill = new THREE.PointLight(0xfff6ec, 0.010, 0.36, 2);
  headFill.position.set(0.0, 0.030, -0.010);
  headPivot.add(headFill);

  // --- frontGrille ----------------------------------------------------------
  {
    const g = new THREE.Group();
    put(buildGrilleRibGeometry(), plasticGrille, g);
    // outer bezel: from the rib crest out to the rounded front lip
    put(
      latheZGeo(
        [
          [0.0896, 0.0338],
          [0.0916, 0.0344],
          [0.0938, 0.0356],
          [0.0952, 0.0378],
          [0.0956, 0.0396],
          [0.0950, 0.0406],
          [0.0928, 0.0410],
          [0.0900, 0.0402],
        ],
        96,
      ),
      plasticGrille,
      g,
    );
    // skirt down to the shell parting line at z 0.016
    put(
      latheZGeo(
        [
          [0.0954, 0.0394],
          [0.0958, 0.0330],
          [0.0958, 0.0250],
          [0.0956, 0.0190],
          [0.0950, 0.0160],
        ],
        96,
      ),
      plasticGrille,
      g,
    );
    // front cap (0.32 D) with a raised centre boss
    put(
      latheZGeo(
        [
          [0.00005, 0.0378],
          [0.0196, 0.0378],
          [0.0266, 0.0384],
          [0.0298, 0.0398],
          [0.0304, 0.0414],
          [0.0294, 0.0428],
          [0.0248, 0.0436],
          [0.0136, 0.0438],
          [0.00005, 0.0438],
        ],
        96,
      ),
      plastic,
      g,
    );
    put(
      latheZGeo(
        [
          [0.00005, 0.0436],
          [0.0052, 0.0438],
          [0.0062, 0.0446],
          [0.0048, 0.0453],
          [0.00005, 0.0454],
        ],
        48,
      ),
      plastic,
      g,
    );
    addPart("frontGrille", g, headCore, V(0, 0, 0), V(0.052, 0.040, 0.036));
  }

  // --- blades (7) -----------------------------------------------------------
  {
    const g = new THREE.Group();
    const [bladeGeo, hubGeo] = buildBladesGeometry();
    put(bladeGeo, bladeMat, g);
    put(hubGeo, plasticSoft, g);
    addPart("blades", g, headCore, V(0, 0, 0), V(0.040, 0.032, 0.019));
  }

  // --- motor ----------------------------------------------------------------
  {
    const g = new THREE.Group();
    put(cylZGeo(0.0140, 0.0140, 0.0240, 40), metalDark, g, 0, 0, 0.0020);
    put(cylZGeo(0.0148, 0.0140, 0.0030, 40), metalDark, g, 0, 0, 0.0155);
    put(cylZGeo(0.0140, 0.0148, 0.0030, 40), metalDark, g, 0, 0, -0.0115);
    put(cylZGeo(0.0024, 0.0024, 0.0200, 20), metal, g, 0, 0, 0.0270);
    put(cylZGeo(0.0110, 0.0110, 0.0050, 36), metalDark, g, 0, 0, -0.0155);
    // counterweight disc behind the motor
    put(cylZGeo(0.0126, 0.0126, 0.0058, 36), metal, g, 0, 0, -0.0212);
    // mounting plate bolted to the rear grille's centre boss
    put(new THREE.BoxGeometry(0.0430, 0.0430, 0.0034), plasticSoft, g, 0, 0, -0.0265);
    for (const a of [90, 210, 330]) {
      const c = Math.cos(deg(a));
      const s = Math.sin(deg(a));
      put(new THREE.BoxGeometry(0.0042, 0.0042, 0.0130), plasticSoft, g, c * 0.0150, s * 0.0150, -0.0195);
      put(new THREE.BoxGeometry(0.0042, 0.0042, 0.0130), metal, g, c * 0.0195, s * 0.0195, -0.0195);
    }
    addPart("motor", g, headCore, V(0, 0, 0), V(0.0130, 0.0128, 0.0060));
  }

  // --- rearGrille (outer shell + spoke cage are one moulding) ---------------
  {
    const g = new THREE.Group();
    // the shell: front parting line at z 0.0172 down to the rear lip at z -0.047
    put(
      latheZGeo(
        [
          [0.0942, 0.0176],
          [0.0949, 0.0090],
          [0.0950, 0.0000],
          [0.0947, -0.0090],
          [0.0942, -0.0190],
          [0.0926, -0.0290],
          [0.0904, -0.0370],
          [0.0876, -0.0430],
          [0.0858, -0.0462],
          [0.0850, -0.0470],
        ],
        112,
      ),
      plasticShell,
      g,
    );
    put(buildRearGrilleGeometry({ count: DIM.ribCount, rIn: 0.0285, rOut: 0.0870, kink: 17 }), plasticGrille, g, 0, 0, Z_GR);
    // rim ring the spokes land on
    put(
      latheZGeo(
        [
          [0.0826, Z_GR - 0.0022],
          [0.0868, Z_GR - 0.0032],
          [0.0884, Z_GR + 0.0010],
          [0.0870, Z_GR + 0.0036],
          [0.0828, Z_GR + 0.0030],
        ],
        96,
      ),
      plasticGrille,
      g,
    );
    // two reinforcing hoops
    for (const rr of [0.0550, 0.0760]) {
      const hoop = new THREE.TorusGeometry(rr, 0.0014, 8, 96);
      put(hoop, plasticGrille, g, 0, 0, Z_GR - 0.0014);
    }
    // central boss the control box screws onto
    put(cylZGeo(0.0392, 0.0392, 0.0034, 48), plasticInner, g, 0, 0, Z_GR - 0.0024);
    addPart("rearGrille", g, headCore, V(0, 0, 0), V(0.058, -0.052, Z_GR + 0.002));
  }

  // --- rearControl (control box: rocker, blank plate, cable) ---------------
  {
    const g = new THREE.Group();
    // body: rounded box from the grille plane back to the face
    const bodyShape = roundedRectShape(0.1280, 0.0920, 0.0170);
    const bodyGeo = new THREE.ExtrudeGeometry(bodyShape, {
      depth: 0.0160,
      bevelEnabled: false,
      curveSegments: 16,
    });
    put(bodyGeo, plasticSoft, g, 0, 0, Z_BOX);
    // raised face lip
    const lipShape = roundedRectShape(0.1264, 0.0904, 0.0168);
    lipShape.holes.push(roundedRectPath(0.1170, 0.0810, 0.0150));
    put(
      new THREE.ExtrudeGeometry(lipShape, { depth: 0.0022, bevelEnabled: false, curveSegments: 16 }),
      plasticSoft,
      g,
      0,
      0,
      Z_BOX - 0.0022,
    );
    // recessed face plate
    put(
      new THREE.ExtrudeGeometry(roundedRectShape(0.1174, 0.0814, 0.0152), {
        depth: 0.0016,
        bevelEnabled: false,
        curveSegments: 16,
      }),
      plasticWell,
      g,
      0,
      0,
      Z_BOX - 0.0012,
    );
    // rocker switch in a shallow well
    put(
      new THREE.ExtrudeGeometry(roundedRectShape(0.0420, 0.0230, 0.0042), {
        depth: 0.0014,
        bevelEnabled: false,
        curveSegments: 8,
      }),
      plasticDark,
      g,
      -0.0050,
      0.0240,
      Z_BOX - 0.0022,
    );
    const rocker = put(
      new THREE.ExtrudeGeometry(roundedRectShape(0.0320, 0.0160, 0.0022), {
        depth: 0.0042,
        bevelEnabled: false,
        curveSegments: 8,
      }),
      dark,
      g,
      -0.0050,
      0.0240,
      Z_BOX - 0.0074,
    );
    rocker.rotation.x = deg(7);
    // blank nameplate (brand removed per the user's instruction)
    put(
      new THREE.ExtrudeGeometry(roundedRectShape(0.0600, 0.0400, 0.0026), {
        depth: 0.0012,
        bevelEnabled: false,
        curveSegments: 8,
      }),
      sticker,
      g,
      -0.0150,
      -0.0150,
      Z_BOX - 0.0028,
    );
    // PCB behind the face plate
    put(new THREE.BoxGeometry(0.0440, 0.0360, 0.0012), pcbMat, g, 0, -0.0060, -0.0480);
    put(new THREE.BoxGeometry(0.0110, 0.0080, 0.0060), metalDark, g, 0.0120, 0.0060, -0.0470);
    put(new THREE.BoxGeometry(0.0070, 0.0120, 0.0050), dark, g, -0.0130, -0.0100, -0.0470);
    // screw ding in the box's lower face
    put(cylZGeo(0.0032, 0.0032, 0.0016, 20), plasticDark, g, 0, -0.0380, Z_BOX - 0.0020);
    // cable strain relief at the box's bottom, then the cable itself
    put(cylZGeo(0.0048, 0.0040, 0.0110, 24), plasticSoft, g, 0.0270, -0.0470, Z_BOX + 0.0030);
    // b_back.jpg: the cable leaves the box's bottom right and sweeps DOWN-LEFT across the
    // base's rear, so the descent has to run toward -X, not +X.
    const cableCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0.0250, -0.0560, Z_BOX + 0.0030),
      new THREE.Vector3(0.0165, -0.0850, -0.0570),
      new THREE.Vector3(0.0040, -0.1170, -0.0665),
      new THREE.Vector3(-0.0110, -0.1500, -0.0790),
      new THREE.Vector3(-0.0250, -0.1770, -0.0940),
      new THREE.Vector3(-0.0350, -0.1905, -0.1060),
      // ... then it reaches the desk and runs off toward the front-left of frame,
      // so the cable never ends in mid-air inside a shot (reference photos all show
      // the cable trailing away across the table).
      new THREE.Vector3(-0.0620, -0.1922, -0.0600),
      new THREE.Vector3(-0.0880, -0.1926, -0.0020),
      new THREE.Vector3(-0.1090, -0.1928, 0.0560),
      new THREE.Vector3(-0.1230, -0.1929, 0.1020),
    ]);
    const cable = new THREE.TubeGeometry(cableCurve, 110, 0.0026, 10, false);
    put(cable, plasticSoft, g);
    g.children[g.children.length - 1].userData.noAnchor = true;
    addPart("rearControl", g, headCore, V(0, 0, 0), V(0.0340, -0.0320, Z_BOX - 0.004));
  }

  // --- tilt knobs -----------------------------------------------------------
  for (const [name, sx] of [
    ["knobL", -1],
    ["knobR", 1],
  ]) {
    const g = new THREE.Group();
    const prof = [
      [0.00005, -0.0072],
      [0.0066, -0.0072],
      [0.0096, -0.0060],
      [0.0107, -0.0030],
      [0.0110, 0.0000],
      [0.0110, 0.0028],
      [0.0096, 0.0042],
      [0.0084, 0.0048],
      [0.0078, 0.0058],
      [0.0058, 0.0064],
      [0.00005, 0.0066],
    ];
    const kg = latheZGeo(prof, 48);
    kg.rotateY(Math.PI / 2);
    put(kg, plastic, g);
    const groove = new THREE.TorusGeometry(0.0084, 0.0008, 8, 40);
    groove.rotateY(Math.PI / 2);
    put(groove, plasticSoft, g, 0.0038, 0, 0);
    const kx = sx * (ARC_R + BAND_T + 0.0042);
    addPart(name, g, root, V(kx, HY - TILT_DROP, KNOB_Z), V(sx * 0.0112, 0, 0));
    g.rotation.y = sx > 0 ? 0 : Math.PI;
  }

  // --- yoke (U strap + bottom bridge) --------------------------------------
  {
    const g = new THREE.Group();
    const wf = (v) => v * BAND_W;
    const bandProfile = [
      [-BAND_T, wf(-0.80)],
      [-BAND_T * 1.05, wf(-0.42)],
      [-BAND_T * 1.05, wf(0.42)],
      [-BAND_T, wf(0.80)],
      [-BAND_T * 0.86, wf(1.0)],
      [-BAND_T * 0.32, wf(1.05)],
      [BAND_T * 0.32, wf(1.05)],
      [BAND_T * 0.86, wf(1.0)],
      [BAND_T, wf(0.80)],
      [BAND_T * 1.05, wf(0.42)],
      [BAND_T * 1.05, wf(-0.42)],
      [BAND_T, wf(-0.80)],
      [BAND_T * 0.86, wf(-1.0)],
      [BAND_T * 0.32, wf(-1.05)],
      [-BAND_T * 0.32, wf(-1.05)],
      [-BAND_T * 0.86, wf(-1.0)],
    ];
    put(
      sweepBandGeometry({
        radius: ARC_R,
        profile: bandProfile,
        theta0: deg(180),
        span: deg(180),
        segs: 132,
        widthAt: (t) => 1 + 0.30 * Math.pow(Math.abs(2 * t - 1), 2.6),
      }),
      plasticBand,
      g,
      0,
      0,
      KNOB_Z,
    );
    // bridge + collar where the neck enters
    put(cylZGeo(0.0130, 0.0130, 0.0300, 32), plastic, g, 0, -ARC_R, KNOB_Z);
    put(latheYGeo([[0.0146, 0.000], [0.0172, 0.0030], [0.0182, 0.0076], [0.0180, 0.0116], [0.0166, 0.0140]], 40), plastic, g, 0, -(ARC_R + 0.0050), KNOB_Z);
    addPart("yoke", g, root, V(0, HY - TILT_DROP, 0), V(0, HY - TILT_DROP - ARC_R, KNOB_Z));
  }

  // --- neck (waisted, 14-facet stalk) --------------------------------------
  {
    const g = new THREE.Group();
    put(
      latheYGeo(
        [
          [0.00005, 0.0450],
          [0.0200, 0.0460],
          [0.0206, 0.0520],
          [0.0180, 0.0560],
          [0.0156, 0.0600],
          [0.0140, 0.0640],
          [0.0130, 0.0680],
          [0.0128, 0.0715],
          [0.0138, 0.0755],
          [0.0152, 0.0790],
          [0.0166, 0.0820],
          [0.0172, 0.0838],
        ],
        14,
      ),
      plastic,
      g,
    );
    // collar rings at both ends
    put(latheYGeo([[0.0206, 0.0446], [0.0214, 0.0472], [0.0206, 0.0498]], 14), plastic, g);
    addPart("neck", g, root, V(0, 0, 0), V(0, 0.0630, 0.0060));
  }

  // --- baseTop (arched pedestal: hook well, parting groove, pan boss) -------
  {
    const g = new THREE.Group();
    const arch = new THREE.Shape();
    arch.moveTo(-0.0340, 0.0140);
    arch.quadraticCurveTo(-0.0348, 0.0385, -0.0285, 0.0455);
    arch.quadraticCurveTo(-0.0220, 0.0505, -0.0130, 0.0505);
    arch.lineTo(0.0130, 0.0505);
    arch.quadraticCurveTo(0.0220, 0.0505, 0.0285, 0.0455);
    arch.quadraticCurveTo(0.0348, 0.0385, 0.0340, 0.0140);
    arch.lineTo(-0.0340, 0.0140);
    const archGeo = new THREE.ExtrudeGeometry(arch, {
      depth: 0.0340,
      bevelEnabled: true,
      bevelThickness: 0.0120,
      bevelSize: 0.0078,
      bevelSegments: 10,
      curveSegments: 28,
    });
    archGeo.translate(0, 0, -0.0170);
    put(toCreasedNormals(archGeo, 0.72), plasticShell, g);
    // parting groove between cover and plate
    put(new THREE.TorusGeometry(0.0400, 0.0020, 8, 64), plasticWell, g, 0, 0.0142, 0);
    // hook well: proud frame + recessed back plate
    const frameShape = roundedRectShape(0.0376, 0.0280, 0.0070);
    frameShape.holes.push(roundedRectPath(0.0312, 0.0216, 0.0052));
    put(
      new THREE.ExtrudeGeometry(frameShape, { depth: 0.0020, bevelEnabled: false, curveSegments: 12 }),
      plastic,
      g,
      0,
      0.0280,
      0.0290,
    );
    put(
      new THREE.ExtrudeGeometry(roundedRectShape(0.0316, 0.0220, 0.0052), {
        depth: 0.0014,
        bevelEnabled: false,
        curveSegments: 12,
      }),
      wellDeep,
      g,
      0,
      0.0280,
      0.0222,
    );
    // pan boss on the cover's left flank
    put(cylXGeo(0.0064, 0.0064, 0.0090, 24), plastic, g, -0.0300, 0.0300, 0.0100);
    addPart("baseTop", g, root, V(0, 0, 0), V(0, 0.0320, 0.0200));
  }

  // --- hook (folded metal jaw + brass leaf springs inside the well) ---------
  {
    const g = new THREE.Group();
    put(new THREE.BoxGeometry(0.0034, 0.0136, 0.0058), steel, g, -0.0122, 0.0008, 0);
    put(new THREE.BoxGeometry(0.0034, 0.0136, 0.0058), steel, g, 0.0122, 0.0008, 0);
    put(new THREE.BoxGeometry(0.0278, 0.0032, 0.0058), steel, g, 0, -0.0062, 0);
    put(cylXGeo(0.0028, 0.0028, 0.0288, 20), metalDark, g, 0, -0.0090, 0);
    for (const sx of [-1, 1]) {
      const leaf = put(new THREE.BoxGeometry(0.0026, 0.0072, 0.0012), brass, g, sx * 0.0122, 0.0072, -0.0008);
      leaf.rotation.x = deg(14);
    }
    addPart("hook", g, root, V(0, 0.0280, 0.0280), V(0, 0.0280, 0.0330));
  }

  // --- baseBottom (round plate, waffle ribs, cable grommet) ----------------
  {
    const g = new THREE.Group();
    put(
      latheYGeo(
        [
          [0.00005, 0.0086],
          [0.0466, 0.0086],
          [0.0498, 0.0094],
          [0.0500, 0.0046],
          [0.0518, 0.0038],
          [0.0562, 0.0042],
          [0.0572, 0.0060],
          [0.0572, 0.0126],
          [0.0562, 0.0150],
          [0.0534, 0.0163],
          [0.0500, 0.0166],
          [0.00005, 0.0166],
        ],
        96,
      ),
      plastic,
      g,
    );
    // waffle grid on the underside: two +/-45 deg families
    for (const sign of [1, -1]) {
      const fam = new THREE.Group();
      for (let i = -4; i <= 4; i++) {
        const d = i * 0.0106;
        const half = Math.sqrt(Math.max(0, 0.0500 * 0.0500 - d * d));
        if (half < 0.006) continue;
        put(new THREE.BoxGeometry(half * 2, 0.0032, 0.0022), plastic, fam, 0, 0.0069, d);
      }
      fam.rotation.y = sign * (Math.PI / 4);
      g.add(fam);
    }
    // cable grommet on the underside
    put(new THREE.CylinderGeometry(0.0062, 0.0054, 0.0060, 24), plasticWell, g, -0.0230, 0.0058, 0.0);
    addPart("baseBottom", g, root, V(0, 0, 0), V(0.0430, 0.0100, 0.0));
  }

  // --- feet (4 rubber pads) -------------------------------------------------
  {
    const g = new THREE.Group();
    for (let i = 0; i < 4; i++) {
      const a = deg(45 + 90 * i);
      const x = 0.0485 * Math.cos(a);
      const z = 0.0485 * Math.sin(a);
      put(
        latheYGeo(
          [
            [0.00005, 0.0000],
            [0.0062, 0.0000],
            [0.0078, 0.0008],
            [0.0080, 0.0032],
            [0.0066, 0.0044],
            [0.00005, 0.0044],
          ],
          32,
        ),
        rubber,
        g,
        x,
        0,
        z,
      );
    }
    addPart("feet", g, root, V(0, 0, 0), V(0.0330, 0.0020, 0.0280));
  }

  // ---------------------------------------------------------------------------
  // explosion layout (p = 0..1)
  // ---------------------------------------------------------------------------
  // Explosion layout: a vertical strip with a slight axial fan, so each of the 13
  // parts clears its neighbour and the label columns can attach cleanly.
  // Offsets are tuned so the exploded column spans y 0.006 .. 0.636 at full
  // separation with the director's 0.212 lift (feet just clear the floor).
  const EXPLODE = {
    frontGrille: V(0.0, 0.135, 0.100),
    blades: V(0.0, 0.100, 0.050),
    motor: V(0.0, 0.066, 0.002),
    rearGrille: V(0.0, 0.032, -0.046),
    rearControl: V(0.0, 0.0, -0.100),
    knobL: V(-0.150, -0.012, -0.030),
    knobR: V(0.150, -0.012, -0.030),
    yoke: V(0.0, -0.046, -0.028),
    neck: V(0.0, -0.090, 0.0),
    hook: V(0.145, -0.128, 0.050),
    baseTop: V(0.0, -0.150, 0.0),
    baseBottom: V(0.0, -0.204, 0.0),
    feet: V(0.0, -0.252, 0.0),
  };
  let explodeMap = null;

  // Anchor each label on a real surface point of its part. The default is the
  // bounding-box centre; parts that are open or hollow (yoke U, base plate, feet
  // pads, hook jaw, control-box face) bias the anchor toward a visible face.
  // Biases are fractions of the part's bbox: 0.5 = centre, 1 = max side.
  const ANCHOR_BIAS = {
    yoke: [0.5, 0.04, 0.5],
    rearControl: [0.5, 0.5, 1.0],
    hook: [0.5, 0.5, 1.0],
    baseTop: [0.5, 0.5, 1.0],
    baseBottom: [0.5, 0.5, 1.0],
    feet: [0.5, 0.5, 1.0],
  };
  scene.updateMatrixWorld(true);
  for (const name of Object.keys(parts)) {
    const part = parts[name];
    const bb = new THREE.Box3();
    part.traverse(function (o) {
      if (o.isMesh && !o.userData.noAnchor) bb.union(new THREE.Box3().setFromObject(o));
    });
    if (bb.isEmpty()) bb.setFromObject(part);
    const bias = ANCHOR_BIAS[name] || [0.5, 0.5, 0.5];
    const c = new THREE.Vector3(
      bb.min.x + (bb.max.x - bb.min.x) * bias[0],
      bb.min.y + (bb.max.y - bb.min.y) * bias[1],
      bb.min.z + (bb.max.z - bb.min.z) * bias[2],
    );
    part.userData.anchorOffset = part.worldToLocal(c);
  }

  // ---------------------------------------------------------------------------
  // state + camera
  // ---------------------------------------------------------------------------
  const state = {
    view: { yaw: -20, pitch: 9, dist: 0.92, target: [0, H, 0], fov: 30 },
    exploded: 0,
    lift: 0,
    spin: 0,
    tiltDeg: DIM.headTiltDeg,
  };

  const targetVec = new THREE.Vector3();

  function applyCamera() {
    const v = state.view;
    const yaw = deg(v.yaw);
    const pitch = deg(v.pitch);
    targetVec.set(v.target[0], v.target[1], v.target[2]);
    camera.position.set(
      targetVec.x + v.dist * Math.sin(yaw) * Math.cos(pitch),
      targetVec.y + v.dist * Math.sin(pitch),
      targetVec.z + v.dist * Math.cos(yaw) * Math.cos(pitch),
    );
    camera.fov = v.fov;
    camera.updateProjectionMatrix();
    camera.lookAt(targetVec);
    camera.updateMatrixWorld(true);
  }

  function applyExplode() {
    for (const name of Object.keys(parts)) {
      const base = EXPLODE[name];
      if (!base) continue;
      // explodeMap may carry a per-part 0..1 amount (staggered teardown) or an
      // explicit offset vector; a plain global amount comes from state.exploded.
      let ox = base.x;
      let oy = base.y;
      let oz = base.z;
      let amt = state.exploded;
      const m = explodeMap ? explodeMap[name] : undefined;
      if (typeof m === "number") {
        amt = m;
      } else if (m) {
        ox = Array.isArray(m) ? m[0] : m.x;
        oy = Array.isArray(m) ? m[1] : m.y;
        oz = Array.isArray(m) ? m[2] : m.z;
        amt = 1;
      }
      const bp = basePos[name];
      parts[name].position.set(bp.x + ox * amt, bp.y + oy * amt, bp.z + oz * amt);
    }
  }

  function render() {
    headPivot.rotation.x = -deg(state.tiltDeg);
    applyExplode();
    root.position.y = state.lift;
    if (key.shadow) key.shadow.intensity = 0.82 - 0.52 * Math.min(1, Math.max(0, state.lift / 0.06));
    applyCamera();
    if (parts.blades) parts.blades.rotation.z = state.spin;
    root.updateMatrixWorld(true);
    renderer.render(scene, camera);
  }

  function getAnchors() {
    const out = {};
    const v = new THREE.Vector3();
    for (const name of Object.keys(parts)) {
      const part = parts[name];
      v.copy(part.userData.anchorOffset).applyMatrix4(part.matrixWorld);
      const world = v.clone();
      v.project(camera);
      out[name] = {
        x: ((v.x + 1) / 2) * width,
        y: ((1 - v.y) / 2) * height,
        z: world.z,
        visible: v.z > -1 && v.z < 1 && Math.abs(v.x) <= 1.02 && Math.abs(v.y) <= 1.02,
      };
    }
    return out;
  }

  const ctl = {
    PARTS,
    setView(view) {
      Object.assign(state.view, view);
      if (view.target) state.view.target = view.target.slice();
    },
    setLift(v) {
      state.lift = v;
    },
    setExplode(p) {
      state.exploded = Math.min(1, Math.max(0, p));
    },
    setExplodeMap(map) {
      explodeMap = map || null;
    },
    setSpin(rad) {
      state.spin = rad;
    },
    setHeadTilt(d) {
      state.tiltDeg = d;
    },
    setQuality(level) {
      key.shadow.mapSize.set(level === "interactive" ? 1024 : 2048, level === "interactive" ? 1024 : 2048);
      if (key.shadow.map) {
        key.shadow.map.dispose();
        key.shadow.map = null;
      }
    },
    render,
    getAnchors,
    resize(w, h) {
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    },
    dispose() {
      renderer.dispose();
    },
    getState() {
      return state;
    },
    renderer,
    camera,
    scene,
  };

  // debug hook for QA renders: ?hide=blades,neck hides parts, ?only=frontGrille shows just one
  if (typeof location !== "undefined" && location.search) {
    const q = new URLSearchParams(location.search);
    const hide = (q.get("hide") || "").split(",").filter(Boolean);
    for (const k of hide) if (parts[k]) parts[k].visible = false;
    const only = q.get("only");
    if (only) {
      const keep = new Set(only.split(","));
      for (const k of Object.keys(parts)) parts[k].visible = keep.has(k);
    }
  }

  render();
  return ctl;
}
