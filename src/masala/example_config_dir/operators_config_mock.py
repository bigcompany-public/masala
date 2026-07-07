from .operators.dcc_free.codex import get_codex
from .operators.dcc_free.print_value import print_value
from .operators.dcc_free.solve_path import solve_path
from .operators.mock.apply_rig import apply_rig
from .operators.mock.assign_materials import assign_materials
from .operators.mock.get_asset_fields import get_asset_fields
from .operators.mock.get_current_scene_path import get_current_scene_path
from .operators.mock.import_materials import import_materials
from .operators.mock.import_rig import import_rig
from .operators.mock.import_static_mesh import import_static_mesh

operators = [get_codex, print_value, solve_path]
operators += [
    import_static_mesh,
    assign_materials,
    import_materials,
    apply_rig,
    import_rig,
    get_asset_fields,
    get_current_scene_path,
]
