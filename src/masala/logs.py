from qtpy.QtWidgets import QApplication, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from masala.gui.container import ContainerDialog, ContainerWidget
from masala.gui.utils import get_qt_app, get_qta_icon


class LogsWidget(QWidget):
    def __init__(self, node_name: str, text: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.text = text
        self.node_name = node_name
        self.setup_ui()
        self.setup_signals()

    def setup_ui(self):
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        label = QLabel(self.node_name)
        label.setProperty("tag", "H2")
        layout.addWidget(label)
        self.logs = QPlainTextEdit()
        self.logs.setPlainText(self.text)
        layout.addWidget(self.logs)
        bottom_widget = QWidget()
        layout.addWidget(bottom_widget)
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.copy_button = QPushButton("Copy Logs")
        self.copy_button.setProperty("status", "important")
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.copy_button)

    def setup_signals(self):
        self.copy_button.clicked.connect(self.copy_logs)

    def copy_logs(self):
        _ = QApplication.instance() or QApplication()
        clipboard = QApplication.clipboard()
        clipboard.clear(mode=clipboard.Mode.Clipboard)
        clipboard.setText(self.text, mode=clipboard.Mode.Clipboard)


def show_logs_dialog(node_name: str, text: str, parent: QWidget | None = None):
    app = get_qt_app()
    widget = LogsWidget(node_name, text)
    container = ContainerWidget(widget, "Logs", icon=get_qta_icon("mdi.clipboard-text"))
    dialog = ContainerDialog(container)
    dialog.exec()


if __name__ == "__main__":
    show_logs_dialog("my node", "yolo")
