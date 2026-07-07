from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence

import numpy as np
from fontTools.pens.ttGlyphPen import TTGlyphPen


Point3 = tuple[float, float, float]
Point2 = tuple[float, float]


@dataclass
class GlyphOutline:
    contours: list[list[Point2]]
    advance_width: int
    left_side_bearing: int
    bounds: tuple[float, float, float, float] | None


class GlyphGenerator:
    def __init__(
        self,
        units_per_em: int = 1000,
        canvas_size: float = 720.0,
        baseline_ratio: float = 0.72,
        x_margin: float = 70.0,
        horizontal_scale: float = 860.0,
        vertical_scale: float = 950.0,
        stroke_width: float = 76.0,
    ) -> None:
        self.units_per_em = units_per_em
        self.canvas_size = canvas_size
        self.baseline_ratio = baseline_ratio
        self.x_margin = x_margin
        self.horizontal_scale = horizontal_scale
        self.vertical_scale = vertical_scale
        self.stroke_width = stroke_width

    def build_outline(self, strokes: Iterable[Iterable[Sequence[float]]]) -> GlyphOutline:
        contours: list[list[Point2]] = []

        for stroke in strokes:
            source_points = self._parse_stroke(stroke)
            if not source_points:
                continue

            font_points = [self._canvas_point_to_font(point) for point in source_points]
            simplified = self._simplify_points(font_points, tolerance=3.2)
            if len(simplified) <= 1:
                contours.append(self._circle_contour(simplified[0], self.stroke_width * 0.5))
                continue

            fitted = self._fit_bezier_path(simplified)
            contour = self._expand_stroke(fitted)
            if len(contour) >= 3:
                contours.append(contour)

        bounds = self._bounds(contours)
        if bounds is None:
            return GlyphOutline(contours=[], advance_width=560, left_side_bearing=0, bounds=None)

        min_x, _, max_x, _ = bounds
        advance_width = int(max(340, min(1180, max_x + self.x_margin)))
        return GlyphOutline(
            contours=contours,
            advance_width=advance_width,
            left_side_bearing=int(math.floor(min_x)),
            bounds=bounds,
        )

    def draw_to_pen(self, outline: GlyphOutline, pen: TTGlyphPen) -> None:
        for contour in outline.contours:
            cleaned = self._dedupe_contour(contour)
            if len(cleaned) < 3:
                continue
            first = cleaned[0]
            pen.moveTo((int(round(first[0])), int(round(first[1]))))
            for point in cleaned[1:]:
                pen.lineTo((int(round(point[0])), int(round(point[1]))))
            pen.closePath()

    def make_glyph(self, strokes: Iterable[Iterable[Sequence[float]]]):
        outline = self.build_outline(strokes)
        pen = TTGlyphPen(None)
        self.draw_to_pen(outline, pen)
        return pen.glyph(), outline

    def _parse_stroke(self, stroke: Iterable[Sequence[float]]) -> list[Point3]:
        points: list[Point3] = []
        for raw_point in stroke:
            if len(raw_point) < 2:
                continue
            x = float(raw_point[0])
            y = float(raw_point[1])
            pressure = float(raw_point[3]) if len(raw_point) >= 4 else 1.0
            pressure = max(0.08, min(pressure, 3.0))
            points.append((x, y, pressure))
        return points

    def _canvas_point_to_font(self, point: Point3) -> Point3:
        x, y, pressure = point
        baseline_y = self.canvas_size * self.baseline_ratio
        font_x = self.x_margin + (x / self.canvas_size) * self.horizontal_scale
        font_y = ((baseline_y - y) / self.canvas_size) * self.vertical_scale
        return (font_x, font_y, pressure)

    def _simplify_points(self, points: list[Point3], tolerance: float) -> list[Point3]:
        if len(points) <= 2:
            return points

        first = points[0]
        last = points[-1]
        max_distance = -1.0
        split_index = 0

        for index in range(1, len(points) - 1):
            distance = self._distance_point_to_segment(points[index], first, last)
            if distance > max_distance:
                max_distance = distance
                split_index = index

        if max_distance > tolerance:
            left = self._simplify_points(points[: split_index + 1], tolerance)
            right = self._simplify_points(points[split_index:], tolerance)
            return left[:-1] + right

        return [first, last]

    def _distance_point_to_segment(self, point: Point3, start: Point3, end: Point3) -> float:
        px, py, _ = point
        ax, ay, _ = start
        bx, by, _ = end
        dx = bx - ax
        dy = by - ay
        length_squared = dx * dx + dy * dy
        if length_squared <= 1e-9:
            return math.hypot(px - ax, py - ay)
        t = ((px - ax) * dx + (py - ay) * dy) / length_squared
        t = max(0.0, min(1.0, t))
        closest_x = ax + t * dx
        closest_y = ay + t * dy
        return math.hypot(px - closest_x, py - closest_y)

    def _fit_bezier_path(self, points: list[Point3]) -> list[Point3]:
        if len(points) <= 2:
            return points

        fitted: list[Point3] = [points[0]]
        for index in range(len(points) - 1):
            p0 = points[max(0, index - 1)]
            p1 = points[index]
            p2 = points[index + 1]
            p3 = points[min(len(points) - 1, index + 2)]

            p0_xy = np.array([p0[0], p0[1]], dtype=float)
            p1_xy = np.array([p1[0], p1[1]], dtype=float)
            p2_xy = np.array([p2[0], p2[1]], dtype=float)
            p3_xy = np.array([p3[0], p3[1]], dtype=float)

            control_1 = p1_xy + (p2_xy - p0_xy) / 6.0
            control_2 = p2_xy - (p3_xy - p1_xy) / 6.0
            distance = float(np.linalg.norm(p2_xy - p1_xy))
            steps = max(4, min(18, int(distance / 28.0) + 1))

            for step in range(1, steps + 1):
                t = step / steps
                xy = self._cubic_bezier(p1_xy, control_1, control_2, p2_xy, t)
                pressure = p1[2] + (p2[2] - p1[2]) * t
                fitted.append((float(xy[0]), float(xy[1]), pressure))

        return self._remove_close_points(fitted, min_distance=1.0)

    def _cubic_bezier(
        self,
        p0: np.ndarray,
        c1: np.ndarray,
        c2: np.ndarray,
        p3: np.ndarray,
        t: float,
    ) -> np.ndarray:
        inv = 1.0 - t
        return (
            (inv**3) * p0
            + 3.0 * (inv**2) * t * c1
            + 3.0 * inv * (t**2) * c2
            + (t**3) * p3
        )

    def _remove_close_points(self, points: list[Point3], min_distance: float) -> list[Point3]:
        if not points:
            return points
        kept = [points[0]]
        for point in points[1:]:
            previous = kept[-1]
            if math.hypot(point[0] - previous[0], point[1] - previous[1]) >= min_distance:
                kept.append(point)
        if len(kept) == 1 and len(points) > 1:
            kept.append(points[-1])
        return kept

    def _expand_stroke(self, points: list[Point3]) -> list[Point2]:
        if len(points) == 1:
            return self._circle_contour(points[0], self.stroke_width * 0.5)

        left: list[Point2] = []
        right: list[Point2] = []
        for index, point in enumerate(points):
            tangent = self._tangent_at(points, index)
            normal = (-tangent[1], tangent[0])
            radius = max(18.0, self.stroke_width * 0.5 * point[2])
            left.append((point[0] + normal[0] * radius, point[1] + normal[1] * radius))
            right.append((point[0] - normal[0] * radius, point[1] - normal[1] * radius))

        start_tangent = self._tangent_at(points, 0)
        end_tangent = self._tangent_at(points, len(points) - 1)
        start_radius = max(18.0, self.stroke_width * 0.5 * points[0][2])
        end_radius = max(18.0, self.stroke_width * 0.5 * points[-1][2])
        start_normal = (-start_tangent[1], start_tangent[0])
        end_normal = (-end_tangent[1], end_tangent[0])

        end_cap = self._cap_arc(
            center=(points[-1][0], points[-1][1]),
            normal=end_normal,
            radius=end_radius,
            from_left=True,
        )
        start_cap = self._cap_arc(
            center=(points[0][0], points[0][1]),
            normal=start_normal,
            radius=start_radius,
            from_left=False,
        )

        return left + end_cap + list(reversed(right)) + start_cap

    def _tangent_at(self, points: list[Point3], index: int) -> Point2:
        if index <= 0:
            dx = points[1][0] - points[0][0]
            dy = points[1][1] - points[0][1]
        elif index >= len(points) - 1:
            dx = points[-1][0] - points[-2][0]
            dy = points[-1][1] - points[-2][1]
        else:
            dx = points[index + 1][0] - points[index - 1][0]
            dy = points[index + 1][1] - points[index - 1][1]

        length = math.hypot(dx, dy)
        if length <= 1e-9:
            return (1.0, 0.0)
        return (dx / length, dy / length)

    def _cap_arc(
        self,
        center: Point2,
        normal: Point2,
        radius: float,
        from_left: bool,
    ) -> list[Point2]:
        left_angle = math.atan2(normal[1], normal[0])
        right_angle = math.atan2(-normal[1], -normal[0])
        start = left_angle if from_left else right_angle
        end = right_angle if from_left else left_angle
        delta = end - start
        if delta > 0:
            delta -= 2.0 * math.pi

        points: list[Point2] = []
        for step in range(1, 8):
            angle = start + delta * (step / 8.0)
            points.append((center[0] + math.cos(angle) * radius, center[1] + math.sin(angle) * radius))
        return points

    def _circle_contour(self, point: Point3, radius: float) -> list[Point2]:
        x, y, pressure = point
        scaled_radius = max(18.0, radius * pressure)
        return [
            (
                x + math.cos(index * math.tau / 20.0) * scaled_radius,
                y + math.sin(index * math.tau / 20.0) * scaled_radius,
            )
            for index in range(20)
        ]

    def _dedupe_contour(self, contour: list[Point2]) -> list[Point2]:
        if not contour:
            return []
        cleaned = [contour[0]]
        for point in contour[1:]:
            previous = cleaned[-1]
            if math.hypot(point[0] - previous[0], point[1] - previous[1]) > 0.7:
                cleaned.append(point)
        if len(cleaned) > 2:
            first = cleaned[0]
            last = cleaned[-1]
            if math.hypot(first[0] - last[0], first[1] - last[1]) <= 0.7:
                cleaned.pop()
        return cleaned

    def _bounds(self, contours: list[list[Point2]]) -> tuple[float, float, float, float] | None:
        points = [point for contour in contours for point in contour]
        if not points:
            return None
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        return min(xs), min(ys), max(xs), max(ys)
