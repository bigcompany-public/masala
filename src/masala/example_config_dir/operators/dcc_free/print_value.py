from typing import Any

from masala import Input, Operator


def callback(value: Any):
    print(value)


print_value = Operator(
    name="PrintValue",
    label="Print Value",
    callback=callback,
    inputs=[
        Input(kwarg="value", label="Value", typ=Any, mandatory=True),
    ],
)
