"""単位円と sin: 円周上の点の高さが sin グラフを描く。"""
from manim import *

from common import jp


class SineFromCircle(Scene):
    def construct(self):
        title = jp("単位円から sin 波へ").to_edge(UP)
        self.add(title)

        origin = LEFT * 4.5
        circle = Circle(radius=1.2, color=WHITE).move_to(origin)
        # y=1 がちょうど円の半径 (1.2) になるように高さを合わせる
        axes = Axes(
            x_range=[0, TAU, PI / 2], y_range=[-1.2, 1.2, 1],
            x_length=7, y_length=2.4 * 1.2, tips=False,
        )
        axes.shift(origin + RIGHT * 2 - axes.c2p(0, 0))
        x_labels = VGroup(*[
            MathTex(s, font_size=28).next_to(axes.c2p(v, 0), DOWN)
            for v, s in [(PI / 2, r"\frac{\pi}{2}"), (PI, r"\pi"), (3 * PI / 2, r"\frac{3\pi}{2}"), (TAU, r"2\pi")]
        ])
        self.play(Create(circle), Create(axes), FadeIn(x_labels))

        theta = ValueTracker(0)
        r = circle.radius

        dot = always_redraw(
            lambda: Dot(origin + r * np.array([np.cos(theta.get_value()), np.sin(theta.get_value()), 0]), color=YELLOW)
        )
        radius = always_redraw(lambda: Line(origin, dot.get_center(), color=YELLOW))
        height = always_redraw(
            lambda: Line(
                np.array([dot.get_center()[0], origin[1], 0]), dot.get_center(), color=RED, stroke_width=6
            )
        )
        graph_dot = always_redraw(
            lambda: Dot(axes.c2p(theta.get_value(), np.sin(theta.get_value())), color=RED)
        )
        connector = always_redraw(
            lambda: DashedLine(dot.get_center(), graph_dot.get_center(), color=GRAY)
        )
        trace = TracedPath(graph_dot.get_center, stroke_color=RED, stroke_width=4)
        arc = always_redraw(
            lambda: Arc(radius=0.35, start_angle=0, angle=theta.get_value(), arc_center=origin, color=BLUE)
        )

        label = MathTex(r"y = \sin\theta", color=RED).to_edge(DOWN)
        self.add(trace)
        self.play(FadeIn(dot, radius, height, graph_dot, connector, arc), Write(label))
        self.play(theta.animate.set_value(TAU), run_time=8, rate_func=linear)
        self.wait(1)
