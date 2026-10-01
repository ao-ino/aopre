"""問題257: 6本の平行線と、それらに交わる7本の平行線でできる平行四辺形の個数。

流れ:
  1. 線の少ない状態 (横2・縦2 → 横2・縦3 → 横3・縦3) で実際に数える
  2. 「横から2本・縦から2本を選ぶと平行四辺形が1つ決まる」と気づく
  3. 横6本・縦7本に増やし、6C2 × 7C2 = 15 × 21 = 315
"""
from itertools import combinations

from manim import *

from common import jp

H_COLOR = BLUE
S_COLOR = GREEN
PICK = YELLOW
T2C = {"横": H_COLOR, "縦": S_COLOR}

N_H, N_S = 6, 7
SLANT = 0.4  # 縦（斜め）の線: x = c + SLANT * y
H_YS = [-2.4 + 0.85 * i for i in range(N_H)]
S_CS = [-4.6 + 0.7 * j for j in range(N_S)]
X_MIN, X_MAX = -6.0, 0.8
Y_MIN, Y_MAX = -2.8, 2.25
PANEL_X = 4.0


def point(i, j):
    """横線 i と縦線 j の交点。"""
    y = H_YS[i]
    return np.array([S_CS[j] + SLANT * y, y, 0])


def parallelogram(i1, i2, j1, j2, opacity=0.45):
    return Polygon(point(i1, j1), point(i1, j2), point(i2, j2), point(i2, j1),
                   color=PICK, fill_color=PICK, fill_opacity=opacity, stroke_width=5)


def make_h(i):
    return Line([X_MIN, H_YS[i], 0], [X_MAX, H_YS[i], 0], color=H_COLOR)


def make_s(j):
    c = S_CS[j]
    return Line([c + SLANT * Y_MIN, Y_MIN, 0], [c + SLANT * Y_MAX, Y_MAX, 0], color=S_COLOR)


def tj(text, size=26, **kw):
    """「横」「縦」を色付けした日本語テキスト。"""
    return jp(text, font_size=size, t2c=T2C, **kw)


