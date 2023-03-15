import pprint
import typing as t

from loguru import logger

from juju_spell.assignment import RunResult


class OutputHandler:
    results: t.List[RunResult] = []

    def call(self, result: RunResult) -> None:
        self.results.append(result)

    def print(self) -> None:
        for result in self.results:
            logger.info(pprint.pformat(result))
