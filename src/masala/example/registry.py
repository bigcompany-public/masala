from masala.api import AssetBlockRegistry
from masala.example.asset_blocks.staticmesh import static_mesh
from masala.example.codex import codex

assetblocks = [static_mesh]

registry = AssetBlockRegistry(assetblocks=assetblocks, codex=codex)
