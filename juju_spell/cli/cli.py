import os
import pathlib
import sys
import typing as t

import typer
from loguru import logger
from pydantic import BaseModel

from juju_spell.container import Container
from juju_spell.settings import DEFAULT_CONFIG_PATH, Settings

app = typer.Typer()


class CtxObj(BaseModel):
    settings: t.Optional[Settings] = None

    def pre_check(self) -> None:
        assert self.settings


@app.callback()
def common(
    ctx: typer.Context,
    config: pathlib.Path = typer.Option(DEFAULT_CONFIG_PATH),
    parallel: bool = typer.Option(False),
) -> None:
    """Common Entry Point"""
    container = Container()
    logger.info(f"load config file {config}")
    if config.is_file() and not os.stat(config).st_size == 0:
        container._settings.from_yaml(config)
    container.init_resources()
    container.wire(modules=[__name__])

    ctx.ensure_object(CtxObj)
    ctx.obj.settings = container.settings()
    ctx.obj.settings.worker.parallel = parallel
    ctx.obj.pre_check()

    logger_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "{extra} - <level>{message}</level>"
    )
    logger.configure(extra={})  # Default values
    logger.remove()
    logger.add(sys.stderr, format=logger_format)
