from dataclasses import dataclass
from pathlib import Path

from NodeGraphQt import BaseNode, NodeBaseWidget, NodeGraph
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


class AssetBlockInnerWidget(QWidget):
    """
    Custom widget to be embedded inside a node.
    """

    def __init__(self):
        super().__init__()
        self.initial_path: Path | None = None
        self.assetblock: AssetBlock | None = None
        self.registry: AssetBlockRegistry | None = None
        self.setup_ui()
        self.setup_signals()

    def setup_signals(self):
        self.search_paths_button.clicked.connect(self.search_button_clicked)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.search_paths_button = QPushButton("Search")
        layout.addWidget(self.search_paths_button)
        self.path_combobox = QComboBox()
        self.path_combobox.addItems(["NAH"])
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
        versions = [self.assetblock.convention.parse(path)["version"] for path in paths]
        self.path_combobox.addItems(versions)
        self.path_combobox.setCurrentIndex(self.path_combobox.count() - 1)

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


class AssetBlockInnerWidgetWrapper(NodeBaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent, label="Path")
        self._widget = AssetBlockInnerWidget()
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

        self._wrapper = AssetBlockInnerWidgetWrapper(self.view)
        self._widget = self._wrapper._widget
        self.add_custom_widget(self._wrapper)
        self.add_output("Path", color=type_to_color("Path"))
        self.add_output("Metadata", color=type_to_color("dict"))


def show_dialog(assetblock_registry: AssetBlockRegistry):
    app = QApplication([])
    graph = NodeGraph()
    graph.register_nodes([AssetBlockNode])

    abnode: AssetBlockNode = graph.create_node("masala.AssetBlockNode")
    abnode._widget.set_registry(assetblock_registry)
    abnode._widget.set_initial_path(
        Path(r"\\srv-bc-fs1\Norman\assetBlocksLibrary\lab\elderSprite\staticMesh\v004\elderSprite_staticMesh_v004.usda")
    )

    graph_widget = graph.widget
    graph_widget.show()

    app.exec_()


if __name__ == "__main__":
    show_dialog()
