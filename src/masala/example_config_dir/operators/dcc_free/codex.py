from lucent import Codex

from masala import Operator, Output

from ...codex_config import codex


def callback() -> list[Codex]:
    print("Fetching Codex Object")
    return [codex]


get_codex = Operator(
    name="GetCodex",
    label="Get Codex",
    callback=callback,
    outputs=[Output(label="Codex", typ=Codex)],
)
