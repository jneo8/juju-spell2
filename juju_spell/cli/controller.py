import typer

from juju_spell.assignment import Runner
from juju_spell.ops import ComposeOps, ControllerWrapOps
from juju_spell.utils import Namespace

from .cli import app


@app.command("example_controller_wraps")
def example_controller_wraps(ctx: typer.Context) -> None:
    Runner(
        ComposeOps(
            [
                ControllerWrapOps(cmd="list_models"),
                ControllerWrapOps(cmd="get_users"),
            ]
        ),
        ctx.obj.settings,
        Namespace(),
    )()
