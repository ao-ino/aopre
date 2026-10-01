"""問題96-4（流水算）: A,B 間 30km、上り 6 時間・下り 4 時間。川の流れの速さは？

流れ:
  1. 船が A→B（上り）を 6 時間、B→A（下り）を 4 時間で進む様子。1 時間ごとに印を残す
     → 上りは 1 時間に 5km、下りは 7.5km
  2. 「なぜ速さが違う？」 船の速さと流れの速さを矢印で
     下り = 船 + 流れ、上り = 船 − 流れ
  3. 線分図: 下りと上りの差 = 流れ 2 つ分 → 2.5 ÷ 2 = 1.25
  答: 時速 1.25km（静水時の船の速さは 6.25km）
"""
from manim import *

from common import jp
from sfx import SfxMixin

UP_C = RED_C        # 上り
DOWN_C = GREEN_C    # 下り
BOAT_C = BLUE_B     # 船の速さ（静水時）
FLOW_C = ORANGE     # 流れの速さ
PICK = YELLOW
T2C = {"上り": UP_C, "下り": DOWN_C, "流れ": FLOW_C, "船": BOAT_C}

DIST = 30
UP_H, DOWN_H = 6, 4
V_UP, V_DOWN = DIST / UP_H, DIST / DOWN_H          # 5, 7.5
V_FLOW = (V_DOWN - V_UP) / 2                        # 1.25
V_BOAT = V_UP + V_FLOW                              # 6.25

RIVER_Y = 1.3
X_A, X_B = -5.2, 5.2


def tj(text, size=28, **kw):
    kw.setdefault("t2c", T2C)
    return jp(text, font_size=size, **kw)


def x_at(km):
    """A から km の地点の x 座標。"""
    return X_A + (X_B - X_A) * km / DIST


def make_boat():
    hull = Polygon([-0.5, 0.12, 0], [0.62, 0.12, 0], [0.38, -0.14, 0], [-0.42, -0.14, 0],
                   color="#C8874A", fill_color="#C8874A", fill_opacity=1, stroke_width=2)
    cabin = Rectangle(width=0.36, height=0.22, color=WHITE, fill_color=WHITE, fill_opacity=0.9,
                      stroke_width=1).move_to([-0.1, 0.24, 0])
    return VGroup(hull, cabin)   # 船首は右向き


def make_town(name):
    body = Square(0.42, color=WHITE, fill_color=GREY_D, fill_opacity=1, stroke_width=2)
    roof = Triangle(color=WHITE, fill_color=RED_E, fill_opacity=1, stroke_width=2)
    roof.stretch_to_fit_width(0.56).stretch_to_fit_height(0.3).next_to(body, UP, buff=0)
    label = jp(name, font_size=26).next_to(roof, UP, buff=0.08)
    return VGroup(body, roof, label)


