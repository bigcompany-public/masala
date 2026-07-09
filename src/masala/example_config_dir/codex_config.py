from pathlib import Path

from lucent import Codex, Convention, Conventions, Rule, Rules


class MasalaRules(Rules):
    default = Rule(r"[a-zA-Z0-9]+")
    extension = Rule(r"[a-zA-Z0-9]+", examples=["mp3", "png", "mov"])
    asset = Rule(r"([a-z]+)([A-Z][a-z]*)*", examples=["redApple", "philip", "chair"])
    assetBlockType = Rule(r"[a-zA-Z]+", examples=["staticMesh", "materials", "rig"])
    task = Rule(r"[a-zA-Z0-9]+", examples=["mdl", "rig", "surf"])
    version = Rule(r"\d{3}", examples=["001", "002", "003"])


class MasalaConventions(Conventions):
    # Project
    project_root = Convention(f"{Path.home().as_posix()}/myMasalaProject")

    # Assets
    asset_work_dir = Convention("{@project_root}/assetWorkspace/{asset}/{task}")
    asset_workfile = Convention(
        "{@asset_work_dir}/{asset}_{task}_v{version}.{extension}",
        fixed_fields={"extension": "blend"},
    )
    asset_modeling_workfile = Convention(
        "{@asset_workfile}",
        fixed_fields={"task": "mdl"},
    )

    # AssetBlocks
    assetblock_dir = Convention("{@project_root}/assetBlocksLibrary/{asset}/{assetBlock}")
    assetblock_static_mesh = Convention(
        "{@assetblock_dir}/v{version}/{asset}_{assetBlock}_v{version}.{extension}",
        fixed_fields={"assetBlock": "staticMesh", "extension": "usda"},
    )
    static_mesh_prim_root = Convention("/root/{asset}")
    assetblock_materials = Convention(
        "{@assetblock_dir}/v{version}/{asset}_{assetBlock}_v{version}.{extension}",
        fixed_fields={"assetBlock": "materials", "extension": "blend"},
    )
    assetblock_rig = Convention(
        "{@assetblock_dir}/v{version}/{asset}_{assetBlock}_v{version}.{extension}",
        fixed_fields={"assetBlock": "rig", "extension": "blend"},
    )

    # Blender
    blender_asset_main_collection = Convention("Scene/{asset}")
    blender_asset_meshes_collection = Convention("{@blender_asset_main_collection}/staticMesh")


class MasalaCodex(Codex):
    convs: MasalaConventions = MasalaConventions()
    rules: MasalaRules = MasalaRules()


codex = MasalaCodex()
