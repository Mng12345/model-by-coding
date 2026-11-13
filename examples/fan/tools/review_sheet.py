"""Review sheet: reference photo vs matching model render, both cropped to the fan's
own bounding box and fitted to the same tile, so the two panels are directly comparable
in size and position. Photo boxes were hand-read from grid overlays (tools/grid6.py);
model boxes are projected analytically (head rim + base rim circles).

Runs as-is inside this repository: reads reference/ photos and
out/verify2/*-render.png, writes out/review-sheet.png."""
from PIL import Image, ImageDraw
import numpy as np, math, os

W, H = 1920, 1080
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "out", "verify2")
TW, TH = 520, 620
PAD = 0.04


def project(p, yaw, pitch, dist, target, fov):
    yr, pr = math.radians(yaw), math.radians(pitch)
    cam = (target[0] + dist * math.sin(yr) * math.cos(pr),
           target[1] + dist * math.sin(pr),
           target[2] + dist * math.cos(yr) * math.cos(pr))
    fwd = [target[i] - cam[i] for i in range(3)]
    n = math.sqrt(sum(v * v for v in fwd)); fwd = [v / n for v in fwd]
    right = (fwd[1] * 0 - fwd[2] * 1, fwd[2] * 0 - fwd[0] * 0, fwd[0] * 1 - fwd[1] * 0)
    n = math.sqrt(sum(v * v for v in right)); right = [v / n for v in right]
    up = (right[1] * fwd[2] - right[2] * fwd[1], right[2] * fwd[0] - right[0] * fwd[2], right[0] * fwd[1] - right[1] * fwd[0])
    d = [p[i] - cam[i] for i in range(3)]
    z = sum(d[i] * fwd[i] for i in range(3))
    f = (H / 2) / math.tan(math.radians(fov) / 2)
    return (W / 2 + f * sum(d[i] * right[i] for i in range(3)) / z,
            H / 2 - f * sum(d[i] * up[i] for i in range(3)) / z, f / z)


def model_bbox(cam):
    yaw, pitch, dist, ty, fov, with_head = cam
    pts = []
    for i in range(96):
        a = 2 * math.pi * i / 96
        if with_head:
            for zz in (0.045, -0.050):
                pts.append((0.095 * math.cos(a), 0.194 + 0.095 * math.sin(a), zz))
            pts.append((0.0330 * math.cos(a), 0.194 + 0.0330 * math.sin(a), 0.052))
        for yy in (0.000, 0.010):
            pts.append((0.0572 * math.cos(a), yy, 0.0572 * math.sin(a)))
        pts.append((0.020 * math.cos(a), 0.300, 0.020 * math.sin(a)))
    proj = [project(p, yaw, pitch, dist, (0, ty, 0), fov) for p in pts]
    xs = [q[0] for q in proj]; ys = [q[1] for q in proj]
    return min(xs), min(ys), max(xs), max(ys)


def fit(img, tw, th):
    s = min(tw / img.width, th / img.height)
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)


JOBS = [
    ("front",     r"fan.jpg",                (130, 245, 1195, 1455), (-10, 12, 0.85, 0.185, 30, True)),
    ("side-left", r"angles\a_side-left.jpg",  (640, 430, 1300, 1460), (-62, 10, 0.85, 0.175, 30, True)),
    ("back",      r"angles\b_back.jpg",       (600, 375, 1405, 1605), (176, 8, 0.85, 0.185, 30, True)),
    ("back-3q",   r"angles\c_back-3q.jpg",    (470, 380, 1430, 1710), (138, 10, 0.85, 0.185, 30, True)),
    ("top",       r"angles\e_top.jpg",        (1010, 760, 1560, 1420), (15, 50, 0.95, 0.130, 30, True)),
    ("bottom",    r"angles\d_bottom.jpg",     (620, 780, 1400, 1560), (0, -62, 0.40, 0.020, 34, False)),
]

sheet = Image.new("RGB", (TW * 2 + 44, (TH + 46) * len(JOBS) + 10), (255, 255, 255))
d = ImageDraw.Draw(sheet)
for i, (name, prel, pbox, cam) in enumerate(JOBS):
    y = i * (TH + 46) + 10
    p_crop = Image.open(os.path.join(ROOT, "reference", prel)).convert("RGB").crop(pbox)
    m_render = Image.open(os.path.join(OUT, name + "-render.png")).convert("RGB")
    bx0, by0, bx1, by1 = model_bbox(cam)
    pw, ph = bx1 - bx0, by1 - by0
    m_crop = m_render.crop((int(bx0 - pw * PAD), int(by0 - ph * PAD), int(bx1 + pw * PAD), int(by1 + ph * PAD)))
    p_im = fit(p_crop, TW, TH); m_im = fit(m_crop, TW, TH)
    sheet.paste(p_im, (10 + (TW - p_im.width) // 2, y + 30 + (TH - p_im.height) // 2))
    sheet.paste(m_im, (TW + 34 + (TW - m_im.width) // 2, y + 30 + (TH - m_im.height) // 2))
    d.text((10, y + 4), "%s   PHOTO  %s" % (name, os.path.basename(prel)), fill=(25, 25, 25))
    d.text((TW + 34, y + 4), "MODEL  yaw %d pitch %d fov %d" % (cam[0], cam[1], cam[4]), fill=(25, 25, 25))
    d.line([TW + 12, y + 24, TW + 12, y + TH + 26], fill=(210, 210, 210), width=1)
sheet.save(os.path.join(ROOT, "out", "review-sheet.png"))
print("saved", sheet.size)


