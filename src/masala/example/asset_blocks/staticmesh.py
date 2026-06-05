from pathlib import Path

from masala.api import AssetBlock, EntryPoint
from masala.example.codex import codex

DOCUMENT = {"_id": "6a21916d8459ebb4f5618e41", "type": "lab", "asset": "elderSprite", "_aquariumKey": 755557654}


def current_scene_callback():
    return codex.convs.asset_modeling_workfile.get_last_path(DOCUMENT)


def export(assetblock: AssetBlock):
    path = assetblock.get_destination_path()
    print(f"Exporting {DOCUMENT['asset']} to {path}")
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text("Hello World")
    return path


def assemble(assetblock: AssetBlock):
    print(f"Assembling {DOCUMENT['asset']}")


def load(assetblock: AssetBlock, path: Path):
    print(f"Loading {path}")
    assetblock.entry_points["main_group"].object = "MAIN_GROUP"


main_group = EntryPoint(name="main_group")

static_mesh = AssetBlock(
    "static_mesh",
    label="Static Mesh",
    description="Geometries of the asset, without materials, deformers...",
    convention=codex.convs.assetblock_static_mesh,
    current_path_callback=current_scene_callback,
    export_callback=export,
    assembly_callback=assemble,
    load_callback=load,
    entry_points=[main_group],
)
