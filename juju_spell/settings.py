import logging
import os
import pathlib
import typing as t

from loguru import logger
from pydantic import BaseModel, BaseSettings, validator

BASE_DIR = pathlib.Path(__file__).parent
DEFAULT_CONFIG_DIR = BASE_DIR.parent
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.yaml"


class CtrSettings(BaseModel):
    name: str
    uuid: str
    user: str
    password: str
    endpoint: str
    ca_cert: str

    @property
    def safe_output(self) -> t.Dict[str, t.Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "endpoint": self.endpoint,
        }


class WorkerSettings(BaseModel):
    parallel: bool = False


class Settings(BaseSettings):
    controllers: t.List[CtrSettings]
    worker: WorkerSettings = WorkerSettings()


def get_settings(data: t.Dict[t.Any, t.Any]) -> Settings:
    return Settings(**data)
