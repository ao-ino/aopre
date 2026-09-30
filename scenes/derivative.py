"""微分: 割線が接線に近づく様子で f'(x) の意味を見せる。"""
from manim import *

from common import jp


class SecantToTangent(Scene):
    def construct(self):
        title = jp("微分 = 接線の傾き").to_edge(UP)
        self.play(Write(title))

        axes = Axes(
            x_range=[-1, 4, 1], y_range=[-1, 9, 2],
            x_length=6, y_length=5, tips=False,
        ).to_edge(LEFT).shift(DOWN * 0.5)
        f = lambda x: 0.5 * x**2 + 0.5
        graph = axes.plot(f, x_range=[-1, 4], color=BLUE)
        graph_label = MathTex("f(x) = \\tfrac{1}{2}x^2 + \\tfrac{1}{2}", color=BLUE, font_size=36)
        graph_label.next_to(axes.c2p(1.5, 8), RIGHT)
        self.play(Create(axes), Create(graph), FadeIn(graph_label))

        x0 = 1.0
        h = ValueTracker(2.0)

        p = Dot(color=YELLOW).move_to(axes.c2p(x0, f(x0)))
        q = always_redraw(
            lambda: Dot(color=ORANGE).move_to(axes.c2p(x0 + h.get_value(), f(x0 + h.get_value())))
        )

        def secant():
            x1 = x0 + h.get_value()
            slope = (f(x1) - f(x0)) / (x1 - x0)
            line = lambda x: f(x0) + slope * (x - x0)
            return axes.plot(line, x_range=[-1, 4], color=ORANGE).set_z_index(-1)

        sec = always_redraw(secant)
        self.play(FadeIn(p, q), Create(sec))

        slope_tex = always_redraw(
            lambda: MathTex(
                r"\frac{f(x+h)-f(x)}{h} = " + f"{(f(x0 + h.get_value()) - f(x0)) / h.get_value():.2f}",
                font_size=40,
            ).move_to(RIGHT * 3.3 + UP * 1.5)
        )
        h_tex = always_redraw(
            lambda: MathTex(f"h = {h.get_value():.2f}", font_size=40).next_to(slope_tex, DOWN, aligned_edge=LEFT)
        )
        self.play(FadeIn(slope_tex, h_tex))

        self.play(h.animate.set_value(0.01), run_time=4, rate_func=smooth)
        self.wait(0.5)

        result = MathTex(r"f'(1) = \lim_{h\to 0}\frac{f(1+h)-f(1)}{h} = 1", color=YELLOW, font_size=40)
        result.move_to(RIGHT * 3.3 + DOWN * 1.5)
        self.play(Write(result))
        self.wait(2)
