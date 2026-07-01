from pathlib import Path

from masala.api import Exporter
from masala.example.assetblocks_dir.staticmesh import static_mesh


def get_path() -> Path:
    return Path("//srv-bc-fs1/Norman/assetWorkspace/lab/elderSprite/mdl/blender/elderSprite_mdl_v001_init.blend")


def export(path: Path):
    print(f"Writing placeholder file to {path}")
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text("placeholder")


def meta() -> dict:
    return {"hello": "world"}


static_mesh_exporter = Exporter(
    static_mesh, current_path_callback=get_path, export_callback=export, metadata_callback=meta
)
