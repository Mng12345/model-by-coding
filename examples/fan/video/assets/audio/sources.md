# Audio sources, synthesis and final mix (v3)

Delivery directory: `video/assets/audio/`
Revised: 2026-11-13 (Asia/Shanghai). Film spec: **43.5 s** / 1920×1080 / 30 fps (`SPEC-v2.md` §4).

This revision (v3) replaces the music bed only; timeline, the 27 foley cues (13 + 13 + 1), the
whirr/room beds, cue constants and delivery targets are unchanged from v2. Previous delivery: v2
mix (SHA256 `6cc9faefccf2298f0babaa4df3eafc7ff1c2ce56c190755fa4a98e36ad88b543`); v1 (40 s) backup
at `work/v1-mix.wav`.

## 1. Music bed — "Real Life"

| item | value |
| --- | --- |
| Title | Real Life |
| Artist | GreenRocketAudio |
| Source site | Pixabay (music library) |
| Work page | https://pixabay.com/music/corporate-real-life-612733/ |
| License | Pixabay Content License (as stated on the work page) |
| Content ID evidence | the string `content id` appears **0 times** in the page text |
| File used | `03-real-life.mp3` — 140.904469 s, 44.1 kHz stereo, MP3 256 kbps, 4,508,943 bytes, SHA256 `bfc1ceaaf9eb6b6022c2114127362b95e68af554b87bd490b28997a680338b8c` |
| Used window | source 14.295 s → 57.795 s (43.5 s slice) |

The v2 bed was `fugu_vibes` — "Minimal Technology"
(`https://pixabay.com/music/ambient-minimal-technology-623485/`, 102.034281 s, 44.1 kHz stereo).
That page carried a **Content ID Registered** marking, so a published film using it risked a
YouTube Content ID claim; the bed was replaced with "Real Life" to reduce that risk, and the v2
track no longer ships.

Tempo measurement: **105.0 BPM**, bar (4 beats) = **2.2857 s**, bar-line grid 0.295 s + k × 2.2857 s
(fitted on the low-band amplitude envelope, ±10 ms). Music fades in over film 2.00–2.30 s (0.30 s)
= source **16.295 s**, bar line k = 7 (k = 6 → 14.009 s, k = 8 → 18.581 s): the bar line nearest to
the auto-picked quiet window (entry 17.09 s); it fades out over 42.30–43.50 s (1.20 s). RMS of the
1 s before the start point (source 13.295–14.295 s): **−12.71 dBFS stereo** (−13.62 dBFS mono) — not
a weak pickup, not silence.

## 2. Foley — 27 plastic-mechanism sounds

| item | value |
| --- | --- |
| Files | `foley-part-release-01..13.wav` (13 separate-part sounds), `foley-part-close-01..13.wav` (13 reassembly sounds), `foley-final-seat.wav` (final seat) |
| Source | **local synthesis** (not recordings, not downloads) |
| Generator | `work/synth_foley.py` (numpy + scipy), 2026-11-12 14:08, Python 3.11.1 |
| Format | 48 kHz / 16-bit / stereo; releases and closes 0.165–0.240 s, seat 0.300000 s |

Synthesis model (same for every hit): 1–2 ms broadband contact transient (decaying noise) → 3
plastic-body resonant modes (damped sines, 960–6880 Hz depending on timbre) → low thud
(118–286 Hz panel resonance) → small air puff → second micro-contact (clip / shell / seat timbres
only) → 130 ms small-room impulse response. Transient weight 0.90 vs 0.22 / 0.22 / 0.08, so the
contact transient is always the file's peak sample. File peaks fall into three groups: −6.0, −6.8
and −7.6 dBFS. The 13 release sounds rotate through 7 timbres (shell / pull / seat / clip / knob /
thud / snap); each close sound is the matching release reversed end-to-end (`close-NN` =
`release-(14-NN)`, mapping in `work/sfx/foley_manifest_v2.json`) with a 0.5 ms tail, so its peak
is the contact attack.

Cue grid, pre-master (`work/build_mix.py`): releases at 21.15 + 0.30 × i s (13 hits, levels
−8.2…−6.0 dBFS, pans within ±0.18); closes at 35.18 + 0.25 × i s (13 hits, levels
−8.6 + 0.21 × i dBFS); final seat at 38.45 s.

## 3. Fan whirr and room tone — synthesised beds

Both from `work/synth_beds.py` (numpy + scipy), generated 2026-11-12 10:44, 48 kHz / 16-bit /
stereo, not recordings.

| file | length | measured level |
| --- | --- | --- |
| `foley-fan-whirr.wav` | 22.800000 s (1,094,400 frames) | L/R RMS −25.87 / −26.13 dBFS, peaks −11.88 / −12.89 dBFS |
| `foley-room-tone.wav` | 5.000000 s (240,000 frames) | L/R RMS −58.14 / −58.03 dBFS, peaks −45.91 / −45.60 dBFS |

Whirr: 62 Hz blade-pass tone plus harmonics, band-limited pink airflow, light chuff amplitude
modulation, faint high whistle; seamless loop tiled across the film with a 2 ms splice crossfade
(only splice point 22.798 s). Room tone is the very low air bed under the whole film. Mix targets:
whirr −52.5 dBFS (3–8 s), room tone −58.0 dBFS.

## 4. Mix chain and mastering

Music chain (`work/build_mix.py`, executed for this revision by `remix_music.py`):
1. Slice source 14.295–57.795 s (43.5 s).
2. Compressor: threshold −28 dBFS, ratio 3.5, attack 15 ms, release 220 ms.
3. EQ: peaking −2.6 dB at 3.2 kHz, Q 0.9 (carves room for the plastic clicks).
4. Low band split at 120 Hz: ×0.72 static, superseded by automation ×0.55 during the 26.8–33.2 s
   "space" section (ramps 26.0–26.8 s and 33.2–34.0 s).
