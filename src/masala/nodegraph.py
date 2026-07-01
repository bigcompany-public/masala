from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from NodeGraphQt import BackdropNode, BaseNode, NodeBaseWidget, NodeGraph, Port
from NodeGraphQt.widgets.node_widgets import NodeButton
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QComboBox, QFileDialog, QPushButton, QVBoxLayout, QWidget

from masala.api import (
    AssetBlock,
    Input,
    NodeDescription,
    NodeState,
    Operator,
    Output,
    PortType,
    get_metadata_path,
)
from masala.gui.container import ContainerDialog, ContainerWidget
from masala.gui.utils import get_masala_assembler_icon, get_qt_app

NOT_SET = "NOT SET"

STATE_COLORS = {
    NodeState.EXECUTED: "#032C03",
    NodeState.FAILED: "#310404",
}


def type_to_color(port_type: PortType) -> tuple[int, int, int]:
    mapping = {
        str: "#1f78b4",
        int: "#ff7f0e",
        float: "#e6550d",
        bool: "#393b79",
        list: "#2ca02c",
        tuple: "#31a354",
        set: "#bcbd22",
        dict: "#9467bd",
        Path: "#56a5d4",
    }
    base_type = port_type.origin or port_type.typ
    color = mapping.get(base_type, "#ACACAC")
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


class MasalaNode(BaseNode):
    NODE_DESCRIPTION: NodeDescription

    def __init__(self) -> None:
        super().__init__()
        self._state = NodeState.UNSET
        self.add_input_ports()
        self.add_output_ports()

    @property
    def state(self) -> NodeState:
        return self._state

    @property
    def is_executed(self) -> bool:
        return self._state is NodeState.EXECUTED

    def set_state(self, state: NodeState) -> None:
        self._state = state
        color = STATE_COLORS.get(state)
        if color:
            self.set_color(*hex_to_tuple(color))

    def add_input_ports(self) -> None:
        for input_description in self.NODE_DESCRIPTION.inputs:
            self.add_typed_input(input_description)

    def add_output_ports(self) -> None:
        for output_description in self.NODE_DESCRIPTION.outputs:
            self.add_typed_output(output_description)

    def add_typed_input(self, input_description: Input) -> MasalaInputPort:
        port = self.add_input(input_description.label, color=type_to_color(input_description.typ))
        port.input_description = input_description
        return port

    def add_typed_output(self, output_description: Output) -> MasalaOutputPort:
        port = self.add_output(output_description.label, color=type_to_color(output_description.typ))
        port.output_description = output_description
        port.value = NOT_SET
        return port

    # NodeGraphQt.Port objects are plain Port instances at runtime; swapping
    # __class__ here is a lightweight trick so type checkers/autocomplete see
    # MasalaInputPort/MasalaOutputPort without forking NodeGraphQt.
    def add_input(self, *args, **kwargs) -> MasalaInputPort:
        port = super().add_input(*args, **kwargs)
        port.__class__ = MasalaInputPort
        return port

    def add_output(self, *args, **kwargs) -> MasalaOutputPort:
        port = super().add_output(*args, **kwargs)
        port.__class__ = MasalaOutputPort
        return port

    def input(self, index) -> MasalaInputPort:
        return super().input(index)

    def inputs(self) -> dict[str, MasalaInputPort]:
        return super().inputs()

    def input_ports(self) -> list[MasalaInputPort]:
        return super().input_ports()

    def output(self, index) -> MasalaOutputPort:
        return super().output(index)

    def outputs(self) -> dict[str, MasalaOutputPort]:
        return super().outputs()

    def output_ports(self) -> list[MasalaOutputPort]:
        return super().output_ports()


