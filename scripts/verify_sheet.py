#!/usr/bin/env python
"""Build a side-by-side photo-vs-render comparison sheet.

Both panels are cropped to their own object's bounding box and fitted to the
same tile, so the two panels can be compared in size and position without any
normalisation guesswork. The photo box comes from --bbox (read it off a grid
overlay, see references/03-verify.md); the render box is auto-detected from the
background colour or passed explicitly with --render-bbox.

Usage:
    python verify_sheet.py \
        --photo reference/front.jpg \
        --render out/front-render.png \
        --out out/sheet-front.png \
        --bbox "130,245,1195,1455"

    # explicit model box and bigger tiles
    python verify_sheet.py --photo ... --render ... --out ... \
        --bbox "130,245,1195,1455" --render-bbox "410,300,1510,1600" \
        --tile 640x760 --pad 0.06

Requires Pillow. numpy is optional: it only speeds up the background mask and
is not needed for correctness.
"""

from __future__ import annotations

import argparse
import os
import sys

try:
    from PIL import Image, ImageDraw

    _HAVE_PIL = True
except ImportError:  # handled in main() so --help still works
    _HAVE_PIL = False

try:
    import numpy as np

    _HAVE_NUMPY = True
except ImportError:
    _HAVE_NUMPY = False

DEFAULT_BG = "#f3f1ec"


