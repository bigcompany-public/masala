from __future__ import annotations

import graphlib
import json
import time
import traceback
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
from masala.logs import show_logs_dialog
from masala.stdout import CaptureStdout

NOT_SET = "NOT SET"


class EvaluationError(Exception): ...


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
        self._value: Any = NOT_SET

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        self._value = value
        self.update_tooltip()

    def update_tooltip(self):
        if self.value == NOT_SET:
            tooltip = "Not set yet"
        else:
            try:
                tooltip = json.dumps(self.value, indent=4)
            except Exception:
                tooltip = str(self.value)
        self._Port__view.setToolTip(tooltip)  # type: ignore


class MasalaInputPort(Port):
    _last_valid_output_port: MasalaOutputPort | None = None

    def __init__(self, node, port):
        super().__init__(node, port)
        self.input_description: Input

    def validate_connection(self, out_port: MasalaOutputPort) -> None:
        if self.input_description.typ.matches(out_port.output_description.typ):
            self._last_valid_output_port = out_port
            return
        self.disconnect_from(out_port)
        self.restore_last_valid_connection()

    def restore_last_valid_connection(self) -> None:
        out_port = self._last_valid_output_port
        if out_port is None:
            return
        try:
            self.connect_to(out_port)
        except Exception:
            self._last_valid_output_port = None


