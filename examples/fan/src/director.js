// FanDirector — deterministic choreography for the 43.5 s teardown film and the
// interactive demo. No dependencies; runs as a classic script and exposes
// window.FanDirector.
//
// World/model contract: fan faces +Z, base on y = 0, camera via ctl.setView
// ({yaw,pitch,dist,target,fov}); yaw 0 = facing the front, 90 = camera on +X.
// v2 model: 13 parts, head centre y = 0.194 (1.02 x head Ø), base Ø 0.114.
(function () {
  "use strict";

  var DURATION = 43.5;
  var FPS = 30;

  // Disassembly order. Matches the scene's PART_ORDER and the audio contract:
  // release hit i lands at 21.15 + 0.30 i, reassembly touch i at 35.18 + 0.25 i,
  // final seat at 38.45.
  var PARTS = [
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
  ];

  var LABELS = {
    frontGrille: "Front grille",
    blades: "Blades (x7)",
    motor: "Motor + struts",
    rearGrille: "Rear grille + shell",
    rearControl: "Control box",
    knobL: "Tilt knob (left)",
    knobR: "Tilt knob (right)",
    yoke: "Yoke strap",
    neck: "Neck",
    hook: "Clip hook",
    baseTop: "Upper base",
    baseBottom: "Lower base",
    feet: "Rubber feet",
  };

  // ---- easing -------------------------------------------------------------
  function clamp01(x) {
    return x < 0 ? 0 : x > 1 ? 1 : x;
  }
  function lerp(a, b, t) {
    return a + (b - a) * t;
  }
  function easeOutQuad(t) {
    return 1 - (1 - t) * (1 - t);
  }
  function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
  }
  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }
  function easeInOutSine(t) {
    return -(Math.cos(Math.PI * t) - 1) / 2;
  }

  // ---- camera per shot (hard cuts between shots) --------------------------
  // Each shot takes u = local progress 0..1 and returns {yaw,pitch,dist,target,fov}.
  // Head centre sits at y 0.194; the base disc spans y 0..0.0166.
  var TARGET_FRONT = [0, 0.196, 0];
  var TARGET_EXPLODED = [-0.030, 0.330, 0.055];

  var SHOTS = [
    {
      name: "title",
      start: 0.0,
      end: 2.0,
      view: function (u) {
        return {
          yaw: lerp(-26, -20, u),
          pitch: lerp(7, 9, easeInOutCubic(u)),
          dist: 1.06,
          target: [-0.090, 0.200, 0],
          fov: 30,
        };
      },
    },
    {
      name: "orbit",
      start: 2.0,
      end: 9.0,
      view: function (u) {
        var s = easeInOutCubic(u);
        return {
          yaw: -22 + 360 * s,
          pitch: 7 + 5 * Math.sin(Math.PI * u),
          dist: lerp(1.04, 0.96, s),
          target: TARGET_FRONT.slice(),
          fov: 30,
        };
      },
    },
    {
      name: "grille-macro",
      start: 9.0,
      end: 12.5,
      view: function (u) {
        return {
          yaw: lerp(-16, -8, u),
          pitch: lerp(12, 5, easeInOutCubic(u)),
          dist: lerp(0.62, 0.56, easeInOutCubic(u)),
          target: [0, 0.200, 0.050],
          fov: 24,
        };
      },
    },
    {
      name: "back-3q",
      start: 12.5,
      end: 16.0,
      view: function (u) {
        var e = easeInOutSine(u);
        return {
          yaw: lerp(148, 172, e),
          pitch: lerp(6, 9, e),
          dist: lerp(0.98, 0.92, e),
          target: [0, 0.200, -0.012],
          fov: 30,
        };
      },
    },
    {
      name: "hub-macro",
      start: 16.0,
      end: 18.5,
      view: function (u) {
        return {
          yaw: lerp(14, 23, u),
          pitch: lerp(7, 2, u),
          dist: lerp(0.36, 0.32, u),
          target: [0, 0.194, 0.026],
          fov: 26,
        };
      },
    },
    {
      name: "wide",
      start: 18.5,
      end: 21.0,
      view: function (u) {
        return {
          yaw: lerp(-8, -6, u),
          pitch: 8,
          dist: 0.86,
          target: TARGET_FRONT.slice(),
          fov: 30,
        };
      },
    },
    {
      name: "explode",
      start: 21.0,
      end: 29.5,
      view: function (u) {
        var e = easeInOutCubic(u);
        // pull back fast: the grille travels 135 mm toward the lens in the first second
        var d = easeOutCubic(u);
        return {
          yaw: lerp(-6, 56, e),
          pitch: lerp(8, 11, e),
          dist: lerp(0.86, 1.58, d),
          target: [lerp(0, TARGET_EXPLODED[0], e), lerp(0.196, TARGET_EXPLODED[1], e), lerp(0, TARGET_EXPLODED[2], e)],
          fov: 30,
        };
      },
    },
    {
      name: "exploded-hold",
      start: 29.5,
      end: 34.0,
      view: function (u) {
        var e = easeInOutSine(u);
        return {
          yaw: lerp(56, 52, e),
          pitch: lerp(11, 10, u),
          dist: lerp(1.58, 1.52, e),
          target: TARGET_EXPLODED.slice(),
          fov: 30,
        };
      },
    },
    {
      name: "reassemble",
      start: 34.0,
      end: 39.5,
      view: function (u) {
        var e = easeInOutCubic(u);
        return {
          yaw: lerp(52, -14, e),
          pitch: lerp(10, 8, e),
          dist: lerp(1.52, 0.90, e),
          target: [lerp(TARGET_EXPLODED[0], 0, e), lerp(TARGET_EXPLODED[1], 0.196, e), lerp(TARGET_EXPLODED[2], 0, e)],
          fov: 30,
        };
      },
    },
    {
      name: "end",
      start: 39.5,
      end: 43.5,
      view: function (u) {
        var e = easeInOutCubic(u);
        return {
          yaw: lerp(-14, -17, e),
          pitch: 8,
          dist: lerp(1.06, 1.04, e),
          target: [-0.090, 0.192, 0],
          fov: 30,
        };
      },
    },
  ];

  function getShot(t) {
    for (var i = 0; i < SHOTS.length; i++) {
      var s = SHOTS[i];
      if (t >= s.start && t < s.end) return s;
    }
    return SHOTS[SHOTS.length - 1];
  }

  function getView(t) {
    var s = getShot(t);
    var u = clamp01((t - s.start) / (s.end - s.start));
    var v = s.view(u);
    return {
      yaw: v.yaw,
      pitch: v.pitch,
      dist: v.dist,
      target: v.target.slice(),
      fov: v.fov,
    };
  }

  // ---- explosion staggering ----------------------------------------------
  // Release: part i starts moving at RELEASE_HIT(i) so the foley pop lands on
  // the frame the part breaks contact. Reassembly: reverse order, timed so the
  // part *touches down* on its audio hit at 35.18 + 0.25 j.
  var EXPLODE_START = 21.15;
  var EXPLODE_STAGGER = 0.30;
  var EXPLODE_DUR = 1.6;
  var REASSEMBLE_TOUCH = 35.18;
  var REASSEMBLE_STAGGER = 0.25;
  var REASSEMBLE_DUR = 1.2;
  var REASSEMBLE_START = REASSEMBLE_TOUCH - REASSEMBLE_DUR; // 33.98

  function partExplode(name, t) {
    var i = PARTS.indexOf(name);
    var upStart = EXPLODE_START + i * EXPLODE_STAGGER;
    var up = easeOutCubic(clamp01((t - upStart) / EXPLODE_DUR));
    var iReverse = PARTS.length - 1 - i;
    var downStart = REASSEMBLE_START + iReverse * REASSEMBLE_STAGGER;
    var down = 1 - easeInOutCubic(clamp01((t - downStart) / REASSEMBLE_DUR));
    return Math.min(up, down);
  }

  function explodeMap(t) {
    var m = {};
    var max = 0;
    for (var i = 0; i < PARTS.length; i++) {
      var p = partExplode(PARTS[i], t);
      m[PARTS[i]] = p;
      if (p > max) max = p;
    }
    return { map: m, max: max };
  }

  // ---- blade spin (analytic integral of piecewise-linear angular speed) ---
  // [time, rad/s] keys; speed ramps linearly between keys.
  var SPIN_KEYS = [
    [0.0, 0.4],
    [1.8, 0.4],
    [3.0, 8.0],
    [9.0, 8.0],
    [9.6, 1.6],
    [12.5, 1.6],
    [13.0, 1.2],
    [16.0, 1.2],
    [16.6, 6.0],
    [18.6, 6.0],
    [20.4, 0.0],
    [33.6, 0.0],
    [35.2, 0.0],
    [36.6, 0.0],
    [38.4, 9.0],
    [43.5, 9.0],
  ];
  var SPIN_PHASE = 0.6;

  function spinAngle(t) {
    var angle = SPIN_PHASE;
    for (var i = 0; i < SPIN_KEYS.length - 1; i++) {
      var t0 = SPIN_KEYS[i][0];
      var v0 = SPIN_KEYS[i][1];
      var t1 = SPIN_KEYS[i + 1][0];
      var v1 = SPIN_KEYS[i + 1][1];
      if (t <= t0) break;
      var seg = Math.min(t, t1) - t0;
      if (seg <= 0) continue;
      var vAvg = v0 + ((v1 - v0) * seg) / (2 * (t1 - t0));
      angle += vAvg * seg;
    }
    return angle;
  }

  // ---- labels / titles ----------------------------------------------------
  var LABEL_IN_START = 21.45; // part i pops at 21.15 + 0.30 i, label 0.30 s later
  var LABEL_IN_STAGGER = 0.30;
  var LABEL_IN_DUR = 0.45;
  var LABEL_OUT_LEAD = 0.24;
  var LABEL_OUT_DUR = 0.26;

  function labelAlpha(name, t) {
    var i = PARTS.indexOf(name);
    var inStart = LABEL_IN_START + i * LABEL_IN_STAGGER;
    var aIn = easeOutQuad(clamp01((t - inStart) / LABEL_IN_DUR));
    var iReverse = PARTS.length - 1 - i;
    var outStart = REASSEMBLE_START + iReverse * REASSEMBLE_STAGGER - LABEL_OUT_LEAD;
    var aOut = 1 - clamp01((t - outStart) / LABEL_OUT_DUR);
    return clamp01(Math.min(aIn, aOut));
  }

  function titleAlpha(t) {
    var aIn = easeOutQuad(clamp01((t - 0.15) / 0.6));
    var aOut = 1 - easeInOutCubic(clamp01((t - 1.70) / 0.45));
    return clamp01(Math.min(aIn, aOut));
  }

  function endAlpha(t) {
    return easeOutCubic(clamp01((t - 38.85) / 0.70));
  }

  // the fan lifts off the plinth while it is apart, so the parts can spread
  // downward without cutting into the floor
  function liftAt(t) {
    var up = easeOutCubic(clamp01((t - 21.15) / 3.0));
    var down = easeInOutCubic(clamp01((t - 33.9) / 3.6));
    return 0.256 * up * (1 - down);
  }

  function getFrame(t) {
    var em = explodeMap(t);
    var labels = {};
    for (var i = 0; i < PARTS.length; i++) labels[PARTS[i]] = labelAlpha(PARTS[i], t);
    var s = getShot(t);
    return {
      t: t,
      shot: s.name,
      view: getView(t),
      spin: spinAngle(t),
      exploded: em.max,
      explodeMap: em.map,
      lift: liftAt(t),
      labels: labels,
      title: titleAlpha(t),
      end: endAlpha(t),
    };
  }

  // ---- label layout (screen space, 1920x1080) -----------------------------
  // Left column ends at x = 560 (right-aligned text), right column starts at
  // x = 1360 (left-aligned). Leader lines connect each label edge to its anchor.
  var LAYOUT = {
    width: 1920,
    height: 1080,
    leftEdge: 560,
    rightEdge: 1360,
    gap: 58,
    minY: 190,
    maxY: 890,
    lineInset: 18,
    dotRadius: 3,
  };

  function layoutLabels(anchors, frame) {
    var items = [];
    for (var i = 0; i < PARTS.length; i++) {
      var name = PARTS[i];
      var alpha = frame.labels[name];
      if (!alpha || alpha <= 0.001) continue;
      var a = anchors[name];
      if (!a || !a.visible) continue;
      items.push({
        part: name,
        text: LABELS[name],
        alpha: alpha,
        ax: a.x,
        ay: a.y,
        side: a.x < LAYOUT.width / 2 ? "left" : "right",
      });
    }

    ["left", "right"].forEach(function (side) {
      var list = items.filter(function (it) {
        return it.side === side;
      });
      list.sort(function (a, b) {
        return a.ay - b.ay;
      });
      var prev = LAYOUT.minY - LAYOUT.gap;
      for (var i = 0; i < list.length; i++) {
        list[i].y = Math.max(list[i].ay, prev + LAYOUT.gap);
        prev = list[i].y;
      }
      if (list.length) {
        var overflow = list[list.length - 1].y - LAYOUT.maxY;
        if (overflow > 0) {
          for (var j = 0; j < list.length; j++) {
            list[j].y -= overflow;
            if (list[j].y < LAYOUT.minY) list[j].y = LAYOUT.minY;
          }
          // reenforce gap after clamping
          for (var k = 1; k < list.length; k++) {
            if (list[k].y < list[k - 1].y + LAYOUT.gap) list[k].y = list[k - 1].y + LAYOUT.gap;
          }
        }
      }
      for (var m = 0; m < list.length; m++) {
        var it = list[m];
        it.x = side === "left" ? LAYOUT.leftEdge : LAYOUT.rightEdge;
        it.textAlign = side === "left" ? "right" : "left";
        it.lineEndX = side === "left" ? LAYOUT.leftEdge + LAYOUT.lineInset : LAYOUT.rightEdge - LAYOUT.lineInset;
      }
    });

    return items;
  }

  // ---- model application helper ------------------------------------------
  function apply(ctl, t) {
    var frame = getFrame(t);
    ctl.setView(frame.view);
    if (typeof ctl.setExplodeMap === "function") {
      ctl.setExplodeMap(frame.explodeMap);
    } else {
      ctl.setExplode(frame.exploded);
    }
    ctl.setSpin(frame.spin);
    if (typeof ctl.setLift === "function") ctl.setLift(frame.lift);
    ctl.render();
    var anchors = typeof ctl.getAnchors === "function" ? ctl.getAnchors() : {};
    return { frame: frame, anchors: anchors };
  }

  window.FanDirector = {
    DURATION: DURATION,
    FPS: FPS,
    PARTS: PARTS,
    LABELS: LABELS,
    LAYOUT: LAYOUT,
    getFrame: getFrame,
    getView: getView,
    getShot: getShot,
    layoutLabels: layoutLabels,
    apply: apply,
    ease: {
      outQuad: easeOutQuad,
      outCubic: easeOutCubic,
      inOutCubic: easeInOutCubic,
      inOutSine: easeInOutSine,
    },
  };
})();
