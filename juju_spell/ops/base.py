from abc import ABCMeta, abstractmethod
from enum import Enum
import traceback
import typing as t
import dataclasses

from loguru import logger
from juju.controller import Controller

from .result import OpsResult, OpsOutput


class OpsLevel(Enum):
    CONTROLLER = "CONTROLLER"
    MODEL = "MODEL"


class Ops(metaclass=ABCMeta):
    level: OpsLevel = OpsLevel.CONTROLLER

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        self.args = args
        self.kwargs = kwargs

    def __await__(self):  # type: ignore
        return self.__call(*self.args, **self.kwargs).__await__()

    async def __call(self, *args: t.Any, **kwargs: t.Any) -> OpsResult:
        logger.info(self.__class__.__name__)
        try:
            output: t.Union[OpsOutput, bool] = await self._run(*args, **kwargs)
            return OpsResult(output=output)
        except Exception as err:
            logger.warning(traceback.format_exc())
            return OpsResult(err=err)

    @abstractmethod
    async def _run(self, *args: t.Any, **kwargs: t.Any) -> t.Union[OpsOutput, bool]:
        pass


OPS = t.TypeVar("OPS", bound=t.Union[Ops, "ComposeOps"])


class ComposeOps(t.Generic[OPS]):
    list_ops: t.List[OPS] = []

    def __init__(self, *args: t.List[OPS]):
        self.list_ops = list(*args)

    def __iter__(self) -> t.Iterator:
        for obj in self.list_ops:
            yield obj
