"""Build the 43.500 s stereo mix for the fan teardown demo (v2, 13 parts).

Timeline contract: SPEC-v2.md §4 (the single source of truth).
Layers
  room tone   0.00 -> 43.50  (very quiet air, fades with everything)
  whirr       0.80 -> 42.50  (tiled 22.800 s seamless loop, 2 ms crossfade at
                              the splice; +3 dB for the grille close-up 9.0-12.5;
                              its <120 Hz band pulled down 26.0-34.0)
  music       2.00 -> 43.50  (offset 8.0 s of music.mp3, 0.30 s fade-in,
                              low end pulled out 26.0-34.0, fades to zero at 43.50)
  foley       21.15 + i*0.30   i=0..12  (13 parts separating)
              35.18 + i*0.25   i=0..12  (13 parts going back together, reversed
                                         releases re-aligned to their peak)
              38.45                   (final seat click)

Run:  python build_mix.py   -> work/mix_raw.wav + work/mix_build_v2.json
"""
import os
import sys
import json
import wave
import subprocess
import numpy as np
from scipy import signal

SR = 48000
DUR = 43.5
N = int(round(DUR * SR))
FF = r"D:\ffmpeg\bin\ffmpeg.exe"

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.dirname(HERE)

MUSIC = os.path.join(AUDIO, 'music.mp3')
MUSIC_OFFSET = 8.0          # seconds into the source track (same as v1)

RELEASE_T = [21.15 + i * 0.30 for i in range(13)]      # 21.15 .. 24.75
CLOSE_T = [35.18 + i * 0.25 for i in range(13)]        # 35.18 .. 38.18
SEAT_T = 38.45

# deterministic variation so the 13 repeats do not feel mechanical
RELEASE_LVL = [-7.0, -8.2, -6.2, -7.6, -6.8, -7.9, -6.0, -7.3,
               -6.5, -8.0, -6.6, -7.1, -6.9]
RELEASE_PAN = [-0.16, 0.08, -0.05, 0.14, -0.11, 0.03, -0.18, 0.17,
               0.00, 0.10, -0.13, 0.12, -0.07]
CLOSE_PAN = [-0.14, 0.12, -0.08, 0.16, -0.10, 0.06, -0.18, 0.15,
             -0.03, 0.11, -0.12, 0.09, -0.05]


