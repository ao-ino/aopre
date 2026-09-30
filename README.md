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
