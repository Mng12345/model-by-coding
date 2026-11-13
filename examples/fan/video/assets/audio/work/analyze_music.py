"""Analyse a music bed: transients, spectral balance, level, and structure.

Usage: python analyze_music.py <file>
"""
import subprocess
import sys
import json
import numpy as np

FF = r"D:\ffmpeg\bin\ffmpeg.exe"

def decode(path, sr=48000):
    cmd = [FF, "-hide_banner", "-v", "error", "-i", path,
           "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64), sr

def main(path):
    x, sr = decode(path)
    dur = len(x) / sr
    print(f"duration {dur:.2f}s  samples {len(x)}")

    # --- level ---
    rms = np.sqrt(np.mean(x ** 2))
    peak = np.max(np.abs(x))
    print(f"rms {20*np.log10(rms+1e-12):.1f} dBFS  peak {20*np.log10(peak+1e-12):.1f} dBFS  crest {20*np.log10(peak/(rms+1e-12)):.1f} dB")

    # --- frames ---
    n = 2048
    hop = 512
    win = np.hanning(n)
    nf = (len(x) - n) // hop
    frames = np.lib.stride_tricks.sliding_window_view(x, n)[::hop][:nf] * win
    spec = np.abs(np.fft.rfft(frames, axis=1))
    freqs = np.fft.rfftfreq(n, 1 / sr)

    # spectral flux -> onsets
    flux = np.maximum(0, np.diff(spec, axis=0)).sum(axis=1)
    flux = flux / (np.median(flux) + 1e-9)
    fps = sr / hop
    thr = 3.0
    peaks = []
    for i in range(1, len(flux) - 1):
        if flux[i] > thr and flux[i] >= flux[i - 1] and flux[i] > flux[i + 1]:
            peaks.append(i / fps)
    # merge peaks closer than 80 ms
    merged = []
    for t in peaks:
        if not merged or t - merged[-1] > 0.08:
            merged.append(t)
    print(f"strong transients (> {thr}x median flux): {len(merged)}  -> {len(merged)/dur*60:.0f} per minute")
    if merged:
        iois = np.diff(merged)
        iois = iois[iois < 2.0]
        if len(iois):
            print(f"median inter-onset {np.median(iois)*1000:.0f} ms -> {60/np.median(iois):.0f} BPM-ish")
    # onset density in 5s buckets
    buckets = {}
    for t in merged:
        buckets.setdefault(int(t // 5) * 5, 0)
        buckets[int(t // 5) * 5] += 1
    print("transient count per 5s bucket:", [buckets.get(k, 0) for k in range(0, int(dur) + 1, 5)])

    # --- spectral centroid over time + band energy ---
    mag_sum = spec.sum(axis=1) + 1e-9
    centroid = (spec * freqs).sum(axis=1) / mag_sum
    print(f"spectral centroid: mean {centroid.mean():.0f} Hz  p10 {np.percentile(centroid,10):.0f}  p90 {np.percentile(centroid,90):.0f}")

    band_edges = [(20, 60), (60, 150), (150, 400), (400, 1000), (1000, 3000), (3000, 8000), (8000, 16000)]
    total = (spec ** 2).sum()
    print("band energy share:")
    for lo, hi in band_edges:
        m = (freqs >= lo) & (freqs < hi)
        share = (spec[:, m] ** 2).sum() / total
        print(f"  {lo:5d}-{hi:5d} Hz  {10*np.log10(share+1e-12):6.1f} dB  ({share*100:5.1f}%)")

    # --- loudness contour (1 s) ---
    rms1 = np.array([np.sqrt(np.mean(x[i:i+sr] ** 2)) for i in range(0, len(x) - sr, sr)])
    db = 20 * np.log10(rms1 + 1e-12)
    print("per-second RMS dBFS:", " ".join(f"{v:.0f}" for v in db))

    # --- stereo width ---
    cmd = [FF, "-hide_banner", "-v", "error", "-i", path, "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    st = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).astype(np.float64)
    L, R = st[:, 0], st[:, 1]
    corr = np.corrcoef(L, R)[0, 1]
    side = (L - R) / 2
    mid = (L + R) / 2
    print(f"stereo correlation {corr:.3f}  side/mid energy {10*np.log10((side**2).sum()/(mid**2).sum()+1e-12):.1f} dB")

if __name__ == "__main__":
    main(sys.argv[1])
