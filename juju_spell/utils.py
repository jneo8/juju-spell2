import typing as t
from juju.controller import Controller
from juju.model import Model

__all__ = ["Namespace", "flatten", "ModelFilterMixin"]


class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def flatten(items):
    """Flatten arbitrarily nested iterable items."""
    for i in items:
        if hasattr(i, '__iter__'):
            for j in flatten(i):
                yield j
        else:
            yield i


class ModelFilterMixin:
    async def _get_model_names(
        self, ctr: Controller, models: t.Optional[t.List[str]] = []
    ) -> t.List[str]:
        exists_model_names = await ctr.list_models()
        if len(models) <= 0:  # Filter not provides
            return exists_model_names
        return set(models).intersection(exists_model_names)

    async def _model_async_generator(
        self, ctr: Controller, model_names: t.List[str]
    ) -> t.AsyncGenerator[t.Tuple[str, Model], None]:
        for model_name in model_names:
            model = await ctr.get_model(model_name)
            yield model_name, model
            await model.disconnect()
