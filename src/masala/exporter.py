from __future__ import annotations

import importlib.util
import os
import sys
from enum import StrEnum, auto
from importlib.machinery import ModuleSpec
from pathlib import Path

import qtawesome
from qtpy.QtCore import QEvent, Qt
from qtpy.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from masala.api import Exporter
from masala.gui.container import ContainerDialog, ContainerWidget
from masala.gui.utils import format_widgets, get_masala_exporter_icon, get_qt_app, get_theme

THEME = get_theme()
FRAME_HEIGHT = 200


class ExporterStatus(StrEnum):
    """Lists the available statuses for Exporters"""

    WAITING = auto()
    OK = auto()
    ERROR = auto()


class TableMenu(QMenu):
    """Context menu shown on right-click within the exporter table."""

    def __init__(self, table: ExportersTableWidget):
        """Create a table context menu for the given table widget."""
        super().__init__(table)
        self.table = table
        self.masala_exporter_widget = table.masala_exporter_widget

        # Collapse all
        action = self.addAction("Collapse All")
        action.setIcon(qtawesome.icon("mdi.arrow-collapse-vertical", color=THEME["icon_color"]))
        action.triggered.connect(self.collapse_all)

        # Sort by name
        action = self.addAction("Sort By Name")
        action.setIcon(qtawesome.icon("fa5s.sort-alpha-down", color=THEME["icon_color"]))
        action.triggered.connect(self.sort_by_name)

        # Sort by status
        action = self.addAction("Sort By Status")
        action.setIcon(qtawesome.icon("mdi.sort-bool-ascending-variant", color=THEME["icon_color"]))
        action.triggered.connect(self.sort_by_status)

        # Disable sorting
        action = self.addAction("Disable Sorting")
        action.setIcon(qtawesome.icon("mdi6.sort-variant-off", color=THEME["icon_color"]))
        action.triggered.connect(self.sort_by_index)

    def collapse_all(self):
        """Collapse all expandable exporter sections in the table."""
        for exporter_widget in self.masala_exporter_widget.exporter_widgets:
            exporter_widget.toggle_logs_button.collapse_frame()

    def sort_by_status(self):
        """Sort table rows by exporter status."""
        self.table.sortByColumn(self.table._status_column_index, Qt.SortOrder.AscendingOrder)

    def sort_by_name(self):
        """Sort table rows by exporter label."""
        self.table.sortByColumn(self.table._label_column_index, Qt.SortOrder.AscendingOrder)

    def sort_by_index(self):
        """Restore the original table order by index."""
        self.table.sortByColumn(self.table._index_column_index, Qt.SortOrder.AscendingOrder)


class ToggleAreaButton(QPushButton):
    """Button that toggles visibility of a collapsible section inside a exporter."""

    def __init__(
        self,
        area_name: str,
        exporter_widget: ExporterWidget,
        collapsible_frame: QFrame,
    ):
        """Initialize a collapsible area toggle button.

        Args:
            area_name: Human-readable section name.
            exporter_widget: Parent exporter widget.
            collapsible_frame: Frame that is shown or hidden.
        """
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setProperty("status", "invisible")
        self.area_name = area_name.capitalize()
        self.exporter_widget = exporter_widget
        self.collapsible_frame = collapsible_frame
        self.collapsed = True
        self.update_look()
        self.clicked.connect(self.toggle_area)
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumHeight(0)
        self.setStyleSheet("margin:0px; padding:3px")

    def expand_frame(self):
        """Expand the associated collapsible frame."""
        self.collapsed = False
        self.update()

    def collapse_frame(self):
        """Collapse the associated collapsible frame."""
        self.collapsed = True
        self.update()

    def toggle_area(self):
        """Toggle the expanded/collapsed state of the area."""
        self.collapsed = not self.collapsed
        self.update()

    def update(self):
        """Refresh button appearance and update row height."""
        self.update_look()
        self.update_collapsible_frame()
        self.exporter_widget.update_row_height()

    def update_look(self):
        """Update the button label and icon based on current state."""
        self.setText(f"Show {self.area_name}" if self.collapsed else f"Hide {self.area_name}")
        icon_name = "fa6s.caret-right" if self.collapsed else "fa6s.caret-down"
        self.setIcon(qtawesome.icon(icon_name, color=THEME["icon_color"]))

    def update_collapsible_frame(self):
        """Show or hide the target collapsible frame."""
        self.collapsible_frame.setHidden(self.collapsed)


