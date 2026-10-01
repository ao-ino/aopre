"""問題257: 6本の平行線と、それらに交わる7本の平行線でできる平行四辺形の個数。

流れ:
  1. 実験: 横3本・縦4本で、小さい順・左上から（横優先）に 1 つずつ数える
  2. 大きさごとの個数を表にしてパターンを見つける  → 横の場所 × 縦の場所
  3. パターンで本番（横6本・縦7本）を解く        → 21 × 15 = 315
  4. 「もっと簡単にできない？」 → 縦2本・横2本を選べば決まる → 7C2 × 6C2
  5. 縦20本・横30本でも一発                      → 20C2 × 30C2 = 82650
"""
from manim import *

from common import jp
from sfx import SfxMixin

H_COLOR = BLUE      # 横の線
S_COLOR = GREEN     # 縦（斜め）の線
PICK = YELLOW
H_POS = ORANGE      # 横に置ける場所の数
V_POS = TEAL        # 縦に置ける場所の数
T2C = {"横": H_COLOR, "縦": S_COLOR}

SLANT = 0.4
GRID_CENTER = (-2.8, -0.3)
PANEL_X = 4.0


def tj(text, size=26, **kw):
    """「横」「縦」を色付けした日本語テキスト。"""
    kw.setdefault("t2c", T2C)
    return jp(text, font_size=size, **kw)


class Grid(VGroup):
    """横線 n_h 本（上から 0,1,..）と、縦（斜め）線 n_s 本（左から 0,1,..）。"""

    def __init__(self, n_h, n_s, w, h, stroke=4, ext=0.45, **kwargs):
        super().__init__(**kwargs)
        cx, cy = GRID_CENTER
        self.n_h, self.n_s, self.cy = n_h, n_s, cy
        self.ys = [cy + h / 2 - h * i / (n_h - 1) for i in range(n_h)]
        self.cs = [cx - w / 2 + w * j / (n_s - 1) for j in range(n_s)]
        self.h_lines = VGroup(*[
            Line(self.pt(i, 0) + LEFT * ext, self.pt(i, n_s - 1) + RIGHT * ext,
                 color=H_COLOR, stroke_width=stroke)
            for i in range(n_h)
        ])
        d = np.array([SLANT, 1, 0]) / np.hypot(SLANT, 1)
        self.s_lines = VGroup(*[
            Line(self.pt(n_h - 1, j) - d * ext, self.pt(0, j) + d * ext,
                 color=S_COLOR, stroke_width=stroke)
            for j in range(n_s)
        ])
        self.add(self.h_lines, self.s_lines)

    def pt(self, i, j):
        y = self.ys[i]
        return np.array([self.cs[j] + SLANT * (y - self.cy), y, 0])

    def para(self, i1, i2, j1, j2, opacity=0.45, stroke=5):
        return Polygon(self.pt(i1, j1), self.pt(i1, j2), self.pt(i2, j2), self.pt(i2, j1),
                       color=PICK, fill_color=PICK, fill_opacity=opacity, stroke_width=stroke)

    def block(self, r, c, w, h, **kw):
        """左上のマスが (行 r, 列 c) で、横 w マス × 縦 h マスの平行四辺形。"""
        return self.para(r, r + h, c, c + w, **kw)

    def labels(self, size=24):
        hl = tj(f"横 {self.n_h}本", size).rotate(PI / 2).next_to(self.h_lines, LEFT, buff=0.15)
        sl = tj(f"縦 {self.n_s}本", size).next_to(self.s_lines, DOWN, buff=0.1)
        return VGroup(hl, sl)


def size_icon(w, h, s=0.2):
    """横 w × 縦 h マスの小さなアイコン。"""
    def p(c, r):
        return np.array([c * s - SLANT * r * s, -r * s, 0])
    return VGroup(*[
        Polygon(p(c, r), p(c + 1, r), p(c + 1, r + 1), p(c, r + 1),
                color=PICK, fill_color=PICK, fill_opacity=0.5, stroke_width=1.5)
        for r in range(h) for c in range(w)
    ])


