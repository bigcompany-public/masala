from masala.api import FunctionNodeDescription, Output


def callback() -> list[dict[str, str]]:
    return [{"asset": "elderSprite", "type": "chr"}]


get_asset_fields = FunctionNodeDescription(
    name="GetAssetFields",
    label="Get Asset Fields",
    callback=callback,
    outputs=[Output(label="Fields", typ="dict")],
)
