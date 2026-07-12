from __future__ import annotations

from PyQt6.QtCore import QEvent, QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPen, QTabletEvent
from PyQt6.QtWidgets import QSizePolicy, QWidget

from src.editor.stroke_manager import StrokeManager, StrokePoint


class HandwritingCanvas(QWidget):
    stroke_changed = pyqtSignal()
    mode_changed = pyqtSignal(str)

    CANVAS_SIZE = 720.0

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.manager = StrokeManager()
        self.target_character = "A"
        self.tool_mode = "pen"
        self.eraser_radius = 28.0
        self._drawing = False
        self._last_canvas_point: QPointF | None = None
        self._hover_canvas_point: QPointF | None = None
        self.setMinimumSize(520, 520)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_target_character(self, character: str) -> None:
        self.target_character = character
        self.update()

    def set_tool_mode(self, mode: str) -> None:
        if mode not in {"pen", "eraser", "move"}:
            return
        self.tool_mode = mode
        self.mode_changed.emit(mode)
        self.update()

    def set_eraser_radius(self, radius: int | float) -> None:
        self.eraser_radius = float(max(4.0, min(float(radius), 120.0)))
        self.update()

    def load_json_strokes(self, strokes: list[list[list[float]]]) -> None:
        self.manager.load_json_strokes(strokes)
        self.stroke_changed.emit()
        self.update()

    def to_json_strokes(self) -> list[list[list[float]]]:
        return self.manager.to_json_strokes()

    def clear(self) -> None:
        self.manager.clear()
        self.stroke_changed.emit()
        self.update()

    def undo(self) -> None:
        if self.manager.undo():
            self.stroke_changed.emit()
            self.update()

    def redo(self) -> None:
        if self.manager.redo():
            self.stroke_changed.emit()
            self.update()

    def center_strokes(self) -> None:
        self.manager.center_in_canvas(self.CANVAS_SIZE, self.CANVAS_SIZE)
        self.stroke_changed.emit()
        self.update()

    def fit_strokes_to_guides(self) -> None:
        """Fit a glyph inside the writing area while keeping its baseline consistent."""
        baseline = self.CANVAS_SIZE * 0.72
        horizontal_margin = self.CANVAS_SIZE * 0.16
        top = self.CANVAS_SIZE * 0.14
        if self.manager.fit_to_rect(
            horizontal_margin,
            top,
            self.CANVAS_SIZE - horizontal_margin * 2,
            baseline - top,
        ):
            self.stroke_changed.emit()
            self.update()

    def scale_strokes(self, factor: float) -> None:
        self.manager.scale_about_center(factor)
        self.stroke_changed.emit()
        self.update()

    def nudge_strokes(self, dx: float, dy: float) -> None:
        self.manager.translate(dx, dy)
        self.stroke_changed.emit()
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        self._paint_background(painter)
        self._paint_target_character(painter)
        self._paint_strokes(painter)
        self._paint_tool_overlay(painter)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton:
            return
        point = self._event_to_canvas(event.position())
        if point is None:
            return
        self._drawing = True
        self._last_canvas_point = point
        if self.tool_mode == "pen":
            self.manager.begin_stroke(point.x(), point.y(), pressure=1.0)
        elif self.tool_mode == "eraser":
            self.manager.begin_batch_edit()
            self.manager.erase_near(point.x(), point.y(), self.eraser_radius)
        elif self.tool_mode == "move":
            self.manager.begin_batch_edit()
        self.stroke_changed.emit()
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        point = self._event_to_canvas(event.position())
        self._hover_canvas_point = point
        if not self._drawing:
            self.update()
            return
        if point is None:
            return
        if self.tool_mode == "pen":
            self.manager.add_point(point.x(), point.y(), pressure=1.0)
        elif self.tool_mode == "eraser":
            self.manager.erase_near(point.x(), point.y(), self.eraser_radius)
        elif self.tool_mode == "move" and self._last_canvas_point is not None:
            dx = point.x() - self._last_canvas_point.x()
            dy = point.y() - self._last_canvas_point.y()
            self.manager.translate(dx, dy)
            self._last_canvas_point = point
        self.stroke_changed.emit()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton or not self._drawing:
            return
        point = self._event_to_canvas(event.position())
        if point is not None and self.tool_mode == "pen":
            self.manager.add_point(point.x(), point.y(), pressure=1.0)
        if self.tool_mode == "pen":
            self.manager.end_stroke()
        elif self.tool_mode in {"eraser", "move"}:
            self.manager.end_batch_edit()
        self._drawing = False
        self._last_canvas_point = None
        self.stroke_changed.emit()
        self.update()

    def leaveEvent(self, event) -> None:  # noqa: N802
        del event
        self._hover_canvas_point = None
        self.update()

    def tabletEvent(self, event: QTabletEvent) -> None:  # noqa: N802
        event_type = event.type()
        if event_type not in {
            QEvent.Type.TabletPress,
            QEvent.Type.TabletMove,
            QEvent.Type.TabletRelease,
        }:
            event.ignore()
            return

        point = self._event_to_canvas(event.position())
        if point is None:
            event.ignore()
            return

        pressure = max(0.05, float(event.pressure()))
        if event_type == QEvent.Type.TabletPress:
            self._drawing = True
            self._last_canvas_point = point
            if self.tool_mode == "pen":
                self.manager.begin_stroke(point.x(), point.y(), pressure=pressure)
            elif self.tool_mode == "eraser":
                self.manager.begin_batch_edit()
                self.manager.erase_near(point.x(), point.y(), self.eraser_radius)
            elif self.tool_mode == "move":
                self.manager.begin_batch_edit()
        elif event_type == QEvent.Type.TabletMove and self._drawing and self.tool_mode == "pen":
            self.manager.add_point(point.x(), point.y(), pressure=pressure)
        elif event_type == QEvent.Type.TabletMove and self._drawing and self.tool_mode == "eraser":
            self.manager.erase_near(point.x(), point.y(), self.eraser_radius)
        elif (
            event_type == QEvent.Type.TabletMove
            and self._drawing
            and self.tool_mode == "move"
            and self._last_canvas_point is not None
        ):
            self.manager.translate(
                point.x() - self._last_canvas_point.x(),
                point.y() - self._last_canvas_point.y(),
            )
            self._last_canvas_point = point
        elif event_type == QEvent.Type.TabletRelease and self._drawing and self.tool_mode == "pen":
            self.manager.add_point(point.x(), point.y(), pressure=pressure)
            self.manager.end_stroke()
            self._drawing = False
            self._last_canvas_point = None
        elif event_type == QEvent.Type.TabletRelease and self._drawing:
            self.manager.end_batch_edit()
            self._drawing = False
            self._last_canvas_point = None

        self.stroke_changed.emit()
        self.update()
        event.accept()

    def _paint_background(self, painter: QPainter) -> None:
        widget_rect = QRectF(self.rect())
        painter.fillRect(widget_rect, QColor("#edf2f7"))

        canvas_rect = self._canvas_rect()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#ffffff"))
        painter.drawRoundedRect(canvas_rect, 8.0, 8.0)

        border_pen = QPen(QColor("#bcc8d6"), 1.5)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(canvas_rect.adjusted(0.75, 0.75, -0.75, -0.75), 8.0, 8.0)

        grid_pen = QPen(QColor("#e6ecf3"), 1)
        painter.setPen(grid_pen)
        step = canvas_rect.width() / 8.0
        for index in range(1, 8):
            x = canvas_rect.left() + step * index
            y = canvas_rect.top() + step * index
            painter.drawLine(QPointF(x, canvas_rect.top()), QPointF(x, canvas_rect.bottom()))
            painter.drawLine(QPointF(canvas_rect.left(), y), QPointF(canvas_rect.right(), y))

        baseline_pen = QPen(QColor("#1d9a8a"), 2, Qt.PenStyle.DashLine)
        painter.setPen(baseline_pen)
        baseline_y = canvas_rect.top() + canvas_rect.height() * 0.72
        midline_y = canvas_rect.top() + canvas_rect.height() * 0.43
        painter.drawLine(QPointF(canvas_rect.left(), baseline_y), QPointF(canvas_rect.right(), baseline_y))
        midline_pen = QPen(QColor("#f2b84b"), 1.5, Qt.PenStyle.DashLine)
        painter.setPen(midline_pen)
        painter.drawLine(QPointF(canvas_rect.left(), midline_y), QPointF(canvas_rect.right(), midline_y))

    def _paint_target_character(self, painter: QPainter) -> None:
        painter.save()
        canvas_rect = self._canvas_rect()
        font = painter.font()
        font.setPointSize(max(80, int(canvas_rect.height() * 0.42)))
        font.setBold(True)
        painter.setFont(font)
        painter.setOpacity(0.08)
        painter.setPen(QColor("#1f2937"))
        painter.drawText(canvas_rect, Qt.AlignmentFlag.AlignCenter, self.target_character)
        painter.restore()

    def _paint_strokes(self, painter: QPainter) -> None:
        strokes = list(self.manager.strokes)
        if self.manager.current_stroke:
            strokes.append(self.manager.current_stroke)

        for stroke in strokes:
            self._paint_single_stroke(painter, stroke)

    def _paint_tool_overlay(self, painter: QPainter) -> None:
        if self.tool_mode != "eraser" or self._hover_canvas_point is None:
            return
        rect = self._canvas_rect()
        if not rect.contains(self._canvas_to_view_point(self._hover_canvas_point)):
            return

        center = self._canvas_to_view_point(self._hover_canvas_point)
        scale = rect.width() / self.CANVAS_SIZE
        radius = self.eraser_radius * scale
        painter.save()
        painter.setPen(QPen(QColor("#e11d48"), 1.5, Qt.PenStyle.DashLine))
        painter.setBrush(QColor(225, 29, 72, 24))
        painter.drawEllipse(center, radius, radius)
        painter.restore()

    def _paint_single_stroke(self, painter: QPainter, stroke: list[StrokePoint]) -> None:
        if not stroke:
            return

        if len(stroke) == 1:
            view_point = self._canvas_to_view(stroke[0])
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#111827"))
            painter.drawEllipse(view_point, 3.0, 3.0)
            return

        for left, right in zip(stroke, stroke[1:]):
            start = self._canvas_to_view(left)
            end = self._canvas_to_view(right)
            pressure = (left.pressure + right.pressure) / 2.0
            pen_width = max(2.0, 5.0 * pressure)
            pen = QPen(
                QColor("#111827"),
                pen_width,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
            painter.setPen(pen)
            painter.drawLine(start, end)

    def _canvas_rect(self) -> QRectF:
        side = min(self.width(), self.height()) - 28.0
        side = max(100.0, side)
        left = (self.width() - side) / 2.0
        top = (self.height() - side) / 2.0
        return QRectF(left, top, side, side)

    def _event_to_canvas(self, point: QPointF) -> QPointF | None:
        rect = self._canvas_rect()
        if not rect.contains(point):
            return None
        scale = self.CANVAS_SIZE / rect.width()
        x = (point.x() - rect.left()) * scale
        y = (point.y() - rect.top()) * scale
        return QPointF(max(0.0, min(self.CANVAS_SIZE, x)), max(0.0, min(self.CANVAS_SIZE, y)))

    def _canvas_to_view(self, point: StrokePoint) -> QPointF:
        return self._canvas_to_view_point(QPointF(point.x, point.y))

    def _canvas_to_view_point(self, point: QPointF) -> QPointF:
        rect = self._canvas_rect()
        scale = rect.width() / self.CANVAS_SIZE
        return QPointF(rect.left() + point.x() * scale, rect.top() + point.y() * scale)
