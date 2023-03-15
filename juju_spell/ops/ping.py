"""Ping."""
import typing as t

from juju.controller import Controller

from .base import Ops


class _PingOps(Ops):
    async def _run(self, ctr: Controller, *args: t.Any, **kwargs: t.Any) -> bool:
        ctr.is_connected()
        return True


PingOps: Ops = _PingOps()