5. Level automation: bed RMS normalised to −22.5 dBFS over 5–18 s; ×0.94 dip across 26.8–33.2 s;
   equal-power (sin/cos) fade-in 2.00–2.30 s and fade-out 42.30–43.50 s with a 0.30 s terminal
   linear taper (anti-click); slice de-click 10 ms in / 30 ms out.
6. Sidechain ducking from the foley bus: 1 − 0.42 × clip(envelope / −8 dBFS, 0, 1), attack 8 ms,
   release 200 ms → up to 4.7 dB of music reduction under hits.

Non-music layers: whirr fade-in 0.80–1.60 s, +3.0 dB (×1.4125) over 8.55–9.00 s, back at
12.50–13.40 s; whirr and room low band ×0.55 during 26.0–34.0 s; both fade out 42.30–43.50 s.

Mastering (`work/master.py`): +3.80 dB into a stereo-linked look-ahead brickwall limiter (sample
ceiling −3.2 dBFS, 6 ms look-ahead, 120 ms release, max gain reduction 3.2 dB), then a +0.10 dB
fine trim to land exactly on −16.0 LUFS. The ceiling leaves about 1.2 dB of headroom for true-peak
overshoot of the sharp synthetic transients; measured TP is −2.0 dBTP.

Consistency with the existing film: all non-music processing is the v2 code and v2 source files, and
the pre-master fx stem is **bit-identical** to the v2 build (SHA256
`d5d8f92e8eef161f5914be4e20cfaffb62a6957ecd211326ecd8415a0ad16eae`, 2,088,000 frames, 0 differing
samples), so the 27 foley cues, whirr and room tone are unchanged. Only the music bed differs; the
master gain moves from +4.00 dB (v2) to +3.90 dB (v3) because the new track reaches the same −16.0
LUFS with slightly different program material.

## 5. Measured QC of `mix.wav`

| metric | measured |
| --- | --- |
| Duration | **43.500000 s** (2,088,000 frames @ 48 kHz) |
| Format | WAV / PCM 16-bit / 48,000 Hz / 2 ch (stereo), 8,352,044 bytes |
| Integrated loudness | **−16.0 LUFS** (`ffmpeg ebur128=peak=true`) |
| True peak | **−2.0 dBTP** (target ≤ −1.9, QC limit ≤ −1.5) |
| Loudness range | **1.5 LU** (limit ≤ 6) |
| Sample peak | −3.10 dBFS; 0 full-scale samples |
| Cue alignment | **27/27 within ±5 ms, max \|dev\| 0.854 ms** (1.5–6 kHz band peak, ±30 ms window) |
| Stereo | correlation 0.6203, L/R −0.07 dB, side/mid −6.3 dB |
| Tail | last 100 ms RMS −55.60 dBFS; last sample −0.000275 |
| Peak safety | max single-sample \|value\| −3.10 dBFS; no sample above −1.0 dBFS |
| SHA256 | `9fd816e8aba2510e68927a22dd9fb1b1da523f287e0d0d855176eb90cda02a20` |

Command (working directory `video/assets/audio`):

```
D:\Python\Python311\python.exe work\verify_mix.py mix.wav <report.json>
```

Result of that run: `ALL: PASS` (duration_frames_exact, format_48k_16bit_stereo, lufs_within_0.5,
true_peak_le_-1.5_dbtp, lra_le_6_lu, all_events_within_5ms, no_full_scale_samples). The per-cue
table lives in `work/mix.verify.json` when the tool is pointed there; that JSON is generated, not
committed. v2 reference: I −16.0 LUFS / TP −1.9 dBTP / LRA 2.7 LU, same max cue deviation 0.854 ms.

## 6. File inventory

```
video/assets/audio/
├── mix.wav                        final mix — release asset, excluded from git by `*.wav`
├── sources.md                     this file — tracked
└── work/                          build scripts and reports — tracked (*.py, *.json)
    ├── synth_foley.py             27 foley sounds
    ├── synth_beds.py              whirr + room tone
    ├── build_mix.py               timeline, cue constants, layer builder
    ├── master.py                  −16 LUFS / true-peak mastering
    ├── verify_mix.py              measurement + QC checks
    ├── build_report_v2.json       v2 measurement report (27 events + checks)
    ├── mix_build_v2.json          v2 build parameters and layer levels
    ├── build_report.json          v1 build parameters (levels, cue hits, spectral analysis)
    └── analyze_music.py / check_drums.py   analysis helpers
```

- **In git**: `sources.md`, and the `work/*.py` / `work/*.json` scripts and reports above.
- **Release assets**: `mix.wav` plus the binary source media (27 foley WAVs, whirr, room tone,
  music MP3) in the build workspace; `.gitignore` line 15 excludes all `*.wav`, so these are
  delivered as files, not repository blobs.
- **Work intermediates** (build workspace only): `mix_raw.wav` (pre-master mix), the generated
  verify JSON, the v1 backup `v1-mix.wav`, and the v3 tool `remix_music.py` at
  `D:\projects\learn-with-ai\tmp\fan-3d-demo\video\assets\audio\work\remix_music.py`.

Only `mix.wav` and `sources.md` were written in this revision; no other file was touched. Rebuild:
`remix_music.py --music <Real-Life>.mp3 --start 14.295 --out mix.wav`, then
`work/verify_mix.py mix.wav <report.json>`; the foley and bed WAVs are unchanged from v2, and cue
times/levels live at the top of `work/build_mix.py` (`RELEASE_T` / `CLOSE_T` / `SEAT_T` / `RELEASE_LVL`).
