from pathlib import Path

from masala import Input, Operator, Output


def callback(path: Path) -> list[list[str]]:
    print("Importing rig")
    return [["controller1", "controller2"]]


import_rig = Operator(
    name="ImportRig",
    label="Import Rig",
    callback=callback,
    inputs=[
        Input(kwarg="path", label="Path", typ=Path, mandatory=True),
    ],
    outputs=[Output(label="Controllers", typ=list)],
)
