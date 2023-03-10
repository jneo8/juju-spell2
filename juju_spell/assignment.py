import traceback
import typing as t
import dataclasses
import uuid
from juju_spell.ops import Ops, OpsLevel, ComposeOps, OpsResult
from loguru import logger

from juju_spell.utils import Namespace
from juju_spell.asyncio import run_async
from juju.controller import Controller
from juju.model import Model
from juju_spell.settings import Settings
from juju_spell.settings import Controller as CtrSettings


@dataclasses.dataclass
class Run:
    target: uuid.UUID
    ops: Ops
    result: OpsResult
    id: uuid.UUID = dataclasses.field(default_factory=lambda: str("abc"))


class Runner:
    def __init__(
        self,
        ops: t.Union[ComposeOps, Ops],
        settings: Settings,
        options: t.Optional[Namespace] = None,
    ):
        if isinstance(ops, Ops):
            ops = ComposeOps([ops])
        assert isinstance(ops, ComposeOps)
        self.compose_ops = ops
        self.options = Namespace() if options is None else options
        self.settings = settings
        self.result: t.List[Run] = []

    def __call__(self):
        logger.info(f"Run parallel: {self.settings.parallel}")
        if self.settings.parallel:
            tasks = []
            for ctr_settings in self.settings.controllers:
                settings = self.settings.copy()
                settings.controllers = [ctr_settings]
                tasks.append(
                    self._loop(ops=self.compose_ops, options=self.options, settings=settings),
                )
            run_async(tasks)
        else:
            self._loop(ops=self.compose_ops, options=self.options, settings=self.settings),
        return self.result

    def add_result(self, target, ops: Ops, result: OpsResult):
        self.result.append(Run(target=target, ops=ops, result=result))

    async def get_model_names(
        self, ctr: Controller, models: t.Optional[t.List[str]] = []
    ) -> t.List[str]:
        exists_model_names = await ctr.list_models()
        if len(models) <= 0:  # Filter not provides
            logger.debug("Model filter not provided. Get all models from controller")
            return exists_model_names
        return set(models).intersection(exists_model_names)

    async def model_async_generator(
        self, ctr: Controller, model_names: t.List[str]
    ) -> t.AsyncGenerator[t.Tuple[str, Model], None]:
        for model_name in model_names:
            model = await ctr.get_model(model_name)
            logger.debug(model)
            yield model_name, model
            await model.disconnect()

    async def _loop_model(
        self,
        ctr: Controller,
        ops: Ops,
        settings: Settings,
        ctr_settings: CtrSettings,
        options: Namespace,
    ):
        model_names = await self.get_model_names(ctr=ctr, models=options.models)

        async for model_name, model in self.model_async_generator(
            ctr=ctr, model_names=model_names
        ):
            logger.debug((model_name, ops.__name__))
            result = await ops(model=model, settings=settings, options=options)
            self.add_result(ops=ops, result=result, target=ctr.controller_uuid)

    async def _loop_ctr(
        self,
        ctr: Controller,
        compose_ops: ComposeOps,
        ctr_settings: CtrSettings,
        options: Namespace,
    ):
        logger.info(compose_ops)
        # Iterate over ops
        for ops in compose_ops:
            logger.info((ops, ctr_settings.safe_output))
            if isinstance(ops, ComposeOps):
                result = await self._loop_ctr(
                    ctr=ctr,
                    compose_ops=compose_ops,
                    ctr_settings=ctr_settings,
                    options=options,
                )
            elif ops.level == OpsLevel.CONTROLLER:
                result = await ops(ctr=ctr)
                self.add_result(ops=ops, result=result, target=ctr.controller_uuid)
            elif ops.level == OpsLevel.MODEL:
                await self._loop_model(
                    ctr=ctr,
                    ops=ops,
                    ctr_settings=ctr_settings,
                    options=options,
                )

    async def _loop(
        self,
        ops: t.Union[Ops, ComposeOps],
        options: Namespace,
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
                ctr._connector.controller_uuid = ctr_settings.uuid
                ctr._connector.controller_name = ctr_settings.name

                await self._loop_ctr(
                    ctr=ctr,
                    compose_ops=ops,
                    ctr_settings=ctr_settings,
                    options=options,
                )
            except Exception as e:
                logger.error(traceback.format_exc())
            finally:
                await ctr.disconnect()
