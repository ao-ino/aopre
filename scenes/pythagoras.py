"""三平方の定理: 各辺の上の正方形の面積で a^2 + b^2 = c^2 を見せる。"""
from manim import *

from common import jp


class Pythagoras(Scene):
    def construct(self):
        title = jp("三平方の定理").to_edge(UP)
        self.play(Write(title))

        a, b = 1.5, 2.0
        A = np.array([-2.5, -0.8, 0])
        B = A + RIGHT * b
        C = A + UP * a
        tri = Polygon(A, B, C, color=WHITE, fill_opacity=0.2)
        right_angle = RightAngle(Line(A, B), Line(A, C), length=0.25)

        la = MathTex("a").next_to(Line(A, C), LEFT, buff=0.1)
        lb = MathTex("b").next_to(Line(A, B), DOWN, buff=0.1)
        lc = MathTex("c").move_to((B + C) / 2 + 0.3 * (UP + RIGHT))

        self.play(Create(tri), Create(right_angle))
        self.play(FadeIn(la, lb, lc))

        def square_on(p, q, color):
            # 辺 pq の外側に正方形を作る
            v = q - p
            n = np.array([v[1], -v[0], 0])  # 時計回りに 90° 回した法線
            return Polygon(p, q, q + n, p + n, color=color, fill_opacity=0.5)

        sq_a = square_on(C, A, BLUE)
        sq_b = square_on(A, B, GREEN)
        sq_c = square_on(B, C, RED)

        for sq, sym in [(sq_a, "a^2"), (sq_b, "b^2"), (sq_c, "c^2")]:
            label = MathTex(sym).move_to(sq)
            self.play(DrawBorderThenFill(sq), FadeIn(label), run_time=1)

        formula = MathTex("a^2", "+", "b^2", "=", "c^2", font_size=60)
        formula[0].set_color(BLUE)
        formula[2].set_color(GREEN)
        formula[4].set_color(RED)
        formula.move_to(RIGHT * 3.5 + UP * 0.5)
        self.play(Write(formula))

        note = jp("直角三角形では、斜辺の正方形の面積 = 他の2辺の正方形の面積の和",
                  font_size=24).to_edge(DOWN)
        self.play(FadeIn(note, shift=UP))
        self.wait(2)
