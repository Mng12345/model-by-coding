"""Verify the rendered 43.500 s mix against SPEC-v2.md §4 and the delivery spec.

Usage:
    python verify_mix.py [mix.wav] [build_report_v2.json]

Everything in the written JSON is measured from the file (WAV header, raw PCM,
ffprobe, ffmpeg ebur128); contract values are kept separately under "targets".
"""
import os
import re
import sys
import json
import wave
import hashlib
import datetime
import subprocess
import numpy as np
from scipy import signal
from scipy.ndimage import maximum_filter1d

SR = 48000
DUR = 43.5
EXPECTED_FRAMES = 2088000
FF = r"D:\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"D:\ffmpeg\bin\ffprobe.exe"

RELEASE_T = [21.15 + i * 0.30 for i in range(13)]
CLOSE_T = [35.18 + i * 0.25 for i in range(13)]
SEAT_T = 38.45
CUES = ([(t, 'release', i + 1) for i, t in enumerate(RELEASE_T)]
        + [(t, 'close', i + 1) for i, t in enumerate(CLOSE_T)]
        + [(SEAT_T, 'seat', 1)])

TOL_MS = 5.0
# events are >=250 ms apart, so a 30 ms search window cannot reach a neighbour;
# it only has to be wide enough to find the click when the bed masks the attack
SEARCH_WIN_S = 0.030
TARGET_LUFS = -16.0
LUFS_TOL = 0.5
MAX_TP = -1.5
MAX_LRA = 6.0


def db(x):
    return 20 * np.log10(max(float(x), 1e-12))


def read_pcm(path):
    with wave.open(path, 'rb') as w:
        params = dict(nchannels=w.getnchannels(), sampwidth=w.getsampwidth(),
                      framerate=w.getframerate(), nframes=w.getnframes(),
                      comptype=w.getcomptype(), compname=w.getcompname())
        raw = w.readframes(w.getnframes())
    ch = params['nchannels']
    pcm = np.frombuffer(raw, dtype='<i2')
    if ch > 1:
        pcm = pcm.reshape(-1, ch)
    x = pcm.astype(np.float64) / 32768.0
    return params, pcm, x


def ffprobe(path):
    cmd = [FFPROBE, '-v', 'error', '-show_entries',
           'format=duration,size,format_name:stream=codec_name,sample_rate,channels,bits_per_sample',
           '-of', 'json', path]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)


def ebur128(path):
    cmd = [FF, '-hide_banner', '-nostats', '-i', path,
           '-filter_complex', 'ebur128=peak=true', '-f', 'null', 'NUL']
    out = subprocess.run(cmd, capture_output=True, text=True).stderr
    tail = out[out.rfind('Summary'):] if 'Summary' in out else out
    i = re.search(r'I:\s+(-?[\d.]+) LUFS', tail)
    tp = re.search(r'Peak:\s+(-?[\d.]+) dBFS', tail)
    lra = re.search(r'LRA:\s+(-?[\d.]+) LU', tail)
    return {
        'integrated_lufs': float(i.group(1)) if i else None,
        'true_peak_dbtp': float(tp.group(1)) if tp else None,
        'lra_lu': float(lra.group(1)) if lra else None,
        'summary_text': tail.strip(),
    }


def band_sos(lo, hi, order=4):
    return signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], btype='band', output='sos')


def band_rms(x, lo, hi):
    y = signal.sosfiltfilt(band_sos(lo, hi), x)
    return float(np.sqrt(np.mean(y ** 2)))


