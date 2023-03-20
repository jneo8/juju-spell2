"""Assignment helper."""
from collections.abc import AsyncGenerator

from juju.controller import Controller
from juju.model import Model

__all__ = ["ModelMixin"]


class ModelMixin:
    """Mixin class for juju model connection and filter."""

    async def get_model_names(self, ctr: Controller, models: list[str] | None = None) -> set[str]:
        """Model name filter."""
        exists_model_names = await ctr.list_models()
        if models is None or len(models) <= 0:  # Filter not provides
            return exists_model_names
        return set(models).intersection(exists_model_names)

    async def model_async_generator(
        self, ctr: Controller, models: list[str]
    ) -> AsyncGenerator[tuple[str, Model], None]:
        """Async generator build connection to juju model and returns model_name and juju model."""
        model_names = await self.get_model_names(ctr=ctr, models=models)
        for model_name in model_names:
            model = await ctr.get_model(model_name)
            yield model_name, model
            await model.disconnect()