class ExporterTableItem(QTableWidgetItem):
    """Table item used as a bridge to retrieve the row from an exporter widget."""

    def __init__(self):
        """Initialize a exporter table item capable of storing a widget reference."""
        super().__init__()
        self.exporter_widget: ExporterWidget


class ExporterWidget(QFrame):
    """UI representation of a single Exporter inside the SpicyQC table."""

    def __init__(
        self,
        exporter: Exporter,
        masala_exporter_widget: MasalaExporterWidget,
    ):
        """Create a Exporter widget and its collapsible sections."""
        super().__init__()
        self.masala_exporter_widget = masala_exporter_widget
        self.table = self.masala_exporter_widget.table
        self.exporter = exporter
        self.table_item: ExporterTableItem | None = None
        self.assistant_frame_scroll_area: QScrollArea | None = None
        self.icon_toggle_collapsed = qtawesome.icon("fa6s.caret-right", scale_factor=1.2, color=THEME["icon_color"])
        self.icon_toggle_expanded = qtawesome.icon("fa6s.caret-down", scale_factor=1.2, color=THEME["icon_color"])
        self.collapsed_height: int = 10
        self.status = ExporterStatus.WAITING
        self.setup_ui()
        self.setup_signals()

    def setup_ui(self):
        """Build the internal user interface for the Exporter widget."""
        # Add a container with a few pixels of margin to make the selection more visually clear
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 0, 0, 0)

        # Layout with the "main frame" and the frame that appears when expanded
        container_frame = QFrame()
        layout.addWidget(container_frame)
        container_layout = QVBoxLayout(container_frame)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Main frame
        main_frame = QFrame()
        container_layout.addWidget(main_frame)
        self.main_layout = QVBoxLayout(main_frame)
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.main_layout.setSpacing(3)

        # sub-frames
        frame_top = QFrame()
        frame_top_layout = QHBoxLayout(frame_top)
        frame_top_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(frame_top)

        frame_left = QFrame()
        frame_left.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        frame_left_layout = QVBoxLayout(frame_left)
        frame_left_layout.setContentsMargins(0, 0, 0, 0)
        frame_left_layout.setSpacing(2)
        frame_top_layout.addWidget(frame_left)

        frame_right = QFrame()
        frame_right_layout = QVBoxLayout(frame_right)
        frame_right_layout.setContentsMargins(0, 0, 0, 0)
        frame_top_layout.addWidget(frame_right)

        subframe_right = QFrame()
        subframe_right_layout = QHBoxLayout(subframe_right)
        subframe_right_layout.setContentsMargins(0, 0, 0, 0)
        frame_right_layout.addWidget(subframe_right)

        # Name & description
        label = QLabel(self.exporter.assetblock.label)
        frame_left_layout.addWidget(label)
        description = QLabel(self.exporter.assetblock.description)
        description.setProperty("status", "secondary")
        frame_left_layout.addWidget(description)

        # Export Button
        self.export_button = QPushButton("Export")
        self.export_button.setProperty("status", "important")
        subframe_right_layout.addWidget(self.export_button)

        # Status label
        self.status_label = QLabel()
        size = 24
        self.status_label.setFixedSize(size, size)
        subframe_right_layout.addWidget(self.status_label)
        self.update_status_label()

        # Toggle buttons frame
        toggle_areas_frame = QFrame()
        toggle_areas_layout = QHBoxLayout(toggle_areas_frame)
        toggle_areas_layout.setContentsMargins(0, 0, 0, 0)
        toggle_areas_layout.setSpacing(0)
        frame_left_layout.addWidget(toggle_areas_frame)

        # HIDDEN Log Frame
        self.log_frame = QFrame()
        self.log_frame.setFixedHeight(FRAME_HEIGHT)
        log_frame_layout = QVBoxLayout(self.log_frame)
        log_frame_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.log_frame)
        self.log_frame.setHidden(True)

        self.stdout_view = QPlainTextEdit()
        self.stdout_view.setProperty("status", "code")
        self.stdout_view.setReadOnly(True)
        log_frame_layout.addWidget(self.stdout_view)
        self.stdout_view.setPlainText("Export was not done yet")

        # Toggle Logs Button
        self.toggle_logs_button = ToggleAreaButton("logs", self, self.log_frame)
        toggle_areas_layout.addWidget(self.toggle_logs_button)

        # Stretch
        toggle_areas_layout.addStretch()

        # Format widgets
        format_widgets(self)

    def setup_signals(self):
        """Connect widget button signals to the appropriate handlers."""
        self.export_button.clicked.connect(self.export_button_clicked)
        # self.toggle_logs_button.clicked.connect(self.logs_button_clicked)

    def update_row_height(self):
        """Recompute and set the table row height based on visible sections."""
        top_height = 83
        log_height = self.log_frame.height() + self.main_layout.spacing()
        log_multiplier = int(self.log_frame.isVisible())

        total_height = top_height + (log_height * log_multiplier)
        self.table.setRowHeight(self.current_row, total_height)

    @property
    def current_row(self) -> int:
        """Return the table row index for this exporter widget."""
        if not self.table_item:
            return -1
        return self.table_item.row()

    def update_status_label(self):
        """Update the visible status icon based on the exporter status."""
        color = {
            ExporterStatus.WAITING: THEME["disabled"],
            ExporterStatus.OK: THEME["ok"],
            ExporterStatus.ERROR: THEME["error"],
        }[self.status]

        icon_name = {
            ExporterStatus.WAITING: "ri.question-fill",
            ExporterStatus.OK: "ri.checkbox-circle-fill",
            ExporterStatus.ERROR: "ri.close-circle-fill",
        }[self.status]
        icon = qtawesome.icon(icon_name, color=color)
        size = self.status_label.width()
        pixmap = icon.pixmap(size, size)
        self.status_label.setPixmap(pixmap)

    def update_status_column(self):
        """Update the hidden status column used for table sorting."""
        statuses_order = [
            ExporterStatus.WAITING,
            ExporterStatus.OK,
            ExporterStatus.ERROR,
        ]
        index_str = str(statuses_order.index(self.status)).zfill(2)
        self.table.item(self.current_row, self.table._status_column_index).setText(index_str)  # type: ignore

    def export_button_clicked(self):
        self.update_selection()
        self.masala_exporter_widget.run_selected_exporters()

    def update_selection(self):
        """Ensure this Exporter widget is selected when export is triggered."""
        if self not in self.masala_exporter_widget.selected_exporter_widgets:
            self.table.clearSelection()
            self.table.selectRow(self.current_row)

    def run(self):
        """Trigger execution of the exporter and refresh related views."""
        self.exporter.export(raise_on_error=False)
        self.update_status()
        self.update_stdout_text()

    def update_status(self):
        if self.exporter.error:
            self.status = ExporterStatus.ERROR
        else:
            self.status = ExporterStatus.OK
        self.update_status_label()
        self.update_status_column()

    def update_stdout_text(self):
        """Refresh the log text displayed in the log panel."""
        self.stdout_view.setPlainText(self.exporter.logs)


