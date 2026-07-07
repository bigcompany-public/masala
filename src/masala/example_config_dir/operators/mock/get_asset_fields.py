from masala import Operator, Output


def callback() -> list[dict[str, str]]:
    return [{"asset": "elderSprite", "type": "lab"}]


get_asset_fields = Operator(
    name="GetAssetFields",
    label="Get Asset Fields",
    callback=callback,
    outputs=[Output(label="Fields", typ=dict)],
)
