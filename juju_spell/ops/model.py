import dataclasses
import typing as t

from juju.model import Model

from .base import ComposeOps, Ops, OpsLevel
from .result import OpsOutput


@dataclasses.dataclass(frozen=True)
class ModelConfigOutput(OpsOutput):
    config: t.Dict[str, t.Any]


class _ModelConfigOps(Ops):
    level = OpsLevel.MODEL

    async def _run(self, model: Model, *args: t.Any, **kwargs: t.Any) -> ModelConfigOutput:
        result = await model.get_config()
        return ModelConfigOutput(config=result)


ModelConfigOps: ComposeOps = ComposeOps([_ModelConfigOps()])