class River96_4(SfxMixin, Scene):
    def construct(self):
        self.intro()
        self.setup_river()
        self.trips()
        self.why()
        self.solve()

    # ------------------------------------------------------------------
    def intro(self):
        num = Text("96-4", font_size=44, weight=BOLD, color=BLUE)
        problem = VGroup(
            jp("川に沿った2つの町 A, B 間は 30km あります。"),
            jp("この川を上るのに 6時間、下るのに 4時間かかるとき、"),
            jp("川の流れの速さは？"),
        ).arrange(DOWN, aligned_edge=LEFT)
        header = VGroup(num, problem).arrange(RIGHT, buff=0.5)
        header.scale_to_fit_width(min(header.width, config.frame_width - 1))
        self.play(FadeIn(header, shift=UP))
        self.wait(3)
        self.title = jp("96-4  川の流れの速さは？", font_size=30).to_edge(UP, buff=0.25)
        self.play(ReplacementTransform(header, self.title))

    # ------------------------------------------------------------------
    def setup_river(self):
        river = Rectangle(width=13, height=0.8, stroke_width=0, fill_color=BLUE_E, fill_opacity=0.8)
        river.move_to([0, RIVER_Y, 0])
        banks = VGroup(*[Line([-6.5, RIVER_Y + s * 0.4, 0], [6.5, RIVER_Y + s * 0.4, 0],
                              color=BLUE_D, stroke_width=3) for s in (-1, 1)])

        # 流れ（右から左へ）を表す筋。updater で流し続ける
        streaks = VGroup(*[
            Line(ORIGIN, LEFT * 0.35, color=BLUE_A, stroke_width=2, stroke_opacity=0.7)
            .move_to([-6.2 + 0.9 * k + 0.45 * (k % 2), RIVER_Y + (0.2 if k % 2 else -0.2), 0])
            for k in range(14)
        ])

        def flow(m, dt):
            for s in m:
                s.shift(LEFT * 0.8 * dt)
                if s.get_center()[0] < -6.3:
                    s.shift(RIGHT * 12.6)
        streaks.add_updater(flow)

        town_a = make_town("A町").move_to([-5.9, RIVER_Y + 0.85, 0], aligned_edge=DOWN)
        town_b = make_town("B町").move_to([5.9, RIVER_Y + 0.85, 0], aligned_edge=DOWN)
        self.play(FadeIn(river, banks), FadeIn(town_a, town_b))
        self.add(streaks)

        flow_arrow = Arrow([1.2, 0, 0], [-1.2, 0, 0], color=FLOW_C, buff=0, stroke_width=6)
        flow_arrow.move_to([0, RIVER_Y, 0])
        flow_lab = tj("川の流れ", 24, color=FLOW_C).next_to(flow_arrow, DOWN, buff=0.45)
        self.play(GrowArrow(flow_arrow), FadeIn(flow_lab))
        self.wait(1)
        self.play(FadeOut(flow_arrow, flow_lab))

        dist = DoubleArrow([X_A, 0.45, 0], [X_B, 0.45, 0], color=WHITE, buff=0, stroke_width=3,
                           tip_length=0.2)
        dist_lab = jp("30km", font_size=28).next_to(dist, DOWN, buff=0.1)
        self.play(GrowFromCenter(dist), FadeIn(dist_lab))
        note = tj("B町は上流、A町は下流", 24).move_to([0, -0.7, 0])
        self.play(FadeIn(note))
        self.wait(1.5)
        self.play(FadeOut(note))

        self.boat = make_boat().move_to([X_A, RIVER_Y + 0.05, 0])
        self.play(FadeIn(self.boat, shift=UP * 0.2))
        self.dist = VGroup(dist, dist_lab)

    # ------------------------------------------------------------------
    def trip(self, start, end, hours, color, label, marker_y, label_y):
        """船を start→end に hours 秒（=時間）で動かし、1時間ごとに印を残す。"""
        h = ValueTracker(0)
        v = abs(end - start) / hours
        timer = always_redraw(lambda: VGroup(
            tj(label, 30), jp("経過", font_size=26),
            Integer(int(h.get_value() + 1e-6), font_size=44, color=color),
            jp("時間", font_size=26),
        ).arrange(RIGHT, buff=0.2).move_to([0, -0.7, 0]))
        self.add(timer)

        def boat_pos(b):
            km = start + (end - start) * h.get_value() / hours
            b.move_to([x_at(km), RIVER_Y + 0.05, 0])
        self.boat.add_updater(boat_pos)

        marks = VGroup()
        for k in range(1, hours + 1):
            km = start + (end - start) * k / hours
            dot = Dot([x_at(km), marker_y, 0], color=color, radius=0.08)
            tick = DashedLine([x_at(km), RIVER_Y - 0.4, 0], [x_at(km), RIVER_Y + 0.4, 0],
                              color=color, stroke_width=2)
            mid = (km + start + (end - start) * (k - 1) / hours) / 2
            seg = jp(f"{v:g}km", font_size=20, color=color).move_to([x_at(mid), label_y, 0])
            marks.add(VGroup(dot, tick, seg))

        # 1 時間ごとに「ポン」（ドレミ…）と印
        shown = set()

        def reveal(m):
            for k in range(1, hours + 1):
                if h.get_value() >= k - 1e-6 and k not in shown:
                    shown.add(k)
                    self.add(marks[k - 1])
        updater_holder = Mobject().add_updater(reveal)
        self.add(updater_holder)
        for k in range(1, hours + 1):
            self.sfx("pop", offset=k, step=k - 1)
        self.play(h.animate.set_value(hours), run_time=hours, rate_func=linear)
        self.boat.clear_updaters()
        self.remove(updater_holder)
        self.wait(0.5)
        self.remove(timer)
        return marks

    def trips(self):
        up_marks = self.trip(0, DIST, UP_H, UP_C, "上り", RIVER_Y + 0.62, RIVER_Y + 0.62 + 0.28)
        up_res = tj(f"上り：30km ÷ 6時間 ＝ 時速 {V_UP:g}km", 30).move_to([0, -0.8, 0])
        self.sfx("chime", gain_db=-6)
        self.play(FadeIn(up_res, shift=UP * 0.2))
        self.wait(1.5)

        self.play(FadeOut(self.dist), Rotate(self.boat, PI, axis=UP), run_time=0.8)
        self.play(up_res.animate.move_to([0, -1.7, 0]))
        down_marks = self.trip(DIST, 0, DOWN_H, DOWN_C, "下り", RIVER_Y - 0.62, RIVER_Y - 0.62 - 0.28)
        down_res = tj(f"下り：30km ÷ 4時間 ＝ 時速 {V_DOWN:g}km", 30).move_to([0, -0.8, 0])
        self.sfx("chime", gain_db=-6)
        self.play(FadeIn(down_res, shift=UP * 0.2))
        hint = tj("下りの方が、1時間に 2.5km 多く進む", 24, color=GRAY_A).move_to([0, -2.6, 0])
        self.play(FadeIn(hint))
        self.wait(2)
        self.up_res, self.down_res = up_res, down_res
        self.marks = VGroup(up_marks, down_marks)
        self.hint = hint

    # ------------------------------------------------------------------
    def speed_arrows(self, heading, scale=0.45):
        """船の上に「船の速さ」と「流れの速さ」の矢印。heading=+1 右向き(上り), -1 左向き(下り)。"""
        base = self.boat.get_center() + UP * 0.75
        b_end = base + RIGHT * heading * V_BOAT * scale
        boat_arr = Arrow(base, b_end, buff=0, color=BOAT_C, stroke_width=8, max_tip_length_to_length_ratio=0.12)
        f_end = b_end + LEFT * V_FLOW * scale
        flow_arr = Arrow(b_end + UP * 0.25, f_end + UP * 0.25, buff=0, color=FLOW_C, stroke_width=8,
                         max_tip_length_to_length_ratio=0.4)
        return boat_arr, flow_arr

    def why(self):
        self.play(FadeOut(self.marks, self.up_res, self.down_res, self.hint))
        q = tj("なぜ 上りと下りで 速さが違う？", 32).move_to([0, -0.8, 0])
        self.play(Write(q))
        self.wait(1)

        # 下り（左向き）: 船の速さ + 流れ
        self.play(self.boat.animate.move_to([1.6, RIVER_Y + 0.05, 0]))
        b, f = self.speed_arrows(-1)
        b_lab = tj("船の速さ", 22).next_to(b, UP, buff=0.35)
        self.sfx("pop", step=0)
        self.play(GrowArrow(b), FadeIn(b_lab))
        self.sfx("pop", step=2)
        self.play(GrowArrow(f))
        f_lab = tj("流れ", 22).next_to(f, UP, buff=0.05)
        self.play(FadeIn(f_lab))
        down_eq = tj("下りの速さ ＝ 船の速さ ＋ 流れの速さ", 28).move_to([0, -1.6, 0])
        self.sfx("pop", step=4)
        self.play(FadeIn(down_eq, shift=UP * 0.2))
        self.wait(1.5)
        self.play(FadeOut(b, f, b_lab, f_lab))

        # 上り（右向き）: 船の速さ − 流れ
        self.play(Rotate(self.boat, PI, axis=UP), run_time=0.6)
        self.play(self.boat.animate.move_to([-3.4, RIVER_Y + 0.05, 0]))
        b, f = self.speed_arrows(+1)
        b_lab = tj("船の速さ", 22).next_to(b, UP, buff=0.35)
        self.sfx("pop", step=0)
        self.play(GrowArrow(b), FadeIn(b_lab))
        self.sfx("pop", step=2)
        self.play(GrowArrow(f))
        f_lab = tj("流れ", 22).next_to(f, UP, buff=0.05)
        self.play(FadeIn(f_lab))
        up_eq = tj("上りの速さ ＝ 船の速さ − 流れの速さ", 28).move_to([0, -2.3, 0])
        self.sfx("pop", step=4)
        self.play(FadeIn(up_eq, shift=UP * 0.2))
        self.wait(2)
        self.play(FadeOut(b, f, b_lab, f_lab, q))
        self.play(VGroup(down_eq, up_eq).animate.scale(0.8).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
                  .move_to([-3.4, -0.3, 0]))
        self.eqs = VGroup(down_eq, up_eq)

    # ------------------------------------------------------------------
    def solve(self):
        unit = 0.6            # 1 km/h あたりの長さ
        x0 = -4.6
        y_down, y_up = -1.55, -2.45
        bh = 0.45

        def bar(a, b, y, color, dashed=False):
            r = Rectangle(width=(b - a) * unit, height=bh, color=color, stroke_width=3,
                          fill_color=color, fill_opacity=0 if dashed else 0.75)
            if dashed:
                r = DashedVMobject(r, num_dashes=24)
            return r.move_to([x0 + (a + b) / 2 * unit, y, 0])

        down_lab = tj("下り", 26).move_to([x0 - 0.65, y_down, 0])
        up_lab = tj("上り", 26).move_to([x0 - 0.65, y_up, 0])

        d_boat = bar(0, V_BOAT, y_down, BOAT_C)
        d_flow = bar(V_BOAT, V_DOWN, y_down, FLOW_C)
        u_boat = bar(0, V_UP, y_up, BOAT_C)
        u_cut = bar(V_UP, V_BOAT, y_up, FLOW_C, dashed=True)
        d_val = jp(f"{V_DOWN:g}", font_size=26, color=DOWN_C).next_to(d_flow, RIGHT, buff=0.15)
        u_val = jp(f"{V_UP:g}", font_size=26, color=UP_C).next_to(u_cut, RIGHT, buff=0.15)

        head = jp("線分図にすると…", font_size=24).move_to([-4.6, -1.0, 0], aligned_edge=LEFT)
        self.play(FadeIn(head))
        self.play(FadeIn(down_lab, up_lab))
        self.sfx("pop", step=0)
        self.play(GrowFromEdge(d_boat, LEFT))
        self.sfx("pop", step=2)
        self.play(GrowFromEdge(d_flow, LEFT), FadeIn(d_val))
        self.sfx("pop", step=1)
        self.play(GrowFromEdge(u_boat, LEFT))
        self.sfx("pop", step=3)
        self.play(Create(u_cut), FadeIn(u_val))
        minus = jp("−流れ", font_size=20, color=FLOW_C).next_to(u_cut, DOWN, buff=0.08)
        self.play(FadeIn(minus))
        self.wait(1)

        # 差の部分 = 流れ 2 つ分
        xa, xb = x0 + V_UP * unit, x0 + V_DOWN * unit
        guides = VGroup(*[DashedLine([x, y_down + 0.35, 0], [x, y_up - 0.35, 0], color=GRAY, stroke_width=2)
                          for x in (xa, xb)])
        self.play(Create(guides), FadeOut(head))
        two = VGroup(u_cut.copy(), d_flow.copy())
        self.play(Indicate(u_cut, color=FLOW_C), Indicate(d_flow, color=FLOW_C))
        self.sfx("pop", step=4)
        self.play(two[0].animate.move_to([(xa + x0 + V_BOAT * unit) / 2, -3.35, 0]),
                  two[1].animate.move_to([(x0 + V_BOAT * unit + xb) / 2, -3.35, 0]))
        two_lab = tj("差 ＝ 流れ 2つ分", 22).next_to(two, LEFT, buff=0.25)
        self.play(FadeIn(two_lab))
        self.wait(1)

        # 計算（右側）
        cx = 3.9
        calc = VGroup(
            tj("流れ×2 ＝ 7.5 − 5 ＝ 2.5", 28),
            tj("流れ ＝ 2.5 ÷ 2 ＝ 1.25", 28),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([cx, -0.6, 0])
        self.sfx("pop", step=5)
        self.play(Write(calc[0]))
        self.sfx("pop", step=7)
        self.play(Write(calc[1]))

        answer = jp("答  時速 1.25km", font_size=40, color=PICK, weight=BOLD)
        box = SurroundingRectangle(answer, color=PICK, buff=0.2)
        ans = VGroup(answer, box).next_to(calc, DOWN, buff=0.45).set_x(cx)
        self.sfx("chime")
        self.play(Write(answer), Create(box))
        bonus = tj(f"（船の速さ ＝ 5 ＋ 1.25 ＝ 時速 {V_BOAT:g}km）", 20, color=GRAY_A).next_to(ans, DOWN, buff=0.2)
        self.play(FadeIn(bonus))
        self.wait(3)
