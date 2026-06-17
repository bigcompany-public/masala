from masala.api import AssetBlockRegistry
from masala.example.asset_blocks.materials import materials
from masala.example.asset_blocks.rig import rig
from masala.example.asset_blocks.staticmesh import static_mesh
from masala.example.codex import codex

assetblocks = [static_mesh, materials, rig]

registry = AssetBlockRegistry(assetblocks=assetblocks, codex=codex)