class Problem257(Scene):
    def construct(self):
        self.h = {}  # 表示中の横線 index -> Line
        self.s = {}  # 表示中の縦線 index -> Line

        self.intro()
        self.count_small_cases()
        self.find_rule()
        self.full_case()

    # ------------------------------------------------------------------
    def intro(self):
        num = Text("257", font_size=48, weight=BOLD, color=H_COLOR)
        problem = VGroup(
            jp("6本の平行線と、それらに交わる7本の平行線とによって"),
            jp("できる平行四辺形は何個あるか。"),
        ).arrange(DOWN, aligned_edge=LEFT)
        header = VGroup(num, problem).arrange(RIGHT, buff=0.5)
        header.scale_to_fit_width(config.frame_width - 1)
        self.play(FadeIn(header, shift=UP))
        self.wait(2)
        self.title = jp("257  平行四辺形はいくつ？", font_size=32).to_edge(UP, buff=0.3)
        self.play(ReplacementTransform(header, self.title))

    # ------------------------------------------------------------------
    def add_lines(self, hs=(), ss=(), run_time=0.8):
        anims = []
        for i in hs:
            self.h[i] = make_h(i)
            anims.append(Create(self.h[i]))
        for j in ss:
            self.s[j] = make_s(j)
            anims.append(Create(self.s[j]))
        self.play(LaggedStart(*anims, lag_ratio=0.2), run_time=run_time)

    def count_all(self, counter, flash_time):
        """表示中の線でできる平行四辺形を1つずつ光らせて数える。"""
        k = 0
        for i1, i2 in combinations(sorted(self.h), 2):
            for j1, j2 in combinations(sorted(self.s), 2):
                k += 1
                para = parallelogram(i1, i2, j1, j2)
                counter.set_value(k)
                self.play(FadeIn(para), Indicate(counter, scale_factor=1.3), run_time=flash_time)
                self.play(FadeOut(para), run_time=flash_time * 0.6)
        return k

    def count_small_cases(self):
        head = tj("まずは線を少なくして数えてみよう", 26).move_to([PANEL_X, 2.5, 0])
        self.play(Write(head))

        self.rows = VGroup()
        cases = [  # (追加する横, 追加する縦)
            ((2, 3), (2, 3)),
            ((), (4,)),
            ((4,), ()),
        ]
        for idx, (hs, ss) in enumerate(cases):
            self.add_lines(hs, ss)
            label = tj(f"横{len(self.h)}本・縦{len(self.s)}本", 26)
            arrow = MathTex(r"\to")
            counter = Integer(0, font_size=40, color=PICK)
            unit = jp("個", font_size=26)
            row = VGroup(label, arrow, counter, unit).arrange(RIGHT, buff=0.2)
            row.move_to([PANEL_X, 1.5 - idx * 0.8, 0])
            self.play(FadeIn(label, arrow, counter, unit))
            self.count_all(counter, flash_time=0.6 if idx < 2 else 0.35)
            self.rows.add(row)
            self.wait(0.5)

        self.head = head

    # ------------------------------------------------------------------
    def find_rule(self):
        q = tj("1つの平行四辺形は、何で決まる？", 26).move_to([PANEL_X, -1.1, 0])
        self.play(Write(q))

        # 例の平行四辺形を作る 4 本の線を強調
        i1, i2, j1, j2 = 2, 4, 2, 4
        para = parallelogram(i1, i2, j1, j2)
        chosen = VGroup(self.h[i1], self.h[i2], self.s[j1], self.s[j2])
        self.play(FadeIn(para))
        self.play(chosen.animate.set_stroke(PICK, width=8))
        rule = VGroup(
            tj("横から 2本、縦から 2本 を選ぶ", 26),
            tj("→ 平行四辺形がちょうど 1つ決まる！", 26, color=PICK),
        ).arrange(DOWN, buff=0.2).next_to(q, DOWN, buff=0.3)
        rule[1].set_color_by_t2c(T2C)
        self.play(FadeIn(rule[0]))
        self.play(FadeIn(rule[1]))
        self.wait(1.5)
        self.play(
            FadeOut(para),
            *[self.h[i].animate.set_stroke(H_COLOR, width=4) for i in (i1, i2)],
            *[self.s[j].animate.set_stroke(S_COLOR, width=4) for j in (j1, j2)],
        )

        # 数えた個数を「選び方」で書き直す
        formulas = [
            r"{}_2\mathrm{C}_2 \times {}_2\mathrm{C}_2 = 1 \times 1",
            r"{}_2\mathrm{C}_2 \times {}_3\mathrm{C}_2 = 1 \times 3",
            r"{}_3\mathrm{C}_2 \times {}_3\mathrm{C}_2 = 3 \times 3",
        ]
        for row, tex in zip(self.rows, formulas):
            label, arrow, counter, unit = row
            new = MathTex(tex + f"= {counter.get_value()}", font_size=30)
            new.next_to(label, RIGHT, buff=0.25)
            old = VGroup(arrow, counter, unit)
            row.remove(arrow, counter, unit)
            self.play(FadeOut(old), run_time=0.4)
            self.play(FadeIn(new, shift=LEFT * 0.3), run_time=0.6)
            row.add(new)
        # はみ出さないようにまとめて中央へ
        self.play(self.rows.animate.arrange(DOWN, aligned_edge=LEFT, buff=0.35)
                  .scale_to_fit_width(min(self.rows.width, 5.4)).move_to([PANEL_X, 1.0, 0]))
        self.wait(2)
        self.play(FadeOut(self.rows, self.head, q, rule))

    # ------------------------------------------------------------------
    def full_case(self):
        head = tj("線を増やしても考え方は同じ！", 26).move_to([PANEL_X, 2.5, 0])
        self.play(Write(head))

        # 残りの線を少しずつ増やす
        for hs, ss in [((), (1,)), ((1,), ()), ((), (5,)), ((5,), ()), ((), (0,)), ((0,), ()), ((), (6,))]:
            self.add_lines(hs, ss, run_time=0.5)
            # 増えるたびに平行四辺形を1つ光らせる
            i1, i2 = sorted(self.h)[0], sorted(self.h)[-1]
            j1, j2 = sorted(self.s)[0], sorted(self.s)[-1]
            para = parallelogram(i1, i2, j1, j2, opacity=0.25)
            self.play(FadeIn(para), run_time=0.25)
            self.play(FadeOut(para), run_time=0.25)

        h_lines = VGroup(*[self.h[i] for i in sorted(self.h)])
        s_lines = VGroup(*[self.s[j] for j in sorted(self.s)])
        h_label = tj("横 6本", 26).rotate(PI / 2).next_to(h_lines, LEFT, buff=0.15)
        s_label = tj("縦 7本", 26).next_to(s_lines, DOWN, buff=0.1)
        self.play(FadeIn(h_label, s_label))

        h_row = VGroup(
            tj("横 6本から 2本", 26),
            MathTex(r"{}_6\mathrm{C}_2 = \frac{6\cdot 5}{2\cdot 1} = 15", font_size=36),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        s_row = VGroup(
            tj("縦 7本から 2本", 26),
            MathTex(r"{}_7\mathrm{C}_2 = \frac{7\cdot 6}{2\cdot 1} = 21", font_size=36),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        prod_row = VGroup(
            jp("独立に選べるので 積の法則", font_size=24),
            MathTex(r"15 \times 21 = 315", font_size=44),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        VGroup(h_row, s_row, prod_row).arrange(DOWN, aligned_edge=LEFT, buff=0.35) \
            .next_to(head, DOWN, buff=0.35).set_x(PANEL_X)

        self.play(h_lines.animate.set_stroke(width=7), Indicate(h_label))
        self.play(FadeIn(h_row))
        self.play(h_lines.animate.set_stroke(width=4))
        self.play(s_lines.animate.set_stroke(width=7), Indicate(s_label))
        self.play(FadeIn(s_row))
        self.play(s_lines.animate.set_stroke(width=4))
        self.play(FadeIn(prod_row[0]))
        self.play(Write(prod_row[1]))

        answer = jp("答  315 個", font_size=40, color=PICK, weight=BOLD)
        box = SurroundingRectangle(answer, color=PICK, buff=0.25)
        VGroup(answer, box).next_to(prod_row, DOWN, buff=0.35).set_x(PANEL_X)
        self.play(Write(answer), Create(box))

        for i1, i2, j1, j2 in [(0, 1, 0, 1), (0, 5, 0, 6), (2, 4, 1, 5), (1, 2, 3, 6), (3, 5, 2, 4)]:
            para = parallelogram(i1, i2, j1, j2, opacity=0.35)
            self.play(FadeIn(para), run_time=0.35)
            self.play(FadeOut(para), run_time=0.35)
        self.wait(2)
