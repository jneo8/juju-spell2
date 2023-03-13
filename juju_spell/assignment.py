import traceback
import typing as t
import dataclasses
import asyncio
import uuid
from juju_spell.ops import Ops, OpsLevel, ComposeOps, OpsResult
from loguru import logger

from juju_spell.utils import Namespace
from juju_spell.asyncio import run_async
from juju.controller import Controller
from juju.model import Model
from juju_spell.settings import Settings, WorkerSettings, CtrSettings


@dataclasses.dataclass
class RunResult:
    target: uuid.UUID
    ops: Ops
    result: OpsResult
    id: uuid.UUID = dataclasses.field(default_factory=lambda: str("abc"))


class Worker:
    """Run worker for single controller."""

    def __init__(
        self,
        settings: CtrSettings,
        work_settings: WorkerSettings,
        ops_queue: asyncio.Queue,
        result_queue: asyncio.Queue,
        options: Namespace,
    ):
        self._uuid = uuid.uuid4()
        self._settings = settings
        self._work_settings = WorkerSettings
        self._ops_queue = ops_queue
        self._result_queue = result_queue
        self._ctr: Controller
        self._options = options
        logger.debug(f"Init worker {self.uuid} for ctr {self.ctr_uuid}")

    @property
    def uuid(self):
        return self._uuid

    @property
    def ctr_uuid(self):
        return self._settings.uuid

    async def start(
        self,
    ):
        self._ctr = Controller()
        try:
            await self._ctr._connector.connect(
                username=self._settings.user,
                password=self._settings.password,
                endpoint=self._settings.endpoint,
                cacert=self._settings.ca_cert,
            )
            self._ctr._connector.controller_uuid = self._settings.uuid
            self._ctr._connector.controller_name = self._settings.name
            while True:
                ops = await self._ops_queue.get()
                logger.debug(f"Worker {self.uuid} {ops.__name__}")
                result = await self.exec_ops(ops)
                self._result_queue.put_nowait(ops)
                self._ops_queue.task_done()
        except asyncio.CancelledError:
            logger.info(f"Cancel worker {self.uuid}")
        except Exception as e:
            logger.error(traceback.format_exc())
        finally:
            await self._ctr.disconnect()

    async def exec_ops(self, ops):
        if ops.level == OpsLevel.CONTROLLER:
            result = await ops(ctr=self._ctr)
            return result
        elif ops.level == OpsLevel.MODEL:
            await self._loop_models(ops)

    async def _loop_models(self, ops: Ops):
        model_names = await self.get_model_names(models=self._options.models)

        async for model_name, model in self.model_async_generator(model_names=model_names):
            logger.debug((model_name, ops.__name__))
            result = await ops(model=model)

    async def get_model_names(self, models: t.Optional[t.List[str]] = []) -> t.List[str]:
        exists_model_names = await self._ctr.list_models()
        if len(models) <= 0:  # Filter not provides
            logger.debug("Model filter not provided. Get all models from controller")
            return exists_model_names
        return set(models).intersection(exists_model_names)

    async def model_async_generator(
        self, model_names: t.List[str]
    ) -> t.AsyncGenerator[t.Tuple[str, Model], None]:
        for model_name in model_names:
            model = await self._ctr.get_model(model_name)
            logger.debug(model)
            yield model_name, model
            await model.disconnect()

    @staticmethod
    def format_run_result(target, ops: Ops, result: OpsResult):
        return RunResult(target=target, ops=ops, result=result)

    def add_result(self, target, ops: Ops, result: OpsResult):
        self.result.append(format_run_result(target=target, ops=ops, result=result))


class Receiver:
    def __init__(
        self,
        queue: asyncio.Queue,
    ):
        self._uuid = uuid.uuid4()
        self._queue = queue
        logger.debug(f"Init receiver {self.uuid}")

    async def start(self):
        logger.debug("Receiver Start")
        n = 0
        try:
            while True:
                n += 1
                logger.debug(n)
                result = await self._queue.get()
                logger.debug(f"Receiver {self.uuid} {result.__name__}")
                self._queue.task_done()
        except asyncio.CancelledError:
            pass

    @property
    def uuid(self):
        return self._uuid

    @property
    def queue(self):
        return self._queue


class Runner:
    def __init__(
        self,
        ops: t.Union[ComposeOps, Ops],
        settings: Settings,
        options: t.Optional[Namespace] = None,
        output_handler: t.Optional[t.Callable] = None,
    ):
        if isinstance(ops, Ops):
            ops = ComposeOps([ops])
        assert isinstance(ops, ComposeOps)
        self.compose_ops = ops
        self.options = Namespace() if options is None else options
        self.settings = settings
        self.result: t.List[Run] = []

    def __call__(self):
        logger.info(f"Run parallel: {self.settings.worker.parallel}")
        result_queue = asyncio.Queue()

        workers = []
        ops_queues = []
        for ctr_settings in self.settings.controllers:
            ops_queue = asyncio.Queue()
            worker = Worker(
                settings=ctr_settings,
                work_settings=self.settings.worker,
                ops_queue=ops_queue,
                result_queue=result_queue,
                options=self.options,
            )
            workers.append(worker)
            ops_queues.append(ops_queue)
        receiver = Receiver(result_queue)

        if self.settings.worker.parallel:
            asyncio.run(self._parallel(workers, receiver, ops_queues))
        if not self.settings.worker.parallel:
            asyncio.run(self._serial(workers, receiver, ops_queues))

    async def _parallel(self, workers, receiver, ops_queues):
        receiver_task = asyncio.create_task(receiver.start())

        worker_tasks = []
        for idx, worker in enumerate(workers):
            queue = ops_queues[idx]
            worker_task = asyncio.create_task(worker.start())
            worker_tasks.append(worker_task)
            for ops in self.compose_ops:
                queue.put_nowait(ops)

        for queue in ops_queues:
            await queue.join()
        for worker_task in worker_tasks:
            worker_task.cancel()
        await asyncio.gather(*worker_tasks)

        await receiver.queue.join()
        receiver_task.cancel()
        await asyncio.gather(receiver_task)

    async def _serial(self, workers, receiver, ops_queues):
        receiver_task = asyncio.create_task(receiver.start())

        for idx, worker in enumerate(workers):
            queue = ops_queues[idx]
            worker_task = asyncio.create_task(worker.start())

            for ops in self.compose_ops:
                queue.put_nowait(ops)

            await queue.join()
            worker_task.cancel()
            await asyncio.gather(worker_task)
        await receiver.queue.join()
        receiver_task.cancel()
        await asyncio.gather(receiver_task)

    def add_result(self, target, ops: Ops, result: OpsResult):
        self.result.append(Run(target=target, ops=ops, result=result))
