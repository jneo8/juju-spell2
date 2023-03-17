"""User relate cli."""
from enum import Enum

import typer

from juju_spell.assignment import Runner
from juju_spell.ops import AddUserOps
from juju_spell.utils import Namespace

from .cli import app
from .output import OutputHandler


class ACL(str, Enum):
    """Allow acl input."""

    # Controller ACL
    LOGIN = "login"
    ADD_MODEL = "add-model"
    SUPERUSER = "superuser"
    # Model ACL
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


@app.command("add_user")
def add_user(
    ctx: typer.Context,
    user: str = typer.Option(..., help="username"),
    password: str = typer.Option("", prompt=True, confirmation_prompt=True),
    display_name: str = typer.Option(None, help="display_name"),
    models: list[str] = typer.Option([]),
    acl: ACL = typer.Option(...),
    overwrite: bool = typer.Option(False),
) -> None:
    """Add user and grant permission."""
    if display_name is None:
        display_name = user

    output_handler = OutputHandler()
    Runner(
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
