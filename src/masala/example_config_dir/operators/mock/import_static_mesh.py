from pathlib import Path

from masala import Input, Operator, Output

from ...codex_config import codex


def callback(path: Path, metadata: dict | None = None, other: bool = True):
    fields = codex.get_fields(path)
    group = f"grp_{fields['asset']}"
    geometries = ["head", "arm", "leg"]
    if fields["version"] == "004":
        geometries += ["mouth", "hand", "foot"]
    geometries = [f"{fields['asset']}_{geo}" for geo in geometries]
    return [group, geometries]


import_static_mesh = Operator(
    name="StaticMeshImport",
    label="Import Static Mesh",
    callback=callback,
    inputs=[
        Input(kwarg="path", label="Path", typ=Path, mandatory=False),
    ],
    outputs=[Output(label="Main Group", typ=str), Output(label="Geometries", typ=list)],
)
