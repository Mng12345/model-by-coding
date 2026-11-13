// fan-ui.js — interactive layer for fan.html / fan-single.html.
// Requires: window.FanScene (bundle) and window.FanDirector (choreography).
(function () {
  "use strict";

  var DURATION = 40;
  var TARGET = [0, 0.155, 0];
  var HERO_VIEW = { yaw: -22, pitch: 9, dist: 0.92, target: TARGET.slice(), fov: 30 };
  var END_VIEW = { yaw: -17, pitch: 8, dist: 0.8, target: [-0.045, 0.15, 0], fov: 30 };

  var canvas = document.getElementById("stage");
  var svg = document.getElementById("leaders");
  var labelLayer = document.getElementById("labels");
  var titleCard = document.getElementById("titleCard");
  var endCard = document.getElementById("endCard");
  var slider = document.getElementById("explodeSlider");
  var sliderValue = document.getElementById("explodeValue");
  var demoBtn = document.getElementById("demoBtn");
  var resetBtn = document.getElementById("resetBtn");

  function dims() {
    return { w: window.innerWidth, h: window.innerHeight };
  }

  var size = dims();
  var ctl = FanScene.create(canvas, {
    width: size.w,
    height: size.h,
    pixelRatio: Math.min(window.devicePixelRatio || 1, 2),
  });

  var state = {
    mode: "manual", // "manual" | "demo"
    demoTime: 0,
    explode: 0,
    spin: 0.6,
    yaw: HERO_VIEW.yaw,
    pitch: HERO_VIEW.pitch,
    dist: HERO_VIEW.dist,
    target: TARGET.slice(),
    lastFrame: null,
    lastAnchors: null,
    dragging: false,
    dragX: 0,
    dragY: 0,
    spinOn: true,
  };

  // ---- label / leader DOM -------------------------------------------------
  var NS = "http://www.w3.org/2000/svg";
  var lineEls = {};
  var labelEls = {};
  FanDirector.PARTS.forEach(function (name) {
    var g = document.createElementNS(NS, "g");
    g.setAttribute("opacity", "0");
    var line = document.createElementNS(NS, "polyline");
    line.setAttribute("fill", "none");
    line.setAttribute("stroke", "#17181a");
    line.setAttribute("stroke-opacity", "0.3");
    line.setAttribute("stroke-width", "1");
    var dot = document.createElementNS(NS, "circle");
    dot.setAttribute("r", "2.6");
    dot.setAttribute("fill", "#17181a");
    dot.setAttribute("fill-opacity", "0.55");
    g.appendChild(line);
    g.appendChild(dot);
    svg.appendChild(g);
    lineEls[name] = { g: g, line: line, dot: dot };

    var el = document.createElement("div");
    el.className = "label";
    labelLayer.appendChild(el);
    labelEls[name] = el;
  });

  function renderLabels(frame, anchors) {
    var name;
    for (var i = 0; i < FanDirector.PARTS.length; i++) {
      name = FanDirector.PARTS[i];
      labelEls[name].style.opacity = "0";
      lineEls[name].g.setAttribute("opacity", "0");
    }
    var items = FanDirector.layoutLabels(anchors, frame);
    for (var j = 0; j < items.length; j++) {
      var it = items[j];
      var el = labelEls[it.part];
      el.textContent = it.text;
      var shift = it.side === "left" ? " translateX(-100%)" : "";
      el.style.transform = "translate(" + it.x + "px," + it.y + "px) translateY(-50%)" + shift;
      el.style.opacity = String(it.alpha);

      var elbowX = it.ax + (it.side === "left" ? -22 : 22);
      var lg = lineEls[it.part];
      lg.line.setAttribute(
        "points",
        it.ax + "," + it.ay + " " + elbowX + "," + it.y + " " + it.lineEndX + "," + it.y,
      );
      lg.dot.setAttribute("cx", it.ax);
      lg.dot.setAttribute("cy", it.ay);
      lg.g.setAttribute("opacity", String(it.alpha));
    }
  }

  function allLabelsAlpha() {
    var labels = {};
    for (var i = 0; i < FanDirector.PARTS.length; i++) {
      labels[FanDirector.PARTS[i]] = state.explode > 0.82 ? 1 : 0;
    }
    return labels;
  }

  function manualFrame() {
    return { labels: allLabelsAlpha(), title: 0, end: 0 };
  }

  function renderAt(t) {
    var applied;
    if (state.mode === "demo") {
      applied = FanDirector.apply(ctl, t);
      titleCard.style.opacity = String(applied.frame.title);
      titleCard.style.transform = "translateY(" + (1 - applied.frame.title) * 16 + "px)";
      endCard.style.opacity = String(applied.frame.end);
      endCard.style.transform = "translateY(" + (1 - applied.frame.end) * 16 + "px)";
    } else {
      ctl.setView({
        yaw: state.yaw,
        pitch: state.pitch,
        dist: state.dist,
        target: state.target.slice(),
        fov: 30,
      });
      ctl.setExplode(state.explode);
      ctl.setSpin(state.spin);
      ctl.render();
      applied = { frame: manualFrame(), anchors: ctl.getAnchors() };
      titleCard.style.opacity = "0";
      endCard.style.opacity = "0";
    }
    state.lastFrame = applied.frame;
    state.lastAnchors = applied.anchors;
    renderLabels(applied.frame, applied.anchors);
  }

  // ---- interaction --------------------------------------------------------
  function setMode(mode) {
    state.mode = mode;
    if (mode === "demo") {
      state.demoTime = 0;
      demoBtn.textContent = "Stop demo";
      demoBtn.classList.remove("primary");
    } else {
      demoBtn.textContent = "Play auto demo";
      demoBtn.classList.add("primary");
    }
  }

  function adoptCurrentCamera() {
    // Copy the last applied camera into manual state so switching modes doesn't jump.
    var v = FanDirector.getView(state.lastFrame && state.lastFrame.t != null ? state.lastFrame.t : 0);
    state.yaw = v.yaw;
    state.pitch = v.pitch;
    state.dist = v.dist;
    state.target = v.target.slice();
  }

  demoBtn.addEventListener("click", function () {
    if (state.mode === "demo") {
      adoptCurrentCamera();
      setMode("manual");
    } else {
      slider.value = "0";
      sliderValue.textContent = "0%";
      state.explode = 0;
      setMode("demo");
    }
  });

  resetBtn.addEventListener("click", function () {
    setMode("manual");
    state.yaw = HERO_VIEW.yaw;
    state.pitch = HERO_VIEW.pitch;
    state.dist = HERO_VIEW.dist;
    state.target = TARGET.slice();
    state.explode = 0;
    slider.value = "0";
    sliderValue.textContent = "0%";
  });

  slider.addEventListener("input", function () {
    if (state.mode === "demo") {
      adoptCurrentCamera();
      setMode("manual");
    }
    state.explode = Number(slider.value) / 100;
    sliderValue.textContent = slider.value + "%";
  });

  canvas.addEventListener("pointerdown", function (e) {
    if (state.mode === "demo") {
      adoptCurrentCamera();
      setMode("manual");
    }
    state.dragging = true;
    state.dragX = e.clientX;
    state.dragY = e.clientY;
    canvas.classList.add("dragging");
    canvas.setPointerCapture(e.pointerId);
  });

  canvas.addEventListener("pointermove", function (e) {
    if (!state.dragging) return;
    var dx = e.clientX - state.dragX;
    var dy = e.clientY - state.dragY;
    state.dragX = e.clientX;
    state.dragY = e.clientY;
    state.yaw += dx * 0.32;
    state.pitch = Math.max(-28, Math.min(72, state.pitch + dy * 0.22));
  });

  function endDrag(e) {
    if (!state.dragging) return;
    state.dragging = false;
    canvas.classList.remove("dragging");
    if (e && e.pointerId !== undefined && canvas.hasPointerCapture(e.pointerId)) {
      canvas.releasePointerCapture(e.pointerId);
    }
  }
  canvas.addEventListener("pointerup", endDrag);
  canvas.addEventListener("pointercancel", endDrag);
  canvas.addEventListener("pointerleave", endDrag);

  canvas.addEventListener(
    "wheel",
    function (e) {
      e.preventDefault();
      if (state.mode === "demo") {
        adoptCurrentCamera();
        setMode("manual");
      }
      state.dist = Math.max(0.4, Math.min(2.8, state.dist * Math.exp(e.deltaY * 0.0011)));
    },
    { passive: false },
  );

  window.addEventListener("resize", function () {
    size = dims();
    ctl.resize(size.w, size.h);
    mq.setAttribute("viewBox", "0 0 " + size.w + " " + size.h);
    if (state.mode === "manual") renderAt(0);
  });

  // leaders SVG uses pixel coordinates of the window
  var mq = svg;
  mq.setAttribute("viewBox", "0 0 " + size.w + " " + size.h);

  // ---- loop ---------------------------------------------------------------
  var last = 0;
  function tick(now) {
    if (state.frozenT !== undefined) {
      // QA freeze: repaint the same deterministic frame (headless screenshots need a
      // produced frame after WebGL init; the time never advances).
      renderAt(state.frozenT);
      requestAnimationFrame(tick);
      return;
    }
    if (!last) last = now;
    var dt = Math.min(0.05, (now - last) / 1000);
    last = now;

    if (state.mode === "demo") {
      state.demoTime += dt;
      if (state.demoTime >= DURATION) {
        setMode("manual");
        state.yaw = END_VIEW.yaw;
        state.pitch = END_VIEW.pitch;
        state.dist = END_VIEW.dist;
        state.explode = 0;
        slider.value = "0";
        sliderValue.textContent = "0%";
        renderAt(0);
      } else {
        renderAt(state.demoTime);
      }
    } else {
      if (state.spinOn) state.spin += dt * 3.2;
      renderAt(0);
    }
    requestAnimationFrame(tick);
  }

  // ---- QA hooks (?t=12.5 freezes the film timeline; ?explode=1 freezes a pose) ----
  var qs = new URLSearchParams(window.location.search);
  var frozen = qs.has("t") || qs.has("explode");

  setMode("manual");
  if (qs.has("explode")) {
    var ex = Math.max(0, Math.min(100, parseFloat(qs.get("explode")) || 0));
    state.explode = ex / 100;
    slider.value = String(ex);
    sliderValue.textContent = ex + "%";
    state.frozenT = 0;
    renderAt(0);
  } else if (qs.has("t")) {
    var qt = Math.max(0, Math.min(DURATION, parseFloat(qs.get("t")) || 0));
    state.mode = "demo";
    state.demoTime = qt;
    state.frozenT = qt;
    demoBtn.textContent = "Stop demo";
    demoBtn.classList.remove("primary");
    renderAt(qt);
  } else {
    renderAt(0);
    requestAnimationFrame(tick);
  }
  if (frozen) {
    // keep the page deterministic for screenshots
    window.__fanFrozen = true;
    requestAnimationFrame(tick);
  }
})();
