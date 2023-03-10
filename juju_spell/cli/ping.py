import typer

from juju_spell.ops import PingOps
from juju_spell.assignment import Runner

from .cli import app


@app.command("ping")
def ping(ctx: typer.Context) -> None:
    Runner.run(PingOps, ctx.obj.settings)
