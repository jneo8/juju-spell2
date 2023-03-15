from dependency_injector import containers, providers

from juju_spell.settings import Settings, get_settings


class Container(containers.DeclarativeContainer):
    _settings = providers.Configuration()
    settings = providers.Singleton(
        get_settings,
        _settings,
    )
