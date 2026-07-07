from masala import AssetBlock

from ..codex_config import codex

rig = AssetBlock(
    name="Rig",
    label="Rig",
    description="Skeleton and constraints to apply to geometries",
    convention=codex.convs.assetblock_rig,
)
