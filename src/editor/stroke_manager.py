from __future__ import annotations

from dataclasses import dataclass
import math
import time
from typing import Iterable


@dataclass
class StrokePoint:
    x: float
    y: float
    timestamp: float
    pressure: float = 1.0

    def to_json(self) -> list[float]:
        return [
            round(float(self.x), 3),
            round(float(self.y), 3),
            round(float(self.timestamp), 6),
            round(float(self.pressure), 4),
        ]

    @classmethod
    def from_json(cls, value: object) -> "StrokePoint":
        if isinstance(value, dict):
            return cls(
                x=float(value.get("x", 0.0)),
                y=float(value.get("y", 0.0)),
                timestamp=float(value.get("time", value.get("timestamp", time.time()))),
                pressure=float(value.get("pressure", 1.0)),
            )

        if isinstance(value, (list, tuple)) and len(value) >= 2:
            timestamp = float(value[2]) if len(value) >= 3 else time.time()
            pressure = float(value[3]) if len(value) >= 4 else 1.0
            return cls(
                x=float(value[0]),
                y=float(value[1]),
                timestamp=timestamp,
                pressure=pressure,
            )

        raise ValueError(f"Invalid stroke point: {value!r}")


Stroke = list[StrokePoint]


class StrokeManager:
    def __init__(self) -> None:
        self.strokes: list[Stroke] = []
        self.current_stroke: Stroke | None = None
        self._undo_stack: list[list[Stroke]] = []
        self._redo_stack: list[list[Stroke]] = []
        self._batch_depth = 0

    def begin_stroke(
        self,
        x: float,
        y: float,
        pressure: float = 1.0,
        timestamp: float | None = None,
    ) -> None:
        self.current_stroke = [
            StrokePoint(x=float(x), y=float(y), timestamp=timestamp or time.time(), pressure=pressure)
        ]

    def add_point(
        self,
        x: float,
        y: float,
        pressure: float = 1.0,
        timestamp: float | None = None,
    ) -> None:
        if self.current_stroke is None:
            self.begin_stroke(x=x, y=y, pressure=pressure, timestamp=timestamp)
            return

        point = StrokePoint(
            x=float(x),
            y=float(y),
            timestamp=timestamp or time.time(),
            pressure=float(max(0.05, min(pressure, 4.0))),
        )

        previous = self.current_stroke[-1]
        if math.hypot(point.x - previous.x, point.y - previous.y) >= 0.35:
            self.current_stroke.append(point)

    def end_stroke(self) -> bool:
        if self.current_stroke is None:
            return False

        stroke = self.current_stroke
        self.current_stroke = None
        if len(stroke) == 1:
            point = stroke[0]
            stroke.append(
                StrokePoint(
                    x=point.x + 0.01,
                    y=point.y + 0.01,
                    timestamp=point.timestamp,
                    pressure=point.pressure,
                )
            )

        self._push_undo()
        self.strokes.append(stroke)
        self._redo_stack.clear()
        return True

    def clear(self) -> None:
        if self.strokes:
            self._push_undo()
            self._redo_stack.clear()
        self.strokes = []
        self.current_stroke = None

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        self._redo_stack.append(self._snapshot())
        self._restore(self._undo_stack.pop())
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        self._undo_stack.append(self._snapshot())
        self._restore(self._redo_stack.pop())
        return True

    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def load_json_strokes(self, strokes: Iterable[Iterable[object]]) -> None:
        self.strokes = []
        for stroke in strokes:
            parsed = [StrokePoint.from_json(point) for point in stroke]
            if parsed:
                self.strokes.append(parsed)
        self.current_stroke = None
        self._undo_stack.clear()
        self._redo_stack.clear()

    def to_json_strokes(self) -> list[list[list[float]]]:
        return [[point.to_json() for point in stroke] for stroke in self.strokes]

    def all_points(self) -> list[StrokePoint]:
        points = [point for stroke in self.strokes for point in stroke]
        if self.current_stroke:
            points.extend(self.current_stroke)
        return points

    def bounds(self) -> tuple[float, float, float, float] | None:
        points = self.all_points()
        if not points:
            return None
        xs = [point.x for point in points]
        ys = [point.y for point in points]
        return min(xs), min(ys), max(xs), max(ys)

    def begin_batch_edit(self) -> None:
        if self._batch_depth == 0 and self.strokes:
            self._push_undo()
            self._redo_stack.clear()
        self._batch_depth += 1

    def end_batch_edit(self) -> None:
        self._batch_depth = max(0, self._batch_depth - 1)

    def translate(self, dx: float, dy: float) -> None:
        self._transform(lambda point: (point.x + dx, point.y + dy))

    def scale_about_center(self, factor: float) -> None:
        bounds = self.bounds()
        if bounds is None:
            return
        min_x, min_y, max_x, max_y = bounds
        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0
        self._transform(
            lambda point: (
                center_x + (point.x - center_x) * factor,
                center_y + (point.y - center_y) * factor,
            )
        )

    def center_in_canvas(self, width: float, height: float) -> None:
        bounds = self.bounds()
        if bounds is None:
            return
        min_x, min_y, max_x, max_y = bounds
        current_center_x = (min_x + max_x) / 2.0
        current_center_y = (min_y + max_y) / 2.0
        self.translate(width / 2.0 - current_center_x, height / 2.0 - current_center_y)

    def erase_near(self, x: float, y: float, radius: float) -> bool:
        if not self.strokes:
            return False

        radius = max(1.0, float(radius))
        kept: list[Stroke] = []
        removed = False
        for stroke in self.strokes:
            if self._stroke_is_near(stroke, x, y, radius):
                removed = True
            else:
                kept.append(stroke)

        if removed:
            if self._batch_depth == 0:
                self._push_undo()
                self._redo_stack.clear()
            self.strokes = kept

        return removed

    def _transform(self, transform) -> None:
        if not self.strokes and not self.current_stroke:
            return
        if self._batch_depth == 0:
            self._push_undo()
            self._redo_stack.clear()
        for stroke in self.strokes:
            for point in stroke:
                point.x, point.y = transform(point)
        if self.current_stroke:
            for point in self.current_stroke:
                point.x, point.y = transform(point)

    def _push_undo(self) -> None:
        self._undo_stack.append(self._snapshot())
        if len(self._undo_stack) > 100:
            self._undo_stack.pop(0)

    def _snapshot(self) -> list[Stroke]:
        return [
            [
                StrokePoint(
                    x=point.x,
                    y=point.y,
                    timestamp=point.timestamp,
                    pressure=point.pressure,
                )
                for point in stroke
            ]
            for stroke in self.strokes
        ]

    def _restore(self, strokes: list[Stroke]) -> None:
        self.strokes = [
            [
                StrokePoint(
                    x=point.x,
                    y=point.y,
                    timestamp=point.timestamp,
                    pressure=point.pressure,
                )
                for point in stroke
            ]
            for stroke in strokes
        ]
        self.current_stroke = None

    def _stroke_is_near(self, stroke: Stroke, x: float, y: float, radius: float) -> bool:
        if not stroke:
            return False
        if len(stroke) == 1:
            return math.hypot(stroke[0].x - x, stroke[0].y - y) <= radius

        for start, end in zip(stroke, stroke[1:]):
            if self._distance_to_segment(x, y, start.x, start.y, end.x, end.y) <= radius:
                return True
        return False

    def _distance_to_segment(
        self,
        px: float,
        py: float,
        ax: float,
        ay: float,
        bx: float,
        by: float,
    ) -> float:
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
