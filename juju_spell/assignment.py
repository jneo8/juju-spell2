import contextvars
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


DONE = "DONE"

ctx_run_result = contextvars.ContextVar('run_result')


@dataclasses.dataclass
class RunResult:
    target: uuid.UUID
    ops: Ops
    result: OpsResult
    id: uuid.UUID = dataclasses.field(default_factory=lambda: uuid.uuid4())


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
        self._id = uuid.uuid4().hex
        self._settings = settings
        self._work_settings = WorkerSettings
        self._ops_queue = ops_queue
        self._result_queue = result_queue
        self._ctr: Controller
        self._options = options
        self.logger = logger.bind(id=self._id, _type="worker")
        self.logger.debug(f"Init worker for ctr {self.ctr_uuid}")

    @property
    def id(self):
        return self._id

    @property
    def ctr_uuid(self):
        return self._settings.uuid

    async def build_conn(self):
        self._ctr = Controller()
        await self._ctr._connector.connect(
            username=self._settings.user,
            password=self._settings.password,
            endpoint=self._settings.endpoint,
            cacert=self._settings.ca_cert,
        )
        self._ctr._connector.controller_uuid = self._settings.uuid
        self._ctr._connector.controller_name = self._settings.name

    async def start(
        self,
    ):
        try:
            await self.build_conn()
            while True:
                ops = await self._ops_queue.get()
                if ops is DONE:  # End of queue
                    break
                self.logger.debug(f"Get ops {ops.__class__.__name__}")
                results = await self._exec_ops(ops)
                for result in results:
                    self._result_queue.put_nowait(result)
                self._ops_queue.task_done()
        except asyncio.CancelledError:
            self.logger.debug(f"Cancel")
        except Exception as e:
            self.logger.error(traceback.format_exc())
            raise e
        finally:
            self._result_queue.put_nowait(DONE)  # Signal to tell receiver finish.
            await self._release_resource()
            self.logger.info("Worker finish")

    async def _release_resource(self):
        logger.debug("Release resource")
        if self._ctr:
            await self._ctr.disconnect()

    async def _exec_ops(self, ops) -> t.List[RunResult]:
        if ops.level == OpsLevel.CONTROLLER:
            result = await ops(ctr=self._ctr)
            run_result = self.format_run_result(target=self.ctr_uuid, ops=ops, result=result)
            ctx_run_result.set(run_result)
            return [run_result]
        elif ops.level == OpsLevel.MODEL:
            results = await self._loop_models(ops)
            return results

    async def _loop_models(self, ops: Ops):
        model_names = await self._get_model_names(models=self._options.models)

        results = []
        async for model_name, model in self._model_async_generator(model_names=model_names):
            self.logger.debug((model_name, ops.__class__.__name__))
            result = await ops(model=model)
            run_result = self.format_run_result(target=self.ctr_uuid, ops=ops, result=result)
            ctx_run_result.set(run_result)
            results.append(run_result)
        return results

    async def _get_model_names(self, models: t.Optional[t.List[str]] = []) -> t.List[str]:
        exists_model_names = await self._ctr.list_models()
        if len(models) <= 0:  # Filter not provides
            self.logger.debug("Model filter not provided. Get all models from controller")
            return exists_model_names
        return set(models).intersection(exists_model_names)

    async def _model_async_generator(
        self, model_names: t.List[str]
    ) -> t.AsyncGenerator[t.Tuple[str, Model], None]:
        for model_name in model_names:
            model = await self._ctr.get_model(model_name)
            yield model_name, model
            await model.disconnect()

    @staticmethod
    def format_run_result(target, ops: Ops, result: OpsResult):
        return RunResult(target=target, ops=ops, result=result)


class Receiver:
    def __init__(
        self,
        queue: asyncio.Queue,
        output_handler: t.Optional[t.Callable] = None,
    ):
        self._id = uuid.uuid4().hex
        self._queue = queue
        self._output_handler = output_handler
        self.logger = logger.bind(id=self._id, _type="receiver")
        self.logger.debug(f"Init receiver {self._id}")

    async def start(self, worker_num: int = 1):
        self.logger.debug(f"Receiver Start, worker_num: {worker_num}")
        done_worker = 0
        try:
            while True:
                result = await self._queue.get()
                if result is DONE:
                    done_worker += 1
                    if done_worker == worker_num:
                        break
                    else:
                        continue
                assert isinstance(result, RunResult)
                if self._output_handler:
                    self._output_handler(result)
                else:
                    self.logger.debug(result)
                self._queue.task_done()
        except asyncio.CancelledError:
            self.logger.debug("Cancel")
        finally:
            self.logger.debug("Receiver Finish")

    @property
    def id(self):
        return self._id

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
        self.output_handler = output_handler

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
        receiver = Receiver(result_queue, output_handler=self.output_handler)

        if self.settings.worker.parallel:
            asyncio.run(self._parallel(workers, receiver, ops_queues))
        if not self.settings.worker.parallel:
            asyncio.run(self._serial(workers, receiver, ops_queues))
        for ops_queue in ops_queues:
            logger.debug(ops_queue.qsize())
        logger.debug(result_queue.qsize())

    async def _parallel(self, workers, receiver, ops_queues):
        receiver_task = asyncio.create_task(receiver.start(len(workers)))

        worker_tasks = []
        for idx, worker in enumerate(workers):
            queue = ops_queues[idx]
            worker_task = asyncio.create_task(worker.start())
            worker_tasks.append(worker_task)
            for ops in self.compose_ops:
                queue.put_nowait(ops)
            queue.put_nowait(DONE)  # The end of ops
        await asyncio.gather(*worker_tasks, receiver_task)

    async def _serial(self, workers, receiver, ops_queues):
        receiver_task = asyncio.create_task(receiver.start())

        for idx, worker in enumerate(workers):
            queue = ops_queues[idx]
            worker_task = asyncio.create_task(worker.start())

            for ops in self.compose_ops:
                queue.put_nowait(ops)
            queue.put_nowait(DONE)  # The end of ops

            await worker_task
        await receiver_task
        await asyncio.gather(receiver_task)
