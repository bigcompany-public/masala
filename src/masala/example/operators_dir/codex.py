from lucent import Codex

from masala.api import Operator, Output
from masala.example.codex import codex


def callback() -> list[Codex]:
    return [codex]


get_codex = Operator(
    name="GetCodex",
    label="Get Codex",
    callback=callback,
    outputs=[Output(label="Codex", typ=Codex)],
)
