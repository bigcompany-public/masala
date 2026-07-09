from __future__ import annotations

import enum
import json
import logging
import os
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, get_args, get_origin

from lucent import Convention

from masala.stdout import CaptureStdout

logger = logging.getLogger(__name__)


class ExportFailed(Exception): ...


def default_destination_path_callback(exporter: Exporter) -> Path:
    fields = exporter.get_current_fields()
    paths = exporter.convention.get_paths()
    if paths:
        return Path(exporter.convention.increment(paths[-1]))
    fields["version"] = 1  # type: ignore
    return Path(exporter.convention.format(fields))


def get_metadata_path(path: Path) -> Path:
    return path.with_suffix(".abmd")


class NodeState(enum.Enum):
    UNSET = "unset"
    EXECUTED = "executed"
    FAILED = "failed"


class PortType:
    def __init__(self, typ: type | Any) -> None:
        if isinstance(typ, str):
            raise TypeError(
                f"PortType no longer accepts string type names (got {typ!r}); "
                "pass a real type instead, e.g. typ=str, typ=list[int], typ=Path"
            )
        if typ is None:
            typ = type(None)
        self.typ = typ
        self.origin = get_origin(typ)
        self.args = get_args(typ)

    @property
    def is_any(self) -> bool:
        return self.typ is Any

    def matches(self, other: PortType) -> bool:
        if self.is_any or other.is_any:
            return True
        return self.typ == other.typ

    @property
    def key(self) -> str:
        if self.is_any:
            return "Any"
        base = self.origin or self.typ
        base_name = getattr(base, "__name__", str(base))
        if not self.args:
            return base_name
        args_key = ", ".join(getattr(arg, "__name__", str(arg)) for arg in self.args)
        return f"{base_name}[{args_key}]"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PortType) and self.typ == other.typ

    def __hash__(self) -> int:
        return hash(self.typ)

    def __repr__(self) -> str:
        return f"PortType({self.key})"


class AssetBlock:
    def __init__(
        self,
        name: str,
        label: str,
        description: str,
        convention: Convention,
    ) -> None:
        self.name = name
        self.label = label or name.replace("_", " ").replace("-", " ").title()
        self.description = description
        self.convention = convention
        self.codex = convention._codex

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"


class Exporter:
    def __init__(
        self,
        assetblock: AssetBlock,
        current_path_callback: Callable[..., Path],
        export_callback: Callable[[Path], dict | None],
        destination_path_callback: Callable[[Exporter], Path] | None = None,
        metadata_callback: Callable[..., dict] | None = None,
        variable_fields: list[str] | None = None,
    ) -> None:
        self.assetblock = assetblock
        self.convention = self.assetblock.convention
        self.codex = self.assetblock.codex
        self.current_path_callback = current_path_callback
        self.destination_path_callback = destination_path_callback or default_destination_path_callback
        self.export_callback = export_callback
        self.metadata_callback = metadata_callback
        self.variable_fields = variable_fields if variable_fields is not None else ["version", "description"]
        self.logs: str = ""
        self.error: bool = False
        self.result: dict | None = None

    def __repr__(self) -> str:
        return f"{__class__.__name__}({self.assetblock.label})"

    def __str__(self) -> str:
        return f"{__class__.__name__}({self.assetblock.label})"

    def get_current_path(self) -> Path:
        return self.current_path_callback()

    def get_current_fields(self) -> dict[str, str]:
        fields = self.codex.get_fields(self.get_current_path())  # type: ignore
        for field_name in self.variable_fields:
            if fields.get(field_name):
                fields.pop(field_name)
        return fields

    def get_destination_path(self) -> Path:
        return self.destination_path_callback(self)

    def export(self, raise_on_error=True):
        with CaptureStdout() as stdout:
            start_time = time.perf_counter()

            try:
                self._monitored_export()
            except Exception:
                elapsed = time.perf_counter() - start_time
                self.error = True
                print(f"Export failed after {elapsed:.4f} seconds")
                if raise_on_error:
                    raise
                else:
                    print(traceback.format_exc())
            else:
                elapsed = time.perf_counter() - start_time
                self.error = False
                print(f"Export took {elapsed:.4f} seconds")
            finally:
                self.logs = stdout.text()

    def _monitored_export(self):
        path = self.get_destination_path()
        logger.info(f"Exporting {self.assetblock.label} to {path}")
        path.parent.mkdir(exist_ok=True, parents=True)
        self.result = self.export_callback(path)
        self.ensure_path(path)
        metadata_path = get_metadata_path(path)
        self.write_metadata(metadata_path)

    def get_base_metadata(self) -> dict:
        metadata = {
            "user": os.environ["USERNAME"],
            "computer": os.environ["COMPUTERNAME"],
            "date": "{year}_{month}_{day}_{hour}_{min}_{sec}".format(**self.codex.get_datetime_fields()),
        }
        return metadata

    def get_extra_metadata(self) -> dict:
        if not self.metadata_callback:
            return {}
        return self.metadata_callback()

    def get_metadata(self) -> dict:
        metadata = self.get_base_metadata()
        if self.result and not self.metadata_callback:
            metadata.update(self.result)
        metadata.update(self.get_extra_metadata())
        return metadata

    def ensure_path(self, path: Path):
        if not path.exists():
            raise ExportFailed(f"No file found at {path}. Export most likely failed.")

    def write_metadata(self, path: Path):
        logger.info(f"Writing metadata to {path}")
        path.write_text(json.dumps(self.get_metadata(), indent=4))


@dataclass
class Input:
    kwarg: str
    label: str
    typ: type | Any
    mandatory: bool = False

    def __post_init__(self) -> None:
        self.typ = PortType(self.typ)


@dataclass
class Output:
    label: str
    typ: type | Any

    def __post_init__(self) -> None:
        self.typ = PortType(self.typ)


@dataclass
class NodeDescription:
    name: str
    label: str
    inputs: list[Input] = field(default_factory=list)
    outputs: list[Output] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"{__class__.__name__}({self.label})"

    def __str__(self) -> str:
        return f"{__class__.__name__}({self.label})"


@dataclass
class Operator(NodeDescription):
    callback: Callable = field(kw_only=True)

    def __repr__(self) -> str:
        return f"{__class__.__name__}({self.label})"

    def __str__(self) -> str:
        return f"{__class__.__name__}({self.label})"
