from masala.api import AssetBlock
from masala.example.codex import codex

materials = AssetBlock(
    name="Materials",
    label="Materials",
    description="Materials to assign to geometries",
    convention=codex.convs.assetblock_materials,
)