class MasalaNode(BaseNode):
    NODE_DESCRIPTION: NodeDescription
    EXECUTE_BUTTON_LABEL = "Run"

    def __init__(self) -> None:
        super().__init__()
        self.logs = ""
        self._state = NodeState.UNSET
        self._dependencies_port = self.add_dependency_port()
        self._described_input_ports = self.add_input_ports()
        self._executed_port = self.add_executed_port()
        self._described_output_ports = self.add_output_ports()
        # self.add_execute_button()

    @property
    def described_input_ports(self) -> list[MasalaInputPort]:
        return self._described_input_ports

    @property
    def described_output_ports(self) -> list[MasalaOutputPort]:
        return self._described_output_ports

    @property
    def dependencies_port(self) -> MasalaInputPort:
        return self._dependencies_port

    @property
    def executed_port(self) -> MasalaOutputPort:
        return self._executed_port

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
        self.executed_port.value = self.is_executed

    def execute(self) -> None:
        self.logs = ""
        with CaptureStdout() as stdout:
            print(f"Executing node : {self.name()}")
            start_time = time.perf_counter()

            try:
                self._monitored_execution()
            except Exception:
                elapsed = time.perf_counter() - start_time
                self.error = True
                print(traceback.format_exc())
                print(f"An error occured after {elapsed:.4f} seconds")
            else:
                elapsed = time.perf_counter() - start_time
                self.error = False
                print(f"Execution took {elapsed:.4f} seconds")
            finally:
                self.logs = stdout.text()

    def _monitored_execution(self):
        raise NotImplementedError

    def add_execute_button(self) -> None:
        self.add_button("execute")
        nodebutton: NodeButton = self.get_widget("execute")
        self.model.__dict__["execute"] = "placeholder"  # The button needs a property so it can be saved & copy pasted
        self.button = nodebutton._button
        self.button.setFixedWidth(100)
        self.button.setText(self.EXECUTE_BUTTON_LABEL)
        self.button.clicked.connect(self.button_clicked)
        self.button.setHidden(True)

    def add_logs_button(self) -> None:
        self.add_button("logs")
        nodebutton: NodeButton = self.get_widget("logs")
        self.model.__dict__["execute"] = "placeholder"  # The button needs a property so it can be saved & copy pasted
        self.logs_button = nodebutton._button
        self.logs_button.setFixedWidth(100)
        self.logs_button.setText("Show Logs")
        self.logs_button.clicked.connect(self.show_logs)

    def add_invisible_button(self) -> None:
        """
        This button is just here to create extra width to the node
        NodeGraphQt is quite complex in the way node size is computed, so the simplest way is to create an invisible widget
        """
        self.add_button("invisible")
        nodebutton: NodeButton = self.get_widget("invisible")
        nodebutton._button.setHidden(True)

    def button_clicked(self) -> None:
        self.execute()

    def show_logs(self) -> None:
        show_logs_dialog(self.NODE_NAME, self.logs)

    def get_kwargs(self) -> dict[str, Any]:
        kwargs = {}
        for port in self.described_input_ports:
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

    def get_dependency_nodes(self) -> set[MasalaNode]:
        dependencies = set()
        for port in self.input_ports():
            for connected_port in port.connected_ports():
                connected_node = connected_port.node()
                if isinstance(connected_node, MasalaNode):
                    dependencies.add(connected_node)
        return dependencies

    def add_input_ports(self) -> list[MasalaInputPort]:
        return [self.add_typed_input(input_description) for input_description in self.NODE_DESCRIPTION.inputs]

    def add_output_ports(self) -> list[MasalaOutputPort]:
        return [self.add_typed_output(output_description) for output_description in self.NODE_DESCRIPTION.outputs]

    def add_typed_input(self, input_description: Input) -> MasalaInputPort:
        port = self.add_input(input_description.label, color=type_to_color(input_description.typ))
        port.input_description = input_description
        return port

    def add_typed_output(self, output_description: Output) -> MasalaOutputPort:
        port = self.add_output(output_description.label, color=type_to_color(output_description.typ))
        port.output_description = output_description
        port.value = NOT_SET
        return port

    def add_dependency_port(self) -> MasalaInputPort:
        description = Input(kwarg="dependencies", label="Dependencies", typ=Any)
        port = self.add_input(description.label, multi_input=True, color=type_to_color(description.typ))
        port.input_description = description
        return port

    def add_executed_port(self) -> MasalaOutputPort:
        description = Output(label="Executed", typ=bool)
        port = self.add_output(description.label, color=type_to_color(description.typ))
        port.output_description = description
        port.value = False
        return port

    # NodeGraphQt.Port objects are plain Port instances at runtime; swapping
    # __class__ here is a lightweight trick so type checkers/autocomplete see
    # MasalaInputPort/MasalaOutputPort without forking NodeGraphQt.
    def add_input(self, *args, **kwargs) -> MasalaInputPort:
        port = super().add_input(*args, **kwargs)
        port.__class__ = MasalaInputPort
        return port  # type: ignore

    def add_output(self, *args, **kwargs) -> MasalaOutputPort:
        port = super().add_output(*args, **kwargs)
        port.__class__ = MasalaOutputPort
        return port  # type: ignore

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

    def on_input_connected(self, in_port: MasalaInputPort, out_port: MasalaOutputPort):
        in_port.validate_connection(out_port)


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
        self.version_combobox.currentIndexChanged.connect(self.version_index_changed)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.browse_button = QPushButton("Browse")
        layout.addWidget(self.browse_button)
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
        self.assetblock_node.logs = "Browsing"
        path = self.show_file_dialog()
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
    ASSETBLOCK: AssetBlock
    EXECUTE_BUTTON_LABEL = "Update"

    def __init__(self) -> None:
        super().__init__()
        self._wrapper = AssetBlockWidgetWrapper(parent=self.view, assetblock_node=self)
        self._widget = self._wrapper._widget
        self.add_custom_widget(self._wrapper)
        # self.add_logs_button()

    @property
    def fields_port(self) -> MasalaInputPort:
        return self.described_input_ports[0]

    @property
    def path_port(self) -> MasalaOutputPort:
        return self.described_output_ports[0]

    @property
    def metadata_port(self) -> MasalaOutputPort:
        return self.described_output_ports[1]

    def update_browse_visibility(self) -> None:
        is_connected = bool(self.fields_port.connected_ports())
        self._widget.browse_button.setHidden(is_connected)

    def on_input_connected(self, in_port: MasalaInputPort, out_port: MasalaOutputPort):
        super().on_input_connected(in_port, out_port)
        self.update_browse_visibility()

    def on_input_disconnected(self, in_port, out_port):
        self.update_browse_visibility()

    def _monitored_execution(self):
        try:
            # Get fields
            if self.fields_port.connected_ports():
                fields: dict = self.get_kwargs()["fields"]
            else:
                if self.path_port.value == NOT_SET:
                    raise ValueError("Please browse for a file")
                fields = self.ASSETBLOCK.convention.parse(self.path_port.value)
            if fields.get("version"):
                fields.pop("version")

            # Get paths
            paths = self.ASSETBLOCK.convention.get_paths(fields)
            if not paths:
                raise FileNotFoundError(f"No asset found on disk for fields: {fields}")

            # Update paths
            self._widget.update_all_paths(paths[-1])
        except Exception:
            self.set_state(NodeState.FAILED)
            raise


