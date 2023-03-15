"""Base class of ops."""
import traceback
import typing as t
from abc import ABCMeta, abstractmethod
from collections.abc import Iterator
from enum import Enum

from loguru import logger

from juju_spell.utils import flatten

from .result import DefaultOpsOutput, OpsOutput, OpsResult


class OpsLevel(Enum):
    """OpsLevel represent the target resource own."""

    CONTROLLER = "CONTROLLER"
    MODEL = "MODEL"


class OpsType(Enum):
    """OpsType represent type of ops."""

    NORMAL = "NORMAL"
    DRY_RUN = "DRY_RUN"
    PRECHECK = "PRECHECK"


class Ops(metaclass=ABCMeta):
    """Basic operation unit."""

    _level: OpsLevel = OpsLevel.CONTROLLER
    _must_success: bool = False
    _type: OpsType = OpsType.NORMAL
    _name: str | None = None

    def __init__(
        self,
        level: OpsLevel | None = None,
        must_success: bool | None = None,
        type_: OpsType | None = None,
        name: str | None = None,
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
            output: OpsOutput | bool = await self._run(*args, **kwargs)
            if not isinstance(output, OpsOutput) or not isinstance(output, bool):
                output = DefaultOpsOutput(value=output)
            return OpsResult(output=output)
        except Exception as err:  # pylint: disable=broad-except
            logger.warning(traceback.format_exc())
            return OpsResult(err=err)

    @abstractmethod
    async def _run(
        self,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> OpsOutput | bool | t.Any:
        pass

    @property
    def info(self) -> str:
        """Return information string of ops."""
        return self._name if self._name is not None else self.__class__.__name__

    @property
    def level(self) -> OpsLevel:
        """Return OpsLevel."""
        return self._level

    @property
    def must_success(self) -> bool:
        """Does this ops need to success."""
        if self._type == OpsType.PRECHECK:
            return True
        return self._must_success

    @property
    def type_(self) -> OpsType:
        """Return self._type."""
        return self._type


OPS = t.TypeVar(
    "OPS", bound=t.Union[Ops, "ComposeOps"]  # pylint: disable=consider-alternative-union-syntax
)


class ComposeOps(t.Generic[OPS]):
    """Composeable operation unit."""

    list_ops: list[OPS] = []

    def __init__(self, *args: list[OPS]):
        self.list_ops = list(flatten([self.list_ops, *args]))

    def __iter__(self) -> Iterator:
        for obj in self.list_ops:
            yield obj
