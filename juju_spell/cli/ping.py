import typer
from loguru import logger

from juju_spell.ops import PingOps
from juju_spell.assignment import Runner

from .cli import app


@app.command("ping")
def ping(ctx: typer.Context) -> None:
    result = Runner(PingOps, ctx.obj.settings)()
    logger.info(result)
