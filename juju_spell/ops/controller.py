import typing as t
import dataclasses

from loguru import logger

from juju.controller import Controller

from .base import Ops
from .result import OpsOutput


__all__ = ["WrapOpsOutput", "ControllerWrapOps"]


@dataclasses.dataclass(frozen=True)
class WrapOpsOutput(OpsOutput):
    value: t.Any


class ControllerWrapOps(Ops):
    def __init__(
        self,
        cmd: str,
        *args,
        options: t.Dict[str, t.Any] = {},
        **kwargs,
    ):
        self._cmd = cmd
        self._options = options

    async def _run(self, ctr: Controller, *args: t.Any, **kwargs: t.Any) -> bool:
        func = getattr(ctr, self._cmd)
        result = await func(**self._options)
        return WrapOpsOutput(value=result)

    @property
    def info(self):
        return self.__class__.__name__ + ":" + self._cmd
