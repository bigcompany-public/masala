# Usage

Configuring Masala for your project implies the following steps. 

- Defining naming conventions for the AssetBlocks
- Registering the AssetBlocks
- Creating Exporter(s) for each AssetBlock
- Creating Assembly Operators to indicate how AssetBlocks should be combined
- Save node graphs, that act as recipes for your end products.

!!! tip
    This documentation teaches you how to create AssetBlocks "in a vaccuum", but you will most likely have to perform this steps in the context of a specific DCC. Thus, keep in mind everything we do here has to be fed into the configuration of:

    - [Masala For Blender](https://github.com/bigcompany-public/masala_blender#)
    - [Masala For Maya](https://github.com/bigcompany-public/masala_maya#)

## Defining Naming Conventions

Masala uses the python package [Lucent](https://pypi.org/project/lucent-codex/) to define where AssetBlocks should be stored.
For more information, see [Lucent official documentation](https://tristanlanguebien.github.io/lucent/)

In Lucent, naming conventions are registered in a `Codex` objects that contains `Rules` (regexes that the paths must respect) and `Conventions` (templates for paths).

Here is a minimal example to setup a few AssetBlocks.

=== "masala_codex.py :memo:"
    ```python
    from lucent import Codex, Convention, Conventions, Rule, Rules


    class MasalaRules(Rules):
        default = Rule(r"[a-zA-Z0-9]+")
        extension = Rule(r"[a-zA-Z0-9]+", examples=["mp3", "png", "mov"])
        asset = Rule(r"([a-z]+)([A-Z][a-z]*)*", examples=["peach", "redApple", "philip", "cassie"])
        assetBlockType = Rule(r"[a-zA-Z]+", examples=["staticMesh", "materials", "rig"])
        version = Rule(r"\d{3}", examples=["001", "002", "003"])


    class MasalaConventions(Conventions):
        project_root = Convention("C:/myProject")
        # First, we define a generic template for all AssetBlocks
        assetblock = Convention(
            "{@project_root}/AssetBlockLibrary/{asset}/{assetBlockType}/{asset}_{assetBlockType}_v{version}.{extension}"
        )
        # The Static Mesh AssetBlock is basically an assetblock, where assetBlockType is "staticMesh", and extension is "usda"
        assetblock_static_mesh = Convention(
            "{@assetblock}", fixed_fields={"assetBlockType": "staticMesh", "extension": "usda"}
        )
        # From there, you can add as many AssetBlocks Conventions as you like
        assetblock_materials = Convention(
            "{@assetblock}", fixed_fields={"assetBlockType": "materials", "extension": "blend"}
        )


    class MasalaCodex(Codex):
        convs: MasalaConventions = MasalaConventions()
        rules: MasalaRules = MasalaRules()


    codex = MasalaCodex()
    ```

!!! success "The Codex object created at the end will be used to validate and generate all paths related to AssetBlocks"

## Creating an AssetBlock

Now that masala knows where to store the AssetBlocks, we can feed the Convention into an AssetBlock object.

=== "assetblocks.py"
    ```python
    from masala import AssetBlock
    from masala_codex import codex

    static_mesh = AssetBlock(
        name="StaticMesh",
        label="Static Mesh",
        description="Geometries of the asset, without materials, deformers...",
        convention=codex.convs.assetblock_static_mesh,
    )
    ```

!!! success "This AssetBlock object will later be used to serve as a shared base for exporters and importers"

# Creating an Exporter

Exporting an AssetBlock is made of 4 steps: 

1. Identifying the path of the current scene.
2. Parse the current scene's path to generate a destination path.
2. Execute a function that does the export itself.
3. Write metadata to a `.abmd` file that lies next to the exported file (abmd stands for "AssetBlockMetaData")

These steps are encapsulated into an Exporter object.

=== "blender_exporters.py"
    ```python
    from pathlib import Path
    import bpy
    from assetblocks import static_mesh
    from masala import Exporter


    def get_path() -> Path:
        path = bpy.data.filepath
        if not path:
            raise RuntimeError("Cannot extract current path. Please save your scene first")
        return Path(path)


    def export_static_mesh(path: Path):
        bpy.ops.wm.usd_export(
            filepath=str(path),
            selected_objects_only=True,
        )
        return {"status": "success"}


    def extra_metadata() -> dict:
        return {"extra data": "hello world"}


    static_mesh_exporter = Exporter(
        assetblock=static_mesh,
        current_path_callback=get_path,
        export_callback=export,
        metadata_callback=extra_metadata,
    )
    ```

!!! success "This example Exporter file can be fed into the [Masala For Blender](https://github.com/bigcompany-public/masala_blender#) extension."
    When running the Masala Exporter Tool, your newly created AssetBlock Exporter should show up.
    ![masala_mesh_exporter](img/masala_mesh_exporter.png)

!!! tip
    As stated earlier in this documentation, an AssetBlock can have multiple exporters. For instance, your asset pipeline may authorize artists to generate a mesh from both maya and blender.

## Creating Operators for Masala Assembler Tool

When your AssetBlock is registered, it will appear in the available AssetBlocks of the Masala Assembler Tool.

![masala_mesh_assembler](img/masala_mesh_assembler.png)

Thas is a good start, but we cannot really do anything with it at the moment. For that, we need to create `Operators`, which are nodes in which data such as the AssetBlock's path or the AssetBlock's metadata can be plugged.

=== "operators.py :memo:"
    ```python
    from pathlib import Path
    from masala import Input, Operator, Output


    def callback(path: Path) -> list:
        print(f"IMPORTING {path}")
        return ["success"]


    import_static_mesh = Operator(
        name="StaticMeshImport",
        label="Import Static Mesh",
        callback=callback,
        inputs=[
            Input(
                kwarg="path",  # Indicates that the input's value will be passed to the "path" argument of the callback
                label="Path",
                typ=Path,
                mandatory=True,
            )
        ],
        outputs=[Output(label="Status", typ=str)],
    )
    ```

The newly created Operator shows up in the available Operators in the Masala Assembler Tool.

![example_import_operator0](img/example_import_operator0.png)

As you can see, the AssetBlock's path can be plugged into the Path input plug, and the proper value is returned in the Status output plug.

![example_import_operator1](img/example_import_operator1.png)

!!! tip
    Inputs have type validation : in this case, you won't be able to plug an integer into the Path input. If you want to be more permissive (for instance, to allow for str and Path objects) you may set `typ` to `typing.Any`

## Sharing Assembler Recipes

Masala Assembler gives you the option to save your node graphs at the json format, so they can be loaded or imported. Within a Recipe Library, these files become your main way of sharing an asset pipeline across a team.

![save_graph](img/save_graph.png)

:rocket: Congratulations, you now have all the keys to create as many AssetBlocks, Exporters, Operators and Recipes as you like. With a little of creativity, you can use Masala to build the asset pipeline that fits your needs.

---

!!! info ""
    <a href="Next Section"> <div style="text-align: right; font-weight: bold"> [Next Section : Tools](./tools.md) </div>
