from pathlib import Path

from lucent import Convention

from masala.api import Input, Operator, Output
from masala.example.codex import codex


def callback(path: Path) -> tuple[Convention, dict]:
    convention, fields = codex.solve(path)
    return (convention, fields)


solve_path = Operator(
    name="SolvePath",
    label="Solve Path",
    callback=callback,
    inputs=[Input(kwarg="path", label="Path", typ=Path, mandatory=True)],
    outputs=[Output(label="Convention", typ=Convention), Output(label="Fields", typ=dict)],
)
