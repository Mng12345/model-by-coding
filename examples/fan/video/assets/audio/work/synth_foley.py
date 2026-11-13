"""Synthesise the plastic-mechanism foley for the fan teardown (v2: 13 parts).

Every sound here is generated from scratch (damped resonators + noise bursts +
a small synthetic room), so nothing is licensed from a third party.  The model
is a real plastic snap: a very short broadband contact transient, two or three
ringing body modes, a low "thunk" from the panel it is attached to, and a
second micro-contact when the sprung plastic relaxes.

Outputs (16-bit 48 kHz stereo WAV), v2 = 13 separating parts:
  foley-part-release-01..13.wav   0.165-0.240 s  part separating
  foley-part-close-01..13.wav     reversed family, peak re-aligned when mixed
  foley-final-seat.wav            0.30 s         last part seating home
  foley_manifest_v2.json          per-voice parameters + measured features

The 13 releases rotate over 8 distinct plastic voices and vary pitch/brightness/
body/decay, so every hit is audibly different from its neighbours.
"""
import os
import sys
import json
import wave
import numpy as np
from scipy import signal

SR = 48000


# ----------------------------------------------------------------- helpers
def bp(x, lo, hi, order=4):
    sos = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], btype='band', output='sos')
    return signal.sosfilt(sos, x)


def lp(x, fc, order=4):
    sos = signal.butter(order, fc / (SR / 2), btype='low', output='sos')
    return signal.sosfilt(sos, x)


def hp(x, fc, order=4):
    sos = signal.butter(order, fc / (SR / 2), btype='high', output='sos')
    return signal.sosfilt(sos, x)


def room_ir(ms=130, seed=3, decay=0.055):
    """A small, slightly dead room: early reflections plus a short diffuse tail."""
    rng = np.random.default_rng(seed)
    n = int(ms / 1000 * SR)
    t = np.arange(n) / SR
    tail = rng.normal(0, 1, n) * np.exp(-t / decay)
    tail = lp(tail, 5200)
    ir = tail * 0.25
    for i, (ms_delay, g) in enumerate([(7, 0.5), (13, 0.35), (19, 0.28), (27, 0.2), (41, 0.12)]):
        idx = int(ms_delay / 1000 * SR)
        if idx < n:
            ir[idx] += g * (1 if i % 2 == 0 else -1)
    ir[0] += 1.0
    return ir / np.max(np.abs(ir))


def add_room(x, ir, wet=0.18):
    wet_sig = signal.fftconvolve(x, ir)[: len(x)]
    return x * (1 - wet) + wet_sig * wet


def env_ar(n, attack_ms, release_ms):
    """Smooth attack + raised-cosine release, used to kill any edge click."""
    t = np.arange(n) / SR
    a = np.clip(t / (attack_ms / 1000), 0, 1)
    r = np.clip((n / SR - t) / (release_ms / 1000), 0, 1)
    return (a ** 1.5) * (np.sin(r * np.pi / 2) ** 1.2)


def norm_peak(x, db):
    p = np.max(np.abs(x)) + 1e-12
    return x * (10 ** (db / 20) / p)


def write_wav(path, x):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    pcm = (np.clip(x, -1, 1) * 32767.0).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ------------------------------------------------------------------ voices
KINDS = {
    # name        modes(Hz)                 mode decay  thunk Hz  noise band        sharpness
    'clip':  dict(modes=[2650, 3930, 5210], mdec=[0.016, 0.011, 0.007], thunk=212, band=(1400, 9500), sharp=1.00),
    'shell': dict(modes=[1460, 2330, 3180], mdec=[0.030, 0.020, 0.013], thunk=168, band=(900, 7000), sharp=0.80),
    'pull':  dict(modes=[1780, 2720, 3600], mdec=[0.026, 0.017, 0.010], thunk=196, band=(1100, 8200), sharp=0.88),
    'knob':  dict(modes=[3100, 4400, 5800], mdec=[0.010, 0.007, 0.005], thunk=260, band=(1800, 11000), sharp=1.10),
    'seat':  dict(modes=[2280, 3350, 4620], mdec=[0.022, 0.015, 0.009], thunk=150, band=(1000, 8800), sharp=0.95),
    'thud':  dict(modes=[960, 1480, 2160], mdec=[0.048, 0.030, 0.018], thunk=118, band=(520, 4600), sharp=0.68),
    'snap':  dict(modes=[3420, 5060, 6880], mdec=[0.008, 0.006, 0.004], thunk=286, band=(2200, 12000), sharp=1.18),
    'twist': dict(modes=[2070, 3050, 4180], mdec=[0.019, 0.013, 0.008], thunk=232, band=(1350, 9200), sharp=0.98),
}


