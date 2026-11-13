"""Mastering: push the raw mix to -16 LUFS integrated, true peak <= -1.5 dBTP.

mix_raw.wav -> mix.wav   (48 kHz, 16-bit PCM, stereo, exactly 43.500000 s)
"""
import os
import re
import sys
import subprocess
import wave
import numpy as np
from scipy.ndimage import maximum_filter1d

SR = 48000
FF = r"D:\ffmpeg\bin\ffmpeg.exe"
EBUR = r"D:\ffmpeg\bin\ffmpeg.exe"


def load(path):
    cmd = [FF, '-hide_banner', '-v', 'error', '-i', path, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64).reshape(-1, 2)


def write(path, x):
    pcm = (np.clip(x, -1.0, 1.0) * 32767.0).round().astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def measure(path):
    out = subprocess.run([EBUR, '-hide_banner', '-nostats', '-i', path,
                          '-af', 'ebur128=peak=true', '-f', 'null', 'NUL'],
                         capture_output=True, text=True).stderr
    tail = out[out.rfind('Summary'):] if 'Summary' in out else out
    i = re.search(r'I:\s+(-?[\d.]+) LUFS', tail)
    tp = re.search(r'Peak:\s+(-?[\d.]+) dBFS', tail)
    lra = re.search(r'LRA:\s+(-?[\d.]+) LU', tail)
    return float(i.group(1)), float(tp.group(1)), float(lra.group(1)) if lra else float('nan')


def limiter(x, ceiling_db=-1.6, lookahead=0.006, release=0.12):
    """Transparent look-ahead brickwall limiter (stereo linked)."""
    ceil = 10 ** (ceiling_db / 20.0)
    peak = np.max(np.abs(x), axis=1)
    la = int(lookahead * SR)
    pk = maximum_filter1d(peak, size=2 * la + 1, mode='nearest')
    target = np.minimum(1.0, ceil / np.maximum(pk, 1e-12))
    g = np.empty_like(target)
    coef = np.exp(-1.0 / (release * SR))
    cur = 1.0
    for i in range(len(target)):
        t = target[i]
        if t < cur:
            cur = t                      # clamp instantly (look-ahead already moved it early)
        else:
            cur = t + (cur - t) * coef   # release smoothly
        g[i] = cur
    # smooth the gain a touch so the clamps do not zipper (edge-padded: a plain
    # 'same' convolve would fade the first/last few ms of the file)
    k = np.hanning(la * 2 + 1)
    k /= k.sum()
    g = np.convolve(np.pad(g, (la, la), mode='edge'), k, mode='valid')[:len(target)]
    g = np.minimum(g, target)
    y = x * g[:, None]
    # last-resort safety: nothing above the ceiling at sample level
    m = np.max(np.abs(y))
    if m > ceil:
        y *= ceil / m
    return y, 20 * np.log10(1.0 / max(g.min(), 1e-9))


def main(src, dst, target=-16.0, ceiling=-3.2):
    """target = integrated LUFS; ceiling = sample-peak ceiling in dBFS.

    The dsp limiter acts on sample peaks, so the ceiling needs ~1.3 dB of head
    room below the -1.5 dBTP delivery limit: the synthetic plastic clicks are
    very sharp and overshoot the sample peak by that much at 4x oversampling.
    """
    x = load(src)
    gain = 0.0
    for it in range(5):
        y = x * 10 ** (gain / 20.0)
        y, gr = limiter(y, ceiling_db=ceiling)
        write(dst, y)
        i, tp, lra = measure(dst)
        print(f'iter {it}: gain {gain:+.2f} dB  I {i:.2f} LUFS  TP {tp:.2f} dBTP  '
              f'LRA {lra:.1f}  max GR {gr:.1f} dB')
        err = target - i
        if abs(err) < 0.15:
            break
        gain += err
    i, tp, lra = measure(dst)
    print(f'FINAL  I {i:.2f} LUFS  TP {tp:.2f} dBTP  LRA {lra:.1f} LU')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
