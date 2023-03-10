import typing as t
import dataclasses


@dataclasses.dataclass(frozen=True)
class OpsOutput(t.Protocol):
    pass


@dataclasses.dataclass(frozen=True)
class OpsResult:
    err: t.Optional[Exception] = None
    output: t.Optional[t.Union[bool, OpsOutput]] = None

    @property
    def success(self) -> bool:
        if self.err is not None:
            return False
        return True
