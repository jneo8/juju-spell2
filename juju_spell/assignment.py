import typing as t
from juju_spell.ops import Ops, OpsLevel, ComposeOps
from loguru import logger

from juju_spell.asyncio import run_async
from juju.controller import Controller
from juju_spell.settings import Settings


class Runner:
    @classmethod
    def run(
        cls,
        compose_ops: ComposeOps,
        settings: Settings,
    ):
        return run_async(cls._loop(compose_ops, settings))

    @classmethod
    async def _loop_ctr(
        cls,
        ctr: Controller,
        compose_ops: ComposeOps,
        settings: Settings,
        ctr_settings,
    ):
        logger.info(compose_ops)
        # Iterate over ops
        for ops in compose_ops:
            logger.info((ops, ctr_settings.safe_output))
            await ops(ctr=ctr)
            if isinstance(ops, ComposeOps):
                await _run(controller=controller, compose_ops=compose_ops)
            elif ops.level == OpsLevel.CONTROLLER:
                result = await ops(ctr=ctr)
            elif ops.level == OpsLevel.MODEL:
                pass  # TODO

    @classmethod
    async def _loop(
        cls,
        compose_ops: ComposeOps,
        settings: Settings,
    ):
        for ctr_settings in settings.controllers:
            ctr = Controller()
            try:
                # Get controller connection
                await ctr._connector.connect(
                    username=ctr_settings.user,
                    password=ctr_settings.password,
                    endpoint=ctr_settings.endpoint,
                    cacert=ctr_settings.ca_cert,
                )
                await cls._loop_ctr(
                    ctr=ctr, compose_ops=compose_ops, settings=settings, ctr_settings=ctr_settings
                )
            except Exception as e:
                logger.error(e)
            finally:
                await ctr.disconnect()
