"""Controller Operations."""
import typing as t

from juju.controller import Controller

from .base import Ops
from .result import DefaultOpsOutput, OpsOutput

__all__ = ["ControllerWrapOps"]


class ControllerWrapOps(Ops):
    """Wrapper ops to call controller method directly."""

    def __init__(  # pylint: disable=dangerous-default-value
        self,
        cmd: str,
        *args: t.Any,
        allow_options: list[str] = [],
        **kwargs: t.Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._cmd = cmd
        self._allow_options = allow_options

    async def _run(self, ctr: Controller, *args: t.Any, **kwargs: t.Any) -> OpsOutput:
        options = {}
        for key in self._allow_options:
            if kwargs.get(key):
                options[key] = kwargs.get(key)
        func = getattr(ctr, self._cmd)
        result = await func(**options)
        return DefaultOpsOutput(value=result)

    @property
    def info(self) -> str:
        return self.__class__.__name__ + ":" + self._cmd if self._name is None else self._name
