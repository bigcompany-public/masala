from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Callable

from lucent import Codex, Convention

logger = logging.getLogger(__name__)


class DuplicateAssetBlockError(Exception): ...


class AssetBlockNotFoundError(Exception): ...


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
        export_callback: Callable[[Path], None],
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

    def get_current_path(self) -> Path:
        return self.current_path_callback()

    def get_current_fields(self) -> dict[str, str]:
        fields = self.codex.get_fields(self.get_current_path())  # type: ignore
        for field in self.variable_fields:
            if fields.get(field):
                fields.pop(field)
        return fields

    def get_destination_path(self) -> Path:
        return self.destination_path_callback(self)

    def export(self):
        path = self.get_destination_path()
        logger.info(f"Exporting {self.assetblock.label} to {path}")
        path.parent.mkdir(exist_ok=True, parents=True)
        self.export_callback(path)
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
        metadata.update(self.get_extra_metadata())
        return metadata

    def ensure_path(self, path: Path):
        if not path.exists():
            raise ExportFailed(f"No file found at {path}. Export most likely failed.")

    def write_metadata(self, path: Path):
        logger.info(f"Writing metadata to {path}")
        path.write_text(json.dumps(self.get_metadata(), indent=4))


class AssetBlockRegistry:
    def __init__(self, assetblocks: list[AssetBlock], codex: Codex) -> None:
        self._assetblocks: list[AssetBlock] = []
        self._codex = codex
        for assetblock in sorted(assetblocks, key=lambda x: x.name):
            self.register_assetblock(assetblock)

    def register_assetblock(self, assetblock: AssetBlock):
        if assetblock.name in self.get_assetblock_names():
            raise DuplicateAssetBlockError(f'Multiple AssetBlocks with name "{assetblock.name}" cannot be registered')
        if assetblock.label in self.get_assetblock_labels():
            raise DuplicateAssetBlockError(f'Multiple AssetBlocks with label "{assetblock.label}" cannot be registered')
        self._assetblocks.append(assetblock)

    def __repr__(self) -> str:
        count = len(self._assetblocks)
        return f"{self.__class__.__name__}({count} AssetBlock{'s' if count > 1 else ''})"

    def __iter__(self):
        return iter(self._assetblocks)

    def get_assetblock_names(self) -> list[str]:
        return [assetblock.name for assetblock in self._assetblocks]

    def get_assetblock_labels(self) -> list[str]:
        return [assetblock.label for assetblock in self._assetblocks]

    def get_assetblock_by_name(self, name: str) -> AssetBlock:
        assetblocks = [assetblock for assetblock in self._assetblocks if assetblock.name == name]
        if not assetblocks:
            raise AssetBlockNotFoundError(f'AssetBlock name not found : "{name}"')
        return assetblocks[0]

    def get_assetblock_by_label(self, label: str) -> AssetBlock:
        assetblocks = [assetblock for assetblock in self._assetblocks if assetblock.label == label]
        if not assetblocks:
            raise AssetBlockNotFoundError(f'AssetBlock label not found : "{label}"')
        return assetblocks[0]

    def __getitem__(self, key: str | int):
        if isinstance(key, str):
            return self.get_assetblock_by_name(key)
        elif isinstance(key, int):
            return self._assetblocks[key]