class OperatorNode(MasalaNode):
    __identifier__ = "Operator"
    NODE_NAME = "OperatorNode"
    NODE_DESCRIPTION: Operator
    EXECUTE_BUTTON_LABEL = "Run"

    def __init__(self) -> None:
        super().__init__()
        # self.add_logs_button()
        self.add_invisible_button()

    def _monitored_execution(self) -> None:
        try:
            self.run_callback()
        except Exception:
            self.set_state(NodeState.FAILED)
            raise

    def run_callback(self):
        kwargs = self.get_kwargs()
        result = self.NODE_DESCRIPTION.callback(**kwargs)
        self.update_output_port_values(result)
        self.set_state(NodeState.EXECUTED)

    def update_output_port_values(self, result: tuple | list | None):
        described_ports = self.described_output_ports
        num_ports = len(described_ports)
        if num_ports == 0:
            return

        if not isinstance(result, (list, tuple)):
            raise TypeError("Function should return a list or a tuple of objects")
        if len(result) != num_ports:
            raise IndexError("Mismatch between number of ports and number of returned objects")
        for port, value in zip(described_ports, result):
            port.value = value


class AssemblerGraph(NodeGraph):
    def __init__(self, assetblocks: list[AssetBlock], operators: list[Operator], recipes_dir: Path) -> None:
        super().__init__()
        self.assetblocks = assetblocks
        self.operators = operators
        self.recipes_dir = recipes_dir
        self.configure_hotkeys()
        self.register_assetblock_nodes()
        self.register_operator_nodes()
        self.register_other_nodes()

    def selected_nodes(self) -> list[MasalaNode]:
        return super().selected_nodes()

    def configure_hotkeys(self):
        hotkey_path = Path(__file__).parent / "hotkeys.json"
        self.set_context_menu_from_file(hotkey_path, "graph")

    def _register_builtin_nodes(self):
        """Prevents backdrop node from being automatically registered"""
        return

    def get_masala_nodes(self) -> list[MasalaNode]:
        return [node for node in self.all_nodes() if isinstance(node, MasalaNode)]

    def get_selected_masala_nodes(self) -> list[MasalaNode]:
        return [node for node in self.selected_nodes() if isinstance(node, MasalaNode)]

    def get_all_dependencies(self, node: MasalaNode) -> set[MasalaNode]:
        visited: set[MasalaNode] = set()
        stack = list(node.get_dependency_nodes())
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            stack.extend(current.get_dependency_nodes())
        return visited

    def get_evaluation_order(self, nodes: list[MasalaNode] | None = None) -> list[MasalaNode]:
        all_nodes = self.get_masala_nodes()
        dependency_graph = {node: node.get_dependency_nodes() for node in all_nodes}
        try:
            order = list(graphlib.TopologicalSorter(dependency_graph).static_order())
        except graphlib.CycleError as error:
            raise EvaluationError("Cannot evaluate: the node graph contains a cycle") from error
        if nodes is None:
            return order
        subset = set(nodes)
        return [node for node in order if node in subset]

    def run_nodes(self, nodes: list[MasalaNode]) -> None:
        for node in nodes:
            if node.state is NodeState.UNSET:
                try:
                    node.execute()
                except Exception as error:
                    raise EvaluationError(
                        f"Evaluation stopped: node '{node.name()}' failed during execution"
                    ) from error
            if node.state is NodeState.FAILED:
                raise EvaluationError(
                    f"Evaluation stopped: node '{node.name()}' is in a failed state. "
                    "Fix it and re-run it manually before continuing."
                )

    def evaluate(self) -> None:
        self.run_nodes(self.get_evaluation_order())

    def execute_nodes(self, nodes: list[MasalaNode]) -> None:
        self.run_nodes(self.get_evaluation_order(nodes))

    def evaluate_nodes(self, nodes: list[MasalaNode]) -> None:
        dependencies: set[MasalaNode] = set()
        for node in nodes:
            dependencies |= self.get_all_dependencies(node)
        self.run_nodes(self.get_evaluation_order(list(dependencies | set(nodes))))

    def execute_selected_nodes(self) -> None:
        self.execute_nodes(self.get_selected_masala_nodes())

    def evaluate_selected_nodes(self) -> None:
        self.evaluate_nodes(self.get_selected_masala_nodes())

    def register_assetblock_nodes(self):
        for assetblock in self.assetblocks:
            node_description = NodeDescription(
                name=assetblock.name,
                label=assetblock.label,
                inputs=[Input(kwarg="fields", label="Fields", typ=dict, mandatory=False)],
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
