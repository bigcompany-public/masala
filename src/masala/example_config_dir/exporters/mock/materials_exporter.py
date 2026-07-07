from pathlib import Path

from masala import Exporter

from ...assetblocks.materials import materials


def get_path() -> Path:
    return Path(
        "//srv-bc-fs1/Norman/assetWorkspace/lab/elderSprite/mdl/blender/elderSprite_mdl_v001_init.blend"
    )


def export(path: Path):
    print(f"Writing placeholder file to {path}")
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text("placeholder")


def meta() -> dict:
    return {"hello": "world"}


materials_exporter = Exporter(
    materials,
    current_path_callback=get_path,
    export_callback=export,
    metadata_callback=meta,
)
