from pathlib import Path

from masala.api import FunctionNodeDescription, Input


def callback(path: Path, metadata: dict | None = None, other: bool = True):
    print("#" * 30)
    print(path)
    print(metadata)


import_static_mesh = FunctionNodeDescription(
    name="StaticMeshImport",
    label="Import Static Mesh",
    callback=callback,
    inputs=[
        Input(kwarg="path", label="Path", typ="Path", mandatory=True),
        Input(kwarg="metadata", label="Metadata", typ="dict", mandatory=False),
        Input(kwarg="other", label="Test", typ="bool", mandatory=False),
    ],
)
