from pathlib import Path

import bpy

from masala.api import Exporter
from masala.example.asset_blocks.staticmesh import static_mesh
from masala.example.codex import codex


def get_path() -> Path:
    path = bpy.data.filepath
    if not path:
        raise RuntimeError("Cannot extract current path. Please save your scene first")
    return Path(path)


def export(path: Path):
    bpy.ops.wm.usd_export(
        filepath=str(path),
        selected_objects_only=False,
        export_animation=False,
        export_hair=False,
        export_uvmaps=True,
        rename_uvmaps=False,
        export_normals=True,
        export_materials=False,
        export_subdivision="BEST_MATCH",
        export_armatures=False,
        export_shapekeys=False,
        use_instancing=False,
        convert_orientation=False,
        relative_paths=True,
        root_prim_path=codex.transmute(path, target_convention=codex.convs.static_mesh_prim_root),
        export_custom_properties=True,
        custom_properties_namespace="masala",
        accessibility_label="",
        accessibility_description="",
        author_blender_name=True,
        allow_unicode=False,
        export_meshes=True,
        export_lights=False,
        export_cameras=False,
        export_curves=False,
        export_points=False,
        export_volumes=False,
        triangulate_meshes=False,
        merge_parent_xform=False,
    )


def meta() -> dict:
    return {"hello": "world"}


static_mesh_exporter = Exporter(
    static_mesh, current_path_callback=get_path, export_callback=export, metadata_callback=meta
)
