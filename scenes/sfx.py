"""効果音のタイミングを記録するミックスイン。

manim の add_sound はキャッシュ済みアニメーションの直後だと無視され、
音声トラックも映像と少しずつずれるため使わない。代わりに
「映像の何秒目に何を鳴らすか」を JSON に書き出し、
tools/add_audio.py がサンプル単位で正確に合成する。

    class MyScene(SfxMixin, Scene):
        def construct(self):
            self.sfx("pop", step=3)     # ポン（step が大きいほど高い）
            self.sfx("chime")           # キラーン
"""
import json
from pathlib import Path

from manim import config

EVENT_DIR = Path(__file__).resolve().parent.parent / "media" / "audio_events"


class SfxMixin:
    def sfx(self, name, offset=0.0, gain_db=0.0, **params):
        """次のアニメーション開始時（+offset 秒）に効果音を鳴らす。"""
        if not hasattr(self, "_sfx_events"):
            self._sfx_events = []
        # renderer.time = これまでに書き出したフレーム数 / fps（キャッシュ無効時）
        t = self.renderer.time + offset
        self._sfx_events.append({"t": round(t, 4), "name": name, "gain_db": gain_db, **params})

    def tear_down(self):
        super().tear_down()
        EVENT_DIR.mkdir(parents=True, exist_ok=True)
        name = config.output_file or type(self).__name__
        path = EVENT_DIR / f"{Path(name).stem}.json"
        path.write_text(json.dumps(getattr(self, "_sfx_events", []), indent=1))
