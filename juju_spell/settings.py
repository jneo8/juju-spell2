import pathlib
import os
import logging
import typing as t
from loguru import logger

from pydantic import BaseModel, BaseSettings, validator


BASE_DIR = pathlib.Path(__file__).parent
DEFAULT_CONFIG_DIR = BASE_DIR.parent
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.yaml"


class Controller(BaseModel):
    name: str
    uuid: str
    user: str
    password: str
    endpoint: str
    ca_cert: str

    @property
    def safe_output(self):
        return {
            "uuid": self.uuid,
            "name": self.name,
            "endpoint": self.endpoint,
        }


class Settings(BaseSettings):
    controllers: t.List[Controller] = []

def get_settings(data):
    return Settings(**data)
