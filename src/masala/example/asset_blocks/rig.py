from masala.api import AssetBlock
from masala.example.codex import codex

rig = AssetBlock(
    name="Rig",
    label="Rig",
    description="Skeleton and constraints to apply to geometries",
    convention=codex.convs.assetblock_rig,
)
