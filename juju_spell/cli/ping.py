import typer

from juju_spell.asyncio import run_async
from juju_spell.ops.base import PingOps
from juju_spell.assignment import run

from .cli import app


@app.command("ping")
def ping(
    ctx: typer.Context,
):
    run_async(
        run([PingOps, PingOps], ctx.obj.settings)
    )
