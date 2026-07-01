from pathlib import Path

from masala.api import Operator, Output


def callback() -> list[Path]:
    return [Path("//srv-bc-fs1/Norman/assetWorkspace/lab/elderSprite/mdl/blender/elderSprite_mdl_v001_init.blend")]


get_current_scene_path = Operator(
    name="GetCurrentScenePath",
    label="Get Current Scene Path",
    callback=callback,
    outputs=[Output(label="Path", typ=Path)],
)
