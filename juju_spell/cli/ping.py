import typer
from loguru import logger

from juju_spell.ops import PingOps
from juju_spell.assignment import Runner

from .cli import app


@app.command("ping")
def ping(ctx: typer.Context) -> None:
    logger.debug(ctx)
    result = Runner(PingOps, ctx.obj.settings)()
    for run in result:
        logger.info(run)
