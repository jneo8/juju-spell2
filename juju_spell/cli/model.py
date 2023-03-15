import typing as t

import typer
from loguru import logger

from juju_spell.assignment import Runner
from juju_spell.ops import ModelConfigOps
from juju_spell.utils import Namespace

from .cli import app


@app.command("model_config")
def model_config(
    ctx: typer.Context,
    models: t.List[str] = [],
) -> None:
    result = Runner(
        ModelConfigOps,
        ctx.obj.settings,
        Namespace(
            models=models,
        ),
    )()
    logger.info(result)
