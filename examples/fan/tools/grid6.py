# ---------------------------------------------------------------------------
# Historical one-off measurement script, kept here as provenance for the numbers
# quoted in the fan case study. Its input paths point at the author's original
# working copy (photos, grid overlays, HyperFrames snapshot frames); those inputs
# are not part of this repository, so this file does not run as-is.
# The reusable, parameterized tooling lives in ../../../scripts/.
# ---------------------------------------------------------------------------
from PIL import Image, ImageDraw
import os
R = r"D:\projects\learn-with-ai\tmp\fan-3d-demo\reference"
jobs = [("front", R + r"\fan.jpg"), ("side-left", R + r"\angles\a_side-left.jpg"), ("back", R + r"\angles\b_back.jpg"),
        ("back-3q", R + r"\angles\c_back-3q.jpg"), ("bottom", R + r"\angles\d_bottom.jpg"), ("top", R + r"\angles\e_top.jpg")]
CW = 560
cells = []
for name, path in jobs:
    im = Image.open(path).convert("RGB")
    sc = CW / im.width
    ch = int(im.height * sc)
    im = im.resize((CW, ch), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    step = int(100 * sc)
    ox = int(100 * sc)
    x = ox
    while x < CW:
        d.line([x, 0, x, ch], fill=(0, 160, 220), width=1)
        x += step
    y = step
    lab = 100
    while y < ch:
        d.line([0, y, CW, y], fill=(0, 160, 220), width=1)
        y += step
    # axis labels every 200 original px
    for gx in range(100, im.width and 2000, 200):
        px = int(gx * sc)
        if px < CW:
            d.text((px + 2, 2), str(gx), fill=(0, 90, 140))
    for gy in range(200, 2400, 200):
        py = int(gy * sc)
        if py < ch:
            d.text((2, py + 1), str(gy), fill=(0, 90, 140))
    d.text((4, ch - 14), "%s  %dx%d  scale %.3f" % (name, Image.open(path).width, Image.open(path).height, sc), fill=(160, 0, 0))
    cells.append((name, im, sc))
W = CW * 3 + 16
H = max(c[1].height for c in cells) * 2 + 24
out = Image.new("RGB", (W, H), (255, 255, 255))
for i, (name, im, sc) in enumerate(cells):
    x = (i % 3) * (CW + 8)
    y = (i // 3) * (max(c[1].height for c in cells) + 12) + 6
    out.paste(im, (x, y))
out.save(r"D:\projects\learn-with-ai\tmp\fan-3d-demo\out\verify2\_grid6.png")
print("saved", out.size, "cells", [(n, i.size) for n, i, s in cells])
