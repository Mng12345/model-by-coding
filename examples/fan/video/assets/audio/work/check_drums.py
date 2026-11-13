"""Is the bed driven by drums, or just plucks/pads?  Look at low-band transients."""
import sys
import subprocess
import numpy as np
from scipy import signal

SR = 48000
FF = r"D:\ffmpeg\bin\ffmpeg.exe"


def load(path):
    cmd = [FF, '-hide_banner', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout,
                         dtype=np.float32).astype(np.float64)


def band(x, lo, hi):
    sos = signal.butter(4, [lo / (SR / 2), hi / (SR / 2)], btype='band', output='sos')
    return signal.sosfilt(sos, x)


def db(x):
    return 20 * np.log10(max(float(x), 1e-12))


def main(path):
    x = load(path)
    print(f'{path}\n  {len(x)/SR:.1f} s')

    for label, lo, hi in [('kick band 40-110', 40, 110), ('snare band 180-500', 180, 500),
                          ('hat band 5k-12k', 5000, 12000), ('pluck 500-2k', 500, 2000)]:
        y = band(x, lo, hi)
        hop = int(0.005 * SR)
        n = len(y) // hop
        e = np.array([np.max(np.abs(y[i*hop:(i+1)*hop])) for i in range(n)])
        dbe = 20 * np.log10(e + 1e-12)
        med = np.median(dbe)
        # transient events: local maxima more than 9 dB above the running median
        strong = 0
        for i in range(2, n - 2):
            if dbe[i] > med + 9 and dbe[i] >= dbe[i-1] and dbe[i] > dbe[i+1]:
                strong += 1
        print(f'  {label:18s} median {med:6.1f} dB  p95 {np.percentile(dbe,95):6.1f}  '
              f'crest {dbe.max()-med:5.1f}  events(+9dB) {strong:4d}  -> {strong/(len(x)/SR)*60:5.0f}/min')

    # is there a periodic kick? autocorrelation of the low-band envelope
    y = band(x, 40, 110)
    hop = int(0.01 * SR)
    n = len(y) // hop
    e = np.array([np.sqrt(np.mean(y[i*hop:(i+1)*hop]**2)) for i in range(n)])
    e = np.maximum(e - np.median(e), 0)
    ac = np.correlate(e, e, mode='full')[n-1:]
    ac /= ac[0] + 1e-12
    lag = np.argmax(ac[20:60]) + 20            # 0.20 s .. 0.60 s  (100..300 BPM)
    print(f'  low-band envelope periodicity: peak at {lag*10} ms ({6000/lag:.0f} BPM), r={ac[lag]:.2f}')
    print(f'  first 20 s of 10 ms low-band RMS (dB): ' +
          ' '.join(f'{v:.0f}' for v in 20*np.log10(e[:2000]+1e-12)[::50]))


if __name__ == '__main__':
    main(sys.argv[1])
