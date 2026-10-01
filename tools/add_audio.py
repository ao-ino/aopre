"""動画に BGM と効果音を付ける（すべてコードで合成・著作権フリー）。

使い方:
    python tools/add_audio.py media/videos/xxx/1080p60/Scene.mp4 [--style rock|pop|cute] [--bgm-volume 0.35]

- 効果音: シーンが書き出した media/audio_events/<Scene>.json（SfxMixin）を読み、
  映像の時刻どおりにサンプル単位で配置する。
- BGM: 動画の長さに合わせて合成。効果音の瞬間だけ少し下げて（ダッキング）聞き取りやすくする。
- 出力: <元のファイル名>_audio.mp4（映像はコピー、音声は AAC ステレオ）
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

SR = 44100
ROOT = Path(__file__).resolve().parent.parent
EVENT_DIR = ROOT / "media" / "audio_events"
rng = np.random.default_rng(257)


# ======================================================================
# 共通
# ======================================================================
def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tt(dur):
    return np.arange(int(dur * SR)) / SR


def env(n, attack=0.005, decay=0.3):
    t = np.arange(n) / SR
    return np.clip(t / attack, 0, 1) * np.exp(-t / decay)


def lowpass(x, cutoff, order=2):
    b, a = butter(order, min(cutoff, SR / 2 - 100) / (SR / 2), "low")
    return lfilter(b, a, x)


def highpass(x, cutoff, order=2):
    b, a = butter(order, cutoff / (SR / 2), "high")
    return lfilter(b, a, x)


def saw(freq, t, phase=0.0):
    return 2 * ((t * freq + phase) % 1) - 1


class Track:
    """ステレオのミックスバス。"""

    def __init__(self, dur):
        self.buf = np.zeros((int(dur * SR) + SR * 3, 2))

    def put(self, sig, t, pan=0.0, gain=1.0):
        s = int(round(t * SR))
        if s >= len(self.buf) or s < 0:
            return
        e = min(len(self.buf), s + len(sig))
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        self.buf[s:e, 0] += sig[: e - s] * gain * l * np.sqrt(2)
        self.buf[s:e, 1] += sig[: e - s] * gain * r * np.sqrt(2)


# ======================================================================
# 効果音
# ======================================================================
MAJOR = [0, 2, 4, 5, 7, 9, 11]   # ド レ ミ ファ ソ ラ シ


def sfx_pop(step=0):
    """「ポン」。step=0,1,2,… が ド,レ,ミ,ファ,ソ,ラ,シ,ド(高),… （C メジャー、ド=C5）。"""
    step = int(step) % 15   # 2 オクターブ（ド〜高いド2つ上）まで
    m = 72 + 12 * (step // 7) + MAJOR[step % 7]
    t = tt(0.18)
    f0 = midi_hz(m)
    freq = f0 * (0.6 + 0.4 * np.minimum(t / 0.012, 1))   # 一瞬しゃくり上げる
    ph = 2 * np.pi * np.cumsum(freq) / SR
    x = (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)) * np.exp(-t / 0.06)
    x *= np.minimum(t / 0.001, 1)
    return x / np.max(np.abs(x))


def sfx_chime():
    """正解の「キラーン」。上昇アルペジオ + きらめきノイズ。"""
    t = tt(1.8)
    x = np.zeros_like(t)
    for k, m in enumerate([76, 79, 84, 88, 91]):
        s = int(k * 0.055 * SR)
        u = t[: len(t) - s]
        f = midi_hz(m)
        x[s:] += (np.sin(2 * np.pi * f * u) + 0.3 * np.sin(2 * np.pi * 3 * f * u)) * np.exp(-u / 0.55)
    sparkle = highpass(rng.standard_normal(len(t)), 8000) * np.exp(-t / 0.25) * 0.3
    x = x + sparkle
    return x / np.max(np.abs(x))


SFX = {"pop": sfx_pop, "chime": sfx_chime}


def render_sfx(events, dur):
    tr = Track(dur)
    spans = []
    cache = {}
    for ev in events:
        params = {k: v for k, v in ev.items() if k not in ("t", "name", "gain_db")}
        key = (ev["name"], json.dumps(params, sort_keys=True))
        if key not in cache:
            cache[key] = SFX[ev["name"]](**params)
        sig = cache[key]
        tr.put(sig, ev["t"], gain=10 ** (ev.get("gain_db", 0) / 20) * 0.75)
        spans.append((ev["t"], ev["t"] + min(len(sig) / SR, 0.6)))
    return tr.buf, spans


def duck_curve(n, spans, depth_db=-7, ramp=0.03):
    """効果音が鳴っている間だけ BGM を下げるゲインカーブ。"""
    g = np.ones(n)
    low = 10 ** (depth_db / 20)
    r = int(ramp * SR)
    for a, b in spans:
        s, e = int((a - 0.01) * SR), int(b * SR)
        seg = np.full(max(e - s, 0) + 2 * r, low)
        seg[:r] = np.linspace(1, low, r)
        seg[-r:] = np.linspace(low, 1, r)
        s0 = s - r
        lo, hi = max(s0, 0), min(s0 + len(seg), n)
        if hi > lo:
            g[lo:hi] = np.minimum(g[lo:hi], seg[lo - s0: hi - s0])
    return g


# ======================================================================
# ドラム
# ======================================================================
def kick(punch=1.0):
    t = tt(0.4)
    freq = 45 + 120 * np.exp(-t / 0.03)
    body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * env(len(t), 0.001, 0.18)
    click = highpass(rng.standard_normal(len(t)), 3000) * np.exp(-t / 0.004) * 0.4 * punch
    return np.tanh((body + click) * 1.5)


def snare(rock=False):
    t = tt(0.35 if rock else 0.25)
    noise = highpass(rng.standard_normal(len(t)), 1200) * env(len(t), 0.001, 0.13 if rock else 0.08)
    tone = (np.sin(2 * np.pi * 185 * t) + 0.5 * np.sin(2 * np.pi * 330 * t)) * env(len(t), 0.001, 0.06)
    return np.tanh((0.7 * noise + 0.6 * tone) * (1.6 if rock else 1.0)) * 0.8


def hihat(open_=False):
    t = tt(0.3 if open_ else 0.06)
    return highpass(rng.standard_normal(len(t)), 7000) * env(len(t), 0.001, 0.12 if open_ else 0.02) * 0.3


def crash():
    t = tt(1.8)
    return highpass(rng.standard_normal(len(t)), 4500) * env(len(t), 0.002, 0.7) * 0.35


def clap():
    t = tt(0.2)
    x = highpass(rng.standard_normal(len(t)), 1000)
    e = np.zeros(len(t))
    for d in (0, 0.01, 0.02):
        s = int(d * SR)
        e[s:] += env(len(t) - s, 0.001, 0.05)
    return x * e * 0.25


# ======================================================================
# ロック
# ======================================================================
ROCK_PROG = [45, 41, 48, 43]   # Am - F - C - G のパワーコード（ルート）
ROCK_LEAD_A = [  # (拍, MIDI, 長さ[拍]) 4小節
    (0, 76, 1), (1, 74, .5), (1.5, 72, .5), (2, 69, 1.5), (3.5, 72, .5),
    (4, 72, 1), (5, 74, 1), (6, 76, 1.5), (7.5, 74, .5),
    (8, 79, 1), (9, 76, .5), (9.5, 74, .5), (10, 72, 1), (11, 74, 1),
    (12, 71, 1), (13, 74, 1), (14, 79, 2),
]
ROCK_LEAD_B = ROCK_LEAD_A[:-3] + [(12, 76, 1), (13, 74, .5), (13.5, 71, .5), (14, 69, 2)]


def guitar(root, dur, mute, detune=0.0):
    """歪んだパワーコード（ルート・5度・オクターブ）。"""
    t = tt(dur + (0.05 if mute else 0.25))
    x = np.zeros_like(t)
    for iv in (0, 7, 12):
        f = midi_hz(root + iv)
        x += saw(f * (1 + detune), t) + saw(f * (1.004 + detune), t, 0.3)
    x = np.tanh(highpass(x, 90) * 5)
    if mute:
        x = lowpass(x, 1100) * env(len(t), 0.002, 0.07)
    else:
        x = lowpass(x, 3800, 4)
        e = env(len(t), 0.004, dur * 2.5)
        rel = int(0.2 * SR)
        e[-rel:] *= np.linspace(1, 0, rel)
        x *= e
    return x * 0.22


def rock_bass(m, dur):
    t = tt(dur)
    f = midi_hz(m)
    x = lowpass(np.tanh(saw(f, t) * 2), 700) + 0.6 * np.sin(2 * np.pi * f * t)
    return x * env(len(t), 0.003, dur * 0.9) * 0.5


def lead(m, dur):
    t = tt(dur + 0.15)
    f = midi_hz(m) * (1 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.15) / 0.2, 0, 1))
    ph = np.cumsum(f) / SR
    x = 2 * (ph % 1) - 1 + 0.5 * (2 * ((2 * ph) % 1) - 1)
    x = lowpass(np.tanh(x * 2.5), 3500)
    e = env(len(t), 0.01, 2.0)
    rel = int(0.12 * SR)
    e[-rel:] *= np.linspace(1, 0, rel)
    return x * e * 0.16


def compose_rock(dur, bpm=140):
    beat = 60 / bpm
    bar_len = 4 * beat
    tr = Track(dur)
    for bar in range(int(np.ceil(dur / bar_len))):
        t0 = bar * bar_len
        root = ROCK_PROG[bar % 4]
        intro = bar < 4
        # イントロ4小節のあと、Aメロ8小節 → サビ8小節 を繰り返す
        chorus = not intro and ((bar - 4) // 8) % 2 == 1
        last_of_section = not intro and (bar - 4) % 8 == 7

        # --- ドラム ---
        if bar == 0 or (not intro and (bar - 4) % 8 == 0):
            tr.put(crash(), t0, pan=0.3)
        if intro:
            tr.put(kick(), t0)
            tr.put(kick(), t0 + 2 * beat)
            if bar == 3:  # フィル
                for k in range(8):
                    tr.put(snare(True), t0 + k * beat / 2, gain=0.5 + k * 0.07)
            for k in range(8):
                tr.put(hihat(), t0 + k * beat / 2, pan=-0.3)
        else:
            for kb in ((0, 1.5, 2, 2.5) if chorus else (0, 2, 2.5)):
                tr.put(kick(), t0 + kb * beat)
            if last_of_section:
                tr.put(snare(True), t0 + beat)
                for k in range(4, 8):
                    tr.put(snare(True), t0 + k * beat / 2, gain=0.6 + (k - 4) * 0.1)
            else:
                for sb in (1, 3):
                    tr.put(snare(True), t0 + sb * beat)
            for k in range(8):
                tr.put(hihat(open_=chorus and k % 2 == 1), t0 + k * beat / 2, pan=-0.3)

        # --- ギター（左右ダブル） ---
        if intro:
            for pan, dt in ((-0.7, 0), (0.7, 0.012)):
                tr.put(guitar(root, bar_len * 0.95, mute=False), t0 + dt, pan=pan)
        elif chorus:
            for half in range(2):
                for pan, dt, dtn in ((-0.75, 0, 0), (0.75, 0.012, 0.002)):
                    tr.put(guitar(root, bar_len / 2 * 0.95, mute=False, detune=dtn),
                           t0 + half * bar_len / 2 + dt, pan=pan)
        else:
            for k in range(8):
                for pan, dt, dtn in ((-0.75, 0, 0), (0.75, 0.01, 0.002)):
                    tr.put(guitar(root, beat / 2, mute=True, detune=dtn), t0 + k * beat / 2 + dt, pan=pan)

        # --- ベース ---
        if not intro:
            for k in range(8):
                tr.put(rock_bass(root - 12 + (12 if k == 7 and chorus else 0), beat / 2 * 0.9),
                       t0 + k * beat / 2)

        # --- リード（サビ） ---
        if chorus:
            phrase = ROCK_LEAD_B if ((bar - 4) // 4) % 2 else ROCK_LEAD_A
            part = bar % 4
            for st, m, d in phrase:
                if part * 4 <= st < part * 4 + 4:
                    tr.put(lead(m, d * beat), t0 + (st - part * 4) * beat, pan=0.1)
    return tr.buf


# ======================================================================
# ポップ
# ======================================================================
POP_CHORDS = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])]
POP_MELODY_A = [
    (0, 76, 1), (1, 79, .5), (1.5, 81, .5), (2, 79, 1), (3, 76, 1),
    (4, 74, 1), (5, 79, .5), (5.5, 74, .5), (6, 71, 1.5), (7.5, 74, .5),
    (8, 72, 1), (9, 76, .5), (9.5, 79, .5), (10, 81, 1), (11, 79, 1),
    (12, 77, .5), (12.5, 76, .5), (13, 74, 1), (14, 72, 2),
]
POP_MELODY_B = POP_MELODY_A[:-4] + [(12, 77, .5), (12.5, 79, .5), (13, 81, 1), (14, 84, 2)]


def keys(m, dur):
    t = tt(dur)
    f = midi_hz(m)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.1 * np.sin(6 * np.pi * f * t)
    return x * env(len(t), 0.003, 0.35) * 0.12


def bell(m, dur):
    t = tt(dur + 0.3)
    f = midi_hz(m)
    x = np.sin(2 * np.pi * f * t + 0.8 * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.15)) \
        + 0.25 * np.sin(4 * np.pi * f * t)
    return x * env(len(t), 0.002, 0.4) * 0.22


def pop_bass(m, dur):
    t = tt(dur)
    f = midi_hz(m)
    x = lowpass(saw(f, t), 600) + 0.5 * np.sin(2 * np.pi * f * t)
    return x * env(len(t), 0.005, dur * 0.8) * 0.45


def compose_pop(dur, bpm=118):
    beat = 60 / bpm
    tr = Track(dur)
    for bar in range(int(np.ceil(dur / (4 * beat)))):
        t0 = bar * 4 * beat
        root, chord = POP_CHORDS[bar % 4]
        intro = bar < 4
        for b in range(4):
            if not intro or b in (0, 2):
                tr.put(kick(0.3), t0 + b * beat)
            if not intro and b in (1, 3):
                tr.put(snare(), t0 + b * beat)
                tr.put(clap(), t0 + b * beat)
        for e in range(8):
            tr.put(hihat(open_=(e % 2 == 1 and not intro)), t0 + e * beat / 2, pan=-0.3)
            if not intro:
                tr.put(pop_bass(root + (12 if e in (3, 7) else 0), beat / 2 * 0.9), t0 + e * beat / 2)
            if e % 2 == 1 or intro:
                for m in chord:
                    tr.put(keys(m, beat / 2), t0 + e * beat / 2, pan=0.3)
        if bar >= 8 and (bar // 8) % 3 != 2:
            phrase = POP_MELODY_B if (bar // 4) % 2 else POP_MELODY_A
            part = bar % 4
            for st, m, d in phrase:
                if part * 4 <= st < part * 4 + 4:
                    tr.put(bell(m, d * beat), t0 + (st - part * 4) * beat)
    return tr.buf


# ======================================================================
# かわいい（オルゴール・ウクレレ・はねるリズム）
# ======================================================================
CUTE_PROG = [(48, [60, 64, 67]), (45, [60, 64, 69]), (41, [60, 65, 69]), (43, [59, 62, 67])]  # C-Am-F-G
CUTE_MELODY_A = [  # (拍, MIDI, 長さ[拍]) 4小節。裏拍はスウィングでぴょこぴょこ
    (0, 79, .5), (.5, 76, .5), (1, 79, .5), (1.5, 84, 1), (3, 81, .5), (3.5, 79, .5),
    (4, 76, .5), (4.5, 72, .5), (5, 76, .5), (5.5, 81, 1), (7, 79, 1),
    (8, 77, .5), (8.5, 81, .5), (9, 84, .5), (9.5, 81, .5), (10, 77, 1), (11, 76, .5), (11.5, 74, .5),
    (12, 74, .5), (12.5, 79, .5), (13, 83, .5), (13.5, 86, .5), (14, 84, 2),
]
CUTE_MELODY_B = CUTE_MELODY_A[:-4] + [(12, 74, .5), (12.5, 76, .5), (13, 79, 1), (14, 72, 2)]
SWING = 0.17   # 裏拍の遅れ（拍の割合）


def swung(beat_pos):
    return beat_pos + (SWING if abs(beat_pos % 1 - 0.5) < 1e-6 else 0)


def music_box(m, dur):
    """オルゴール／グロッケン風。高い倍音が速く減衰する。"""
    t = tt(min(dur, 0.6) + 0.9)
    f = midi_hz(m)
    x = (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.7)
         + 0.45 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t / 0.12)
         + 0.2 * np.sin(2 * np.pi * 5.4 * f * t) * np.exp(-t / 0.05))
    return x * np.minimum(t / 0.002, 1) * 0.2


def uke(m, dur):
    """ウクレレ風のはじく音。"""
    t = tt(dur + 0.2)
    f = midi_hz(m)
    x = sum(np.sin(2 * np.pi * k * f * t) * np.exp(-t * (6 + 5 * k)) / k for k in range(1, 6))
    return x * np.minimum(t / 0.003, 1) * 0.11


def boing(m, dur):
    """ぽよんと跳ねるベース（ピッチが少し下がる）。"""
    t = tt(dur)
    f = midi_hz(m) * (1 + 0.25 * np.exp(-t / 0.02))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return x * env(len(t), 0.004, dur * 0.5) * 0.5


def snap():
    t = tt(0.12)
    x = highpass(rng.standard_normal(len(t)), 2500) * np.exp(-t / 0.015)
    return x * 0.3


def shaker():
    t = tt(0.07)
    return highpass(rng.standard_normal(len(t)), 6000) * env(len(t), 0.01, 0.02) * 0.12


def soft_kick():
    t = tt(0.25)
    f = 60 + 60 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.002, 0.08) * 0.6


def compose_cute(dur, bpm=112):
    beat = 60 / bpm
    bar_len = 4 * beat
    tr = Track(dur)
    for bar in range(int(np.ceil(dur / bar_len))):
        t0 = bar * bar_len
        root, chord = CUTE_PROG[bar % 4]
        intro = bar < 2
        sec = (bar - 2) // 8 if not intro else -1
        melody_on = not intro and sec % 2 == 0        # メロディ8小節 → 伴奏+合いの手8小節

        def at(b):
            return t0 + swung(b) * beat

        # リズム（はねる 8 分）
        if not intro:
            for b in (0, 2):
                tr.put(soft_kick(), at(b))
            for b in (1, 3):
                tr.put(snap(), at(b), pan=0.2)
            for e in range(8):
                tr.put(shaker(), at(e / 2), pan=-0.4, gain=1.0 if e % 2 else 0.6)

        # ベース: 1・3 拍目にぽよん、裏でオクターブ上
        if not intro:
            for b, iv in ((0, 0), (1.5, 12), (2, 7), (3.5, 12)):
                tr.put(boing(root - 12 + iv, beat * 0.45), at(b))

        # ウクレレ: ジャ・カ・ジャカ のストローク
        for b in ((0, 1, 1.5, 2.5, 3) if not intro else (0, 2)):
            for k, m in enumerate(chord + [chord[0] + 12]):
                tr.put(uke(m, beat * 0.8), at(b) + k * 0.012, pan=0.35)

        # オルゴールのメロディ
        if melody_on:
            phrase = CUTE_MELODY_B if ((bar - 2) // 4) % 2 else CUTE_MELODY_A
            part = (bar - 2) % 4
            for st, m, d in phrase:
                if part * 4 <= st < part * 4 + 4:
                    tr.put(music_box(m, d * beat), t0 + swung(st - part * 4) * beat, pan=-0.1)
        elif not intro:
            # 合いの手: キラキラした分散和音
            for k, b in enumerate((0.5, 1.5, 2.5, 3.5)):
                tr.put(music_box(chord[k % 3] + 24 - (12 if k == 3 else 0), beat / 2), at(b), gain=0.6, pan=0.3)
        else:
            for k, m in enumerate(chord):
                tr.put(music_box(m + 24, beat), t0 + k * beat / 3, gain=0.7)
    return tr.buf


STYLES = {"rock": compose_rock, "pop": compose_pop, "cute": compose_cute}


# ======================================================================
def master(x, dur, fade_out=3.0):
    x = x[: int(dur * SR)]
    x = np.tanh(x * 1.1)
    x /= np.max(np.abs(x)) + 1e-9
    fi, fo = int(0.3 * SR), int(fade_out * SR)
    x[:fi] *= np.linspace(0, 1, fi)[:, None]
    x[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return x


def video_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                        str(path)], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("--style", choices=STYLES, default="rock")
    ap.add_argument("--bgm-volume", type=float, default=0.35)
    ap.add_argument("--events", type=Path, help="効果音タイミングの JSON（省略時はシーン名から推定）")
    ap.add_argument("-o", "--output", type=Path)
    args = ap.parse_args()

    dur = video_duration(args.video)
    n = int(dur * SR)

    bgm = master(STYLES[args.style](dur), dur) * args.bgm_volume

    ev_path = args.events or EVENT_DIR / f"{args.video.stem}.json"
    events = json.loads(ev_path.read_text()) if ev_path.exists() else []
    sfx, spans = render_sfx(events, dur)
    bgm *= duck_curve(n, spans)[:, None]

    mix = bgm + sfx[:n]
    peak = np.max(np.abs(mix))
    if peak > 0.98:
        mix *= 0.98 / peak
    print(f"効果音 {len(events)} 個 ({ev_path.name if events else 'なし'}), BGM={args.style}, 長さ {dur:.2f}s")

    out = args.output or args.video.with_name(args.video.stem + "_audio.mp4")
    with tempfile.TemporaryDirectory() as d:
        wav = Path(d) / "mix.wav"
        wavfile.write(wav, SR, (mix * 32767).astype(np.int16))
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-i", str(args.video), "-i", str(wav),
             "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
             "-t", f"{dur:.3f}", str(out)],
            check=True,
        )
    print(out)


if __name__ == "__main__":
    main()
