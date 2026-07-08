import importlib.util
import os
import sys
from importlib.machinery import ModuleSpec
from pathlib import Path

from qtpy.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

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


def get_assembler_config_from_path(
    operators_module_path: Path | str,
) -> tuple[list[AssetBlock], list[Operator]]:
    operators_module_path = Path(operators_module_path)
    config_package_path = operators_module_path.parent

    # Ensure package structure
    required_paths = [
        operators_module_path,
        config_package_path,
        config_package_path.joinpath("__init__.py"),
        config_package_path.joinpath("assetblocks_config.py"),
        config_package_path.joinpath("codex_config.py"),
    ]
    for _path in required_paths:
        if not _path.exists():
            raise FileNotFoundError(f"Wrong config package structure. File is missing : {_path}")

    # Import the package (__init__.py)
    package_name = "masala_assembler_config"
    spec = importlib.util.spec_from_file_location(
        package_name,
        config_package_path.joinpath("__init__.py"),
        submodule_search_locations=[config_package_path.as_posix()],
    )
    assert isinstance(spec, ModuleSpec)
    package_module = importlib.util.module_from_spec(spec)
    sys.modules[package_name] = package_module
    spec.loader.exec_module(package_module)  # type: ignore

    # Load AssetBlocks from the submodule
    full_submodule_name = f"{package_name}.assetblocks_config"
    submodule = importlib.import_module(full_submodule_name)
    assetblocks = getattr(submodule, "assetblocks")

    # Load operators from the submodule
    full_submodule_name = f"{package_name}.{operators_module_path.stem}"
    submodule = importlib.import_module(full_submodule_name)
    operators = getattr(submodule, "operators")

    return (assetblocks, operators)


def show_assembler_dialog(assetblocks: list[AssetBlock] | None = None, operators: list[Operator] | None = None):
    if assetblocks is None or operators is None:
        var = "MASALA_OPERATORS_CONFIG"
        path = os.environ.get(var)
        if not path:
            raise RuntimeError(
                f"Please provide assetblocks and operators, or provide a path to the operators configuration file with the {var} environment variable"
            )
        assetblocks, operators = get_assembler_config_from_path(path)

    app = get_qt_app()
    widget = MasalaAssemblerWidget(assetblocks=assetblocks, operators=operators)
    container = ContainerWidget(widget=widget, title="Masala Assembler", icon=get_masala_assembler_icon())
    dialog = ContainerDialog(container=container)
    dialog.show()
    app.exec_()
