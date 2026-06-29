from qtpy.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from masala.api import Exporter
from masala.gui.container import ContainerDialog, ContainerWidget
from masala.gui.utils import get_masala_exporter_icon, get_qt_app


class ExporterCheckbox(QCheckBox):
    def __init__(self, exporter: Exporter):
        self.exporter = exporter
        super().__init__(exporter.assetblock.label)


class MasalaExporterWidget(QWidget):
    def __init__(
        self,
        exporters: list[Exporter],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.exporters = exporters
        self.exporter_ckeckboxes: list[ExporterCheckbox] = []
        self.setup_ui()
        self.setup_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Masala Exporter")
        title.setProperty("tag", "H2")
        layout.addWidget(title)

        # Exporter Checkboxes
        frame = QFrame()
        frame.setProperty("depth", "0")
        layout.addWidget(frame)
        exporters_layout = QVBoxLayout(frame)
        exporters_layout.setSpacing(0)
        exporters_layout.setContentsMargins(6, 0, 6, 0)
        for exporter in self.exporters:
            checkbox = ExporterCheckbox(exporter)
            exporters_layout.addWidget(checkbox)
            self.exporter_ckeckboxes.append(checkbox)
        layout.addStretch()

        # Bottom buttons
        frame = QFrame()
        layout.addWidget(frame)
        frame_layout = QHBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addStretch()
        self.export_button = QPushButton("Export")
        self.export_button.setProperty("status", "important")
        frame_layout.addWidget(self.export_button)

    def setup_signals(self):
        self.export_button.clicked.connect(self.export_button_clicked)

    def export_button_clicked(self):
        for checkbox in self.exporter_ckeckboxes:
            if not checkbox.isChecked():
                continue
            checkbox.exporter.export()


def show_dialog(exporters: list[Exporter]):
    app = get_qt_app()
    widget = MasalaExporterWidget(exporters=exporters)
    container = ContainerWidget(widget=widget, title="Masala Exporter", icon=get_masala_exporter_icon())
    dialog = ContainerDialog(container=container)
    dialog.show()
    app.exec_()
