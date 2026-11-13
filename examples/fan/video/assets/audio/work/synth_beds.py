"""Synthesise the two continuous layers the mix needs:
  * fan-whirr  : table-fan motor + air, 24 s seamless loop, stereo
  * room-tone  : very quiet room air, 6 s seamless loop, stereo

Everything is generated from noise + oscillators, so both files are original
("合成生成", no third-party rights).  Run:  python synth_beds.py <outdir>
"""
import sys
import os
import wave
import numpy as np

SR = 48000


def write_wav(path, x, sr=SR):
    """x: float array shape (n,) or (n, 2) in [-1, 1]."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    pcm = np.clip(x, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def pink(n, rng, alpha=1.0):
    """Pink-ish noise via spectral shaping of white noise."""
    w = rng.normal(0, 1, n)
    spec = np.fft.rfft(w)
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    spec = spec / (f ** (alpha / 2.0))
    out = np.fft.irfft(spec, n)
    return out / (np.max(np.abs(out)) + 1e-12)


def one_pole_lp(x, fc, sr=SR):
    a = np.exp(-2 * np.pi * fc / sr)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def one_pole_hp(x, fc, sr=SR):
    return x - one_pole_lp(x, fc, sr)


def fft_bandpass(x, lo, hi, sr=SR, tilt=0.0):
    """Zero-phase FFT band filter with optional spectral tilt (dB/oct-ish)."""
    n = len(x)
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / sr)
    mask = np.ones_like(f)
    # soft edges (log domain) so there is no ringing
    if lo > 0:
        mask *= 1.0 / (1.0 + (lo / np.maximum(f, 1e-6)) ** 4)
    mask *= 1.0 / (1.0 + (f / hi) ** 4)
    if tilt:
        m = f > 0
        mask[m] *= (f[m] / 1000.0) ** (tilt / 6.02)
    out = np.fft.irfft(spec * mask, n)
    return out


def seamless(x, fade):
    """Crossfade the tail into the head so `x` loops without a seam."""
    n = len(x)
    f = int(fade * SR)
    body = x[: n - f].copy()
    tail = x[n - f:]
    ramp = np.linspace(0, 1, f) ** 0.5
    if body.ndim == 2:
        ramp = ramp[:, None]
    body[:f] = body[:f] * ramp + tail * (1 - ramp)
    return body


def make_whirr(seconds=24.0, seed=7):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR

    # --- motor tone: blade-pass fundamental + harmonics, slow drift ---------
    f0 = 62.0                      # blade pass of a small table fan (~1240 rpm, 3 blades)
    drift = 0.35 * np.sin(2 * np.pi * 0.07 * t) + 0.18 * np.sin(2 * np.pi * 0.023 * t + 1.1)
    phase = 2 * np.pi * np.cumsum(f0 + drift) / SR
    motor = np.zeros(n)
    for k, amp in enumerate([1.0, 0.62, 0.34, 0.20, 0.12, 0.07, 0.04], start=1):
        # tiny random detune keeps it from sounding like a pure synth tone
        det = 1.0 + rng.normal(0, 0.0007)
        motor += amp * np.sin(k * phase * det + rng.uniform(0, 2 * np.pi))
    motor /= np.max(np.abs(motor))

    # --- air: broadband noise, band-limited, gently "chuffed" --------------
    air_l = fft_bandpass(pink(n, rng, alpha=0.8), 90, 5200, tilt=-1.6)
    air_r = fft_bandpass(pink(n, rng, alpha=0.8), 90, 5200, tilt=-1.6)
    air_l /= np.max(np.abs(air_l)) + 1e-12
    air_r /= np.max(np.abs(air_r)) + 1e-12

    # blade chuff: soft periodic pulse at the blade rate, plus a slower swell
    chuff = 0.5 + 0.5 * np.cos(2 * np.pi * f0 * t)
    chuff = chuff ** 2.2                     # sharpen into a soft pulse
    chuff = 0.72 + 0.28 * chuff              # 28 % depth
    swell = 1.0 + 0.05 * np.sin(2 * np.pi * 0.13 * t) + 0.03 * np.sin(2 * np.pi * 0.31 * t + 2.0)

    # a thin upper "whistle" of the airflow, very quiet
    whistle = fft_bandpass(pink(n, rng, alpha=1.4), 2600, 6500)
    whistle /= np.max(np.abs(whistle)) + 1e-12

    l = 0.78 * air_l * chuff * swell + 0.30 * motor + 0.05 * whistle
    r = 0.78 * air_r * chuff * swell + 0.30 * motor + 0.05 * whistle
    # a hair of extra width in the air only
    mid = 0.5 * (l + r)
    l = mid + 1.06 * (l - mid)
    r = mid + 0.94 * (r - mid)

    st = np.stack([l, r], axis=1)
    st = seamless(st, 1.2)
    return st


def make_room(seconds=6.0, seed=11):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    l = fft_bandpass(pink(n, rng, alpha=1.2), 40, 900)
    r = fft_bandpass(pink(n, rng, alpha=1.2), 40, 900)
    l /= np.max(np.abs(l)) + 1e-12
    r /= np.max(np.abs(r)) + 1e-12
    t = np.arange(n) / SR
    # faint airflow movement so it does not read as dead silence
    move = 1.0 + 0.10 * np.sin(2 * np.pi * 0.09 * t)
    st = np.stack([l * move, r * move], axis=1)
    return seamless(st, 1.0)


def rms(x):
    return np.sqrt(np.mean(np.square(x)))


def to_db(x):
    return 20 * np.log10(max(x, 1e-12))


if __name__ == '__main__':
    outdir = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(outdir, exist_ok=True)

    wh = make_whirr()
    # normalise the loop to a comfortable reference: -26 dBFS RMS
    wh *= 10 ** ((-26 - to_db(rms(wh))) / 20)
    p = os.path.join(outdir, 'foley-fan-whirr.wav')
    write_wav(p, wh)
    print(f'whirr  {wh.shape[0]/SR:.2f}s  rms {to_db(rms(wh)):.1f} dBFS  peak {to_db(np.max(np.abs(wh))):.1f}  -> {p}')

    rm = make_room()
    rm *= 10 ** ((-58 - to_db(rms(rm))) / 20)
    p = os.path.join(outdir, 'foley-room-tone.wav')
    write_wav(p, rm)
    print(f'room   {rm.shape[0]/SR:.2f}s  rms {to_db(rms(rm)):.1f} dBFS  -> {p}')
