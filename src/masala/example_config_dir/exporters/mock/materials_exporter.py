from pathlib import Path

from masala import Exporter

from ...assetblocks.materials import materials
from ...codex_config import codex


def get_current_path() -> Path:
    fields = {"asset": "myAsset", "version": "001"}
    return Path(codex.convs.asset_modeling_workfile.format(fields))


def export(path: Path):
    print(f"Writing placeholder file to {path}")
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text("placeholder")


def extra_metadata() -> dict:
    return {"extra data": "hello world"}


materials_exporter = Exporter(
    materials,
    current_path_callback=get_current_path,
    export_callback=export,
    metadata_callback=extra_metadata,
)