class ExportersTableWidget(QTableWidget):
    def __init__(self, masala_exporter_widget: MasalaExporterWidget) -> None:
        """Initialize the exporter table used by the main widget."""
        super().__init__(masala_exporter_widget)
        self.masala_exporter_widget = masala_exporter_widget
        self._columns = ["label", "index", "status", "exporter"]
        self._label_column_index = self._columns.index("label")
        self._index_column_index = self._columns.index("index")
        self._status_column_index = self._columns.index("status")
        self._exporter_column_index = self._columns.index("exporter")
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMinimumWidth(550)
        self.installEventFilter(self)
        self.setColumnCount(len(self._columns))
        self.setHorizontalHeaderLabels(self._columns)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        for i in range(len(self._columns) - 1):
            self.setColumnHidden(i, True)

    def contextMenuEvent(self, event: QEvent):
        """Show the table context menu when the user right-clicks."""
        menu = TableMenu(self)
        menu.exec_(event.globalPos())  # type: ignore


class MasalaExporterWidget(QWidget):
    def __init__(
        self,
        exporters: list[Exporter],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.exporters = exporters
        self.exporter_widgets: list[ExporterWidget] = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Masala Exporter")
        title.setProperty("tag", "H2")
        layout.addWidget(title)

        # Exporters
        frame = QFrame()
        frame.setProperty("depth", "0")
        layout.addWidget(frame)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(1, 1, 1, 1)
        self.table = ExportersTableWidget(self)
        frame_layout.addWidget(self.table)
        for i, exporter in enumerate(self.exporters):
            self.add_exporter_widget(i, exporter)

    def add_exporter_widget(self, index: int, exporter: Exporter):
        """Instantiate and insert a exporter widget into the table."""
        exporter_widget = ExporterWidget(exporter=exporter, masala_exporter_widget=self)
        self.exporter_widgets.append(exporter_widget)
        row_number = self.table.rowCount()
        self.table.insertRow(row_number)

        # label item
        label_item = QTableWidgetItem()
        label_item.setText(exporter_widget.exporter.assetblock.label)
        self.table.setItem(row_number, self.table._label_column_index, label_item)

        # Index item
        index_item = QTableWidgetItem()
        index_item.setText(str(index).zfill(5))
        self.table.setItem(row_number, self.table._index_column_index, index_item)

        # Status item
        status_item = QTableWidgetItem()
        self.table.setItem(row_number, self.table._status_column_index, status_item)

        # exporter item
        exporter_item = ExporterTableItem()

        # Pass item to the ExporterWidget and vice versa to allow row manipulation later on
        exporter_widget.table_item = exporter_item
        exporter_item.exporter_widget = exporter_widget

        # Add item & widget to the table
        self.table.setItem(row_number, self.table._exporter_column_index, exporter_item)
        self.table.setCellWidget(row_number, self.table._exporter_column_index, exporter_widget)

        # Update row height once all widgets are properly inserted to the table
        exporter_widget.update_row_height()

        # Update status
        exporter_widget.update_status_column()

    @property
    def selected_exporter_widgets(self) -> list[ExporterWidget]:
        """Return the currently selected exporter widgets from the table."""
        widgets = []
        for item in self.table.selectedItems():
            if isinstance(item, ExporterTableItem):
                widgets.append(item.exporter_widget)
        return widgets

    def run_selected_exporters(self):
        """Verify all currently selected exporters in the table."""
        for exporter_widget in self.selected_exporter_widgets:
            exporter_widget.run()


def get_exporters_config_from_path(
    exporters_module_path: str | Path,
) -> list[Exporter]:
    exporters_module_path = Path(exporters_module_path)
    config_package_path = exporters_module_path.parent

    # Ensure package structure
    required_paths = [
        config_package_path,
        config_package_path.joinpath("__init__.py"),
        config_package_path.joinpath("assetblocks_config.py"),
        config_package_path.joinpath("codex_config.py"),
        exporters_module_path,
    ]
    for _path in required_paths:
        if not _path.exists():
            raise FileNotFoundError(f"Wrong config package structure. File is missing : {_path}")

    # Import the package (__init__.py)
    package_name = "masala_exporter_config"
    spec = importlib.util.spec_from_file_location(
        package_name,
        config_package_path.joinpath("__init__.py"),
        submodule_search_locations=[config_package_path.as_posix()],
    )
    assert isinstance(spec, ModuleSpec)
    package_module = importlib.util.module_from_spec(spec)
    sys.modules[package_name] = package_module
    spec.loader.exec_module(package_module)  # type: ignore

    # Import the specific submodule dynamically
    full_submodule_name = f"{package_name}.{exporters_module_path.stem}"
    submodule = importlib.import_module(full_submodule_name)

    # Load exporters from the submodule
    exporters = getattr(submodule, "exporters")
    return exporters


def show_exporter_dialog(exporters: list[Exporter] | None = None):
    if not exporters:
        var = "MASALA_EXPORTERS_CONFIG"
        path = os.environ.get(var)
        if not path:
            raise RuntimeError(
                f"Please provide exporters, or provide a path to the exporters configuration file with the {var} environment variable"
            )
        exporters = get_exporters_config_from_path(path)

    app = get_qt_app()
    widget = MasalaExporterWidget(exporters=exporters)
    container = ContainerWidget(widget=widget, title="Masala Exporter", icon=get_masala_exporter_icon())
    dialog = ContainerDialog(container=container)
    dialog.show()
    app.exec_()
