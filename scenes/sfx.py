"""効果音（コードで合成）。初回呼び出し時に media/sfx/ に WAV を書き出す。

    from sfx import pop, chime
    self.add_sound(pop(3))   # 3 段目の高さのポン
"""
from pathlib import Path

import numpy as np
from scipy.io import wavfile

SR = 44100
OUT = Path(__file__).resolve().parent.parent / "media" / "sfx"
PENTA = [0, 2, 4, 7, 9]  # C メジャーペンタトニック


def _write(name, x):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.wav"
    if not path.exists():
        x = x / (np.max(np.abs(x)) + 1e-9) * 0.8
        wavfile.write(path, SR, (x * 32767).astype(np.int16))
    return str(path)


def _note(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pop(step=0):
    """「ポン」。step が大きいほど高い音（ペンタトニックで上がる）。"""
    step = int(step) % 15
    m = 72 + 12 * (step // 5) + PENTA[step % 5]
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    f0 = _note(m)
    freq = f0 * (0.6 + 0.4 * np.minimum(t / 0.015, 1))  # 一瞬下からしゃくり上げる
    phase = 2 * np.pi * np.cumsum(freq) / SR
    x = (np.sin(phase) + 0.3 * np.sin(2 * phase)) * np.exp(-t / 0.05)
    x *= np.minimum(t / 0.002, 1)
    return _write(f"pop_{step}", x)


def chime():
    """正解の「キラーン」。上昇アルペジオ + きらめき。"""
    dur = 1.6
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, m in enumerate([72, 76, 79, 84, 88]):
        s = int(k * 0.06 * SR)
        tt = t[: n - s]
        f = _note(m)
        x[s:] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 3 * f * tt)) * np.exp(-tt / 0.5)
    return _write("chime", x)


def tick():
    """表の数字が動くときなどの軽い「コッ」。"""
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 1800 * t) * np.exp(-t / 0.008)
    return _write("tick", x)
