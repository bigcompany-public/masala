from masala import AssetBlock

from ..codex_config import codex

static_mesh = AssetBlock(
    name="StaticMesh",
    label="Static Mesh",
    description="Geometries of the asset, without materials, deformers...",
    convention=codex.convs.assetblock_static_mesh,
)
