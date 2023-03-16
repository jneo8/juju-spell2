"""Define return result classes."""
import dataclasses
import typing as t


@t.runtime_checkable
@dataclasses.dataclass(frozen=True)
class OpsOutput(t.Protocol):
    """The parent class of opt._run output."""


@dataclasses.dataclass(frozen=True)
class DefaultOpsOutput(OpsOutput):
    """Default output."""

    value: t.Any


@dataclasses.dataclass(frozen=True)
class OpsResult:
    """Return result class of ops.__call__."""

    err: Exception | None = None
    output: bool | OpsOutput | None = None

    @property
    def success(self) -> bool:
        """Does this result success?"""
        if self.err is not None:
            return False
        return True
