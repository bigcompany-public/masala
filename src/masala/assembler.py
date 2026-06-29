from qtpy.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from masala.api import AssetBlockRegistry, FunctionNodeDescription
from masala.gui.container import ContainerDialog, ContainerWidget
from masala.gui.utils import get_masala_assembler_icon, get_qt_app
from masala.nodegraph import AssemblerGraph


class MasalaAssemblerWidget(QWidget):
    def __init__(
        self,
        assetblock_registry: AssetBlockRegistry,
        function_node_descriptions: list[FunctionNodeDescription],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.assetblock_registry = assetblock_registry
        self.function_node_descriptions = function_node_descriptions
        self.setup_ui()

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
        graph_widget = AssemblerGraph(self.assetblock_registry, self.function_node_descriptions)
        frame_layout.addWidget(graph_widget.widget)

        # Bottom buttons
        frame = QFrame()
        layout.addWidget(frame)
        frame_layout = QHBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addStretch()
        self.execute_graph_button = QPushButton("Execute Graph")
        self.execute_graph_button.setProperty("status", "important")
        frame_layout.addWidget(self.execute_graph_button)


def show_dialog(assetblock_registry: AssetBlockRegistry, function_node_descriptions: list[FunctionNodeDescription]):
    app = get_qt_app()
    widget = MasalaAssemblerWidget(
        assetblock_registry=assetblock_registry, function_node_descriptions=function_node_descriptions
    )
    container = ContainerWidget(widget=widget, title="Masala Assembler", icon=get_masala_assembler_icon())
    dialog = ContainerDialog(container=container)
    dialog.show()
    app.exec_()
