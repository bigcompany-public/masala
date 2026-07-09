from pathlib import Path

from masala import Exporter

from ...assetblocks.staticmesh import static_mesh
from ...codex_config import codex


def get_path() -> Path:
    fields = {"asset": "myAsset", "version": "001"}
    return Path(codex.convs.asset_modeling_workfile.format(fields))


def export(path: Path):
    print(f"Writing placeholder file to {path}")
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text("placeholder")
    return


def meta() -> dict:
    return {"hello": "world"}


static_mesh_exporter = Exporter(
    static_mesh, current_path_callback=get_path, export_callback=export, metadata_callback=meta
)
