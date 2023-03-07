import typing as t
from juju_spell.ops import Ops, OpsLevel
from loguru import logger

from juju.controller import Controller
from juju_spell.settings import Settings


async def run(
    list_ops: t.List[Ops],
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

            # Iterate over ops
            for ops in list_ops:
                logger.info((ops, ctr_settings.safe_output))
                if ops.level == OpsLevel.CONTROLLER:
                    output = await ops.run(ctr=ctr)
                    logger.debug(output)
                elif ops.level == OpsLevel.MODEL:
                    pass  # TODO
        except Exception as e:
            logger.error(e)
        finally:
            await ctr.disconnect()