def main(mix_path, out_path):
    report = {
        'version': 2,
        'spec': 'SPEC-v2.md §4',
        'file': os.path.abspath(mix_path),
        'measured_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        'engine': {'ffmpeg': FF, 'python': sys.version.split()[0], 'numpy': np.__version__},
        'targets': {'duration_s': DUR, 'frames': EXPECTED_FRAMES, 'sample_rate': SR,
                    'channels': 2, 'bits_per_sample': 16,
                    'lufs': TARGET_LUFS, 'lufs_tolerance': LUFS_TOL,
                    'max_true_peak_dbtp': MAX_TP, 'max_lra_lu': MAX_LRA,
                    'event_tolerance_ms': TOL_MS},
    }

    # ---------------- container / duration ----------------
    params, pcm, x = read_pcm(mix_path)
    sha = hashlib.sha256(open(mix_path, 'rb').read()).hexdigest()
    probe = ffprobe(mix_path)
    stream = (probe.get('streams') or [{}])[0]
    fmt = probe.get('format', {})
    report['sha256'] = sha
    report['file_size_bytes'] = os.path.getsize(mix_path)
    report['wav_header'] = {
        'channels': params['nchannels'],
        'bits_per_sample': params['sampwidth'] * 8,
        'sample_rate': params['framerate'],
        'frames': params['nframes'],
        'duration_s': params['nframes'] / params['framerate'],
        'comptype': params['comptype'],
    }
    report['ffprobe'] = {
        'format_name': fmt.get('format_name'),
        'duration_s': float(fmt.get('duration', 'nan')),
        'size_bytes': int(fmt.get('size', 0)),
        'codec_name': stream.get('codec_name'),
        'sample_rate': int(stream.get('sample_rate', 0)),
        'channels': int(stream.get('channels', 0)),
        'bits_per_sample': int(stream.get('bits_per_sample', 0)),
    }
    n = len(x)
    duration_ok = (params['nframes'] == EXPECTED_FRAMES and abs(params['nframes'] / SR - DUR) < 1e-9)

    # ---------------- loudness / true peak / LRA ----------------
    ebu = ebur128(mix_path)
    report['loudness'] = ebu
    lufs_ok = ebu['integrated_lufs'] is not None and abs(ebu['integrated_lufs'] - TARGET_LUFS) <= LUFS_TOL
    tp_ok = ebu['true_peak_dbtp'] is not None and ebu['true_peak_dbtp'] <= MAX_TP
    lra_ok = ebu['lra_lu'] is not None and ebu['lra_lu'] <= MAX_LRA

    # ---------------- channel / clip stats ----------------
    left, right = x[:, 0], x[:, 1]
    mono = x.mean(axis=1)
    full_scale = int(np.sum(np.abs(pcm.astype(np.int32)) >= 32767))
    report['channel'] = {
        'correlation': round(float(np.corrcoef(left, right)[0, 1]), 4),
        'lr_rms_diff_db': round(db(np.sqrt(np.mean(left ** 2))) - db(np.sqrt(np.mean(right ** 2))), 2),
        'side_mid_db': round(db(np.sqrt(np.mean(((left - right) / 2) ** 2)))
                             - db(np.sqrt(np.mean(((left + right) / 2) ** 2))), 2),
        'sample_peak_dbfs': round(db(np.max(np.abs(x))), 2),
        'full_scale_samples': full_scale,
        'full_scale_samples_ok': full_scale == 0,
    }

    # ---------------- foley event alignment ----------------
    # measure the click band (1.5-6 kHz) zero-phase so the filter cannot shift
    # the peak; a plastic click dominates that band over the bed
    click = signal.sosfiltfilt(band_sos(1500, 6000), mono)
    absclick = np.abs(click)
    events = []
    for cue, tag, idx in CUES:
        cue_smp = int(round(cue * SR))
        a = max(0, int(round((cue - SEARCH_WIN_S) * SR)))
        b = min(n, int(round((cue + SEARCH_WIN_S) * SR)))
        seg = absclick[a:b]
        peak_idx = a + int(np.argmax(seg))
        peak_t = peak_idx / SR
        dev_ms = (peak_t - cue) * 1000.0
        full_seg = np.abs(mono[a:b])
        full_idx = a + int(np.argmax(full_seg))
        # ambient reference in the click band just before the hit
        aa, bb = max(0, int(round((cue - 0.16) * SR))), max(0, int(round((cue - 0.06) * SR)))
        amb = float(np.sqrt(np.mean(click[aa:bb] ** 2)))
        peak_dbfs = db(seg.max())
        lift = peak_dbfs - db(amb)

        onset_ms = None
        onset_note = None
        if tag == 'release':
            # forward one-shot: first sample above 30 % of the peak amplitude,
            # scanning back at most 15 ms from the peak
            thr = 0.30 * absclick[peak_idx]
            j = peak_idx
            lim = max(a, peak_idx - int(0.015 * SR))
            while j > lim and absclick[j - 1] > thr:
                j -= 1
            onset_ms = (j / SR - cue) * 1000.0
        elif tag == 'close':
            onset_note = 'reversed release: swell before the peak, peak aligned by design'
        else:
            onset_note = 'two-stage seat: peak (2nd stage) aligned, 1st contact 52 ms earlier by design'

        events.append({
            'type': tag,
            'index': idx,
            'cue_s': round(cue, 6),
            'cue_sample': cue_smp,
            'peak_sample': int(peak_idx),
            'peak_time_s': round(peak_t, 6),
            'peak_deviation_ms': round(dev_ms, 3),
            'within_tolerance': bool(abs(dev_ms) <= TOL_MS),
            'click_band_peak_dbfs': round(peak_dbfs, 2),
            'click_band_ambient_dbfs': round(db(amb), 2),
            'lift_db': round(lift, 1),
            'broadband_peak_time_s': round(full_idx / SR, 6),
            'broadband_peak_deviation_ms': round((full_idx / SR - cue) * 1000.0, 3),
            'onset_deviation_ms': None if onset_ms is None else round(onset_ms, 3),
            'note': onset_note,
        })
    max_dev = max(abs(e['peak_deviation_ms']) for e in events)
    max_bb_dev = max(abs(e['broadband_peak_deviation_ms']) for e in events)
    all_ok = all(e['within_tolerance'] for e in events)
    report['events'] = events
    report['event_summary'] = {
        'count': len(events),
        'release_count': len(RELEASE_T),
        'close_count': len(CLOSE_T),
        'seat_count': 1,
        'method': 'peak of the 1.5-6 kHz band (zero-phase) inside cue +-30 ms; '
                  'the band is where the plastic contact transient lives',
        'search_window_ms': SEARCH_WIN_S * 1000,
        'max_abs_peak_deviation_ms': round(max_dev, 3),
        'max_abs_broadband_peak_deviation_ms_reference': round(max_bb_dev, 3),
        'tolerance_ms': TOL_MS,
        'all_within_tolerance': bool(all_ok),
        'min_lift_db': round(min(e['lift_db'] for e in events), 1),
    }

    # ---------------- section levels (for the audited envelope moves) ----------
    sections = [
        ('intro_room_0.2_0.8', 0.2, 0.8),
        ('whirr_fadein_1.0_1.9', 1.0, 1.9),
        ('bed_5_18', 5.0, 18.0),
        ('grille_9.2_12.3', 9.2, 12.3),
        ('grille_ref_13.8_16.5', 13.8, 16.5),
        ('explode_21.15_24.75', 21.15, 24.75),
        ('space_lowcut_26.8_33.2', 26.8, 33.2),
        ('hold_29.5_34', 29.5, 34.0),
        ('reassemble_35.18_38.18', 35.18, 38.18),
        ('end_card_39.5_42.3', 39.5, 42.3),
        ('fade_out_42.3_43.5', 42.3, 43.5),
    ]
    sec_rows = {}
    for name, t0, t1 in sections:
        seg = mono[int(round(t0 * SR)):int(round(t1 * SR))]
        sec_rows[name] = {
            'full_rms_dbfs': round(db(np.sqrt(np.mean(seg ** 2))), 2),
            'rms_20_120_dbfs': round(db(band_rms(seg, 20, 120)), 2),
            'rms_300_4k_dbfs': round(db(band_rms(seg, 300, 4000)), 2),
            'rms_1k5_6k_dbfs': round(db(band_rms(seg, 1500, 6000)), 2),
            'peak_dbfs': round(db(np.max(np.abs(seg))), 2),
        }
    report['sections'] = sec_rows

    # derived checks from the measured sections
    lowcut_delta = sec_rows['space_lowcut_26.8_33.2']['rms_20_120_dbfs'] - sec_rows['bed_5_18']['rms_20_120_dbfs']
    fadein_delta = sec_rows['end_card_39.5_42.3']['full_rms_dbfs'] - sec_rows['intro_room_0.2_0.8']['full_rms_dbfs']
    music_in_delta = db(np.sqrt(np.mean(mono[int(2.4 * SR):int(2.65 * SR)] ** 2))) \
        - db(np.sqrt(np.mean(mono[int(1.7 * SR):int(1.95 * SR)] ** 2)))
    whirr_in_delta = db(np.sqrt(np.mean(mono[int(1.7 * SR):int(1.95 * SR)] ** 2))) \
        - db(np.sqrt(np.mean(mono[int(0.2 * SR):int(0.8 * SR)] ** 2)))
    last_400 = mono[-int(0.4 * SR):]
    last_200 = mono[-int(0.2 * SR):]
    report['envelope_checks'] = {
        'low_end_20_120_space_minus_bed_db': round(lowcut_delta, 2),
        'music_arrival_shift_db_2.4_2.65_vs_1.7_1.95': round(music_in_delta, 2),
        'whirr_arrival_shift_db_1.7_1.95_vs_0.2_0.8': round(whirr_in_delta, 2),
        'peak_last_400ms_dbfs': round(db(np.max(np.abs(last_400))), 2),
        'rms_last_200ms_dbfs': round(db(np.sqrt(np.mean(last_200 ** 2))), 2),
        'peak_first_60ms_dbfs': round(db(np.max(np.abs(mono[:int(0.06 * SR)]))), 2),
        'last_sample': float(mono[-1]),
        'end_card_minus_intro_db': round(fadein_delta, 2),
    }

    # ---------------- checks ----------------
    checks = {
        'duration_frames_exact': {'pass': bool(duration_ok), 'measured_frames': params['nframes'],
                                  'expected_frames': EXPECTED_FRAMES},
        'format_48k_16bit_stereo': {'pass': bool(params['framerate'] == SR and params['nchannels'] == 2
                                                 and params['sampwidth'] == 2),
                                    'measured': [params['framerate'], params['nchannels'], params['sampwidth'] * 8]},
        'lufs_within_0.5': {'pass': bool(lufs_ok), 'measured_lufs': ebu['integrated_lufs'],
                            'target': TARGET_LUFS, 'tolerance': LUFS_TOL},
        'true_peak_le_-1.5_dbtp': {'pass': bool(tp_ok), 'measured_dbtp': ebu['true_peak_dbtp'],
                                   'limit': MAX_TP},
        'lra_le_6_lu': {'pass': bool(lra_ok), 'measured_lra': ebu['lra_lu'], 'limit': MAX_LRA},
        'all_events_within_5ms': {'pass': bool(all_ok), 'max_abs_deviation_ms': round(max_dev, 3),
                                  'tolerance_ms': TOL_MS},
        'no_full_scale_samples': {'pass': bool(full_scale == 0), 'full_scale_samples': full_scale},
        'all_pass': bool(duration_ok and params['framerate'] == SR and params['nchannels'] == 2
                         and params['sampwidth'] == 2 and lufs_ok and tp_ok and lra_ok
                         and all_ok and full_scale == 0),
    }
    report['checks'] = checks

    # ---------------- console report ----------------
    print(f"file      {mix_path}")
    print(f"sha256    {sha}")
    print(f"wav       {params['nframes']} frames / {params['nframes']/SR:.6f} s @ {params['framerate']} Hz "
          f"{params['nchannels']} ch {params['sampwidth']*8}-bit  size {report['file_size_bytes']} B")
    print(f"ffprobe   duration {report['ffprobe']['duration_s']:.6f} s  {report['ffprobe']['codec_name']} "
          f"{report['ffprobe']['sample_rate']} Hz {report['ffprobe']['channels']} ch")
    print(f"loudness  I {ebu['integrated_lufs']} LUFS  TP {ebu['true_peak_dbtp']} dBTP  LRA {ebu['lra_lu']} LU")
    print(f"stereo    corr {report['channel']['correlation']}  L/R {report['channel']['lr_rms_diff_db']:+.2f} dB  "
          f"side/mid {report['channel']['side_mid_db']:+.1f} dB  peak {report['channel']['sample_peak_dbfs']} dBFS")
    print(f"clipping  full-scale samples: {full_scale}")
    print(f'\n-- event peak alignment (click band 1.5-6 kHz, cue +-{SEARCH_WIN_S*1000:.0f} ms) --')
    for e in events:
        onset = '' if e['onset_deviation_ms'] is None else f"  onset {e['onset_deviation_ms']:+7.3f} ms"
        print(f"  {e['cue_s']:8.3f}s {e['type']:7s} {e['index']:2d}  peak {e['peak_time_s']:10.6f}  "
              f"dev {e['peak_deviation_ms']:+7.3f} ms  lift {e['lift_db']:5.1f} dB{onset}")
    print(f"  max |dev| {max_dev:.3f} ms  -> {'OK' if all_ok else 'FAIL'} (limit {TOL_MS} ms)")
    print('\n-- section levels (dBFS RMS) --')
    for name, row in sec_rows.items():
        print(f"  {name:28s} full {row['full_rms_dbfs']:6.1f}  20-120 {row['rms_20_120_dbfs']:6.1f}  "
              f"300-4k {row['rms_300_4k_dbfs']:6.1f}  1.5-6k {row['rms_1k5_6k_dbfs']:6.1f}")
    print('\n-- envelope checks --')
    for k, v in report['envelope_checks'].items():
        print(f"  {k:48s} {v}")
    print('\n-- checks --')
    for k, v in checks.items():
        if k == 'all_pass':
            continue
        print(f"  {k:28s} {'PASS' if v['pass'] else 'FAIL'}")
    print(f"  ALL: {'PASS' if checks['all_pass'] else 'FAIL'}")

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
    print('\nwrote', out_path)
    return 0 if checks['all_pass'] else 1


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    mix = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(here), 'mix.wav')
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, 'build_report_v2.json')
    sys.exit(main(mix, out))
