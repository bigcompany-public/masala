from pathlib import Path

from masala.api import Input, Operator, Output


def callback(path: Path) -> list[list[str]]:
    print("Importing materials")
    return [["mat1", "mat2"]]


import_materials = Operator(
    name="ImportMaterials",
    label="Import Materials",
    callback=callback,
    inputs=[
        Input(kwarg="path", label="Path", typ=Path, mandatory=False),
    ],
    outputs=[Output(label="Materials", typ=list)],
)