def plastic_hit(kind='clip', seed=0, dur=0.35, pitch=1.0, bright=1.0, body=1.0, tight=1.0):
    """One plastic contact event."""
    rng = np.random.default_rng(seed)
    spec = KINDS[kind]
    n = int(dur * SR)
    t = np.arange(n) / SR

    # 1) contact transient: 1-2 ms of broadband noise
    contact = rng.normal(0, 1, n) * np.exp(-t / (0.0011 * tight))
    contact = bp(contact, spec['band'][0], min(spec['band'][1], 19000))
    contact /= np.max(np.abs(contact)) + 1e-12

    # 2) ringing body modes (the plastic itself)
    modes = np.zeros(n)
    for f, d in zip(spec['modes'], spec['mdec']):
        f2 = f * pitch * (1 + rng.normal(0, 0.008))
        # phases stay near zero: the modes must all hit together at the contact,
        # otherwise slow beats can put the file's absolute peak 10-25 ms late
        # and the placed click would no longer land on the sync contract
        ph = rng.uniform(-0.7, 0.7)
        amp = (1.0 / (1 + (f2 / 3000.0) ** 1.4)) * (bright if f2 > 2500 else 1.0)
        modes += amp * np.sin(2 * np.pi * f2 * t + ph) * np.exp(-t / (d * tight))
    modes /= np.max(np.abs(modes)) + 1e-12

    # 3) low thunk from the panel the part sits on
    thunk_f = spec['thunk'] * pitch * (1 + rng.normal(0, 0.02))
    thunk = (np.sin(2 * np.pi * thunk_f * t + rng.uniform(-0.7, 0.7))
             + 0.4 * np.sin(2 * np.pi * thunk_f * 1.94 * t + rng.uniform(-0.7, 0.7)))
    thunk *= np.exp(-t / (0.030 * tight))
    thunk = lp(thunk, 900)
    thunk /= np.max(np.abs(thunk)) + 1e-12

    # 4) a breath of air pushed out of the gap
    air = rng.normal(0, 1, n) * np.exp(-t / 0.012)
    air = bp(air, 700, 5200)
    air /= np.max(np.abs(air)) + 1e-12

    sig = (0.90 * contact * spec['sharp']
           + 0.22 * modes * bright
           + 0.22 * body * thunk
           + 0.08 * air)

    # 5) second micro-contact: the sprung part relaxing a few ms later
    if kind in ('clip', 'shell', 'seat'):
        d2 = int(rng.uniform(0.0035, 0.0085) * SR)
        if d2 + 200 < n:
            second = rng.normal(0, 1, n - d2) * np.exp(-np.arange(n - d2) / SR / 0.0009)
            second = bp(second, 2000, 9000)
            second /= np.max(np.abs(second)) + 1e-12
            sig[d2:] += 0.12 * second

    # 6) a touch of saturation gives the brittle "plastic" edge
    sig = np.tanh(sig * 1.6) / 1.6
    sig = hp(sig, 90)

    # keep the event inside its own window
    sig *= env_ar(n, 0.30, 25.0)
    return sig


