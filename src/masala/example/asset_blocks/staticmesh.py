from pathlib import Path

from masala.api import AssetBlock
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


def load(path: Path):
    print(f"Loading {path}")
    return []


static_mesh = AssetBlock(
    "staticMesh",
    description="Static Mesh",
    convention=codex.convs.assetblock_static_mesh,
    current_path_callback=current_scene_callback,
    export_callback=export,
    assembly_callback=assemble,
    load_callback=load,
)
