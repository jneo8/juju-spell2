import typing as t
import pprint

from loguru import logger

from juju_spell.assignment import RunResult


class OutputHandler:
    results: t.List[RunResult] = []

    def call(self, result):
        self.results.append(result)

    def print(self):
        for result in self.results:
            logger.info(pprint.pformat(result))
