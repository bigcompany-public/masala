from lucent import Codex, Convention, Conventions, Rule, Rules


class MasalaRules(Rules):
    default = Rule(r"[a-zA-Z0-9]+")
    extension = Rule(r"[a-zA-Z0-9]+", examples=["mp3", "png", "mov"])
    project = Rule(r"[a-zA-Z]+", examples=["mySuperProject"])
    asset = Rule(r"([a-z]+)([A-Z][a-z]*)*", examples=["peach", "redApple", "philip", "cassie"])
    type = Rule(r"[a-z]+", examples=["prp", "chr", "elem"])
    version = Rule(r"\d{3}", examples=["001", "002", "003"])
    dcc = Rule(r"[a-z]+", examples=["maya", "blender", "nuke"])
    description = Rule(r"[a-zA-Z0-9]+", examples=["doingStuff", "startWork", "fixingSomething2"])


class MasalaConventions(Conventions):
    # Project
    project_root = Convention("//srv-bc-fs1/Norman")

    # Assets
    asset_work_dir = Convention("{@project_root}/assetWorkspace/{type}/{asset}/{task}/{dcc}")
    asset_workfile = Convention(
        "{@asset_work_dir}/{asset}_{task}_v{version}_{description}.{extension}",
        fixed_fields={"extension": "blend", "dcc": "blender"},
    )
    asset_modeling_workfile = Convention("{@asset_workfile}", fixed_fields={"task": "mdl"})

    # AssetBlocks
    assetblock_dir = Convention("{@project_root}/assetBlocksLibrary/{type}/{asset}/{assetBlock}")
    assetblock_static_mesh = Convention(
        "{@assetblock_dir}/v{version}/{asset}_{assetBlock}_v{version}.{extension}",
        fixed_fields={"assetBlock": "staticMesh", "extension": "usda"},
    )
    static_mesh_prim_root = Convention("/root/{asset}")


class MasalaCodex(Codex):
    convs: MasalaConventions = MasalaConventions()
    rules: MasalaRules = MasalaRules()


codex = MasalaCodex()
