from qtpy.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from masala.api import AssetBlock, Operator
from masala.gui.container import ContainerDialog, ContainerWidget
from masala.gui.utils import get_masala_assembler_icon, get_qt_app
from masala.nodegraph import AssemblerGraph


class MasalaAssemblerWidget(QWidget):
    def __init__(
        self,
        assetblocks: list[AssetBlock],
        operators: list[Operator],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.assetblocks = assetblocks
        self.operators = operators
        self.setup_ui()
        self.setup_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Masala Assembler")
        title.setProperty("tag", "H2")
        layout.addWidget(title)

        # Graph
        frame = QFrame()
        layout.addWidget(frame)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(1, 1, 1, 1)
        frame.setProperty("depth", "3")
        self.graph_widget = AssemblerGraph(self.assetblocks, self.operators)
        frame_layout.addWidget(self.graph_widget.widget)

        # Bottom buttons
        frame = QFrame()
        layout.addWidget(frame)
        frame_layout = QHBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addStretch()
        self.execute_graph_button = QPushButton("Execute Graph")
        self.execute_graph_button.setProperty("status", "important")
        frame_layout.addWidget(self.execute_graph_button)

    def setup_signals(self):
        self.execute_graph_button.clicked.connect(self.execute_graph_button_clicked)

    def execute_graph_button_clicked(self):
        self.graph_widget.evaluate()


def show_dialog(assetblocks: list[AssetBlock], operators: list[Operator]):
    app = get_qt_app()
    widget = MasalaAssemblerWidget(assetblocks=assetblocks, operators=operators)
    container = ContainerWidget(widget=widget, title="Masala Assembler", icon=get_masala_assembler_icon())
    dialog = ContainerDialog(container=container)
    dialog.show()
    app.exec_()
