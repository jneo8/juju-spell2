import typing as t
from juju.controller import Controller
from .base import Ops, ComposeOps


class PingPreCheckOps(Ops):
    async def _run(self, ctr: Controller, *args: t.Any, **kwargs: t.Any) -> bool:
        ctr.is_connected()
        return True


class PingRunOps(Ops):
    async def _run(self, ctr: Controller, *args: t.Any, **kwargs: t.Any) -> bool:
        ctr.is_connected()
        return True


PingOps: ComposeOps = ComposeOps([PingPreCheckOps(), PingRunOps()])
