# 04 — Cutting the GIF

The teardown video is the deliverable; the GIF is the trailer. A 3–4 s loop of
the exploded stack is what gets attached to a post, embedded in a README, or
pasted into a chat, so it is worth cutting deliberately rather than exporting
the whole film.

Two routes: a browser tool (no install, but a login and a credit per download)
or ffmpeg (local, free, scriptable). Use the browser tool when a person is
driving and the cut is a one-off; use ffmpeg when the GIF has to be reproducible
or regenerated after a re-render.

## 0. Pick the clip first

Good GIF segments for a teardown:

- the exploded hold (the camera drifts slowly, every part is visible and the
  labels are steady) — the best default;
- the first two seconds of the explode, if the separation itself is the point;
- a grille macro, only if the GIF is about the grille.

Avoid: the orbit (too fast, too much movement for a short loop), the title card
(text-heavy, unreadable at 480 px), the reassemble tail (ends mid-motion and
looks like a broken loop). A loop should start and end on a settled pose.

In the example (43.5 s film), the exploded hold runs 29.5–34.0 s, so a
29.6–33.4 s cut is 3.8 s of the model standing apart with labels. Write the
timestamps down; both routes need them.

## 1. Browser route: gif-master

Page: <https://gif-master.com/zh/tools/video-to-gif> (English:
<https://gif-master.com/en/tools/video-to-gif>). Processing happens in the
browser in a Web Worker (`rgba-to-gif-worker.js`); the page states the video is
not uploaded. That claim is the page's own; if the material is confidential,
still assume a third-party page and check its current privacy statement.

Operation card:

1. **Open the page and add the MP4.** Drag the rendered file in. Use the H.264
   MP4 that HyperFrames produced; browser decoding of that format is the safest
   path.
2. **Trim and configure.** Time fields take `start` / `end` in `0:00.00` form.
   Then set, in this order: crop ratio (16:9 for a wide post, 1:1 for a square
   embed), output width, FPS, playback speed, play count.
   - output width: 240 / 320 / 480 / 640 / 720
   - FPS: 5 / 8 / 10 / 12 / 15 / 20
   - play count: once / twice / three times / infinite
3. **Process, then download.** Editing and previewing are free; downloading the
   GIF requires a login and costs **1 credit**, with **3 free credits per day**.
   That budget is the practical limit: three downloads a day, not three
   attempts — every configuration you download spends one.

There are no published file-size or duration limits on the page; treat that as
"unknown", keep the source clip short (a few seconds) and the output width at
480 or below, and you will stay far away from whatever the limit is.

Recommended settings for a teardown loop (judgement, tuned for a white object on
a light ground):

| setting | value | why |
| --- | --- | --- |
| clip | the exploded hold, 3–4 s | slow camera, all parts visible |
| width | 480 | readable in a post, ~0.3–0.5 MB for 3 s |
| FPS | 12 | smooth enough for a slow drift, half the frames of 24 |
| play count | infinite (or 3) | a loop is the point |
| crop | 16:9 around the stack, or 1:1 if the platform wants square | avoid letterboxing |

If the download fails, the usual causes are the login session expiring and the
daily credits being used up; the page keeps the edit, so log in and download
again rather than re-trimming.

## 2. ffmpeg route

Two-pass palette conversion is the difference between a GIF that looks like the
render and a GIF with banded grey plastic. Verified command (run on this
machine against a 1920×1080 render; produced a 480×270, 46-frame, 596 KB GIF
from a 3.8 s cut):

```powershell
ffmpeg -hide_banner -loglevel error -y `
  -ss 29.6 -t 3.8 -i "video/renders/video_<date>_<time>.mp4" `
  -vf "fps=12,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=sierra2_4a" `
  -loop 0 "out/teardown.gif"
```

Parameter notes:

- `-ss` before `-i` seeks fast; with a re-encode the cut is accurate enough for
  a loop, but verify the first frame is the pose you wanted.
- `-t` is the clip length in seconds.
- `fps=12` — match the platform; 10 is lighter, 15 smoother and bigger. Do not
  go above the source's 30 fps.
- `scale=480:-1:flags=lanczos` keeps the aspect ratio (the `-1`). Drop the
  width to 320 if the file must be small.
- `max_colors=128` is plenty for flat white plastic; raise it toward 256 if the
  background has a gradient you care about. Lower it for a smaller file.
- `dither=sierra2_4a` — a soft dither that suits flat plastic; stronger modes trade banding for noise.
- `-loop 0` means loop forever; `-loop 2` plays three times total in some
  players, so prefer 0 and let the platform decide.

Check the result mechanically rather than by eye:

```powershell
python -c "from PIL import Image; im=Image.open('out/teardown.gif'); print(im.size, getattr(im,'n_frames',1), im.info.get('duration'), im.info.get('loop'))"
```

For the verified run above this printed `(480, 270) 46 80 0` — 46 frames at
80 ms nominally (12 fps), looping. Expect the duration field to be rounded
(83 ms requested, 80 ms stored); that is normal for GIF's centisecond clock and
does not desync a loop.

## 3. Choosing between them

| | gif-master | ffmpeg |
| --- | --- | --- |
| install | none | ffmpeg on PATH |
| cost | login + 1 credit per download (3/day) | free |
| reproducibility | manual settings, browser-dependent | one command, rerunnable |
| large sources | in-browser processing, slow for long clips | fast |
| control | width/FPS/speed/loop/crop | every filter in ffmpeg |

The pipeline in this skill uses gif-master when a human is publishing the clip
and ffmpeg when the GIF has to be regenerated after a re-render. Keep the ffmpeg
command in the repo (README or a comment) so the GIF is never hand-made twice.

## 4. Failure modes

| symptom | cause | fix |
| --- | --- | --- |
| GIF download button asks for login forever | session expired / no account | log in, keep the edit, download again |
| "credits exhausted" | 3 free downloads used today | wait for the daily reset, or use ffmpeg |
| upload rejected | browser cannot decode the codec | export H.264 MP4 from HyperFrames and retry |
| GIF is huge (tens of MB) | width 720 + 20 fps + long clip | 480 wide, 12 fps, 3 s |
| grey plastic bands | palette too small / no dither | 128–256 colours and dithering |
| loop jumps | clip starts or ends mid-motion | trim to settled poses on both ends |
| GIF is blurry | downscaled from a 1920 frame with a bad filter | use `flags=lanczos` |
| colours shifted vs the video | GIF is 256 colours, the film is not | accept it, or keep the video as the primary artefact |
