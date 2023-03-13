import typer
from loguru import logger

from juju_spell.ops import PingOps, ComposeOps
from juju_spell.assignment import Runner
from juju_spell.asyncio import run_async
from juju_spell.utils import Namespace

from .cli import app


@app.command("ping")
def ping(ctx: typer.Context) -> None:
    result = Runner(
        ComposeOps(PingOps, PingOps),
        ctx.obj.settings,
        Namespace(models=[]),
        output_handler,
    )()


def output_handler(result) -> None:
    logger.debug(result)