class AssetBlockWidget(QWidget):
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
        self.update_button.clicked.connect(self.update_button_clicked)
        self.version_combobox.currentIndexChanged.connect(self.version_index_changed)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.browse_button = QPushButton("Browse")
        layout.addWidget(self.browse_button)
        self.update_button = QPushButton("Update")
        layout.addWidget(self.update_button)
        self.version_combobox = QComboBox()
        layout.addWidget(self.version_combobox)

    def update_items(self, paths: list[Path]):
        self.version_combobox.clear()
        for path in paths:
            version = self.assetblock.convention.parse(path)["version"]
            self.version_combobox.addItem(version, path)
        self.version_combobox.setCurrentIndex(self.version_combobox.count() - 1)

    def get_selected_path(self) -> Path | None:
        return self.version_combobox.currentData()

    def browse_button_clicked(self):
        path = self.show_file_dialog()
        if not path:
            return
        self.update_all_paths(path)

    def update_button_clicked(self):
        path = self.get_selected_path()
        if not path:
            return
        self.update_all_paths(path)

    def update_all_paths(self, path: Path):
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
        conv = self.assetblock.convention
        pattern = conv.glob_pattern(self.get_context_fields())
        pattern = Path(pattern).as_posix()
        root_path = pattern.split("*", 1)[0].rsplit("/", 1)[0]

        extension = conv.fixed_fields.get("extension") or "*"

        path = QFileDialog.getOpenFileName(
            parent=None, dir=root_path, caption="Pick Asset Block", filter=f"(*.{extension})"
        )[0]
        if path:
            return Path(path)

    def version_index_changed(self):
        path = self.get_selected_path()

        self.assetblock_node.path_port.value = path
        if not path:
            self.assetblock_node.set_state(NodeState.UNSET)
            return

        metadata_path = get_metadata_path(path)
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file does not exist: {metadata_path}")
        data = json.loads(metadata_path.read_text())
        self.assetblock_node.metadata_port.value = data
        self.assetblock_node.set_state(NodeState.EXECUTED)


class AssetBlockWidgetWrapper(NodeBaseWidget):
    def __init__(self, parent, assetblock_node: AssetBlockNode):
        super().__init__(parent)
        self.set_name("path")  # A property must be set for ctrl+c ctrl+v to work
        self.assetblock_node = assetblock_node
        self._widget = AssetBlockWidget(assetblock_node=assetblock_node)
        self.set_custom_widget(self._widget)

    def get_value(self):
        value = self._widget.get_selected_path()
        value = value.as_posix() if value else ""
        return value

    def set_value(self, value):
        if not value:
            return

        # For some reason, set_value is called twice when loading a json file
        # bypass set value process if it has already been done
        if self._widget.version_combobox.count():
            return
        self._widget.update_all_paths(Path(value))


class AssetBlockNode(MasalaNode):
    __identifier__ = "AssetBlock"
    NODE_NAME = "AssetBlockNode"
    ASSETBLOCK: AssetBlock | None = None

    def __init__(self) -> None:
        super().__init__()
        self._wrapper = AssetBlockWidgetWrapper(parent=self.view, assetblock_node=self)
        self._widget = self._wrapper._widget
        self.add_custom_widget(self._wrapper)
        self._widget.update_button.setVisible(False)

    @property
    def path_port(self) -> MasalaOutputPort:
        return self.output(0)

    @property
    def metadata_port(self) -> MasalaOutputPort:
        return self.output(1)

    def on_input_connected(self, in_port: MasalaInputPort, out_port: MasalaOutputPort):
        self._widget.browse_button.setHidden(True)
        self._widget.update_button.setHidden(False)

    def on_input_disconnected(self, in_port, out_port):
        self._widget.browse_button.setHidden(False)
        self._widget.update_button.setHidden(True)


