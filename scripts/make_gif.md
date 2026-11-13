# make_gif — operation card

A page-and-terminal card for turning one clip of the rendered film into a
looping GIF. No script, no configuration: read the steps, do them in order, and
check the result at the end.

## Inputs

| input | example | note |
| --- | --- | --- |
| rendered film | `video/renders/video_<date>_<time>.mp4` | `--quality delivery` output |
| clip start | `29.6` s | pick a settled pose, see `references/04-gif.md` §0 |
| clip length | `3.8` s | 3–4 s loops well |
| output width | `480` px | 320 for smaller files, 640 for detail |
| FPS | `12` | 10 light, 12 balanced, 15 smooth |
| output | `out/teardown.gif` | create the directory first |

## Route A — gif-master (browser, no install, download costs a credit)

1. Open <https://gif-master.com/zh/tools/video-to-gif> (English:
   <https://gif-master.com/en/tools/video-to-gif>). Processing runs in the
   browser; the page states the video is not uploaded.
2. Drop the MP4 in, set `start` / `end` in `0:00.00` form, pick the crop ratio,
   then width, FPS, playback speed, play count.
   Ready-made values: width 480, FPS 12, play count infinite, crop 16:9 (or
   1:1 if the target is square).
3. Process, then download. Downloading requires a login and costs **1 credit**;
   the free allowance is **3 credits per day**. Editing and previewing are
   free. No file-size/duration limit is published — keep the clip short and the
   width at or below 480.

If the download prompt repeats, the login session expired; the edit survives, so
log in and download again. If credits are gone, use Route B.

## Route B — ffmpeg (local, free, rerunnable)

Verified command (480×270, 46 frames, 596 KB from a 3.8 s cut of a 1920×1080
render):

```powershell
ffmpeg -hide_banner -loglevel error -y `
  -ss 29.6 -t 3.8 -i "video/renders/video_<date>_<time>.mp4" `
  -vf "fps=12,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=sierra2_4a" `
  -loop 0 "out/teardown.gif"
```

Adjust `-ss` (start), `-t` (length), `fps=12`, `scale=480` and
`max_colors=128`. `-loop 0` loops forever; `scale=480:-1` keeps the aspect
ratio. Two passes (`palettegen` then `paletteuse`) are what keep the white
plastic from banding.

## Verify before posting

```powershell
Test-Path out/teardown.gif
python -c "from PIL import Image; im=Image.open('out/teardown.gif'); print(im.size, getattr(im,'n_frames',1), im.info.get('duration'), im.info.get('loop'))"
```

Expect a size matching the requested width, a frame count around
`FPS × seconds`, a duration near `1000/FPS` ms, and loop `0`. Then watch it
once: the first and last frames should both be settled poses, otherwise the
loop jumps.

## Failure modes

| symptom | fix |
| --- | --- |
| upload rejected | render an H.264 MP4 from HyperFrames and retry |
| login loop | log in in the same browser, then download |
| "credits exhausted" | wait for the daily reset or switch to ffmpeg |
| file too big | width 320, FPS 10, shorter clip |
| grey banding | keep two-pass palette, 128–256 colours, dither `sierra2_4a` |
| blurry | do not upscale; `flags=lanczos` |
| loop jumps | trim to settled poses on both ends |
