from pathlib import Path

from masala.api import AssetBlock
from masala.example.codex import codex

DOCUMENT = {"_id": "6a21916d8459ebb4f5618e41", "type": "lab", "asset": "elderSprite", "_aquariumKey": 755557654}


def custom_path(assetblock: AssetBlock) -> Path:
    return Path("D:/remove_me/staticmesh.usd")


static_mesh = AssetBlock(
    name="static_mesh",
    label="Static Mesh",
    description="Geometries of the asset, without materials, deformers...",
    convention=codex.convs.assetblock_static_mesh,
    destination_path_callback=custom_path,
)
