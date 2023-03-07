from abc import ABCMeta, abstractmethod
from enum import Enum

from loguru import logger
from juju.controller import Controller

class OpsLevel(Enum):

    CONTROLLER = "CONTROLLER"
    MODEL = "MODEL"


class Ops(metaclass=ABCMeta):

    level: OpsLevel = OpsLevel.CONTROLLER

    @staticmethod
    @abstractmethod
    async def run(cls):
        pass


class PingOps(Ops):


    @staticmethod
    async def run(ctr: Controller):
        ctr.is_connected()
        return True