def knob_ratchet(seed=0, dur=0.30, pitch=1.0):
    """Two or three closely spaced clicks — a knob or clip being twisted open."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    out = np.zeros(n)
    t0 = 0.004
    for i in range(rng.integers(2, 4)):
        hit = plastic_hit('knob', seed=seed + 11 * i, dur=dur - t0, pitch=pitch * (1 + rng.normal(0, 0.02)),
                          bright=0.95, body=0.5, tight=0.8)
        idx = int(t0 * SR)
        m = min(len(hit), n - idx)
        # the first click must stay clearly the loudest in the 1.5-6 kHz band,
        # otherwise the mix-level peak finder can latch onto the 2nd/3rd click
        out[idx:idx + m] += (0.45 ** i) * hit[:m]
        t0 += rng.uniform(0.011, 0.020)
    return out


def final_seat(seed=99):
    """Two-stage seat: soft approach, then the crisp click that says 'done'."""
    n = int(0.30 * SR)
    out = np.zeros(n)
    first = plastic_hit('shell', seed=seed, dur=0.20, pitch=0.93, bright=0.8, body=0.9, tight=1.25)
    second = plastic_hit('seat', seed=seed + 1, dur=0.30, pitch=1.08, bright=1.15, body=0.85, tight=0.85)
    out[: len(first)] += 0.55 * first
    d = int(0.052 * SR)
    out[d:d + len(second)] += second[: n - d]
    return out


# -------------------------------------------------------------- measured id
def features(x):
    """Objective fingerprint used to document that the 13 voices differ."""
    x = np.asarray(x, dtype=np.float64)
    mono = x if x.ndim == 1 else x.mean(axis=1)
    k = int(np.argmax(np.abs(mono)))
    # 40 ms window from the loudest sample (the contact itself)
    seg = mono[k: k + int(0.040 * SR)]
    if len(seg) < 64:
        seg = mono
    win = np.hanning(len(seg))
    spec = np.abs(np.fft.rfft(seg * win))
    f = np.fft.rfftfreq(len(seg), 1 / SR)
    m = (f > 80) & (f < 18000)
    centroid = float(np.sum(f[m] * spec[m]) / (np.sum(spec[m]) + 1e-12))
    peak_f = float(f[m][np.argmax(spec[m])])
    return dict(peak_time_ms=round(k / SR * 1000, 3),
                peak_dbfs=round(20 * np.log10(np.max(np.abs(mono)) + 1e-12), 2),
                centroid_hz=round(centroid, 1),
                dominant_hz=round(peak_f, 1),
                duration=round(len(mono) / SR, 4))


# ------------------------------------------------------------------- write
def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    ir = room_ir()
    manifest = {'voices': [], 'close_map': {}, 'final_seat': {}}

    # thirteen separating parts: v2 part order, eight voices, varied parameters
    plan = [
        ('shell', 0.93, 0.90, 1.08, 0.225),   # 0 frontGrille
        ('pull',  1.06, 1.04, 0.88, 0.190),   # 1 blades
        ('seat',  0.90, 0.86, 1.18, 0.235),   # 2 motor
        ('shell', 1.04, 1.03, 0.96, 0.205),   # 3 rearGrille
        ('clip',  0.97, 0.98, 0.92, 0.185),   # 4 rearControl
        ('pull',  0.94, 0.95, 1.06, 0.215),   # 5 yoke
        ('knob',  1.00, 1.00, 0.75, 0.195),   # 6 knobL
        ('knob',  0.93, 0.97, 0.72, 0.205),   # 7 knobR
        ('seat',  1.05, 1.06, 0.92, 0.215),   # 8 neck
        ('shell', 0.98, 0.94, 1.12, 0.210),   # 9 baseTop
        ('thud',  0.92, 0.80, 1.25, 0.240),   # 10 baseBottom
        ('snap',  1.06, 1.10, 0.62, 0.170),   # 11 feet
        ('snap',  0.96, 1.02, 0.58, 0.165),   # 12 hook
    ]

    releases = []
    for i, (kind, pitch, bright, body, dur) in enumerate(plan):
        seed = 1000 + i * 17
        if kind == 'knob':
            x = knob_ratchet(seed=seed, dur=dur, pitch=pitch)
        else:
            x = plastic_hit(kind, seed=seed, dur=dur, pitch=pitch, bright=bright, body=body,
                            tight=1.0 + 0.1 * (i % 3 - 1))
        x = add_room(x, ir, wet=0.11)
        x = norm_peak(x, -6.0 - (i % 3) * 0.8)
        releases.append(x)
        p = os.path.join(outdir, f'foley-part-release-{i+1:02d}.wav')
        write_wav(p, np.stack([x, np.roll(x, 3) * 0.02 + x * 0.98], axis=1))
        feat = features(x)
        feat.update(index=i, kind=kind, pitch=pitch, bright=bright, body=body)
        manifest['voices'].append(feat)
        print(f'release {i+1:02d} {kind:5s} pitch {pitch:.2f} {len(x)/SR:.3f}s '
              f'peak {20*np.log10(np.max(np.abs(x))):5.1f} dBFS  '
              f'centroid {feat["centroid_hz"]:7.1f} Hz  dom {feat["dominant_hz"]:6.1f} Hz')

    # reversed family = the same parts going back together (v1 convention:
    # close-NN = release-(14-NN) reversed, so the order folds back symmetrically)
    for i in range(len(releases)):
        src = len(releases) - 1 - i
        x = releases[src][::-1].copy()
        # the forward one-shot starts at zero and its contact peak sits ~1 ms
        # in, so the reversed file ends on the contact; only a sub-ms taper is
        # needed to guarantee a clean edge, and the reversed click stays the
        # absolute peak so the mix can align it on the sync contract
        x *= env_ar(len(x), 0.5, 0.5)
        x = lp(x, 14000)
        x = norm_peak(x, -7.5 - (i % 3) * 0.7)
        p = os.path.join(outdir, f'foley-part-close-{i+1:02d}.wav')
        write_wav(p, np.stack([x, np.roll(x, 3) * 0.02 + x * 0.98], axis=1))
        manifest['close_map'][f'{i+1:02d}'] = f'{src+1:02d}'
        print(f'close   {i+1:02d} rev of release-{src+1:02d}  {len(x)/SR:.3f}s '
              f'peak {20*np.log10(np.max(np.abs(x))):5.1f} dBFS')

    x = final_seat()
    x = add_room(x, ir, wet=0.13)
    x = norm_peak(x, -5.0)
    write_wav(os.path.join(outdir, 'foley-final-seat.wav'),
              np.stack([x, np.roll(x, 3) * 0.02 + x * 0.98], axis=1))
    manifest['final_seat'] = features(x)
    print(f'seat    {len(x)/SR:.3f}s peak {20*np.log10(np.max(np.abs(x))):.1f} dBFS')

    with open(os.path.join(outdir, 'foley_manifest_v2.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=1)
    print('wrote', os.path.join(outdir, 'foley_manifest_v2.json'))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
