from pathlib import Path

from masala import Operator, Output

from ...codex_config import codex


def callback() -> list[Path]:
    fields = {"asset": "myAsset", "version": "001"}
    return [Path(codex.convs.asset_modeling_workfile.format(fields))]


get_current_scene_path = Operator(
    name="GetCurrentScenePath",
    label="Get Current Scene Path",
    callback=callback,
    outputs=[Output(label="Path", typ=Path)],
)
