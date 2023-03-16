"""Settings."""
import pathlib
import typing as t

from pydantic import BaseModel, BaseSettings

BASE_DIR = pathlib.Path(__file__).parent
DEFAULT_CONFIG_DIR = BASE_DIR.parent
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.yaml"


class CtrSettings(BaseModel):
    """Settings for controllers."""

    name: str
    uuid: str
    user: str
    password: str
    endpoint: str
    ca_cert: str

    @property
    def safe_output(self) -> dict[str, t.Any]:
        """Output without sensitive information."""
        return {
            "uuid": self.uuid,
            "name": self.name,
            "endpoint": self.endpoint,
        }


class WorkerSettings(BaseModel):
    """Settings for worker."""

    parallel: bool = False


class Settings(BaseSettings):
    """Settings."""

    controllers: list[CtrSettings]
    worker: WorkerSettings = WorkerSettings()


def get_settings(data: dict[t.Any, t.Any]) -> Settings:
    """Simple factory for Settings."""
    return Settings(**data)
