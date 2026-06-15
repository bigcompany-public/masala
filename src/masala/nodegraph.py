from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from NodeGraphQt import BaseNode, NodeBaseWidget, NodeGraph, Port
from NodeGraphQt.constants import PortTypeEnum
from NodeGraphQt.widgets.node_widgets import NodeButton
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QApplication, QComboBox, QPushButton, QVBoxLayout, QWidget

from masala.api import AssetBlock, AssetBlockRegistry


def type_to_color(typ: str) -> tuple[int, int, int]:
    mapping = {"Path": "#00FFDD", "dict": "#3CFF00"}
    color = mapping.get(typ, "#FFFFFF")
    return hex_to_tuple(color)


def hex_to_tuple(hex_color: str) -> tuple[int, int, int]:
    hex_color = "#" + hex_color.strip("#")
    qcolor = QColor(hex_color)
    return (qcolor.red(), qcolor.green(), qcolor.blue())


@dataclass
class Output:
    name: str
    typ: str


class AssetBlockWidget(QWidget):
    """
    Custom widget to be embedded inside a node.
    """

    def __init__(self, assetblock_node: AssetBlockNode):
        super().__init__()
        self.assetblock_node = assetblock_node
        self.initial_path: Path | None = None
        self.assetblock: AssetBlock | None = None
        self.registry: AssetBlockRegistry | None = None
        self.setup_ui()
        self.setup_signals()

    def setup_signals(self):
        self.search_paths_button.clicked.connect(self.search_button_clicked)
        self.path_combobox.currentIndexChanged.connect(self.path_changed)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.search_paths_button = QPushButton("Search")
        layout.addWidget(self.search_paths_button)
        self.path_combobox = QComboBox()
        layout.addWidget(self.path_combobox)

    def set_registry(self, assetblock_registry: AssetBlockRegistry):
        self.registry = assetblock_registry

    def set_initial_path(self, path: Path):
        self.initial_path = path
        self.guess_assetblock()
        self.update_items([self.initial_path])

    def update_items(self, paths: list[Path]):
        self.path_combobox.clear()
        if not self.assetblock:
            raise RuntimeError("Cannot fetch paths if the AssetBlock is not defined")
        for path in paths:
            version = self.assetblock.convention.parse(path)["version"]
            self.path_combobox.addItem(version, path)
        self.path_combobox.setCurrentIndex(self.path_combobox.count() - 1)

    def get_selected_path(self) -> Path:
        return self.path_combobox.currentData()

    def guess_assetblock(self):
        if not self.registry:
            raise RuntimeError("Please provide a registry")
        if not self.initial_path:
            raise RuntimeError("Cannot guess the AssetBlock if no path is provided")
        conv = self.registry._codex.get_convention(self.initial_path)
        assetblocks = [assetblock for assetblock in self.registry._assetblocks if assetblock.convention == conv]
        if not assetblocks:
            raise RuntimeError("No AssetBlock type matches the provided path")
        self.assetblock = assetblocks[0]

    def search_button_clicked(self):
        if not self.assetblock:
            raise RuntimeError("Cannot fetch paths if the AssetBlock is not defined")
        if not self.initial_path:
            raise RuntimeError("Cannot parse initial path if none is provided")
        fields = self.assetblock.convention.parse(self.initial_path)
        fields.pop("version")
        paths = self.assetblock.convention.get_paths(fields)
        self.update_items(paths)

    @property
    def path_port(self) -> Port:
        return self.assetblock_node.outputs()["Path"]

    def path_changed(self):
        self.path_port.value = self.get_selected_path()


class AssetBlockWidgetWrapper(NodeBaseWidget):
    def __init__(self, parent, assetblock_node: AssetBlockNode):
        super().__init__(parent, label="Path")
        self.assetblock_node = assetblock_node
        self._widget = AssetBlockWidget(assetblock_node=assetblock_node)
        self.set_custom_widget(self._widget)

    def get_value(self):
        return "A"

    def set_value(self, value):
        return "B"


class AssetBlockNode(BaseNode):
    __identifier__ = "masala"
    NODE_NAME = "AssetBlock"

    def __init__(self) -> None:
        super().__init__()

        self._wrapper = AssetBlockWidgetWrapper(parent=self.view, assetblock_node=self)
        self._widget = self._wrapper._widget
        self.add_custom_widget(self._wrapper)
        self.add_output("Path", color=type_to_color("Path"))
        self.add_output("Metadata", color=type_to_color("dict"))


class FunctionWidget(QWidget):
    """
    Custom widget to be embedded inside a node.
    """

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(500)


class FunctionWidgetWrapper(NodeBaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent, label="")
        self._widget = FunctionWidget()
        self.set_custom_widget(self._widget)

    def get_value(self):
        return "A"

    def set_value(self, value):
        return "B"


class FunctionNode(BaseNode):
    __identifier__ = "masala"
    NODE_NAME = "FunctionNode"

    def __init__(self) -> None:
        super().__init__()

        # self._wrapper = FunctionWidgetWrapper(self.view)
        # self._widget = self._wrapper._widget
        # self.add_custom_widget(self._wrapper)
        self.add_button("test", label="Test")
        button: NodeButton = self.get_widget("test")
        button._button.clicked.connect(self.button_clicked)
        path_input = self.add_input("Path", color=type_to_color("Path"))
        path_input.add_accept_port_type(
            port_name="Path", port_type=PortTypeEnum.OUT.value, node_type="masala.AssetBlockNode"
        )

        self.add_input("Metadata", color=type_to_color("dict"))

        self.add_output("Path", color=type_to_color("Path"))
        self.add_output("Metadata", color=type_to_color("dict"))

    def button_clicked(self):
        port: Port = self.input(0)
        ports = port.connected_ports()
        if not ports:
            raise RuntimeError("Port not connected")
        port = ports[0]
        print(port.value)


def show_dialog(assetblock_registry: AssetBlockRegistry):
    app = QApplication([])
    graph = NodeGraph()
    graph.register_nodes([AssetBlockNode, FunctionNode])

    ab_node: AssetBlockNode = graph.create_node("masala.AssetBlockNode")
    ab_node._widget.set_registry(assetblock_registry)
    ab_node._widget.set_initial_path(
        Path(r"\\srv-bc-fs1\Norman\assetBlocksLibrary\lab\elderSprite\staticMesh\v004\elderSprite_staticMesh_v004.usda")
    )
    func_node: FunctionNode = graph.create_node("masala.FunctionNode", pos=(500, 0))
    func_node: FunctionNode = graph.create_node("masala.FunctionNode", pos=(500, 300))

    graph_widget = graph.widget
    graph_widget.show()

    app.exec_()


if __name__ == "__main__":
    show_dialog()
