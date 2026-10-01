"""動画にポップな BGM（自動生成・著作権フリー）を付ける。

使い方:
    python tools/add_bgm.py media/videos/xxx/1080p60/Scene.mp4 [--bpm 118] [--volume 0.5]

動画の長さに合わせて BGM を合成し、<元のファイル名>_bgm.mp4 を同じ場所に書き出す。
動画に効果音などの音声があれば、BGM と重ねる。
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

SR = 44100
rng = np.random.default_rng(257)


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env(n, attack=0.005, decay=0.3):
    t = np.arange(n) / SR
    a = np.clip(t / attack, 0, 1)
    return a * np.exp(-t / decay)


def lowpass(x, cutoff):
    b, a = butter(2, cutoff / (SR / 2), "low")
    return lfilter(b, a, x)


def highpass(x, cutoff):
    b, a = butter(2, cutoff / (SR / 2), "high")
    return lfilter(b, a, x)


# --- 音色 -------------------------------------------------------------
def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    freq = 50 + 110 * np.exp(-t / 0.04)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    return np.sin(phase) * env(n, 0.001, 0.15) * 1.0


def snare():
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    noise = highpass(rng.standard_normal(n), 1500) * env(n, 0.001, 0.08)
    tone = np.sin(2 * np.pi * 190 * t) * env(n, 0.001, 0.05)
    return 0.5 * noise + 0.4 * tone


def hihat(open_=False):
    n = int((0.2 if open_ else 0.06) * SR)
    return highpass(rng.standard_normal(n), 7000) * env(n, 0.001, 0.08 if open_ else 0.02) * 0.25


def clap():
    n = int(0.2 * SR)
    x = highpass(rng.standard_normal(n), 1000)
    e = np.zeros(n)
    for d in (0, 0.01, 0.02):
        s = int(d * SR)
        e[s:] += env(n - s, 0.001, 0.05)
    return x * e * 0.25


def bass(m, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = midi_hz(m)
    saw = 2 * ((t * f) % 1) - 1
    x = lowpass(saw, 600) + 0.5 * np.sin(2 * np.pi * f * t)
    return x * env(n, 0.005, dur * 0.8) * 0.45


def keys(m, dur):
    """エレピ風の和音用音色。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = midi_hz(m)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.1 * np.sin(6 * np.pi * f * t)
    return x * env(n, 0.003, 0.35) * 0.12


def bell(m, dur):
    """メロディ用の明るいベル／マリンバ風音色。"""
    n = int((dur + 0.3) * SR)
    t = np.arange(n) / SR
    f = midi_hz(m)
    x = (np.sin(2 * np.pi * f * t + 0.8 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.15))
         + 0.25 * np.sin(2 * np.pi * 2 * f * t))
    return x * env(n, 0.002, 0.4) * 0.22


# --- 曲 ---------------------------------------------------------------
CHORDS = [  # I - V - vi - IV（C - G - Am - F）
    (48, [60, 64, 67]),
    (43, [59, 62, 67]),
    (45, [60, 64, 69]),
    (41, [60, 65, 69]),
]
MELODY_A = [  # (拍, MIDI, 長さ[拍]) 4小節
    (0, 76, 1), (1, 79, .5), (1.5, 81, .5), (2, 79, 1), (3, 76, 1),
    (4, 74, 1), (5, 79, .5), (5.5, 74, .5), (6, 71, 1.5), (7.5, 74, .5),
    (8, 72, 1), (9, 76, .5), (9.5, 79, .5), (10, 81, 1), (11, 79, 1),
    (12, 77, .5), (12.5, 76, .5), (13, 74, 1), (14, 72, 2),
]
MELODY_B = MELODY_A[:-4] + [(12, 77, .5), (12.5, 79, .5), (13, 81, 1), (14, 84, 2)]


def compose(duration, bpm):
    beat = 60 / bpm
    n_total = int(duration * SR)
    out = np.zeros(n_total + SR * 2)

    def put(sig, t):
        s = int(t * SR)
        if s >= len(out):
            return
        e = min(len(out), s + len(sig))
        out[s:e] += sig[: e - s]

    n_bars = int(np.ceil(duration / (4 * beat)))
    for bar in range(n_bars):
        t0 = bar * 4 * beat
        root, chord = CHORDS[bar % 4]
        intro = bar < 4                      # 最初の4小節は軽め
        melody_on = bar >= 8 and (bar // 8) % 3 != 2   # 8小節目から。時々メロディを休ませる

        # ドラム
        for b in range(4):
            if not intro or b in (0, 2):
                put(kick(), t0 + b * beat)
            if not intro and b in (1, 3):
                put(snare(), t0 + b * beat)
                put(clap(), t0 + b * beat)
        for e in range(8):
            put(hihat(open_=(e % 2 == 1 and not intro)), t0 + e * beat / 2)

        # ベース（8分）
        if not intro:
            for e in range(8):
                m = root + (12 if e in (3, 7) else 0)
                put(bass(m, beat / 2 * 0.9), t0 + e * beat / 2)

        # 和音（裏拍で刻む）
        for e in range(8):
            if e % 2 == 1 or intro:
                for m in chord:
                    put(keys(m, beat / 2), t0 + e * beat / 2)

        # メロディ（4小節フレーズ）
        if melody_on:
            phrase = MELODY_B if (bar // 4) % 2 else MELODY_A
            part = bar % 4
            for st, m, d in phrase:
                if part * 4 <= st < part * 4 + 4:
                    put(bell(m, d * beat), t0 + (st - part * 4) * beat)

    out = out[:n_total]
    # 簡易マスタリング: ソフトクリップ + 正規化 + フェード
    out = np.tanh(out * 1.2)
    out /= np.max(np.abs(out)) + 1e-9
    fade_in, fade_out = int(0.5 * SR), int(3.0 * SR)
    out[:fade_in] *= np.linspace(0, 1, fade_in)
    out[-fade_out:] *= np.linspace(1, 0, fade_out)
    return out * 0.9


def video_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def has_audio(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return bool(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("--bpm", type=float, default=118)
    ap.add_argument("--volume", type=float, default=0.5, help="BGM の音量 (0-1)")
    ap.add_argument("-o", "--output", type=Path)
    args = ap.parse_args()

    dur = video_duration(args.video)
    music = compose(dur, args.bpm) * args.volume
    out = args.output or args.video.with_name(args.video.stem + "_bgm.mp4")
    with tempfile.TemporaryDirectory() as d:
        wav = Path(d) / "bgm.wav"
        wavfile.write(wav, SR, (music * 32767).astype(np.int16))
        if has_audio(args.video):
            # 効果音などの元の音声と BGM を重ねる
            audio = ["-filter_complex", "[0:a][1:a]amix=inputs=2:duration=longest:normalize=0[a]",
                     "-map", "0:v", "-map", "[a]"]
        else:
            audio = ["-map", "0:v", "-map", "1:a"]
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-i", str(args.video), "-i", str(wav), *audio,
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.3f}", str(out)],
            check=True,
        )
    print(out)


if __name__ == "__main__":
    main()
