import typing as t
from types import SimpleNamespace
from collections.abc import Generator

from juju.controller import Controller
from juju.model import Model

__all__ = ["Namespace", "flatten", "ModelFilterMixin"]


class Namespace(SimpleNamespace):
    pass


def flatten(items: t.List[t.Any]) -> Generator:
    """Flatten arbitrarily nested iterable items."""
    for i in items:
        if hasattr(i, "__iter__"):
            for j in flatten(i):
                yield j
        else:
            yield i


class ModelFilterMixin:
    async def get_model_names(self, ctr: Controller, models: t.List[str] = []) -> t.Set[str]:
        exists_model_names = await ctr.list_models()
        if len(models) <= 0:  # Filter not provides
            return exists_model_names
        return set(models).intersection(exists_model_names)

    async def model_async_generator(
        self, ctr: Controller, models: t.List[str]
    ) -> t.AsyncGenerator[t.Tuple[str, Model], None]:
        model_names = await self.get_model_names(ctr=ctr, models=models)
        for model_name in model_names:
            model = await ctr.get_model(model_name)
            yield model_name, model
            await model.disconnect()
