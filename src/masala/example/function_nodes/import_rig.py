from pathlib import Path

from masala.api import FunctionNodeDescription, Input, Output


def callback(path: Path) -> list[list[str]]:
    print("Importing rig")
    return [["controller1", "controller2"]]


import_rig = FunctionNodeDescription(
    name="ImportRig",
    label="Import Rig",
    callback=callback,
    inputs=[
        Input(kwarg="path", label="Path", typ="Path", mandatory=False),
    ],
    outputs=[Output(label="Controllers", typ="list")],
)