class OperatorNode(MasalaNode):
    __identifier__ = "Operator"
    NODE_NAME = "OperatorNode"
    NODE_DESCRIPTION: Operator

    def __init__(self) -> None:
        super().__init__()
        self.add_execute_button()

    def add_execute_button(self):
        self.add_button("execute")
        nodebutton: NodeButton = self.get_widget("execute")
        self.model.__dict__["execute"] = "placeholder"  # The button needs a property so it can be saved & copy pasted
        self.button = nodebutton._button
        self.button.setText("Run")
        self.button.clicked.connect(self.button_clicked)

    def button_clicked(self):
        try:
            self.run_callback()
        except:
            self.set_state(NodeState.FAILED)
            raise

    def run_callback(self):
        kwargs = self.get_kwargs()
        result = self.NODE_DESCRIPTION.callback(**kwargs)
        self.update_output_port_values(result)
        self.set_state(NodeState.EXECUTED)

    def update_output_port_values(self, result: tuple | list | None):
        num_ports = len(self.output_ports())
        if num_ports == 0:
            return

        if not isinstance(result, (list, tuple)):
            raise TypeError("Function should return a list or a tuple of objects")
        if len(result) != num_ports:
            raise IndexError("Mismatch between number of ports and number of returned objects")
        for port, value in zip(self.output_ports(), result):
            port.value = value

    def get_kwargs(self) -> dict[str, Any]:
        kwargs = {}
        for port in self.input_ports():
            connected_ports: list[MasalaOutputPort] = port.connected_ports()

            if not connected_ports:
                if port.input_description.mandatory:
                    raise RuntimeError(f"The port {port.input_description.label} must be connected")
                continue

            connected_port = connected_ports[0]

            if not port.input_description.typ.matches(connected_port.output_description.typ):
                raise TypeError(f"Type mismatch between {port} and {connected_port}")

            if connected_port.value == NOT_SET:
                raise RuntimeError(f"The connected port {connected_port.name()} has no value yet")

            kwargs[port.input_description.kwarg] = connected_port.value

        return kwargs


class AssemblerGraph(NodeGraph):
    def __init__(self, assetblocks: list[AssetBlock], operators: list[Operator]) -> None:
        super().__init__()
        self.assetblocks = assetblocks
        self.operators = operators
        self.configure_hotkeys()
        self.register_assetbklock_nodes()
        self.register_operator_nodes()
        self.register_other_nodes()

    def configure_hotkeys(self):
        hotkey_path = Path(__file__).parent / "hotkeys.json"
        self.set_context_menu_from_file(hotkey_path, "graph")

    def _register_builtin_nodes(self):
        """Prevents backdrop node from being automatically registered"""
        return

    def register_assetbklock_nodes(self):
        for assetblock in self.assetblocks:
            node_description = NodeDescription(
                name=assetblock.name,
                label=assetblock.label,
                inputs=[Input(kwarg="fields", label="Fields", typ=dict)],
                outputs=[Output(label="Path", typ=Path), Output(label="Metadata", typ=dict)],
            )
            new_class = type(
                assetblock.name,
                (AssetBlockNode,),
                {
                    "__identifier__": "AssetBlocks",
                    "NODE_NAME": assetblock.label,
                    "ASSETBLOCK": assetblock,
                    "NODE_DESCRIPTION": node_description,
                },
            )
            self.register_node(new_class)

    def register_operator_nodes(self):
        for operator in self.operators:
            new_class = type(
                operator.name,
                (OperatorNode,),
                {
                    "__identifier__": "Operators",
                    "NODE_NAME": operator.label,
                    "NODE_DESCRIPTION": operator,
                },
            )
            self.register_node(new_class)

    def register_other_nodes(self):
        new_class = type(
            "BackdropNode",
            (BackdropNode,),
            {
                "__identifier__": "Other",
                "NODE_NAME": "Backdrop",
            },
        )
        self.register_node(new_class)


def show_dialog(assetblocks: list[AssetBlock], operators: list[Operator]):
    app = get_qt_app()
    graph_widget = AssemblerGraph(assetblocks, operators)
    container = ContainerWidget(widget=graph_widget.widget, title="Masala Assembler", icon=get_masala_assembler_icon())
    dialog = ContainerDialog(container=container)
    dialog.show()
    app.exec_()
