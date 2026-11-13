# ---------------------------------------------------------------------------
# Historical one-off measurement script, kept here as provenance for the numbers
# quoted in the fan case study. Its input paths point at the author's original
# working copy (photos, grid overlays, HyperFrames snapshot frames); those inputs
# are not part of this repository, so this file does not run as-is.
# The reusable, parameterized tooling lives in ../../../scripts/.
# ---------------------------------------------------------------------------
import numpy as np
from PIL import Image

def stats(path, cx, cy, r, name):
    im = Image.open(path).convert("L")
    a = np.asarray(im).astype(np.float32)
    h, w = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    m = ((xx - cx) ** 2 + (yy - cy) ** 2) <= r * r
    v = a[m]
    print("%-14s px=%6d mean=%6.1f std=%5.1f  clipped>=250:%5.1f%%  dark<=80:%5.1f%%"
          % (name, v.size, v.mean(), v.std(), 100.0 * (v >= 250).mean(), 100.0 * (v <= 80).mean()))
    return v

ref = stats(r"reference\fan.jpg", 549.4, 803.5, 470, "ref head")
rnd = stats(r"video\.hyperframes\artifacts\snapshots\efc1dd32-43c1-4abd-a0c5-0eadd223b5f9\frame-00-at-11s.png", 950, 490, 370, "render head")
print()
print("hist ref  :", np.histogram(ref, bins=8, range=(0, 256))[0])
print("hist render:", np.histogram(rnd, bins=8, range=(0, 256))[0])
