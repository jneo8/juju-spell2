"""Dependency injector container."""
from dependency_injector import containers, providers

from juju_spell.settings import get_settings


class Container(containers.DeclarativeContainer):
    """Dependency container."""

    _settings = providers.Configuration()
    settings = providers.Singleton(
        get_settings,
        _settings,
    )
