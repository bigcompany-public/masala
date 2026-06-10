from __future__ import annotations

from pathlib import Path
from typing import Callable

from lucent import Convention


class DuplicateAssetBlockError(Exception): ...


class AssetBlockNotFoundError(Exception): ...


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
        label: str,
        description: str,
        convention: Convention,
        destination_path_callback: Callable[[AssetBlock], Path] | None = None,
    ) -> None:
        self.name = name
        self.label = label or name.replace("_", " ").replace("-", " ").title()
        self.description = description
        self.convention = convention
        self.codex = convention._codex
        self.current_path_callback: Callable[..., Path] | None = None
        self.destination_path_callback = destination_path_callback or default_destination_path_callback
        self.loaded = False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def get_current_path(self) -> Path:
        """Returns the path to the current scene"""
        if not self.current_path_callback:
            raise AttributeError("Please provide a current_path_callback")
        return self.current_path_callback()

    def get_current_fields(self) -> dict[str, str]:
        return self.codex.get_fields(self.get_current_path())  # type: ignore

    def get_destination_path(self) -> Path:
        return self.destination_path_callback(self)

    def get_last_path(self) -> Path:
        fields = self.get_current_fields()
        if fields["version"]:
            fields.pop("version")
        if fields["description"]:
            fields.pop("description")
        return self.convention.get_last_path(fields)


class AssetBlockRegistry:
    def __init__(self, assetblocks: list[AssetBlock]) -> None:
        self._assetblocks: list[AssetBlock] = []
        for assetblock in sorted(assetblocks, key=lambda x: x.name):
            self.register_assetblock(assetblock)
        self._iterindex: int = 0

    def register_assetblock(self, assetblock: AssetBlock):
        if assetblock.name in self.get_assetblock_names():
            raise DuplicateAssetBlockError(f'Multiple AssetBlocks with name "{assetblock.name}" cannot be registered')
        if assetblock.label in self.get_assetblock_labels():
            raise DuplicateAssetBlockError(f'Multiple AssetBlocks with label "{assetblock.label}" cannot be registered')
        self._assetblocks.append(assetblock)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({len(self._assetblocks)} AssetBlock{'s' if len(self._assetblocks) > 1 else ''})"
        )

    def __iter__(self):
        self._iterindex = len(self._assetblocks)
        return self

    def __next__(self):
        if self._iterindex == 0:
            raise StopIteration
        self._iterindex = self._iterindex - 1
        return self._assetblocks[self._iterindex]

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

    def __getitem__(self, key: str):
        return self.get_assetblock_by_name(key)
