"""シーン共通の設定。"""
from manim import Text

JP_FONT = "IPAexGothic"


def jp(text: str, **kwargs) -> Text:
    """日本語テキストを作る（フォント指定済み）。"""
    kwargs.setdefault("font", JP_FONT)
    kwargs.setdefault("font_size", 36)
    return Text(text, **kwargs)
