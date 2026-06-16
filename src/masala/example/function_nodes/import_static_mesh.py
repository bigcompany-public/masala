from pathlib import Path

from masala.api import FunctionNodeDescription, Input


def callback(path: Path, metadata: dict | None = None):
    print("#" * 30)
    print(path)
    print(metadata)


import_static_mesh = FunctionNodeDescription(
    name="StaticMeshImport",
    label="Import Static Mesh",
    callback=callback,
    inputs=[Input(label="path", typ="Path", mandatory=True), Input(label="metadata", typ="dict", mandatory=False)],
)
