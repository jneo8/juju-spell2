import typing as t
from enum import Enum

import typer
from loguru import logger

from juju_spell.assignment import Runner
from juju_spell.ops import AddUserOps, ComposeOps
from juju_spell.utils import Namespace

from .cli import app
from .output import OutputHandler


class ACL(str, Enum):
    # Controller ACL
    login = "login"
    add_model = "add-model"
    superuser = "superuser"
    # Model ACL
    read = "read"
    write = "write"
    admin = "admin"


@app.command("add_user")
def add_user(
    ctx: typer.Context,
    user: str = typer.Option(..., help="username"),
    password: t.Optional[str] = typer.Option("", prompt=True, confirmation_prompt=True),
    display_name: t.Optional[str] = typer.Option(None, help="display_name"),
    models: t.List[str] = typer.Option([]),
    acl: ACL = typer.Option(...),
    overwrite: bool = typer.Option(False),
) -> None:
    if display_name is None:
        display_name = user

    output_handler = OutputHandler()
    result = Runner(
        AddUserOps,
        ctx.obj.settings,
        Namespace(
            username=user,
            display_name=display_name,
            password=password,
            overwrite=overwrite,
            acl=acl,
            models=models,
        ),
        output_handler=output_handler.call,
    )()
    output_handler.print()
