# aopre — Manim で数学をビジュアルに解説する

[Manim Community](https://www.manim.community/) を使って、数学の解説アニメーションを作るための環境です。

## セットアップ

```bash
./setup.sh               # apt で依存（Cairo/Pango, ffmpeg, LaTeX, 日本語フォント）+ .venv に manim
source .venv/bin/activate
```

Claude Code on the web では、`.claude/settings.json` の SessionStart フックが
セッション開始時に `setup.sh` を自動実行します。

## レンダリング

```bash
manim -pql scenes/pythagoras.py Pythagoras   # 低画質でプレビュー（-p で再生）
manim -qh  scenes/pythagoras.py Pythagoras   # 1080p で書き出し
manim -s   scenes/derivative.py SecantToTangent  # 最後のフレームだけ PNG で
```

出力は `media/videos/<ファイル名>/<画質>/<シーン名>.mp4` に保存されます。

## サンプルシーン

| ファイル | シーン | 内容 |
|---|---|---|
| `scenes/pythagoras.py` | `Pythagoras` | 三平方の定理を各辺の正方形の面積で見せる |
| `scenes/derivative.py` | `SecantToTangent` | 割線が接線に近づき、微分係数になる様子 |
| `scenes/unit_circle.py` | `SineFromCircle` | 単位円上の点の高さが sin 波を描く |
| `scenes/p257_parallelograms.py` | `Problem257` | 問題257: 平行線でできる平行四辺形の個数（6C2 × 7C2 = 315） |

## 新しいシーンの書き方

```python
from manim import *
from common import jp   # 日本語テキスト（IPAexGothic）

class MyScene(Scene):
    def construct(self):
        self.play(Write(jp("タイトル").to_edge(UP)))
        self.play(Write(MathTex(r"e^{i\pi} + 1 = 0")))
        self.wait()
```

- 日本語の文章は `jp("...")`（= `Text`）、数式は `MathTex(r"...")`（LaTeX）で書く
- 値を動かしながら図を更新するなら `ValueTracker` + `always_redraw`（`derivative.py` 参照）

## BGM と効果音を付ける

```bash
manim -qh scenes/p257_parallelograms.py Problem257                        # 映像 + 効果音タイミング(JSON)を出力
python tools/add_audio.py media/videos/p257_parallelograms/1080p60/Problem257.mp4   # → Problem257_audio.mp4
python tools/add_audio.py <動画> --style pop --bgm-volume 0.3             # BGM をポップに・音量調整
```

- BGM・効果音はすべてコードで合成したオリジナルなので、著作権を気にせず使えます。
  - `rock`（既定）: 140 BPM、Am–F–C–G。歪みギター（左右）・ベース・ドラム、サビにリードギター
  - `pop`: 118 BPM、C–G–Am–F。エレピ・ベル系メロディ
- 効果音が鳴る瞬間だけ BGM を少し下げる（ダッキング）ので、効果音が埋もれません。

### シーンで効果音を鳴らす

```python
from sfx import SfxMixin

class MyScene(SfxMixin, Scene):
    def construct(self):
        self.sfx("pop", step=3)   # 次のアニメーション開始時に「ポン」（step が大きいほど高い）
        self.play(FadeIn(shape, rate_func=rush_from))
        self.sfx("chime")         # 「キラーン」
        self.play(Write(answer))
```

manim の `add_sound` は使いません（キャッシュ済みアニメーションの直後だと音が消え、
音声トラックも映像から少しずつずれるため）。`self.sfx` は映像フレーム基準の時刻を
`media/audio_events/<Scene>.json` に記録し、`tools/add_audio.py` がサンプル単位で配置します。
そのため `manim.cfg` でキャッシュを無効にしています。
