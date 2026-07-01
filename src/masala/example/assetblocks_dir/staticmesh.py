from masala.api import AssetBlock
from masala.example.codex import codex

static_mesh = AssetBlock(
    name="StaticMesh",
    label="Static Mesh",
    description="Geometries of the asset, without materials, deformers...",
    convention=codex.convs.assetblock_static_mesh,
)
