from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from NodeGraphQt import BaseNode, NodeBaseWidget, NodeGraph, Port
from NodeGraphQt.widgets.node_widgets import NodeButton
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QApplication, QComboBox, QFileDialog, QPushButton, QVBoxLayout, QWidget

from masala.api import AssetBlock, AssetBlockRegistry, FunctionNodeDescription, Input, Output, get_metadata_path

NOT_SET = "NOT SET"


def type_to_color(typ: str) -> tuple[int, int, int]:
    mapping = {"Path": "#00FFDD", "dict": "#3CFF00", "bool": "#58608F"}
    color = mapping.get(typ, "#FFFFFF")
    return hex_to_tuple(color)


def hex_to_tuple(hex_color: str) -> tuple[int, int, int]:
    hex_color = "#" + hex_color.strip("#")
    qcolor = QColor(hex_color)
    return (qcolor.red(), qcolor.green(), qcolor.blue())


class MasalaOutputPort(Port):
    def __init__(self, node, port):
        super().__init__(node, port)
        self.output_description: Output
        self.value: Any = NOT_SET


class MasalaInputPort(Port):
    def __init__(self, node, port):
        super().__init__(node, port)
        self.input_description: Input


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
        self.version_combobox.blockSignals(False)
        self.version_combobox.setCurrentIndex(self.version_combobox.count() - 1)

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
        for i in reversed(range(self.version_combobox.count())):
            path_data = self.version_combobox.itemData(i)
            if path_data == path:
                self.version_combobox.setCurrentIndex(i)
                break

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

    def version_index_changed(self):
        path = self.get_selected_path()

        # Update path output port value
        self.assetblock_node.path_port.value = path

        # Update metadata output port value
        metadata_path = get_metadata_path(path)
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file does not exist: {metadata_path}")
        data = json.loads(metadata_path.read_text())
        self.assetblock_node.metadata_port.value = data


class AssetBlockWidgetWrapper(NodeBaseWidget):
    def __init__(self, parent, assetblock_node: AssetBlockNode):
        super().__init__(parent, label="Path")
        self.assetblock_node = assetblock_node
        self._widget = AssetBlockWidget(assetblock_node=assetblock_node)
        self.set_custom_widget(self._widget)

    def get_value(self):
        return ""

    def set_value(self, value):
        return ""


class AssetBlockNode(BaseNode):
    __identifier__ = "masala"
    NODE_NAME = "AssetBlock"
    ASSETBLOCK: AssetBlock | None = None

    def __init__(self) -> None:
        super().__init__()

        self._wrapper = AssetBlockWidgetWrapper(parent=self.view, assetblock_node=self)
        self._widget = self._wrapper._widget
        self.add_custom_widget(self._wrapper)
        self.setup_ports()

    def output(self, index) -> MasalaOutputPort:
        return super().output(index)

    def outputs(self) -> dict[str, MasalaOutputPort]:
        return super().outputs()

    @property
    def path_port(self) -> MasalaOutputPort:
        return self.output(0)

    @property
    def metadata_port(self) -> MasalaOutputPort:
        return self.output(1)

    def setup_ports(self):
        self.add_output("Path", color=type_to_color("Path"))
        self.add_output("Metadata", color=type_to_color("dict"))
        self.path_port.output_description = Output("Path", "Path")
        self.path_port.value = NOT_SET
        self.metadata_port.output_description = Output("Metadata", "dict")
        self.metadata_port.value = NOT_SET


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
        try:
            self.run_callback()
        except:
            self.set_color(*hex_to_tuple("#310404"))
            self.executed_port.value = False
            raise

    def run_callback(self):
        kwargs = self.get_kwargs()
        result = self.FUNCTION_DESCRIPTION.callback(kwargs)
        self.update_output_port_values(result)
        self.set_color(*hex_to_tuple("#032C03"))

    def update_output_port_values(self, result: tuple | list):
        self.executed_port.value = True
        num_ports = len(self.output_ports())
        if num_ports == 1:
            return

        if not (isinstance(result, list) or isinstance(result, tuple)):
            raise TypeError("Function should return a list or a tuple of objects")
        if len(result) != num_ports - 1:
            raise IndexError("Mismatch between number of ports and number of returned objects")
        for i, port in enumerate(self.output_ports()):
            if i == 0:
                continue
            port.value = result[i - 1]

    def get_kwargs(self) -> dict[str, Any]:
        kwargs = {}
        for port in self.input_ports():
            connected_ports: list[MasalaOutputPort] = port.connected_ports()

            # Port is not connected
            if not connected_ports:
                if port.input_description.mandatory:
                    raise RuntimeError(f"The port {port.input_description.label} must be connected")
                continue

            # Port is connected
            connected_port = connected_ports[0]

            # Check port declared type
            if connected_port.output_description.typ != port.input_description.typ:
                raise TypeError(f"Type mismatch between {port} and {connected_port}")

            # Check value
            if connected_port.value == NOT_SET:
                raise RuntimeError(f"The connected port {connected_port.name()} has no value yet")

            kwargs[port.input_description.kwarg] = connected_port.value

        return kwargs

    def add_input_ports(self):
        for input in self.FUNCTION_DESCRIPTION.inputs:
            self.add_input_port(input)

    def add_input_port(self, input: Input):
        port: MasalaInputPort = self.add_input(input.label, color=type_to_color(input.typ))  # type: ignore
        port.input_description = input

    def add_output_ports(self):
        self.FUNCTION_DESCRIPTION.outputs.insert(0, Output(label="Executed", typ="bool"))
        for output in self.FUNCTION_DESCRIPTION.outputs:
            self.add_output_port(output)

    def add_output_port(self, output: Output):
        port: MasalaOutputPort = self.add_output(output.label, color=type_to_color(output.typ))  # type: ignore
        port.output_description = output
        port.value = NOT_SET

    def input(self, index) -> MasalaInputPort:
        return super().input(index)

    def input_ports(self) -> list[MasalaInputPort]:
        return super().input_ports()

    def output(self, index) -> MasalaOutputPort:
        return super().output(index)

    def output_ports(self) -> list[MasalaOutputPort]:
        return super().output_ports()

    @property
    def executed_port(self) -> MasalaOutputPort:
        return self.output(0)


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
