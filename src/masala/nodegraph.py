from __future__ import annotations

from pathlib import Path
from typing import Any

from NodeGraphQt import BaseNode, NodeBaseWidget, NodeGraph, Port
from NodeGraphQt.widgets.node_widgets import NodeButton
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QApplication, QComboBox, QFileDialog, QPushButton, QVBoxLayout, QWidget

from masala.api import AssetBlock, AssetBlockRegistry, FunctionNodeDescription, Input, Output

NOT_SET = "NOT SET"


def type_to_color(typ: str) -> tuple[int, int, int]:
    mapping = {"Path": "#00FFDD", "dict": "#3CFF00", "bool": "#58608F"}
    color = mapping.get(typ, "#FFFFFF")
    return hex_to_tuple(color)


def hex_to_tuple(hex_color: str) -> tuple[int, int, int]:
    hex_color = "#" + hex_color.strip("#")
    qcolor = QColor(hex_color)
    return (qcolor.red(), qcolor.green(), qcolor.blue())


class MasalaPort(Port):
    def __init__(self, node, port):
        super().__init__(node, port)
        self.value: Any = NOT_SET


class AssetBlockWidget(QWidget):
    """
    Custom widget to be embedded inside a node.
    """

    def __init__(self, assetblock_node: AssetBlockNode):
        super().__init__()
        if not assetblock_node.ASSETBLOCK:
            raise RuntimeError("AssetBlock is not defined")
        self.assetblock_node = assetblock_node
        self.assetblock: AssetBlock = assetblock_node.ASSETBLOCK
        self.setup_ui()
        self.setup_signals()

    def setup_signals(self):
        self.browse_button.clicked.connect(self.browse_button_clicked)
        self.version_combobox.currentIndexChanged.connect(self.version_index_changed)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.browse_button = QPushButton("Browse")
        layout.addWidget(self.browse_button)
        self.version_combobox = QComboBox()
        layout.addWidget(self.version_combobox)

    def update_items(self, paths: list[Path]):
        self.version_combobox.blockSignals(True)
        self.version_combobox.clear()
        for path in paths:
            version = self.assetblock.convention.parse(path)["version"]
            self.version_combobox.addItem(version, path)
        self.version_combobox.setCurrentIndex(self.version_combobox.count() - 1)
        self.version_combobox.blockSignals(False)

    def get_selected_path(self) -> Path:
        return self.version_combobox.currentData()

    def browse_button_clicked(self):
        path = self.show_file_dialog()
        if not path:
            return
        paths = self.get_all_paths(path)
        self.update_items(paths)
        self.set_path_index(path)

    def set_path_index(self, path: Path):
        index = self.version_combobox.findData(path)
        self.version_combobox.setCurrentIndex(index)

    def get_all_paths(self, path: Path) -> list[Path]:
        fields = self.assetblock.convention.parse(path)
        fields.pop("version")
        paths = self.assetblock.convention.get_paths(fields)
        return paths

    def get_context_fields(self) -> dict:
        return {}

    def show_file_dialog(self) -> Path | None:
        # Get root dir
        conv = self.assetblock.convention
        pattern = conv.glob_pattern(self.get_context_fields())
        pattern = Path(pattern).as_posix()
        root_path = pattern.split("*", 1)[0].rsplit("/", 1)[0]

        # Get extension
        extension = conv.fixed_fields.get("extension") or "*"

        # Show dialog
        path = QFileDialog.getOpenFileName(
            parent=None, dir=root_path, caption="Pick Asset Block", filter=f"(*.{extension})"
        )[0]
        if path:
            return Path(path)

    @property
    def path_port(self) -> MasalaPort:
        return self.assetblock_node.outputs()["Path"]

    def version_index_changed(self):
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
    ASSETBLOCK: AssetBlock | None = None
    REGISTRY: AssetBlockRegistry | None = None

    def __init__(self) -> None:
        super().__init__()

        self._wrapper = AssetBlockWidgetWrapper(parent=self.view, assetblock_node=self)
        self._widget = self._wrapper._widget
        self.add_custom_widget(self._wrapper)
        self.add_output("Path", color=type_to_color("Path"))
        self.add_output("Metadata", color=type_to_color("dict"))

    def output(self, index) -> MasalaPort:
        return super().output(index)

    def outputs(self) -> dict[str, MasalaPort]:
        return super().outputs()


class FunctionNode(BaseNode):
    __identifier__ = "masala"
    NODE_NAME = "FunctionNode"
    FUNCTION_DESCRIPTION: FunctionNodeDescription

    def __init__(self) -> None:
        super().__init__()
        self.add_execute_button()
        self.add_input_ports()
        self.add_output_ports()

    def add_execute_button(self):
        self.add_button("execute")
        nodebutton: NodeButton = self.get_widget("execute")
        self.button = nodebutton._button
        self.button.clicked.connect(self.button_clicked)

    def button_clicked(self):
        port: MasalaPort = self.input(0)
        ports = port.connected_ports()
        if not ports:
            raise RuntimeError("Port not connected")
        port = ports[0]

    def add_input_ports(self):
        for input in self.FUNCTION_DESCRIPTION.inputs:
            self.add_input_port(input)

    def add_input_port(self, input: Input):
        self.add_input(input.label, color=type_to_color(input.typ))

    def add_output_ports(self):
        self.FUNCTION_DESCRIPTION.outputs.insert(0, Output(label="executed", typ="bool"))
        for output in self.FUNCTION_DESCRIPTION.outputs:
            self.add_output_port(output)

    def add_output_port(self, output: Output):
        self.add_output(output.label, color=type_to_color(output.typ))

    def input(self, index) -> MasalaPort:
        return super().input(index)


class AssemblerGraph:
    def __init__(
        self, assetblock_registry: AssetBlockRegistry, function_node_descriptions: list[FunctionNodeDescription]
    ) -> None:
        self.app = QApplication([])
        self.assetblock_registry = assetblock_registry
        self.function_node_descriptions = function_node_descriptions
        self.graph = NodeGraph()
        self.configure_hotkeys()
        self.register_nodes()

    def configure_hotkeys(self):
        hotkey_path = Path(__file__).parent / "hotkeys.json"
        self.graph.set_context_menu_from_file(hotkey_path, "graph")

    def register_nodes(self):
        all_nodes = []
        for assetblock in self.assetblock_registry.assetblocks:
            new_class = type(
                assetblock.name,
                (AssetBlockNode,),
                {
                    "__identifier__": "masala.assetblocks",
                    "NODE_NAME": assetblock.label,
                    "ASSETBLOCK": assetblock,
                    "REGISTRY": self.assetblock_registry,
                },
            )
            all_nodes.append(new_class)

        for description in self.function_node_descriptions:
            new_class = type(
                description.name,
                (FunctionNode,),
                {
                    "__identifier__": "masala.functions",
                    "NODE_NAME": description.label,
                    "FUNCTION_DESCRIPTION": description,
                },
            )
            all_nodes.append(new_class)

        self.graph.register_nodes(all_nodes)

    def show_dialog(self):
        graph_widget = self.graph.widget
        graph_widget.show()
        self.app.exec_()
