import typer

from juju_spell.ops import PingOps, ComposeOps
from juju_spell.assignment import Runner
from juju_spell.utils import Namespace

from .cli import app
from .output import OutputHandler


@app.command("ping")
def ping(ctx: typer.Context) -> None:
    output_handler = OutputHandler()
    result = Runner(
        PingOps,
        ctx.obj.settings,
        Namespace(),
        output_handler=output_handler.call,
    )()
    output_handler.print()
