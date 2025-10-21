from manim import *


class PythagoreanTheorem(Scene):
    def construct(self):
        triangle = Polygon(
            [-2, -1.5, 0],
            [2, -1.5, 0],
            [2, 1.5, 0],
            color=BLUE
        )

        a_label = Text("a = 3", font_size=36).next_to(triangle, RIGHT, buff=0.2)
        b_label = Text("b = 4", font_size=36).next_to(triangle, DOWN, buff=0.2)
        c_label = Text("c = 5", font_size=36).next_to(triangle, LEFT, buff=0.3).shift(UP * 0.3)

        right_angle = RightAngle(
            Line(triangle.get_vertices()[1], triangle.get_vertices()[0]),
            Line(triangle.get_vertices()[1], triangle.get_vertices()[2]),
            length=0.3
        )

        self.play(Create(triangle), Create(right_angle))
        self.play(Write(a_label), Write(b_label), Write(c_label))
        self.wait()

        square_a = Square(side_length=3, color=RED, fill_opacity=0.5).next_to(triangle, RIGHT, buff=0)
        square_b = Square(side_length=4, color=GREEN, fill_opacity=0.5).next_to(triangle, DOWN, buff=0)
        square_c = Square(side_length=5, color=YELLOW, fill_opacity=0.5).rotate(
            np.arctan(3/4)
        ).move_to(triangle.get_left() + LEFT * 2.5 + UP * 0.5)

        a_sq_label = Text("a² = 9", font_size=32).move_to(square_a.get_center())
        b_sq_label = Text("b² = 16", font_size=32).move_to(square_b.get_center())
        c_sq_label = Text("c² = 25", font_size=32).move_to(square_c.get_center())

        self.play(
            FadeOut(a_label),
            FadeOut(b_label),
            FadeOut(c_label)
        )
        self.play(
            Create(square_a),
            Create(square_b),
            Create(square_c)
        )
        self.play(
            Write(a_sq_label),
            Write(b_sq_label),
            Write(c_sq_label)
        )
        self.wait()

        theorem = Text("a² + b² = c²", font_size=48).to_edge(UP)
        self.play(Write(theorem))
        self.wait()

        calculation = Text("9 + 16 = 25", font_size=40).next_to(theorem, DOWN)
        self.play(Write(calculation))
        self.wait()

        self.play(
            theorem.animate.set_color(YELLOW),
            calculation.animate.set_color(YELLOW)
        )
        self.wait(2)
