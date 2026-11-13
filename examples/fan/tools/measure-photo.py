# ---------------------------------------------------------------------------
# Historical one-off measurement script, kept here as provenance for the numbers
# quoted in the fan case study. Its input paths point at the author's original
# working copy (photos, grid overlays, HyperFrames snapshot frames); those inputs
# are not part of this repository, so this file does not run as-is.
# The reusable, parameterized tooling lives in ../../../scripts/.
# ---------------------------------------------------------------------------
"""Measure grille rib duty cycle / radii from the reference photo.

Pure measurement: no model assumptions except a manually seeded head ellipse that is
then refined by a dark-pixel radial scan. Writes a short text report to stdout.
"""
import math
import numpy as np
from PIL import Image

IM = Image.open(r"D:\projects\learn-with-ai\tmp\fan-3d-demo\reference\fan.jpg").convert("L")
A = np.asarray(IM, dtype=np.float32)
H, W = A.shape
print("photo", W, "x", H)

# Seed: head roughly spans x 90..1060, y 290..1290 in the 1279x1706 photo.
cx0, cy0 = (90 + 1060) / 2, (290 + 1290) / 2
R0 = ((1060 - 90) + (1290 - 290)) / 4
print("seed", cx0, cy0, R0)

# Refine the outer silhouette: for angles with clear background, walk outward from 0.9R
# until the local gradient flips (fan brighter than background at the rim).
angles = np.linspace(0, 2 * math.pi, 720, endpoint=False)
radii = []
for a in angles:
    vals = []
    for rr in np.arange(0.86 * R0, 1.16 * R0, 1.0):
        x = int(cx0 + rr * math.cos(a))
        y = int(cy0 + rr * math.sin(a))
        if 0 <= x < W and 0 <= y < H:
            vals.append((rr, A[y, x]))
    if len(vals) < 10:
        continue
    arr = np.array(vals)
    # fan is white-ish (>=200), background is darker; find the last radius still bright
    bright = arr[:, 1] > 205
    idx = np.where(bright)[0]
    if len(idx) == 0:
        continue
    radii.append(arr[idx[-1], 0])
radii = np.array(radii)
# robust centre/size: median radius, then shift centre by the mean unit vector residual
R = float(np.median(radii))
print("outer radius px", round(R, 1), "ratio sd", round(float(radii.std()), 1))

cx, cy = cx0, cy0
for _ in range(3):
    dx = dy = n = 0.0
    for a, rr in zip(angles, radii):
        dx += (rr - R) * math.cos(a)
        dy += (rr - R) * math.sin(a)
        n += 1
    cx += dx / n * 0.7
    cy += dy / n * 0.7
print("centre", round(cx, 1), round(cy, 1), "R", round(R, 1))


def ring_profile(frac, n=1440):
    """Mean luminance along a circle of radius frac*R, resampled to n samples."""
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x = cx + frac * R * math.cos(a)
        y = cy + frac * R * math.sin(a)
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < W - 1 and 0 <= yi < H - 1:
            out.append(float(A[yi, xi]))
        else:
            out.append(255.0)
    return np.array(out)


def report(frac, n=1440):
    p = ring_profile(frac, n)
    lo, hi = p.min(), p.max()
    thr = (lo + hi) / 2
    dark = p < thr
    # count dark runs
    trans = np.where(np.diff(dark.astype(int)) == 1)[0]
    runs = []
    i = 0
    while i < n:
        if dark[i]:
            j = i
            while j < n and dark[j]:
                j += 1
            runs.append(j - i)
            i = j
        else:
            i += 1
    if len(runs) < 6:
        print(f"r={frac:.2f}R  no clear slots (min {lo:.0f} max {hi:.0f})")
        return
    # merge runs split by wrap-around
    period = n / len(runs)
    duty = float(np.mean(runs)) / period
    print(
        f"r={frac:.2f}R  slots={len(runs)}  period={period:.1f}px  dark_run={np.mean(runs):.1f}px"
        f"  duty(dark)={duty:.2f}  lum {lo:.0f}..{hi:.0f}"
    )


for f in (0.30, 0.38, 0.45, 0.52, 0.60, 0.68, 0.75, 0.82, 0.86, 0.90, 0.93, 0.96):
    report(f)

# radial luminance: where does the solid rim band start (no more slots)?
print("\nradial luminance 0.80R..1.00R (mean over angle, 5 deg bins):")
for f in np.arange(0.80, 1.001, 0.01):
    p = ring_profile(float(f), 360)
    print(f"  {f:.2f}R  mean {p.mean():.1f}  min {p.min():.1f}  p10 {np.percentile(p,10):.0f}  p90 {np.percentile(p,90):.0f}")

# cap radius: walk out from centre until the first dark slot pixel along many angles
edge = []
for i in range(360):
    a = 2 * math.pi * i / 360
    prev = None
    for rr in np.arange(0.10 * R, 0.42 * R, 1.0):
        x = int(round(cx + rr * math.cos(a)))
        y = int(round(cy + rr * math.sin(a)))
        if 0 <= x < W and 0 <= y < H:
            v = A[y, x]
            if prev is not None and prev - v > 18:
                edge.append(rr)
                break
        prev = v
edge = np.array(edge)
if len(edge):
    print("\ncap outer radius px", round(float(np.median(edge)), 1), "=", round(float(np.median(edge)) / R, 3), "R")
