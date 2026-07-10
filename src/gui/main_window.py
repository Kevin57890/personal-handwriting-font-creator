from __future__ import annotations

from pathlib import Path
import re
import shutil
import sys

from PyQt6.QtCore import QPointF, QRectF, QTimer, Qt, QUrl
from PyQt6.QtGui import QColor, QDesktopServices, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QApplication,
    QFrame,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStatusBar,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

from src.data.character_storage import CharacterStorage
from src.data.project_package import ProjectPackage
from src.font.sample_exporter import FontSampleExporter
from src.font.ttf_builder import TTFBuilder
from src.gui.canvas import HandwritingCanvas
from src.gui.styles import APP_STYLESHEET
from src.utils.characters import (
    CHARACTER_GROUPS,
    DEFAULT_CHARACTER_SEQUENCE,
    group_name_for_character,
)


class VectorPreviewWidget(QWidget):
    def __init__(self, storage: CharacterStorage, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.storage = storage
        self.preview_text = "Hello World!"
        self._stroke_cache: dict[str, list[list[list[float]]]] = {}
        self.setMinimumHeight(170)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.reload_data()

    def set_preview_text(self, text: str) -> None:
        self.preview_text = text or " "
        self.update()

    def reload_data(self) -> None:
        self._stroke_cache = {
            character: self.storage.load_strokes(character)
            for character in DEFAULT_CHARACTER_SEQUENCE
        }
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(QRectF(self.rect()), QColor("#ffffff"))

        border_pen = QPen(QColor("#d6dde8"), 1)
        painter.setPen(border_pen)
        painter.drawRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5))

        x = 20.0
        baseline = self.height() * 0.68
        max_height = self.height() * 0.62
        font = painter.font()
        font.setPointSize(24)
        painter.setFont(font)

        for character in self.preview_text:
            if x > self.width() - 30:
                break
            if character == " ":
                x += max_height * 0.36
                continue

            strokes = self._stroke_cache.get(character, [])
            if strokes:
                advance = self._draw_vector_character(
                    painter=painter,
                    character=character,
                    strokes=strokes,
                    origin_x=x,
                    baseline=baseline,
                    max_height=max_height,
                )
                x += advance
            else:
                painter.setPen(QColor("#8b98aa"))
                painter.drawText(QPointF(x, baseline), character)
                x += painter.fontMetrics().horizontalAdvance(character) + 5

    def _draw_vector_character(
        self,
        painter: QPainter,
        character: str,
        strokes: list[list[list[float]]],
        origin_x: float,
        baseline: float,
        max_height: float,
    ) -> float:
        del character
        points = [
            (float(point[0]), float(point[1]))
            for stroke in strokes
            for point in stroke
            if len(point) >= 2
        ]
        if not points:
            return max_height * 0.45

        min_x = min(point[0] for point in points)
        max_x = max(point[0] for point in points)
        min_y = min(point[1] for point in points)
        max_y = max(point[1] for point in points)
        source_width = max(1.0, max_x - min_x)
        source_height = max(1.0, max_y - min_y)
        scale = max_height / source_height
        advance = max(max_height * 0.35, source_width * scale + 16.0)
        draw_top = baseline - max_height

        pen = QPen(
            QColor("#111827"),
            max(2.0, 4.0 * scale / 3.0),
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
        painter.setPen(pen)

        for stroke in strokes:
            if len(stroke) < 2:
                continue
            mapped_points = [
                QPointF(
                    origin_x + (float(point[0]) - min_x) * scale,
                    draw_top + (float(point[1]) - min_y) * scale,
                )
                for point in stroke
                if len(point) >= 2
            ]
            for start, end in zip(mapped_points, mapped_points[1:]):
                painter.drawLine(start, end)

        return advance


class CharacterSetupWizard(QWizard):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Character Setup Wizard")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.addPage(self._page("Step 1", "Write uppercase letters", "A-Z"))
        self.addPage(self._page("Step 2", "Write lowercase letters", "a-z"))
        self.addPage(self._page("Step 3", "Write numbers", "0-9"))
        self.addPage(self._page("Step 4", "Write symbols", ".,!?;:'\"()[]{} and more"))
        self.addPage(self._page("Step 5", "Generate font", "Press Generate Font after saving your characters."))

    def _page(self, title: str, heading: str, body: str) -> QWizardPage:
        page = QWizardPage()
        page.setTitle(title)
        layout = QVBoxLayout(page)

        heading_label = QLabel(heading)
        heading_font = QFont()
        heading_font.setPointSize(18)
        heading_font.setBold(True)
        heading_label.setFont(heading_font)

        body_label = QLabel(body)
        body_label.setWordWrap(True)
        body_label.setMinimumWidth(360)

        layout.addWidget(heading_label)
        layout.addWidget(body_label)
        layout.addStretch(1)
        return page


class MainWindow(QMainWindow):
    def __init__(self, project_root: Path) -> None:
        super().__init__()
        self.project_root = Path(project_root)
        self.storage = CharacterStorage(self.project_root / "characters")
        self.output_dir = self.project_root / "output"
        self.output_dir.mkdir(exist_ok=True)
        self.current_character = DEFAULT_CHARACTER_SEQUENCE[0]
        self._loading_character = False
        self._dirty = False
        self.last_generated_font: Path | None = None
        self.last_sample_path: Path | None = None

        self.setWindowTitle("Personal Handwriting Font Creator")
        self.setStyleSheet(APP_STYLESHEET)
        self._build_ui()
        self._populate_character_list()
        self._select_character(self.current_character)
        self.setStatusBar(QStatusBar())
        self._update_status()

        wizard_marker = self.project_root / "characters" / ".setup_seen"
        if not wizard_marker.exists():
            QTimer.singleShot(150, self._show_startup_wizard)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._save_current_character()
        event.accept()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        modifiers = event.modifiers()
        key = event.key()

        if modifiers & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_S:
            self._save_current_character()
            event.accept()
            return
        if modifiers & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Z:
            self.canvas.undo()
            event.accept()
            return
        if modifiers & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Y:
            self.canvas.redo()
            event.accept()
            return

        if key == Qt.Key.Key_P:
            self.pen_button.setChecked(True)
            self.canvas.set_tool_mode("pen")
            event.accept()
            return
        if key == Qt.Key.Key_E:
            self.eraser_button.setChecked(True)
            self.canvas.set_tool_mode("eraser")
            event.accept()
            return
        if key == Qt.Key.Key_M:
            self.move_button.setChecked(True)
            self.canvas.set_tool_mode("move")
            event.accept()
            return

        nudge = 48 if modifiers & Qt.KeyboardModifier.ShiftModifier else 12
        if key == Qt.Key.Key_Left:
            self.canvas.nudge_strokes(-nudge, 0)
            event.accept()
            return
        if key == Qt.Key.Key_Right:
            self.canvas.nudge_strokes(nudge, 0)
            event.accept()
            return
        if key == Qt.Key.Key_Up:
            self.canvas.nudge_strokes(0, -nudge)
            event.accept()
            return
        if key == Qt.Key.Key_Down:
            self.canvas.nudge_strokes(0, nudge)
            event.accept()
            return

        super().keyPressEvent(event)

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(14, 14, 14, 10)
        root_layout.setSpacing(12)

        self.character_list = QListWidget()
        self.character_list.setMinimumWidth(150)
        self.character_list.setMaximumWidth(190)
        self.character_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.character_list.currentItemChanged.connect(self._on_character_item_changed)

        header = self._build_header()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)

        self.prompt_label = QLabel()
        self.prompt_label.setObjectName("PromptLabel")
        prompt_font = QFont()
        prompt_font.setPointSize(22)
        prompt_font.setBold(True)
        self.prompt_label.setFont(prompt_font)
        self.prompt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.canvas_hint_label = QLabel("Draw inside the guide box. Save moves your work into the font project.")
        self.canvas_hint_label.setObjectName("CanvasHint")
        self.canvas_hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.canvas = HandwritingCanvas()
        self.canvas.stroke_changed.connect(self._on_canvas_changed)

        center_layout.addWidget(self.prompt_label)
        center_layout.addWidget(self.canvas_hint_label)
        center_layout.addWidget(self.canvas, 1)
        center_layout.addLayout(self._build_quick_actions())

        tools_panel = self._build_tools_panel()
        main_layout.addWidget(self._wrap_panel("Character List", self.character_list), 0)
        main_layout.addWidget(center_panel, 1)
        main_layout.addWidget(tools_panel, 0)

        root_layout.addWidget(header)
        root_layout.addLayout(main_layout, 1)
        self.setCentralWidget(root)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("Header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        title_stack = QVBoxLayout()
        title_stack.setSpacing(3)
        title = QLabel("Personal Handwriting Font Creator")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Write, refine, preview, and export an installable TTF font.")
        subtitle.setObjectName("AppSubtitle")
        title_stack.addWidget(title)
        title_stack.addWidget(subtitle)

        self.step_label = QLabel()
        self.step_label.setObjectName("StepLabel")
        self.header_progress = QProgressBar()
        self.header_progress.setRange(0, len(DEFAULT_CHARACTER_SEQUENCE))
        self.header_progress.setTextVisible(False)
        self.header_progress.setFixedWidth(210)
        self.progress_text_label = QLabel()
        self.progress_text_label.setObjectName("ProgressText")

        layout.addLayout(title_stack, 1)
        layout.addWidget(self.step_label)
        layout.addWidget(self.header_progress)
        layout.addWidget(self.progress_text_label)
        return header

    def _build_quick_actions(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.quick_previous_button = QPushButton("Previous")
        self.quick_save_button = QPushButton("Save")
        self.quick_save_button.setObjectName("PrimaryButton")
        self.quick_next_button = QPushButton("Save and Next")
        self.quick_next_button.setObjectName("PrimaryButton")
        self.quick_center_button = QPushButton("Center")
        self.quick_clear_button = QPushButton("Clear")

        self.quick_previous_button.clicked.connect(self._go_previous)
        self.quick_save_button.clicked.connect(self._save_current_character)
        self.quick_next_button.clicked.connect(self._go_next)
        self.quick_center_button.clicked.connect(self.canvas.center_strokes)
        self.quick_clear_button.clicked.connect(self.canvas.clear)

        layout.addStretch(1)
        layout.addWidget(self.quick_previous_button)
        layout.addWidget(self.quick_clear_button)
        layout.addWidget(self.quick_center_button)
        layout.addWidget(self.quick_save_button)
        layout.addWidget(self.quick_next_button)
        layout.addStretch(1)
        return layout

    def _build_tools_panel(self) -> QWidget:
        panel = QWidget()
        panel.setMinimumWidth(330)
        panel.setMaximumWidth(380)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        draw_box = QGroupBox("Draw")
        draw_layout = QGridLayout(draw_box)

        self.pen_button = QPushButton("Pen")
        self.eraser_button = QPushButton("Eraser")
        self.move_button = QPushButton("Move")
        for button in (self.pen_button, self.eraser_button, self.move_button):
            button.setCheckable(True)
        self.pen_button.setChecked(True)
        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(True)
        self.tool_group.addButton(self.pen_button)
        self.tool_group.addButton(self.eraser_button)
        self.tool_group.addButton(self.move_button)
        self.pen_button.clicked.connect(lambda: self.canvas.set_tool_mode("pen"))
        self.eraser_button.clicked.connect(lambda: self.canvas.set_tool_mode("eraser"))
        self.move_button.clicked.connect(lambda: self.canvas.set_tool_mode("move"))

        self.eraser_size_label = QLabel("Eraser: 28")
        self.eraser_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.eraser_size_slider.setRange(8, 80)
        self.eraser_size_slider.setValue(28)
        self.eraser_size_slider.valueChanged.connect(self._on_eraser_size_changed)

        self.pen_button.setToolTip("Draw a new handwriting stroke.")
        self.eraser_button.setToolTip("Remove whole strokes near the cursor.")
        self.move_button.setToolTip("Drag the saved strokes around the canvas.")

        draw_layout.addWidget(self.pen_button, 0, 0)
        draw_layout.addWidget(self.eraser_button, 0, 1)
        draw_layout.addWidget(self.move_button, 0, 2)
        draw_layout.addWidget(self.eraser_size_label, 1, 0)
        draw_layout.addWidget(self.eraser_size_slider, 1, 1, 1, 2)

        refine_box = QGroupBox("Refine")
        refine_layout = QGridLayout(refine_box)

        self.clear_button = QPushButton("Clear")
        self.undo_button = QPushButton("Undo")
        self.redo_button = QPushButton("Redo")
        self.save_button = QPushButton("Save Character")
        self.previous_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.center_button = QPushButton("Center")
        self.scale_up_button = QPushButton("Scale +")
        self.scale_down_button = QPushButton("Scale -")
        self.left_button = QPushButton("Left")
        self.right_button = QPushButton("Right")
        self.up_button = QPushButton("Up")
        self.down_button = QPushButton("Down")
        self.preview_button = QPushButton("Preview Font")
        self.generate_button = QPushButton("Generate Font")
        self.generate_button.setObjectName("ExportButton")

        self.font_family_input = QLineEdit("MyHandwriting")
        self.font_family_input.setPlaceholderText("Font family name")
        self.export_dir_input = QLineEdit(str(self.output_dir))
        self.export_dir_input.setReadOnly(True)
        self.browse_output_button = QPushButton("Choose Folder")
        self.open_output_button = QPushButton("Open Output")
        self.copy_path_button = QPushButton("Copy Font Path")
        self.open_font_button = QPushButton("Open Font")
        self.install_font_button = QPushButton("Install Font")
        self.sample_page_button = QPushButton("Sample Page")
        self.backup_project_button = QPushButton("Backup Project")
        self.restore_project_button = QPushButton("Restore Project")
        self.missing_report_button = QPushButton("Missing Report")

        self.clear_button.clicked.connect(self.canvas.clear)
        self.undo_button.clicked.connect(self.canvas.undo)
        self.redo_button.clicked.connect(self.canvas.redo)
        self.save_button.clicked.connect(self._save_current_character)
        self.previous_button.clicked.connect(self._go_previous)
        self.next_button.clicked.connect(self._go_next)
        self.center_button.clicked.connect(self.canvas.center_strokes)
        self.scale_up_button.clicked.connect(lambda: self.canvas.scale_strokes(1.08))
        self.scale_down_button.clicked.connect(lambda: self.canvas.scale_strokes(0.92))
        self.left_button.clicked.connect(lambda: self.canvas.nudge_strokes(-18, 0))
        self.right_button.clicked.connect(lambda: self.canvas.nudge_strokes(18, 0))
        self.up_button.clicked.connect(lambda: self.canvas.nudge_strokes(0, -18))
        self.down_button.clicked.connect(lambda: self.canvas.nudge_strokes(0, 18))
        self.preview_button.clicked.connect(self._refresh_preview)
        self.generate_button.clicked.connect(self._generate_font)
        self.browse_output_button.clicked.connect(self._choose_output_dir)
        self.open_output_button.clicked.connect(self._open_output_dir)
        self.copy_path_button.clicked.connect(self._copy_last_font_path)
        self.open_font_button.clicked.connect(self._open_last_font)
        self.install_font_button.clicked.connect(self._install_last_font)
        self.sample_page_button.clicked.connect(self._export_sample_page)
        self.backup_project_button.clicked.connect(self._backup_project)
        self.restore_project_button.clicked.connect(self._restore_project)
        self.missing_report_button.clicked.connect(self._write_missing_report)

        refine_layout.addWidget(self.clear_button, 0, 0)
        refine_layout.addWidget(self.undo_button, 0, 1)
        refine_layout.addWidget(self.redo_button, 0, 2)
        refine_layout.addWidget(self.save_button, 1, 0, 1, 3)
        refine_layout.addWidget(self.previous_button, 2, 0)
        refine_layout.addWidget(self.next_button, 2, 1, 1, 2)
        refine_layout.addWidget(self.center_button, 3, 0)
        refine_layout.addWidget(self.scale_up_button, 3, 1)
        refine_layout.addWidget(self.scale_down_button, 3, 2)
        refine_layout.addWidget(self.left_button, 4, 0)
        refine_layout.addWidget(self.up_button, 4, 1)
        refine_layout.addWidget(self.right_button, 4, 2)
        refine_layout.addWidget(self.down_button, 5, 1)

        preview_box = QGroupBox("Font Preview")
        preview_layout = QVBoxLayout(preview_box)
        self.preview_input = QLineEdit("Hello World!")
        self.preview_input.textChanged.connect(self._on_preview_text_changed)
        self.preview_widget = VectorPreviewWidget(self.storage)
        preview_layout.addWidget(self.preview_input)
        preview_layout.addWidget(self.preview_widget)

        project_box = QGroupBox("Project")
        project_layout = QGridLayout(project_box)
        project_layout.addWidget(self.backup_project_button, 0, 0)
        project_layout.addWidget(self.restore_project_button, 0, 1)
        project_layout.addWidget(self.missing_report_button, 1, 0, 1, 2)

        export_box = QGroupBox("Export")
        export_layout = QGridLayout(export_box)
        export_layout.addWidget(QLabel("Font name"), 0, 0)
        export_layout.addWidget(self.font_family_input, 0, 1, 1, 2)
        export_layout.addWidget(QLabel("Folder"), 1, 0)
        export_layout.addWidget(self.export_dir_input, 1, 1)
        export_layout.addWidget(self.browse_output_button, 1, 2)
        export_layout.addWidget(self.generate_button, 2, 0, 1, 3)
        export_layout.addWidget(self.open_output_button, 3, 0)
        export_layout.addWidget(self.open_font_button, 3, 1)
        export_layout.addWidget(self.install_font_button, 3, 2)
        export_layout.addWidget(self.sample_page_button, 4, 0)
        export_layout.addWidget(self.copy_path_button, 4, 1, 1, 2)

        stats_box = QGroupBox("Progress")
        stats_layout = QVBoxLayout(stats_box)
        self.progress_label = QLabel()
        self.progress_label.setWordWrap(True)
        stats_layout.addWidget(self.progress_label)

        layout.addWidget(draw_box)
        layout.addWidget(refine_box)
        layout.addWidget(preview_box)
        layout.addWidget(project_box)
        layout.addWidget(export_box)
        layout.addWidget(stats_box)
        layout.addStretch(1)
        return panel

    def _wrap_panel(self, title: str, widget: QWidget) -> QFrame:
        frame = QFrame()
        frame.setObjectName("Panel")
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        label = QLabel(title)
        label.setObjectName("PanelTitle")
        label_font = QFont()
        label_font.setBold(True)
        label.setFont(label_font)
        layout.addWidget(label)
        layout.addWidget(widget)
        return frame

    def _populate_character_list(self) -> None:
        for group_name, characters in CHARACTER_GROUPS:
            header = QListWidgetItem(group_name)
            header.setFlags(Qt.ItemFlag.NoItemFlags)
            header.setForeground(QColor("#667085"))
            self.character_list.addItem(header)
            for character in characters:
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, character)
                self.character_list.addItem(item)
        self._refresh_character_list_labels()

    def _refresh_character_list_labels(self) -> None:
        for row in range(self.character_list.count()):
            item = self.character_list.item(row)
            character = item.data(Qt.ItemDataRole.UserRole)
            if character is None:
                continue
            status = "DONE" if self.storage.has_character(character) else "TODO"
            item.setText(f"{status:4}  {character}")

    def _select_character(self, character: str) -> None:
        for row in range(self.character_list.count()):
            item = self.character_list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == character:
                self.character_list.setCurrentItem(item)
                return

    def _on_character_item_changed(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        del previous
        if current is None:
            return
        character = current.data(Qt.ItemDataRole.UserRole)
        if character is None:
            return

        if not self._loading_character and character != self.current_character:
            self._save_current_character()

        self.current_character = character
        self._load_current_character()

    def _load_current_character(self) -> None:
        self._loading_character = True
        try:
            data = self.storage.load_character(self.current_character)
            self.canvas.set_target_character(self.current_character)
            self.canvas.load_json_strokes(data.get("strokes", []))
            self.prompt_label.setText(f"Please write: {self.current_character}")
            self._dirty = False
        finally:
            self._loading_character = False
        self._update_status()

    def _on_canvas_changed(self) -> None:
        if not self._loading_character:
            self._dirty = True
        self._update_status()

    def _save_current_character(self) -> None:
        self.storage.save_character(self.current_character, self.canvas.to_json_strokes())
        self._dirty = False
        self._refresh_preview()
        self._refresh_character_list_labels()
        self._update_status()
        self.statusBar().showMessage(f"Saved U+{ord(self.current_character):04X}", 2400)

    def _go_previous(self) -> None:
        index = DEFAULT_CHARACTER_SEQUENCE.index(self.current_character)
        previous_index = max(0, index - 1)
        self._select_character(DEFAULT_CHARACTER_SEQUENCE[previous_index])

    def _go_next(self) -> None:
        self._save_current_character()
        index = DEFAULT_CHARACTER_SEQUENCE.index(self.current_character)
        next_index = min(len(DEFAULT_CHARACTER_SEQUENCE) - 1, index + 1)
        self._select_character(DEFAULT_CHARACTER_SEQUENCE[next_index])

    def _refresh_preview(self) -> None:
        self.preview_widget.reload_data()

    def _on_preview_text_changed(self, text: str) -> None:
        self.preview_widget.set_preview_text(text)

    def _on_eraser_size_changed(self, value: int) -> None:
        self.canvas.set_eraser_radius(value)
        self.eraser_size_label.setText(f"Eraser: {value}")

    def _generate_font(self) -> None:
        self._save_current_character()
        family_name = self.font_family_input.text().strip() or "MyHandwriting"
        saved = self.storage.saved_count()
        total = len(DEFAULT_CHARACTER_SEQUENCE)
        if saved == 0:
            QMessageBox.warning(self, "No Characters Saved", "Write and save at least one character before exporting.")
            return
        if saved < total:
            answer = QMessageBox.question(
                self,
                "Export Partial Font",
                f"{saved}/{total} characters are saved. Export the partial font now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        output_path = self.output_dir / f"{self._safe_font_filename(family_name)}.ttf"
        builder = TTFBuilder(storage=self.storage, family_name=family_name)
        written_path = builder.build(output_path=output_path)
        self.last_generated_font = written_path
        self._export_sample_page(show_message=False)
        QApplication.clipboard().setText(str(written_path))
        QMessageBox.information(
            self,
            "Font Generated",
            f"Generated font:\n{written_path}\n\nA sample page was also created.\nThe font path was copied to the clipboard.",
        )
        self.statusBar().showMessage(f"Generated {written_path}", 5000)

    def _backup_project(self) -> None:
        self._save_current_character()
        family_name = self.font_family_input.text().strip() or "MyHandwriting"
        default_path = self.output_dir / f"{self._safe_font_filename(family_name)}-project.zip"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Backup Project",
            str(default_path),
            "Handwriting Project (*.zip)",
        )
        if not path:
            return
        written = ProjectPackage(self.storage).export_zip(Path(path), family_name)
        QApplication.clipboard().setText(str(written))
        self.statusBar().showMessage(f"Project backup saved: {written}", 5000)

    def _restore_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Restore Project",
            str(self.output_dir),
            "Handwriting Project (*.zip)",
        )
        if not path:
            return
        restored = ProjectPackage(self.storage).import_zip(Path(path))
        self._refresh_preview()
        self._refresh_character_list_labels()
        self._load_current_character()
        self.statusBar().showMessage(f"Restored {restored} characters.", 5000)
        QMessageBox.information(self, "Project Restored", f"Restored {restored} character files.")

    def _write_missing_report(self) -> None:
        self._save_current_character()
        family_name = self.font_family_input.text().strip() or "MyHandwriting"
        default_path = self.output_dir / f"{self._safe_font_filename(family_name)}-missing.txt"
        report = ProjectPackage(self.storage).write_missing_report(default_path)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(report)))
        self.statusBar().showMessage(f"Missing report written: {report}", 5000)

    def _export_sample_page(self, show_message: bool = True) -> None:
        if self.last_generated_font is None or not self.last_generated_font.exists():
            if show_message:
                self.statusBar().showMessage("Generate a font first.", 2400)
            return
        family_name = self.font_family_input.text().strip() or "MyHandwriting"
        sample_path = self.last_generated_font.with_name(f"{self.last_generated_font.stem}-sample.html")
        self.last_sample_path = FontSampleExporter().export_html(
            output_path=sample_path,
            font_path=self.last_generated_font,
            family_name=family_name,
            sample_text=self.preview_input.text(),
            saved_count=self.storage.saved_count(),
            total_count=len(DEFAULT_CHARACTER_SEQUENCE),
        )
        if show_message:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_sample_path)))
            self.statusBar().showMessage(f"Sample page opened: {self.last_sample_path}", 5000)

    def _choose_output_dir(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self,
            "Choose Export Folder",
            str(self.output_dir),
        )
        if not chosen:
            return
        self.output_dir = Path(chosen)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir_input.setText(str(self.output_dir))

    def _open_output_dir(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.output_dir)))

    def _copy_last_font_path(self) -> None:
        if self.last_generated_font is None:
            self.statusBar().showMessage("Generate a font first.", 2400)
            return
        QApplication.clipboard().setText(str(self.last_generated_font))
        self.statusBar().showMessage("Copied font path to clipboard.", 2400)

    def _open_last_font(self) -> None:
        if self.last_generated_font is None or not self.last_generated_font.exists():
            self.statusBar().showMessage("Generate a font first.", 2400)
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_generated_font)))

    def _install_last_font(self) -> None:
        if self.last_generated_font is None or not self.last_generated_font.exists():
            self.statusBar().showMessage("Generate a font first.", 2400)
            return

        if sys.platform == "darwin":
            fonts_dir = Path.home() / "Library" / "Fonts"
            fonts_dir.mkdir(parents=True, exist_ok=True)
            target = fonts_dir / self.last_generated_font.name
            shutil.copy2(self.last_generated_font, target)
            QMessageBox.information(self, "Font Installed", f"Installed font to:\n{target}")
            self.statusBar().showMessage(f"Installed font: {target}", 5000)
            return

        if sys.platform.startswith("win"):
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_generated_font)))
            self.statusBar().showMessage("Opened font file. Use the Install button in the font viewer.", 5000)
            return

        fonts_dir = Path.home() / ".local" / "share" / "fonts"
        fonts_dir.mkdir(parents=True, exist_ok=True)
        target = fonts_dir / self.last_generated_font.name
        shutil.copy2(self.last_generated_font, target)
        QMessageBox.information(self, "Font Installed", f"Installed font to:\n{target}")
        self.statusBar().showMessage(f"Installed font: {target}", 5000)

    def _safe_font_filename(self, family_name: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9_-]+", "", family_name.replace(" ", ""))
        return cleaned or "MyHandwriting"

    def _show_startup_wizard(self) -> None:
        wizard = CharacterSetupWizard(self)
        wizard.exec()
        marker = self.project_root / "characters" / ".setup_seen"
        marker.write_text("shown\n", encoding="utf-8")
        self._select_character(DEFAULT_CHARACTER_SEQUENCE[0])

    def _update_status(self) -> None:
        saved = self.storage.saved_count()
        total = len(DEFAULT_CHARACTER_SEQUENCE)
        group = group_name_for_character(self.current_character)
        dirty = "Unsaved changes" if self._dirty else "Saved"
        index = DEFAULT_CHARACTER_SEQUENCE.index(self.current_character) + 1
        self.step_label.setText(f"{group} {index}/{total}")
        self.header_progress.setValue(saved)
        self.progress_text_label.setText(f"{saved}/{total} saved")
        self.progress_label.setText(
            f"Current: {self.current_character} / U+{ord(self.current_character):04X}\n"
            f"Group: {group}\n"
            f"Saved: {saved}/{total}\n"
            f"State: {dirty}"
        )