# ------------------------------------------------------------------ helpers
def decode(path, ch=2):
    cmd = [FF, '-hide_banner', '-v', 'error', '-i', path, '-ac', str(ch),
           '-ar', str(SR), '-f', 'f32le', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    return x.reshape(-1, ch)


def load_wav(path):
    cmd = [FF, '-hide_banner', '-v', 'error', '-i', path, '-ac', '2',
           '-ar', str(SR), '-f', 'f32le', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    return x.reshape(-1, 2)


def db(x):
    return 20 * np.log10(max(float(x), 1e-12))


def rms(x):
    return float(np.sqrt(np.mean(np.square(x))))


def automation(points, n=N, smooth=True):
    """Piecewise envelope from (time, gain) points; cosine-eased segments."""
    t = np.arange(n) / SR
    pts = sorted(points)
    env = np.full(n, pts[-1][1], dtype=np.float64)
    for i in range(len(pts) - 1):
        t0, g0 = pts[i]
        t1, g1 = pts[i + 1]
        m = (t >= t0) & (t < t1)
        if not np.any(m):
            continue
        u = (t[m] - t0) / max(t1 - t0, 1e-9)
        if smooth:
            u = 0.5 - 0.5 * np.cos(np.pi * u)
        env[m] = g0 + (g1 - g0) * u
    env[t < pts[0][0]] = pts[0][1]
    return env


def fft_split(x, fc=120.0):
    """Zero-phase low/high split for the 'pull the low end out' section."""
    n = x.shape[0]
    f = np.fft.rfftfreq(n, 1 / SR)
    lo_mask = 1.0 / (1.0 + (f / fc) ** 4)
    spec = np.fft.rfft(x, axis=0)
    lo = np.fft.irfft(spec * lo_mask[:, None], n, axis=0)
    return lo, x - lo


def compress(x, thr_db=-26.0, ratio=2.8, attack=0.010, release=0.18):
    """Stereo-linked feed-forward compressor: keeps the bed even under the foley."""
    mono = np.max(np.abs(x), axis=1)
    a_a = np.exp(-1.0 / (attack * SR))
    a_r = np.exp(-1.0 / (release * SR))
    env = np.empty_like(mono)
    acc = 0.0
    for i in range(len(mono)):
        acc = (1 - a_a) * mono[i] + a_a * acc if mono[i] > acc else (1 - a_r) * mono[i] + a_r * acc
        env[i] = acc
    thr = 10 ** (thr_db / 20.0)
    with np.errstate(divide='ignore'):
        g = np.where(env > thr, (thr / np.maximum(env, 1e-12)) ** (1 - 1.0 / ratio), 1.0)
    return x * g[:, None]


def norm_peak(x, db_target):
    p = np.max(np.abs(x)) + 1e-12
    return x * (10 ** (db_target / 20.0) / p)


def carvings(x, freq, gain_db, q=1.0):
    """Peaking cut, used to clear a window in the bed for the plastic clicks."""
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * freq / SR
    alpha = np.sin(w0) / (2 * q)
    b = [1 + alpha * A, -2 * np.cos(w0), 1 - alpha * A]
    a = [1 + alpha / A, -2 * np.cos(w0), 1 - alpha / A]
    return signal.lfilter(b, a, x, axis=0)


def place(buf, sig, t, gain=1.0, pan=0.0):
    """Add sig into buf at time t (seconds), with a constant-power pan."""
    idx = int(round(t * SR))
    if idx >= buf.shape[0]:
        return
    m = min(len(sig), buf.shape[0] - idx)
    gl = np.cos((pan + 1) * np.pi / 4)
    gr = np.sin((pan + 1) * np.pi / 4)
    buf[idx:idx + m, 0] += sig[:m] * gain * gl * 1.4142
    buf[idx:idx + m, 1] += sig[:m] * gain * gr * 1.4142


def place_at_peak(buf, sig, t_cue, gain=1.0, pan=0.0):
    """Place sig so its loudest sample lands exactly on t_cue.

    Needed for the reversed "closing" sounds: their impact sits at the end of
    the file, so a naive placement would push every closure far too late.
    """
    k = int(np.argmax(np.abs(sig)))
    place(buf, sig, t_cue - k / SR, gain, pan)
    return k / SR


def tile_loop(x, n, xf=0.002):
    """Concatenate a seamless loop into n frames with an equal-gain crossfade.

    `x` already loops without a seam (synth_beds.py crossfaded its own tail into
    its head); the short crossfade here is belt-and-braces for the splice and
    leaves the waveform continuous.  The loop content is shifted by xf per
    repeat, which is irrelevant for an ambient bed.
    """
    L = len(x)
    xfn = int(round(xf * SR))
    step = L - xfn
    reps = int(np.ceil(n / step)) + 1
    out = np.zeros((reps * step + xfn, 2))
    head = np.linspace(0.0, 1.0, xfn)[:, None]
    tail = head[::-1]
    for k in range(reps):
        s = k * step
        c = x.copy()
        c[:xfn] *= head
        c[L - xfn:] *= tail
        out[s:s + L] += c
    return out[:n]


def loop_seams(n, xf=0.002):
    """Sample indices of the splice(s) produced by tile_loop (for reporting)."""
    L = 1094400
    step = L - int(round(xf * SR))
    return [k * step for k in range(1, int(np.ceil(n / step)) + 1) if k * step < n]


# ------------------------------------------------------------------- build
def main():
    report = {
        'version': 2,
        'spec': 'SPEC-v2.md §4',
        'sr': SR,
        'duration_s': DUR,
        'frames': N,
        'music_offset_s': MUSIC_OFFSET,
        'release_times': [round(t, 3) for t in RELEASE_T],
        'close_times': [round(t, 3) for t in CLOSE_T],
        'seat_time': SEAT_T,
    }

    # ---------------- music ----------------
    mus = decode(MUSIC)
    start = int(MUSIC_OFFSET * SR)
    need = N
    if start + need > len(mus):
        reps = int(np.ceil((start + need) / len(mus)))
        mus = np.tile(mus, (reps, 1))
    bed = mus[start:start + need].copy()

    # the source peaks hot and is very sub-heavy; tame both so the plastic
    # clicks can sit on top of it
    bed = compress(bed, thr_db=-28.0, ratio=3.5, attack=0.015, release=0.22)
    # clear a small window around 3 kHz so the plastic clicks have room to read
    bed = carvings(bed, 3200.0, -2.6, q=0.9)
    lo, hi = fft_split(bed, 120.0)
    bed = hi + lo * 0.72

    # ---------------- music automation ----------------
    # SPEC: fade in 2.00 -> 2.30; global fade 42.30 -> 43.50; 'space' 26.0-34.0
    bed_env = automation([
        (0.0, 0.0), (2.0, 0.0), (2.3, 1.0),
        (26.0, 1.0), (26.8, 0.94), (33.2, 0.94), (34.0, 1.0),
        (42.3, 1.0), (43.5, 0.0),
    ])
    # <120 Hz gain pulled down to 0.55 (-5.2 dB) for the "space" section
    low_env = automation([
        (0.0, 1.0), (26.0, 1.0), (26.8, 0.55), (33.2, 0.55), (34.0, 1.0), (43.5, 1.0),
    ])
    bed = hi + lo * low_env[:, None]
    bed *= bed_env[:, None]

    # ---------------- whirr ----------------
    whirr_loop = load_wav(os.path.join(HERE, 'beds', 'foley-fan-whirr.wav'))
    whirr = tile_loop(whirr_loop, N, xf=0.002)
    w_lo, w_hi = fft_split(whirr, 120.0)
    whirr = w_hi + w_lo * low_env[:, None]
    w_env = automation([
        (0.0, 0.0), (0.80, 0.0), (1.60, 1.0), (8.55, 1.0),
        (9.0, 1.4125), (12.5, 1.4125), (13.4, 1.0),
        (42.3, 1.0), (43.5, 0.0),
    ])
    whirr *= w_env[:, None]
    seams = loop_seams(N, xf=0.002)
    report['whirr'] = {
        'loop_source_s': round(len(whirr_loop) / SR, 3),
        'splice_xfade_ms': 2.0,
        'splice_samples': [int(s) for s in seams],
        'splice_times_s': [round(s / SR, 4) for s in seams],
        'boost_db_9_12_5': 3.0,
        'lowcut_26_34': {'split_hz': 120, 'gain': 0.55, 'gain_db': round(20 * np.log10(0.55), 2)},
    }

    # ---------------- room tone ----------------
    room_loop = load_wav(os.path.join(HERE, 'beds', 'foley-room-tone.wav'))
    room = tile_loop(room_loop, N, xf=0.002)
    r_env = automation([(0.0, 0.0), (0.05, 1.0), (42.3, 1.0), (43.5, 0.0)])
    room *= r_env[:, None]

    # ---------------- foley ----------------
    buf = np.zeros((N, 2))
    hits = []

    # reference levels from the music bed (5..18 s) as in v1
    ref = rms(bed[int(5 * SR):int(18 * SR)].mean(axis=1))
    bed_gain = 10 ** ((-22.5 - db(ref)) / 20)
    bed *= bed_gain

    # whirr 30 dB under the bed
    w_ref = rms(whirr[int(3 * SR):int(8 * SR)].mean(axis=1))
    whirr *= 10 ** ((-52.5 - db(w_ref)) / 20)

    # room tone: quiet air
    r_ref = rms(room.mean(axis=1))
    room *= 10 ** ((-58.0 - db(r_ref)) / 20)

    report['layer_rms_db'] = {
        'music_bed_5_18': round(db(rms(bed[int(5 * SR):int(18 * SR)].mean(axis=1))), 2),
        'whirr_3_8': round(db(rms(whirr[int(3 * SR):int(8 * SR)].mean(axis=1))), 2),
        'room_1_2': round(db(rms(room[int(1 * SR):int(2 * SR)].mean(axis=1))), 2),
    }

    # 13 separating parts, peak placed exactly on the contract time
    for i, t0 in enumerate(RELEASE_T):
        s = load_wav(os.path.join(HERE, 'sfx', f'foley-part-release-{i+1:02d}.wav'))
        pan = RELEASE_PAN[i]
        tgt = RELEASE_LVL[i]
        g = 10 ** (tgt / 20)
        place_at_peak(buf, norm_peak(s.mean(axis=1), 0.0), t0, g, pan)
        hits.append({'type': 'release', 'index': i + 1, 'time_s': round(t0, 3),
                     'level_db': tgt, 'pan': pan})

    # 13 parts going back together: reversed releases, peak re-aligned
    for i, t0 in enumerate(CLOSE_T):
        s = load_wav(os.path.join(HERE, 'sfx', f'foley-part-close-{i+1:02d}.wav'))
        pan = CLOSE_PAN[i]
        tgt = -8.6 + 0.21 * i          # gentle crescendo as the fan comes back
        g = 10 ** (tgt / 20)
        lead = place_at_peak(buf, norm_peak(s.mean(axis=1), 0.0), t0, g, pan)
        hits.append({'type': 'close', 'index': i + 1, 'time_s': round(t0, 3),
                     'level_db': round(tgt, 2), 'pan': pan,
                     'reversed_lead_s': round(lead, 4)})

    s = load_wav(os.path.join(HERE, 'sfx', 'foley-final-seat.wav'))
    place_at_peak(buf, norm_peak(s.mean(axis=1), 0.0), SEAT_T, 10 ** (-6.8 / 20), 0.0)
    hits.append({'type': 'seat', 'index': 1, 'time_s': SEAT_T, 'level_db': -6.8, 'pan': 0.0})
    report['hits'] = hits

    # ---------------- sum ----------------
    # side-chain the music a few dB under each click so the mechanism reads
    # clearly without pushing the foley louder than the bed
    fx_env = np.max(np.abs(buf), axis=1)
    a_a = np.exp(-1.0 / (0.008 * SR))
    a_r = np.exp(-1.0 / (0.20 * SR))
    sm = np.empty_like(fx_env)
    acc = 0.0
    for i in range(len(fx_env)):
        acc = (1 - a_a) * fx_env[i] + a_a * acc if fx_env[i] > acc else (1 - a_r) * fx_env[i] + a_r * acc
        sm[i] = acc
    duck = 1.0 - 0.42 * np.clip(sm / (10 ** (-8.0 / 20)), 0, 1)

    mix = bed * duck[:, None] + room + whirr + buf

    # tiny DC block + safety clip guard
    mix -= mix.mean(axis=0, keepdims=True)
    peak = np.max(np.abs(mix))
    report['pre_peak_db'] = round(db(peak), 2)
    report['pre_rms_db'] = round(db(rms(mix.mean(axis=1))), 2)
    report['pre_crest_db'] = round(db(peak / rms(mix.mean(axis=1))), 2)

    out = os.path.join(HERE, 'mix_raw.wav')
    pcm = (np.clip(mix, -1, 1) * 32767.0).astype('<i2')
    with wave.open(out, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print('wrote', out, pcm.shape[0] / SR, 's  frames', pcm.shape[0])
    print(json.dumps({k: v for k, v in report.items() if k != 'hits'}, indent=1))
    with open(os.path.join(HERE, 'mix_build_v2.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=1)


if __name__ == '__main__':
    main()
