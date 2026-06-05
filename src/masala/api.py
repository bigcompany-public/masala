from __future__ import annotations

from pathlib import Path
from typing import Callable

from lucent import Convention


class AssetDescription:
    def __init__(self, assetblocks: list[AssetBlock]) -> None:
        self.assetblocks = assetblocks


def default_destination_path_callback(assetblock: AssetBlock) -> Path:
    paths = assetblock.convention.get_paths()
    if paths:
        return Path(assetblock.convention.increment(paths[-1]))
    fields = assetblock.get_current_fields()
    fields["version"] = 1  # type: ignore
    return Path(assetblock.convention.format(fields))


class AssetBlock:
    def __init__(
        self,
        name: str,
        description: str,
        convention: Convention,
        current_path_callback: Callable[..., Path],
        export_callback: Callable[..., Path],
        load_callback: Callable[[Path | None], list[EntryPoint]],
        assembly_callback: Callable,
        destination_path_callback: Callable[[AssetBlock], Path] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.convention = convention
        self.codex = convention._codex
        self.current_path_callback = current_path_callback
        self.destination_path_callback = destination_path_callback or default_destination_path_callback
        self.export_callback = export_callback
        self.load_callback = load_callback
        self.assembly_callback = assembly_callback

    def get_destination_path(self) -> Path:
        return self.destination_path_callback(self)

    def get_current_path(self) -> Path:
        """Returns the path to the current scene"""
        return self.current_path_callback()

    def get_current_fields(self) -> dict[str, str]:
        return self.codex.get_fields(self.get_current_path())  # type: ignore

    def export(self) -> Path:
        return self.export_callback(self)

    def get_last_path(self) -> Path:
        fields = self.get_current_fields()
        if fields["version"]:
            fields.pop("version")
        if fields["description"]:
            fields.pop("description")
        return self.convention.get_last_path(fields)

    def load(self, path: Path | None = None) -> list[EntryPoint]:
        if not path:
            path = self.get_last_path()
        return self.load_callback(path)


class EntryPoint:
    def __init__(self) -> None:
        pass
