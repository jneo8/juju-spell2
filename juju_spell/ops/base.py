from abc import ABCMeta, abstractmethod
from enum import Enum
import contextvars
import traceback
import typing as t
import dataclasses
import itertools

from loguru import logger
from juju.controller import Controller
from juju_spell.utils import flatten

from .result import OpsResult, OpsOutput, DefaultOpsOutput


class OpsLevel(Enum):
    CONTROLLER = "CONTROLLER"
    MODEL = "MODEL"


class OpsType(Enum):
    NORMAL = "NORMAL"
    DRY_RUN = "DRY_RUN"
    PRECHECK = "PRECHECK"


class Ops(metaclass=ABCMeta):
    _level: OpsLevel = OpsLevel.CONTROLLER
    _must_success: bool = False
    _type: OpsType = OpsType.NORMAL
    _name: t.Optional[str] = None

    def __init__(
        self,
        level: t.Optional[OpsLevel] = None,
        must_success: t.Optional[bool] = None,
        type_: t.Optional[OpsType] = None,
        name: t.Optional[str] = None,
    ):
        if level is not None:
            self._level = level
        if must_success is not None:
            self._must_success = must_success
        if type_ is not None:
            self._type = type_
        if name is not None:
            self._name = name

    async def __call__(self, *args: t.Any, **kwargs: t.Any) -> OpsResult:
        try:
            output: t.Union[OpsOutput, bool] = await self._run(*args, **kwargs)
            if not isinstance(output, OpsOutput):
                output = DefaultOpsOutput(value=output)
            return OpsResult(output=output)
        except Exception as err:
            logger.warning(traceback.format_exc())
            return OpsResult(err=err)

    @abstractmethod
    async def _run(
        self,
        ctx: contextvars.ContextVar,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> t.Union[OpsOutput, bool]:
        pass

    @property
    def info(self):
        return self._name if self._name is not None else self.__class__.__name__

    @property
    def level(self):
        return self._level

    @property
    def must_success(self):
        if self._type == OpsType.PRECHECK:
            return True
        return self._must_success

    @property
    def type_(self):
        return self._type


OPS = t.TypeVar("OPS", bound=t.Union[Ops, "ComposeOps"])


class ComposeOps(t.Generic[OPS]):
    list_ops: t.List[OPS] = []

    def __init__(self, *args: t.List[OPS]):
        self.list_ops = flatten([self.list_ops, *args])

    def __iter__(self) -> t.Iterator:
        for obj in self.list_ops:
            yield obj