def parse_box(text, name):
    """Parse 'x0,y0,x1,y1' into a normalised, validated 4-tuple."""
    parts = [p.strip() for p in str(text).split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("%s must be 'x0,y0,x1,y1', got %r" % (name, text))
    try:
        x0, y0, x1, y1 = (float(p) for p in parts)
    except ValueError:
        raise argparse.ArgumentTypeError("%s must be four numbers, got %r" % (name, text))
    if x1 <= x0 or y1 <= y0:
        raise argparse.ArgumentTypeError("%s must satisfy x1>x0 and y1>y0: %r" % (name, text))
    return (x0, y0, x1, y1)


def parse_tile(text):
    try:
        w, h = (int(float(p)) for p in str(text).lower().split("x"))
    except ValueError:
        raise argparse.ArgumentTypeError("--tile must look like 520x620, got %r" % text)
    if w < 32 or h < 32:
        raise argparse.ArgumentTypeError("--tile must be at least 32x32")
    return (w, h)


def parse_bg(text):
    value = str(text).strip()
    if value.lower() == "auto":
        return None
    if value.startswith("#"):
        value = value[1:]
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        raise argparse.ArgumentTypeError("--bg must be 'auto' or #rrggbb, got %r" % text)
    try:
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        raise argparse.ArgumentTypeError("--bg must be 'auto' or #rrggbb, got %r" % text)


def corner_background(img):
    """Median colour of the four corner patches: the render's own backdrop."""
    w, h = img.size
    patch = max(2, min(w, h) // 40)
    pixels = []
    for x0, y0 in ((0, 0), (w - patch, 0), (0, h - patch), (w - patch, h - patch)):
        pixels.extend(img.crop((x0, y0, x0 + patch, y0 + patch)).getdata())
    pixels.sort(key=lambda p: p[0] + p[1] + p[2])
    return pixels[len(pixels) // 2]


def content_bbox(img, bg, threshold):
    """Bounding box of pixels that differ from the background colour."""
    if _HAVE_NUMPY:
        arr = np.asarray(img, dtype=np.int16)
        diff = np.abs(arr - np.asarray(bg, dtype=np.int16)).max(axis=2)
        mask = diff > threshold
        if not mask.any():
            return None
        rows = np.where(mask.any(axis=1))[0]
        cols = np.where(mask.any(axis=0))[0]
        return (int(cols[0]), int(rows[0]), int(cols[-1]) + 1, int(rows[-1]) + 1)
    flat = Image.new("RGB", img.size, bg)
    gray = ImageChops_difference(img, flat).convert("L")
    mask = gray.point(lambda v: 255 if v > threshold else 0)
    return mask.getbbox()


def ImageChops_difference(a, b):
    from PIL import ImageChops

    return ImageChops.difference(a, b)


def clamp_box(box, width, height):
    x0, y0, x1, y1 = box
    x0 = max(0, min(width - 1, int(round(x0))))
    y0 = max(0, min(height - 1, int(round(y0))))
    x1 = max(x0 + 1, min(width, int(round(x1))))
    y1 = max(y0 + 1, min(height, int(round(y1))))
    return (x0, y0, x1, y1)


def padded(box, pad, width, height):
    x0, y0, x1, y1 = box
    grow = pad * max(x1 - x0, y1 - y0)
    return clamp_box((x0 - grow, y0 - grow, x1 + grow, y1 + grow), width, height)


def contain(img, tile_w, tile_h):
    """Scale to fit inside the tile without cropping or stretching."""
    scale = min(tile_w / img.width, tile_h / img.height)
    size = (max(1, int(round(img.width * scale))), max(1, int(round(img.height * scale))))
    return img.resize(size, Image.LANCZOS)


def build_sheet(photo, photo_box, render, render_box, tile, pad, gap, label_h, args):
    tw, th = tile
    sheet_w = tw * 2 + gap * 3
    sheet_h = label_h + th + gap * 2
    sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)

    panels = [
        (photo.crop(photo_box), args.label_photo, tw_column := gap, args.photo),
        (render.crop(render_box), args.label_render, tw + gap * 2, args.render),
    ]
    for src, label, column_x, path in panels:
        # A light rule keeps the two panels visually separate even on a white sheet.
        draw.rectangle([column_x - 1, label_h, column_x + tw, label_h + th], outline=(214, 214, 214))
        img = contain(src, tw, th)
        ox = column_x + (tw - img.width) // 2
        oy = label_h + (th - img.height) // 2
        sheet.paste(img, (ox, oy))
        label_text = "%s  %s" % (label, os.path.basename(path))
        if len(label_text) > 72:
            label_text = label_text[:69] + "..."
        draw.text((column_x, 8), label_text, fill=(30, 30, 30))
        draw.text(
            (column_x, 22),
            "crop %d,%d - %d,%d" % (int(src_box[0]) if False else 0, 0, src.width, src.height),
            fill=(255, 255, 255),  # replaced below; keeps the drawing sequence simple
        ) if False else None
    return sheet


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Side-by-side photo vs model render sheet, both cropped to their own bounding box.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("--photo", required=True, help="reference photo (any format Pillow reads)")
    ap.add_argument("--render", required=True, help="model render PNG for the same pose")
    ap.add_argument("--out", required=True, help="output sheet PNG path")
    ap.add_argument("--bbox", required=True, type=lambda v: parse_box(v, "--bbox"), help="photo crop box 'x0,y0,x1,y1' in photo pixels")
    ap.add_argument(
        "--render-bbox",
        default="auto",
        help="render crop box 'x0,y0,x1,y1', or 'auto' to detect the object against --bg",
    )
    ap.add_argument("--bg", type=parse_bg, default=None, help="render background colour 'auto' or #rrggbb")
    ap.add_argument("--threshold", type=int, default=18, help="per-channel difference that counts as object, 1-255")
    ap.add_argument("--pad", type=float, default=0.04, help="padding around the detected render box, fraction of its size")
    ap.add_argument("--tile", type=parse_tile, default=(520, 620), help="size of each panel, WxH")
    ap.add_argument("--gap", type=int, default=24, help="pixels between and around panels")
    ap.add_argument("--label-height", type=int, default=34, help="pixels reserved above each panel for its label")
    ap.add_argument("--label-photo", default="PHOTO", help="left panel label")
    ap.add_argument("--label-render", default="MODEL", help="right panel label")
    args = ap.parse_args(argv)

    if not _HAVE_PIL:
        print("verify_sheet.py: Pillow is required (pip install Pillow)", file=sys.stderr)
        return 2
    if not (1 <= args.threshold <= 255):
        print("verify_sheet.py: --threshold out of range 1-255", file=sys.stderr)
        return 2
    if args.pad < 0 or args.pad > 1:
        print("verify_sheet.py: --pad out of range 0-1", file=sys.stderr)
        return 2

    for path, what in ((args.photo, "photo"), (args.render, "render")):
        if not os.path.isfile(path):
            print("verify_sheet.py: %s not found: %s" % (what, path), file=sys.stderr)
            return 1

    try:
        photo = Image.open(args.photo).convert("RGB")
        render = Image.open(args.render).convert("RGB")
    except Exception as err:  # Pillow raises many subtypes here
        print("verify_sheet.py: cannot read input: %s" % err, file=sys.stderr)
        return 1

    photo_box = clamp_box(args.bbox, photo.width, photo.height)
    if photo_box != tuple(int(round(v)) for v in args.bbox):
        print(
            "verify_sheet.py: warning: --bbox %r clamped to %r (photo is %dx%d)"
            % (args.bbox, photo_box, photo.width, photo.height),
            file=sys.stderr,
        )

    render_box = None
    if str(args.render_bbox).strip().lower() != "auto":
        render_box = clamp_box(parse_box(args.render_bbox, "--render-bbox"), render.width, render.height)
        render_box_source = "explicit"
    else:
        bg = args.bg if args.bg is not None else corner_background(render)
        box = content_bbox(render, bg, args.threshold)
        if box is None:
            print(
                "verify_sheet.py: warning: no pixel differs from background %r by >%d; "
                "using the whole render. Pass --render-bbox or lower --threshold."
                % (bg, args.threshold),
                file=sys.stderr,
            )
            box = (0, 0, render.width, render.height)
        render_box = padded(box, args.pad, render.width, render.height)
        render_box_source = "auto (bg %02x%02x%02x)" % bg

    tw, th = args.tile
    sheet_w = tw * 2 + args.gap * 3
    sheet_h = args.label_height + th + args.gap * 2
    sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)

    panels = [
        (photo.crop(photo_box), args.label_photo, args.gap, args.photo, "photo box"),
        (render.crop(render_box), args.label_render, tw + args.gap * 2, args.render, "render box " + render_box_source),
    ]
    for src, label, column_x, path, note in panels:
        draw.rectangle([column_x - 1, args.label_height, column_x + tw, args.label_height + th], outline=(214, 214, 214))
        fitted = contain(src, tw, th)
        ox = column_x + (tw - fitted.width) // 2
        oy = args.label_height + (th - fitted.height) // 2
        sheet.paste(fitted, (ox, oy))
        label_text = "%s  %s" % (label, os.path.basename(path))
        if len(label_text) > 72:
            label_text = label_text[:69] + "..."
        draw.text((column_x, 7), label_text, fill=(30, 30, 30))
        draw.text((column_x, 20), "crop %dx%d  %s" % (src.width, src.height, note), fill=(120, 120, 120))

    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    sheet.save(args.out, format="PNG")
    print(
        "saved %s  %dx%d  | photo %s  | render %s"
        % (args.out, sheet.width, sheet.height, photo_box, render_box)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
