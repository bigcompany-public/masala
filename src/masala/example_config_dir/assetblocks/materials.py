from masala import AssetBlock

from ..codex_config import codex

materials = AssetBlock(
    name="Materials",
    label="Materials",
    description="Materials to assign to geometries",
    convention=codex.convs.assetblock_materials,
)
