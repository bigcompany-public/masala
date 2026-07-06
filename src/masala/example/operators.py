from masala.example.operators_dir.apply_rig import apply_rig
from masala.example.operators_dir.assign_materials import assign_materials
from masala.example.operators_dir.codex import get_codex
from masala.example.operators_dir.get_asset_fields import get_asset_fields
from masala.example.operators_dir.get_current_scene_path import get_current_scene_path
from masala.example.operators_dir.import_materials import import_materials
from masala.example.operators_dir.import_rig import import_rig
from masala.example.operators_dir.import_static_mesh import import_static_mesh
from masala.example.operators_dir.print_value import print_value
from masala.example.operators_dir.solve_path import solve_path

operators = [
    import_static_mesh,
    print_value,
    assign_materials,
    import_materials,
    apply_rig,
    import_rig,
    get_asset_fields,
    get_codex,
    get_current_scene_path,
    solve_path,
]
