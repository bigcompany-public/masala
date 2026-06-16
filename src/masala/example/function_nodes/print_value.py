from typing import Any

from masala.api import FunctionNodeDescription, Input


def callback(value: Any):
    print(value)


print_value = FunctionNodeDescription(
    name="PrintValue",
    label="Print Value",
    callback=callback,
    inputs=[
        Input(kwarg="value", label="Value", typ="Any", mandatory=True),
    ],
)