class Problem257(SfxMixin, Scene):
    def construct(self):
        self.intro()
        self.experiment()
        self.find_pattern()
        self.solve_with_pattern()
        self.easier_way()
        self.big_case()

    def lagged_fade_in(self, mobs, lag_ratio, run_time=2):
        """順に FadeIn する LaggedStart。1つ出るごとにポンと鳴らす。"""
        n = len(mobs)
        d = run_time / (1 + lag_ratio * (n - 1))
        for k in range(n):
            self.sfx("pop", offset=k * lag_ratio * d, step=k % 8, gain_db=-5)  # ド〜高いドを繰り返す
        return LaggedStart(*[FadeIn(x, rate_func=rush_from) for x in mobs], lag_ratio=lag_ratio)

    def clear_panel(self, *keep):
        """タイトルと keep 以外の右側パネルを消す。"""
        # 線は Create で個別にシーンへ追加されるので、keep の子孫もまとめて残す
        keep_family = set()
        for k in (self.title, *keep):
            keep_family.update(k.get_family())
        mobs = [m for m in self.mobjects if m not in keep_family]
        if mobs:
            self.play(*[FadeOut(m) for m in mobs])

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
        self.wait(2.5)
        self.title = jp("257  平行四辺形はいくつ？", font_size=32).to_edge(UP, buff=0.3)
        self.play(ReplacementTransform(header, self.title))

    # ------------------------------------------------------------------
    def experiment(self):
        g = Grid(3, 4, w=3.6, h=2.8)
        self.grid = g
        head = tj("まずは 横3本・縦4本 で実験！", 26).move_to([PANEL_X, 2.6, 0])
        self.play(Write(head))
        self.play(LaggedStart(*[Create(l) for l in g.h_lines], lag_ratio=0.3))
        self.play(LaggedStart(*[Create(l) for l in g.s_lines], lag_ratio=0.3))
        self.grid_labels = g.labels()
        self.play(FadeIn(self.grid_labels))
        cap = jp("小さい順に、左上から 1つずつ数える", font_size=22, color=GRAY_A)
        cap.next_to(head, DOWN, buff=0.2)
        self.play(FadeIn(cap))

        cols, rows = g.n_s - 1, g.n_h - 1   # マスは 横3 × 縦2
        sizes = sorted(
            [(w, h) for h in range(1, rows + 1) for w in range(1, cols + 1)],
            key=lambda wh: (wh[0] * wh[1], wh[1]),
        )
        self.counts = {}
        total = 0
        for k, (w, h) in enumerate(sizes):
            y = 1.35 - k * 0.55
            icon = size_icon(w, h).move_to([PANEL_X - 1.9, y, 0])
            label = VGroup(MathTex(rf"{w}\times{h}", font_size=34), jp("のもの", font_size=24))
            label.arrange(RIGHT, buff=0.15).move_to([PANEL_X - 1.2, y, 0], aligned_edge=LEFT)
            counter = Integer(0, font_size=38, color=PICK).move_to([PANEL_X + 1.35, y, 0])
            unit = jp("個", font_size=24).next_to(counter, RIGHT, buff=0.15)
            self.play(FadeIn(icon, label, counter, unit), run_time=0.6)

            n = 0
            for r in range(rows - h + 1):          # 上から
                for c in range(cols - w + 1):      # 左から（横優先）
                    n += 1
                    para = g.block(r, c, w, h)
                    counter.set_value(n)
                    unit.next_to(counter, RIGHT, buff=0.15)
                    self.sfx("pop", step=n - 1)
                    # 音と同時に見えるよう、出だしを速くする（rush_from）
                    self.play(FadeIn(para, rate_func=rush_from), Indicate(counter, scale_factor=1.4), run_time=0.6)
                    self.wait(0.45)
                    self.play(FadeOut(para), run_time=0.4)
            total += n
            self.counts[(w, h)] = counter
            self.wait(0.4)

        tot = VGroup(jp("合計", font_size=26), Integer(total, font_size=40, color=PICK), jp("個", font_size=26))
        tot.arrange(RIGHT, buff=0.2).move_to([PANEL_X, 1.35 - len(sizes) * 0.55 - 0.15, 0])
        line = Line(LEFT, RIGHT, color=GRAY).set_width(4).next_to(tot, UP, buff=0.12)
        self.sfx("chime", gain_db=-4)
        self.play(Create(line), FadeIn(tot))
        self.wait(1.5)
        self.exp_total = total

    # ------------------------------------------------------------------
    def find_pattern(self):
        g = self.grid
        cols, rows = g.n_s - 1, g.n_h - 1
        counters = self.counts
        self.clear_panel(g, self.grid_labels, *counters.values())

        head = jp("大きさごとに並べると…？", font_size=26).move_to([PANEL_X, 2.6, 0])
        self.play(Write(head))

        col_x = [3.75 + 1.0 * k for k in range(cols)]
        row_y = [0.55 - 0.85 * k for k in range(rows)]
        col_head = VGroup(*[tj(f"横{w}", 22).move_to([col_x[w - 1], 1.25, 0]) for w in range(1, cols + 1)])
        row_head = VGroup(*[tj(f"縦{h}", 22).move_to([2.85, row_y[h - 1], 0]) for h in range(1, rows + 1)])
        self.play(FadeIn(col_head, row_head))
        self.play(*[
            counters[(w, h)].animate.move_to([col_x[w - 1], row_y[h - 1], 0])
            for (w, h) in counters
        ], run_time=1.5)
        self.wait(1)

        # 横の場所の数・縦の場所の数
        col_f = VGroup(*[MathTex(str(cols - w + 1), color=H_POS).move_to([col_x[w - 1], 1.85, 0])
                         for w in range(1, cols + 1)])
        row_f = VGroup(*[MathTex(str(rows - h + 1), color=V_POS).move_to([2.15, row_y[h - 1], 0])
                         for h in range(1, rows + 1)])
        why = jp("各数 = 横に置ける場所 × 縦に置ける場所", font_size=22,
                 t2c={"横に置ける場所": H_POS, "縦に置ける場所": V_POS})
        why.move_to([PANEL_X, row_y[-1] - 0.85, 0])
        self.play(FadeIn(col_f, shift=DOWN * 0.2), FadeIn(row_f, shift=RIGHT * 0.2))
        self.play(FadeIn(why))

        # 例: 1×1 は 横3か所 × 縦2か所 → グリッドでも見せる
        cells = VGroup(*[g.block(r, c, 1, 1, opacity=0.4, stroke=3) for r in range(rows) for c in range(cols)])
        self.play(Indicate(col_f[0]), Indicate(row_f[0]), Indicate(counters[(1, 1)]),
                  self.lagged_fade_in(cells, lag_ratio=0.15), run_time=2)
        self.play(FadeOut(cells))
        for (w, h) in [(2, 1), (2, 2)]:
            self.play(Indicate(col_f[w - 1]), Indicate(row_f[h - 1]), Indicate(counters[(w, h)]), run_time=1.2)

        hs = "+".join(str(cols - w + 1) for w in range(1, cols + 1))
        vs = "+".join(str(rows - h + 1) for h in range(1, rows + 1))
        f = MathTex("(", hs, r")\times(", vs, ")", f"= {self.exp_total}", font_size=40)
        f[1].set_color(H_POS)
        f[3].set_color(V_POS)
        f.next_to(why, DOWN, buff=0.4)
        lab = jp("合計", font_size=26).next_to(f, LEFT, buff=0.2)
        VGroup(lab, f).set_x(PANEL_X)
        self.play(FadeIn(lab), Write(f))
        ok = jp("数えた結果と一致！", font_size=22, color=PICK).next_to(f, DOWN, buff=0.2)
        self.sfx("chime")
        self.play(FadeIn(ok))
        self.wait(2.5)

    # ------------------------------------------------------------------
    def solve_with_pattern(self):
        self.clear_panel()
        g = Grid(6, 7, w=4.6, h=4.4)
        self.grid = g
        head = tj("本番： 横6本・縦7本", 28).move_to([PANEL_X, 2.6, 0])
        self.play(Write(head))
        self.play(LaggedStart(*[Create(l) for l in g.h_lines], lag_ratio=0.12),
                  LaggedStart(*[Create(l) for l in g.s_lines], lag_ratio=0.12), run_time=2)
        self.grid_labels = g.labels()
        self.play(FadeIn(self.grid_labels))
        sub = jp("マスは 横6 × 縦5", font_size=24).next_to(head, DOWN, buff=0.25)
        self.play(FadeIn(sub))

        cells = VGroup(*[g.block(r, c, 1, 1, opacity=0.4, stroke=3) for r in range(5) for c in range(6)])
        one = VGroup(MathTex(r"1\times1", font_size=34), jp("だけで", font_size=24),
                     MathTex(r"6\times5=30", font_size=34), jp("個", font_size=24)).arrange(RIGHT, buff=0.15)
        one.next_to(sub, DOWN, buff=0.35)
        self.play(self.lagged_fade_in(cells, lag_ratio=0.25, run_time=5), FadeIn(one), run_time=5)
        self.wait(0.8)
        self.play(FadeOut(cells))

        h_row = VGroup(jp("横の場所", font_size=24, color=H_POS),
                       MathTex(r"6+5+4+3+2+1 = 21", font_size=32)).arrange(RIGHT, buff=0.3)
        v_row = VGroup(jp("縦の場所", font_size=24, color=V_POS),
                       MathTex(r"5+4+3+2+1 = 15", font_size=32)).arrange(RIGHT, buff=0.3)
        prod = MathTex(r"21 \times 15 = 315", font_size=48)
        VGroup(h_row, v_row).arrange(DOWN, aligned_edge=LEFT, buff=0.3).next_to(one, DOWN, buff=0.45).set_x(PANEL_X)
        prod.next_to(v_row, DOWN, buff=0.4).set_x(PANEL_X)
        self.play(FadeIn(h_row))
        self.play(FadeIn(v_row))
        self.play(Write(prod))

        answer = jp("答  315 個", font_size=38, color=PICK, weight=BOLD)
        box = SurroundingRectangle(answer, color=PICK, buff=0.2)
        VGroup(answer, box).next_to(prod, DOWN, buff=0.35).set_x(PANEL_X)
        self.sfx("chime")
        self.play(Write(answer), Create(box))
        self.wait(2.5)

    # ------------------------------------------------------------------
    def show_choice(self, g, i1, i2, j1, j2, hold=1.0, width=8):
        lines = VGroup(g.h_lines[i1], g.h_lines[i2], g.s_lines[j1], g.s_lines[j2])
        old = [l.get_stroke_width() for l in lines]
        para = g.para(i1, i2, j1, j2, stroke=0)
        self.play(lines.animate.set_stroke(PICK, width=width), run_time=0.6)
        self.choice_n = getattr(self, "choice_n", 0) + 1
        self.sfx("pop", step=self.choice_n - 1)
        self.play(FadeIn(para, rate_func=rush_from), run_time=0.5)
        self.wait(hold)
        self.play(
            FadeOut(para),
            *[l.animate.set_stroke(H_COLOR, width=w) for l, w in zip(lines[:2], old[:2])],
            *[l.animate.set_stroke(S_COLOR, width=w) for l, w in zip(lines[2:], old[2:])],
            run_time=0.5,
        )

    def easier_way(self):
        g = self.grid
        self.clear_panel(g, self.grid_labels)

        q = jp("これ、もっと簡単にできない？", font_size=30, color=PICK).move_to([PANEL_X, 2.4, 0])
        self.play(Write(q))
        self.wait(1.5)

        idea = VGroup(
            tj("平行四辺形は", 26),
            tj("縦の線 2本 と 横の線 2本", 28),
            tj("を選べば 1つに決まる！", 26),
        ).arrange(DOWN, buff=0.15).next_to(q, DOWN, buff=0.45)
        self.play(FadeIn(idea[0]))
        self.show_choice(g, 1, 4, 1, 3, hold=0.3)
        self.play(FadeIn(idea[1]), FadeIn(idea[2]))
        self.show_choice(g, 0, 2, 2, 6, hold=0.6)
        self.show_choice(g, 3, 5, 0, 4, hold=0.6)

        s_row = VGroup(tj("縦7本から2本", 24), MathTex(r"{}_7\mathrm{C}_2 = 21", font_size=38)).arrange(RIGHT, buff=0.3)
        same = jp("（さっきの 6+5+4+3+2+1 と同じ！）", font_size=20, color=GRAY_A)
        h_row = VGroup(tj("横6本から2本", 24), MathTex(r"{}_6\mathrm{C}_2 = 15", font_size=38)).arrange(RIGHT, buff=0.3)
        prod = MathTex(r"{}_7\mathrm{C}_2 \times {}_6\mathrm{C}_2 = 21 \times 15 = 315", font_size=40, color=PICK)
        grp = VGroup(s_row, same, h_row, prod).arrange(DOWN, buff=0.25).next_to(idea, DOWN, buff=0.4).set_x(PANEL_X)
        self.play(g.s_lines.animate.set_stroke(width=7))
        self.play(FadeIn(s_row))
        self.play(g.s_lines.animate.set_stroke(width=4), FadeIn(same))
        self.play(g.h_lines.animate.set_stroke(width=7))
        self.play(FadeIn(h_row))
        self.play(g.h_lines.animate.set_stroke(width=4))
        self.sfx("chime")
        self.play(Write(prod))
        self.wait(2.5)

    # ------------------------------------------------------------------
    def big_case(self):
        self.clear_panel()
        g = Grid(30, 20, w=4.8, h=4.6, stroke=1.6, ext=0.3)
        head = tj("縦20本・横30本 だったら？", 30).move_to([PANEL_X, 2.5, 0])
        self.play(Write(head))
        self.play(LaggedStart(*[Create(l) for l in g.h_lines], lag_ratio=0.05),
                  LaggedStart(*[Create(l) for l in g.s_lines], lag_ratio=0.05), run_time=2.5)
        self.play(FadeIn(g.labels(22)))
        hard = jp("1つずつ数えるのは無理…", font_size=22, color=GRAY_A).next_to(head, DOWN, buff=0.25)
        self.play(FadeIn(hard))
        self.show_choice(g, 4, 21, 3, 15, hold=0.4, width=4)
        self.show_choice(g, 10, 13, 8, 18, hold=0.4, width=4)

        calc = VGroup(
            MathTex(r"{}_{20}\mathrm{C}_2 \times {}_{30}\mathrm{C}_2", font_size=44),
            MathTex(r"= \frac{20\cdot19}{2} \times \frac{30\cdot29}{2}", font_size=40),
            MathTex(r"= 190 \times 435", font_size=40),
            MathTex(r"= 82650", font_size=52, color=PICK),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).next_to(hard, DOWN, buff=0.45).set_x(PANEL_X)
        for m in calc:
            self.play(Write(m), run_time=1.0)
        unit = jp("個", font_size=32, color=PICK).next_to(calc[-1], RIGHT, buff=0.15, aligned_edge=DOWN)
        self.play(FadeIn(unit))
        punch = jp("一発で解ける！", font_size=38, color=PICK, weight=BOLD).next_to(calc, DOWN, buff=0.45).set_x(PANEL_X)
        self.sfx("chime")
        self.play(Write(punch))
        self.play(Circumscribe(punch, color=PICK))
        self.wait(3)
